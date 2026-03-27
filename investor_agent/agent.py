from __future__ import annotations

import csv
import time
from typing import Any

import pandas as pd

from .config import OUTPUT_CSV, SERPAPI_KEY, llm_provider
from .llm_client import extract_investors_from_page
from .serpapi_client import search_with_serpapi
from .utils import dedupe_records
from .web_fetcher import fetch_url_text

COLUMNS = [
    "query",
    "search_title",
    "investor_name",
    "investor_type",
    "investor_location_city",
    "investor_location_country",
    "investment_stage_min_usd",
    "investment_stage_max_usd",
    "focus_industries",
    "evidence_quote",
    "source_url",
]


class InvestorDataAgent:
    def __init__(self, *, output_csv: str | None = None, sleep_s: float = 1.0):
        if not SERPAPI_KEY:
            raise RuntimeError("SERPAPI_KEY missing. Set it in .env or environment variables.")
        self.output_csv = output_csv or OUTPUT_CSV
        self.sleep_s = float(sleep_s)

    def _save_csv(self, extracted: list[dict[str, Any]]) -> None:
        df = pd.DataFrame(extracted)
        if df.empty:
            df = pd.DataFrame(columns=COLUMNS)
        df.to_csv(self.output_csv, index=False, quoting=csv.QUOTE_MINIMAL)

    def run(
        self,
        query: str,
        *,
        max_results: int = 8,
        max_pages: int | None = None,
        provider: str | None = None,
        user_agent_max_chars: int = 12000,
    ) -> list[dict[str, Any]]:
        """
        Search the web, extract investor records, and save them to CSV.
        """

        # FIX 1: Normalize provider to lowercase to avoid "Gemini" != "gemini" mismatch
        provider = (provider or llm_provider()).lower()

        search_results = search_with_serpapi(SERPAPI_KEY, query, max_results=max_results)
        print(f"[INFO] Found {len(search_results)} search results.")

        page_count = 0
        extracted: list[dict[str, Any]] = []

        for r in search_results:
            if max_pages is not None and page_count >= max_pages:
                break

            page_count += 1
            print(f"[INFO] Fetching page {page_count}: {r.link}")

            try:
                page_text = fetch_url_text(r.link, max_chars=user_agent_max_chars)
            except Exception as e:
                # FIX 2: Log fetch failures instead of silently skipping
                print(f"[WARN] Fetch failed for {r.link}: {type(e).__name__}: {e}")
                continue

            if not page_text:
                print(f"[WARN] Empty page text for {r.link}")
                continue

            print(f"[INFO] Extracting investors from {r.link} ({len(page_text)} chars)")
            try:
                records = extract_investors_from_page(
                    user_query=query,
                    source_url=r.link,
                    page_text=page_text,
                    provider=provider,
                )
            except Exception as e:
                # FIX 3: Log extraction failures instead of silently skipping
                print(f"[ERROR] Extraction failed for {r.link}: {type(e).__name__}: {e}")
                continue

            print(f"[INFO] Extracted {len(records)} records from {r.link}")
            for rec in records:
                rec["query"] = query
                rec["search_title"] = r.title
            extracted.extend(records)

            time.sleep(self.sleep_s)

        extracted = dedupe_records(extracted)
        print(f"[INFO] Total records after dedup: {len(extracted)}")
        self._save_csv(extracted)
        return extracted

    def run_with_stats(
        self,
        query: str,
        *,
        max_results: int = 8,
        max_pages: int | None = None,
        provider: str | None = None,
        user_agent_max_chars: int = 12000,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:

        # FIX 1: Normalize provider to lowercase to avoid "Gemini" != "gemini" mismatch
        provider_used = (provider or llm_provider()).lower()

        search_results = search_with_serpapi(SERPAPI_KEY, query, max_results=max_results)

        stats: dict[str, Any] = {
            "provider_used": provider_used,
            "search_results_count": len(search_results),
            "max_results": max_results,
            "max_pages": max_pages,
            "pages_considered": 0,
            "pages_fetched_ok": 0,
            "pages_empty_text": 0,
            "pages_fetch_failed": 0,
            "pages_extraction_ok": 0,
            "pages_extraction_failed": 0,
        }

        page_count = 0
        extracted: list[dict[str, Any]] = []

        for r in search_results:
            if max_pages is not None and page_count >= max_pages:
                break

            page_count += 1
            stats["pages_considered"] += 1
            print(f"[INFO] Fetching page {page_count}: {r.link}")

            try:
                page_text = fetch_url_text(r.link, max_chars=user_agent_max_chars)
            except Exception as e:
                # FIX 2: Log fetch failures
                print(f"[WARN] Fetch failed for {r.link}: {type(e).__name__}: {e}")
                stats["pages_fetch_failed"] += 1
                continue

            if not page_text:
                print(f"[WARN] Empty page text for {r.link}")
                stats["pages_empty_text"] += 1
                continue

            stats["pages_fetched_ok"] += 1
            print(f"[INFO] Extracting investors from {r.link} ({len(page_text)} chars)")

            try:
                records = extract_investors_from_page(
                    user_query=query,
                    source_url=r.link,
                    page_text=page_text,
                    provider=provider_used,
                )
            except Exception as e:
                # FIX 3: Log extraction failures
                print(f"[ERROR] Extraction failed for {r.link}: {type(e).__name__}: {e}")
                stats["pages_extraction_failed"] += 1
                continue

            stats["pages_extraction_ok"] += 1
            print(f"[INFO] Extracted {len(records)} records from {r.link}")

            for rec in records:
                rec["query"] = query
                rec["search_title"] = r.title
            extracted.extend(records)
            time.sleep(self.sleep_s)

        extracted = dedupe_records(extracted)
        print(f"[INFO] Total records after dedup: {len(extracted)}")
        self._save_csv(extracted)

        return extracted, stats