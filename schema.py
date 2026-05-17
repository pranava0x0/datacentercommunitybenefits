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
    # Non-hyperscaler developer/operator entities tracked from v1.1 onward.
    # Added when a non-hyperscaler announces a project at hyperscaler scale
    # AND publishes its own community-impact framing (the editorial gate).
    "wonder-valley",
    "qts",
    "nebius",
    "crusoe",
    "coreweave",
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
    "meta",
    "google",
    "microsoft",
    "amazon",
    "openai",
    "anthropic",
    "xai",
    "oracle",
    "wonder-valley",
    "qts",
    "nebius",
    "crusoe",
    "coreweave",
]
ProjectStatus = Literal["announced", "construction", "operational"]
Stance = Literal["positive", "mixed", "negative"]
Constituency = Literal[
    "residents", "local_government", "ngo", "academic", "journalist", "regulator"
]

# Delivered-vs-promised assessment (v1.13). One of four states:
#   delivered  — independent reporting confirms the commitment was met
#   partial    — partly delivered; meaningful progress but short of the stated scope
#   contested  — the company maintains it's delivering; another party documents shortfall
#   shortfall  — independent reporting documents the commitment was not delivered
# Honest curatorial gap (no assessment yet) is represented by `delivered = None`,
# not by adding a fifth "unknown" status — the absence is editorially valuable.
DELIVERED_STATUSES: tuple[str, ...] = ("delivered", "partial", "contested", "shortfall")
DeliveredStatus = Literal["delivered", "partial", "contested", "shortfall"]
DELIVERED_LABELS: dict[str, str] = {
    "delivered": "Delivered",
    "partial": "Partial",
    "contested": "Contested",
    "shortfall": "Shortfall",
}


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
    summary: Optional[str] = Field(
        default=None,
        description=(
            "Curated 1–2 paragraph synthesis of how this company frames data center "
            "community engagement. Surfaced in the Comparison view's company pop-out. "
            "An honest 'no published framework' is editorially valuable — don't paper "
            "over the gap with marketing language."
        ),
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


class Delivered(_StrictBase):
    """Curator assessment of whether the company's claim was actually delivered.

    The dashboard's blueprint framing implicitly assumes commitments translate
    to delivery, but for operational sites we have years of independent
    reporting to compare. This field surfaces that comparison.

    Editorial rules:
    - `summary` is a NEUTRAL 1-2 sentence synthesis — not adversarial framing,
      not a quote. Cite the source for the underlying evidence in `source_url`.
    - `status` is a curator judgment call (per Stance precedent — explicitly
      NOT algorithmic). Use `shortfall` only with strong corroboration.
    - `assessed_at` is when the curator made the call, distinct from the
      source's publication date.
    - Absent = no assessment yet. Don't fabricate a status to fill a row.
    """

    status: DeliveredStatus
    summary: str = Field(
        min_length=1,
        description=(
            "1-2 sentence neutral synthesis of the delivery evidence. "
            "NOT a quote, NOT adversarial — factual description."
        ),
    )
    source_url: HttpUrl
    source_title: str = Field(min_length=1)
    assessed_at: Date


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
    captured_at: Date = Field(
        description=(
            "Date the curator recorded this claim. Distinct from `published_at` "
            "(which is the source's own publication date when known). For "
            "evergreen company pages without a clear publication date, this is "
            "the only date available."
        ),
    )
    published_at: Optional[Date] = Field(
        default=None,
        description=(
            "Source publication date when known (press release date, blog post "
            "date, news article date). Frontend displays this if present, "
            "falling back to captured_at. Don't fabricate — only set when the "
            "source has a clear, citable publication date."
        ),
    )
    metric: Optional[Metric] = None
    project_id: Optional[str] = Field(
        default=None,
        description="If this claim is tied to a specific project, the project id.",
    )
    delivered: Optional[Delivered] = Field(
        default=None,
        description=(
            "Optional delivery assessment when independent reporting allows it. "
            "See Delivered docstring for editorial rules. Absent = no assessment "
            "captured yet (the dashboard treats this honestly as a gap, not as "
            "implied success)."
        ),
    )


class Project(_StrictBase):
    """An individual data center project."""

    @field_validator("at_a_glance", check_fields=False)
    @classmethod
    def _at_a_glance_keys_in_themes(cls, v):
        if v is None:
            return v
        unknown = set(v.keys()) - set(THEMES)
        if unknown:
            raise ValueError(
                f"at_a_glance keys must be in THEMES; got unknown: {sorted(unknown)}"
            )
        return v

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
    project_page_url: Optional[HttpUrl] = Field(
        default=None,
        description=(
            "The canonical project page on the company's official site, when one "
            "exists (e.g. https://datacenters.atmeta.com/location/<slug>/). "
            "Distinct from source_url, which is where THIS record was sourced — "
            "they often differ when source_url is a news article or press release."
        ),
    )
    acreage: Optional[float] = Field(
        default=None,
        ge=0,
        description="Physical site size in acres. Cumulative across phases when expanded.",
    )
    power_mw: Optional[float] = Field(
        default=None,
        ge=0,
        description="Total announced electrical capacity in megawatts. Latest known number.",
    )
    gpu_count: Optional[int] = Field(
        default=None,
        ge=0,
        description=(
            "Total announced AI accelerators (NVIDIA H100/H200/GB200, AMD MI300, "
            "AWS Trainium 2, Google TPU, etc.). Only fill when publicly disclosed; "
            "most owner-operator hyperscaler sites don't disclose this."
        ),
    )
    offtaker: Optional[str] = Field(
        default=None,
        description=(
            "The workload owner / tenant. For owner-operator sites, the operating "
            "company itself (e.g. 'Meta'). For colocation arrangements like Stargate "
            "Abilene or Project Rainier, the AI tenant ('OpenAI', 'Anthropic') — "
            "this is the field that disambiguates 'who is the compute actually for?'"
        ),
    )
    at_a_glance: Optional[dict[str, str]] = Field(
        default=None,
        description=(
            "Curator-written one-line per-theme summaries shown on the project "
            "Overview tab. Keys MUST be from the canonical THEMES vocabulary "
            "(jobs, tax_revenue, energy, water, community_grants, infrastructure, "
            "education, engagement). Values are 1-line plain-English phrases — "
            "e.g. 'Air-cooled, ~0 water use' or '5,000 construction / 500 ops'. "
            "Optional: when absent, the frontend auto-derives from the project's "
            "claims. When present, this curator-written copy WINS — it's an "
            "editorial override for the auto-derivation."
        ),
    )


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
    "DELIVERED_STATUSES",
    "DELIVERED_LABELS",
    "Theme",
    "CompanySlug",
    "ProjectStatus",
    "Stance",
    "Constituency",
    "DeliveredStatus",
    "Company",
    "Metric",
    "Delivered",
    "Claim",
    "Project",
    "CommunityResponse",
    "CompaniesPayload",
    "ClaimsPayload",
    "ProjectsPayload",
    "ResponsesPayload",
]
