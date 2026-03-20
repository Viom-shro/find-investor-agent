from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class InvestorRecord(BaseModel):
    """One extracted investor entry from a web page."""

    investor_name: str = Field(..., description="Name of the investor (firm/person).")
    investor_type: str = Field(
        ...,
        description=(
            "Type of investor: VC, angel, corporate VC, PE, hedge fund, accelerator, family office, "
            "or other (use closest match)."
        ),
    )
    investor_location_city: str | None = Field(
        default=None, description="HQ city if mentioned."
    )
    investor_location_country: str | None = Field(
        default=None, description="HQ country if mentioned."
    )
    investment_stage_min_usd: str | None = Field(
        default=None,
        description="Minimum check size/stage in USD (as a string range value like '500000' or '0.5M').",
    )
    investment_stage_max_usd: str | None = Field(
        default=None,
        description="Maximum check size/stage in USD (as a string range value like '2000000' or '2M').",
    )
    focus_industries: str | None = Field(
        default=None,
        description="Comma-separated list of focus industries if present.",
    )
    evidence_quote: str | None = Field(
        default=None,
        description="Short quote/snippet from the page that supports the extraction.",
    )
    source_url: str = Field(..., description="URL where this information was found.")


class InvestorExtractionResult(BaseModel):
    """LLM extraction output for a single page."""

    records: list[InvestorRecord]


class AgentQuery(BaseModel):
    query: str = Field(..., description="User query in natural language.")
    country: str | None = Field(default=None, description="If extracted/overridden, target country.")
    industry: str | None = Field(default=None, description="If extracted/overridden, target industry.")
    investment_range: str | None = Field(default=None, description="If extracted/overridden, e.g. $500k–$2M.")

