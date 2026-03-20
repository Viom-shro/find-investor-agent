from __future__ import annotations

import os

from dotenv import load_dotenv


load_dotenv()


def _env(name: str, default: str | None = None) -> str | None:
    val = os.getenv(name, default)
    return val.strip() if isinstance(val, str) and val.strip() else val


SERPAPI_KEY = _env("SERPAPI_KEY")

OPENAI_API_KEY = _env("OPENAI_API_KEY")
GEMINI_API_KEY = _env("GEMINI_API_KEY")

OUTPUT_CSV = _env("OUTPUT_CSV", "investors.csv") or "investors.csv"


def llm_provider() -> str:
    """Pick LLM provider based on available keys."""

    if OPENAI_API_KEY:
        return "openai"
    if GEMINI_API_KEY:
        return "gemini"
    raise RuntimeError("No LLM API key found. Set OPENAI_API_KEY or GEMINI_API_KEY in .env.")

