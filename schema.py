"""Pydantic schema for the Data Center Community Benefits Dashboard.

Single source of truth for all four record types: Company, Claim, Project,
CommunityResponse. Used by:
- Curators editing data/seed/*.json (validated on refresh).
- refresh.py (validates seed → emits docs/data/*.json).
- tests/test_schema.py (round-trip + edge cases).

All models use ConfigDict(extra="forbid") so any drift in the curated JSON
fails fast at refresh time, not at runtime in the browser.
"""

from __future__ import annotations

from datetime import date as Date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


# ---------------------------------------------------------------------------
# Canonical vocabularies
# ---------------------------------------------------------------------------

# Frozen for v1. Adding a 9th theme requires a backlog entry + migration of
# every existing claim (see CLAUDE.md > "Theme taxonomy").
THEMES: tuple[str, ...] = (
    "jobs",
    "tax_revenue",
    "energy",
    "water",
    "community_grants",
    "infrastructure",
    "education",
    "engagement",
)

THEME_LABELS: dict[str, str] = {
    "jobs": "Jobs",
    "tax_revenue": "Tax revenue",
    "energy": "Energy",
    "water": "Water",
    "community_grants": "Community grants",
    "infrastructure": "Infrastructure",
    "education": "Education",
    "engagement": "Engagement",
}

COMPANY_SLUGS: tuple[str, ...] = (
    "meta",
    "google",
    "microsoft",
    "amazon",
    "openai",
    "anthropic",
    "xai",
    "oracle",
)

PROJECT_STATUSES: tuple[str, ...] = ("announced", "construction", "operational")

STANCES: tuple[str, ...] = ("positive", "mixed", "negative")

CONSTITUENCIES: tuple[str, ...] = (
    "residents",
    "local_government",
    "ngo",
    "academic",
    "journalist",
    "regulator",
)


Theme = Literal[
    "jobs",
    "tax_revenue",
    "energy",
    "water",
    "community_grants",
    "infrastructure",
    "education",
    "engagement",
]
CompanySlug = Literal[
    "meta", "google", "microsoft", "amazon", "openai", "anthropic", "xai", "oracle"
]
ProjectStatus = Literal["announced", "construction", "operational"]
Stance = Literal["positive", "mixed", "negative"]
Constituency = Literal[
    "residents", "local_government", "ngo", "academic", "journalist", "regulator"
]


# ---------------------------------------------------------------------------
# Core record types
# ---------------------------------------------------------------------------


class _StrictBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Company(_StrictBase):
    """A hyperscaler operating data centers."""

    slug: CompanySlug
    name: str = Field(min_length=1)
    hq: str = Field(min_length=1, description="City, State (or City, Country) of HQ.")
    dedicated_page_url: Optional[HttpUrl] = Field(
        default=None,
        description="The company's published community/economic-impact page, if one exists.",
    )
    last_reviewed: Date = Field(
        description="Date a curator last reviewed this company's claims for staleness."
    )


class Metric(_StrictBase):
    """Optional structured value attached to a Claim for cross-company comparison."""

    value: float
    unit: str = Field(min_length=1, description="e.g. 'jobs', 'usd', 'gallons', 'mwh'")
    kind: Optional[str] = Field(
        default=None,
        description="Subcategory, e.g. 'construction' / 'operational' for jobs.",
    )


class Claim(_StrictBase):
    """A specific benefit claim made by a company. Quote verbatim — don't paraphrase."""

    id: str = Field(min_length=1)
    company_slug: CompanySlug
    theme: Theme
    statement: str = Field(
        min_length=1,
        description="Verbatim quote from the company. NOT a paraphrase.",
    )
    source_url: HttpUrl
    source_title: str = Field(min_length=1)
    captured_at: Date
    metric: Optional[Metric] = None
    project_id: Optional[str] = Field(
        default=None,
        description="If this claim is tied to a specific project, the project id.",
    )


class Project(_StrictBase):
    """An individual data center project."""

    id: str = Field(min_length=1, description="Format: '<company>-<city>-<short>'.")
    company_slug: CompanySlug
    name: str = Field(min_length=1)
    city: str = Field(min_length=1)
    state: str = Field(
        min_length=2, max_length=2, description="Two-letter US state code (or country code)."
    )
    country: str = Field(default="US", min_length=2, max_length=2)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    status: ProjectStatus
    announced_year: int = Field(ge=2000, le=2100)
    claimed_investment_usd: Optional[int] = Field(
        default=None, ge=0, description="Total announced capex, USD. Null if undisclosed."
    )
    claimed_jobs: Optional[int] = Field(
        default=None,
        ge=0,
        description="Combined construction + operational jobs as announced.",
    )
    notes: Optional[str] = None
    source_url: HttpUrl
    source_title: str = Field(min_length=1)
    captured_at: Date


class CommunityResponse(_StrictBase):
    """A documented community / journalist / regulator response to a project."""

    id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    date: Date
    stance: Stance
    constituency: Constituency
    summary: str = Field(
        min_length=1,
        description="1–2 sentences in neutral phrasing. NOT a quote — a brief synthesis.",
    )
    source_url: HttpUrl
    source_title: str = Field(min_length=1)
    single_source: bool = Field(
        default=False,
        description="True when this response is corroborated by only this one source.",
    )


# ---------------------------------------------------------------------------
# Top-level payloads (what refresh.py emits, what the frontend reads)
# ---------------------------------------------------------------------------


class CompaniesPayload(_StrictBase):
    generated_at: Date
    themes: list[str] = Field(default_factory=lambda: list(THEMES))
    companies: list[Company]


class ClaimsPayload(_StrictBase):
    generated_at: Date
    claims: list[Claim]

    @field_validator("claims")
    @classmethod
    def _ids_unique(cls, v: list[Claim]) -> list[Claim]:
        ids = [c.id for c in v]
        if len(ids) != len(set(ids)):
            dup = [i for i in ids if ids.count(i) > 1]
            raise ValueError(f"Duplicate claim ids: {sorted(set(dup))}")
        return v


class ProjectsPayload(_StrictBase):
    generated_at: Date
    projects: list[Project]

    @field_validator("projects")
    @classmethod
    def _ids_unique(cls, v: list[Project]) -> list[Project]:
        ids = [p.id for p in v]
        if len(ids) != len(set(ids)):
            dup = [i for i in ids if ids.count(i) > 1]
            raise ValueError(f"Duplicate project ids: {sorted(set(dup))}")
        return v


class ResponsesPayload(_StrictBase):
    generated_at: Date
    responses: list[CommunityResponse]

    @field_validator("responses")
    @classmethod
    def _ids_unique(cls, v: list[CommunityResponse]) -> list[CommunityResponse]:
        ids = [r.id for r in v]
        if len(ids) != len(set(ids)):
            dup = [i for i in ids if ids.count(i) > 1]
            raise ValueError(f"Duplicate response ids: {sorted(set(dup))}")
        return v


__all__ = [
    "THEMES",
    "THEME_LABELS",
    "COMPANY_SLUGS",
    "PROJECT_STATUSES",
    "STANCES",
    "CONSTITUENCIES",
    "Theme",
    "CompanySlug",
    "ProjectStatus",
    "Stance",
    "Constituency",
    "Company",
    "Metric",
    "Claim",
    "Project",
    "CommunityResponse",
    "CompaniesPayload",
    "ClaimsPayload",
    "ProjectsPayload",
    "ResponsesPayload",
]
