from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from serpapi.google_search import GoogleSearch


@dataclass(frozen=True)
class SearchResult:
    title: str
    link: str
    snippet: str | None = None


def search_with_serpapi(api_key: str, query: str, max_results: int = 10) -> list[SearchResult]:
    """
    Web search using SerpAPI (Google results).

    Note: We do best-effort extraction; for each result we fetch page text separately.
    """

    num = max(1, min(int(max_results), 20))
    params: dict[str, Any] = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": num,
        "hl": "en",
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    organic = results.get("organic_results", []) or []
    out: list[SearchResult] = []
    for item in organic[:num]:
        link = item.get("link") or item.get("url")
        if not link:
            continue
        out.append(
            SearchResult(
                title=str(item.get("title") or ""),
                link=str(link),
                snippet=item.get("snippet"),
            )
        )

    return out

