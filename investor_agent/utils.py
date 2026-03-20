from __future__ import annotations

import re
from typing import Iterable


def normalize_whitespace(s: str | None) -> str | None:
    if s is None:
        return None
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s or None


def dedupe_records(records: list[dict]) -> list[dict]:
    """
    Dedupe by a stable identity: investor_name + source_url.
    """

    seen: set[str] = set()
    out: list[dict] = []
    for r in records:
        name = normalize_whitespace(r.get("investor_name"))
        url = normalize_whitespace(r.get("source_url"))
        if not name or not url:
            continue
        key = f"{name.lower()}|{url}"
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out

