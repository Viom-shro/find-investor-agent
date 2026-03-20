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


class InvestorDataAgent:
    def __init__(self, *, output_csv: str | None = None, sleep_s: float = 1.0):
        if not SERPAPI_KEY:
            raise RuntimeError("SERPAPI_KEY missing. Set it in .env or environment variables.")
        self.output_csv = output_csv or OUTPUT_CSV
        self.sleep_s = float(sleep_s)

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

        provider = provider or llm_provider()

        search_results = search_with_serpapi(SERPAPI_KEY, query, max_results=max_results)
        page_count = 0

        extracted: list[dict[str, Any]] = []
        for r in search_results:
            if max_pages is not None and page_count >= max_pages:
                break

            page_count += 1
            try:
                page_text = fetch_url_text(r.link, max_chars=user_agent_max_chars)
            except Exception:
                # Some sites can fail with unexpected parsing/network errors.
                continue
            if not page_text:
                continue

            try:
                records = extract_investors_from_page(
                    user_query=query,
                    source_url=r.link,
                    page_text=page_text,
                    provider=provider,
                )
            except Exception:
                # If extraction fails on this page, keep going with other pages.
                continue

            # Attach query metadata so the CSV is query-specific.
            for rec in records:
                rec["query"] = query
                rec["search_title"] = r.title
            extracted.extend(records)

            time.sleep(self.sleep_s)

        extracted = dedupe_records(extracted)

        # Normalize columns for CSV output.
        df = pd.DataFrame(extracted)
        if df.empty:
            df = pd.DataFrame(
                columns=[
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
            )
        df.to_csv(self.output_csv, index=False, quoting=csv.QUOTE_MINIMAL)
        return extracted

