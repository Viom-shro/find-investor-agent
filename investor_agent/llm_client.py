from __future__ import annotations

import re
from typing import Any

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableLambda

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from .config import llm_provider
from .schema import InvestorExtractionResult


def _safe_json_from_text(text: str) -> str:
    """Extract the first JSON object from a model response."""

    text = text.strip()
    # Common case: model returns just JSON.
    if text.startswith("{") and text.endswith("}"):
        return text

    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        raise ValueError("No JSON object found in LLM response.")
    return m.group(0)


def build_extraction_chain():
    parser = PydanticOutputParser(pydantic_object=InvestorExtractionResult)
    format_instructions = parser.get_format_instructions()

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=(
                    "You extract structured investor information from web page text. "
                    "Return ONLY JSON, matching the provided schema."
                )
            ),
            (
                "human",
                (
                    "User query: {user_query}\n\n"
                    "Source URL: {source_url}\n\n"
                    "Web page text (may be truncated):\n"
                    "{page_text}\n\n"
                    "Extraction rules:\n"
                    "- Only extract investors that match the user query intent (Fintech investors in India and the investment range if mentioned).\n"
                    "- If you cannot confirm investor name/type or investment size, still return the best possible fields but leave unknown fields as null.\n"
                    "- evidence_quote must be a short quote/snippet from the page text.\n"
                    "- Return empty array if nothing relevant.\n\n"
                    "{format_instructions}"
                ),
            ),
        ]
    )

    return prompt, parser


def extract_investors_from_page(
    *,
    user_query: str,
    source_url: str,
    page_text: str,
    provider: str | None = None,
    openai_model: str = "gpt-4o-mini",
    gemini_model: str = "gemini-2.5-flash",
) -> list[dict[str, Any]]:
    """
    Returns a list of InvestorExtractionResult.records as plain dicts.
    """

    if not provider:
        provider = llm_provider()

    prompt, parser = build_extraction_chain()

    if provider == "openai":
        llm = ChatOpenAI(model=openai_model, temperature=0)
    elif provider == "gemini":
        llm = ChatGoogleGenerativeAI(model=gemini_model, temperature=0)
    else:
        raise ValueError(f"Unknown provider: {provider}")

    chain = prompt | llm | RunnableLambda(lambda x: x.content)  # type: ignore[operator]

    raw = chain.invoke(
        {"user_query": user_query, "source_url": source_url, "page_text": page_text, "format_instructions": parser.get_format_instructions()}
    )

    json_str = _safe_json_from_text(raw)
    result = InvestorExtractionResult.model_validate_json(json_str)
    return [r.model_dump() for r in result.records]

