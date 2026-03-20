from __future__ import annotations

import re
from typing import Optional

import requests
from requests import RequestException
from bs4 import BeautifulSoup


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0 Safari/537.36"
)


def fetch_url_text(
    url: str,
    *,
    timeout_s: int = 20,
    max_chars: int = 12000,
    user_agent: str = DEFAULT_USER_AGENT,
) -> Optional[str]:
    """
    Best-effort HTML -> readable text for LLM extraction.

    Returns None if we can't fetch/parse.
    """

    headers = {"User-Agent": user_agent}
    try:
        resp = requests.get(url, headers=headers, timeout=timeout_s)
        # Avoid raising for some common anti-bot failures.
        if resp.status_code in (401, 403):
            return None
        if resp.status_code == 429:
            # Too many requests: skip for now (or add retry logic if needed).
            return None
        resp.raise_for_status()
    except RequestException:
        # Network error, TLS, DNS, etc. -> skip page.
        return None

    content_type = resp.headers.get("Content-Type", "")
    if "text" not in content_type and "html" not in content_type:
        # Avoid dumping binaries (pdf, images).
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove noisy elements.
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return None

    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[TRUNCATED]"

    return text

