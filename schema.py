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
    "crusoe",
    "coreweave",
    "prologis",
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
    "crusoe",
    "coreweave",
    "prologis",
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
# White House Ratepayer Protection Pledge (v1.15)
# ---------------------------------------------------------------------------
# On 2026-03-04 seven hyperscalers signed a (non-binding) pledge at the White
# House to independently fund the generation + grid-infrastructure costs of
# their data centers so those costs don't shift onto existing utility
# ratepayers. This is the real-world anchor for the "Ratepayer Protection
# Pledge" view. Facts (date + signatory roster) are fixed history, not a
# curator judgment call.
#
# RATEPAYER_PLEDGE_URL is the canonical White House proclamation, which lists
# the five commitments verbatim (quoted in docs/index.html). The signatory
# roster is corroborated by the WH fact sheet + DCD coverage.
#
# Signatory membership lives on Company.ratepayer_pledge_signatory (bool).
# The constants below are the single source of truth for the pledge metadata;
# the frontend mirrors RATEPAYER_PLEDGE_* and the status vocab (a test asserts
# parity, same pattern as THEMES / DELIVERED_STATUSES).
RATEPAYER_PLEDGE_DATE: str = "2026-03-04"
RATEPAYER_PLEDGE_NAME: str = "White House Ratepayer Protection Pledge"
RATEPAYER_PLEDGE_URL: str = (
    "https://www.whitehouse.gov/releases/2026/03/ratepayer-protection-pledge/"
)

# Per-project assessment of how a specific data center reflects the pledge.
# Deliberately NOT a pass/fail score (the dashboard doesn't do trust scores):
#   affirmed     — the company has published a SITE-SPECIFIC ratepayer/
#                  pay-our-own-way commitment for THIS data center (a verbatim
#                  claim, cited in evidence_claim_id).
#   pledge_only  — covered by the company's national pledge signature, but no
#                  site-specific affirmation has been captured for this site.
#   contested    — a credible third party (regulator/reporting) documents the
#                  site shifting costs to ratepayers despite the pledge.
# Absent = not assessed / out of cohort (e.g. announced before the pledge, or a
# non-signatory). Absence is honest — don't fabricate a status to fill a row.
RATEPAYER_STATUSES: tuple[str, ...] = ("affirmed", "pledge_only", "contested")
RatepayerStatus = Literal["affirmed", "pledge_only", "contested"]
RATEPAYER_LABELS: dict[str, str] = {
    "affirmed": "Site-specific commitment",
    "pledge_only": "National pledge only",
    "contested": "Contested",
}

# The five commitments listed verbatim in the White House Ratepayer Protection
# Pledge proclamation. Used as sub-keys in Ratepayer.principles so curators
# can record how each individual site addresses each specific commitment.
#
# Key vocabulary (frozen for v1):
#   new_generation  — "Building, bringing, or buying new power supply"
#   delivery_infra  — "Paying for new power delivery infrastructure upgrades"
#   separate_rate   — "Paying whether they use the power or not" (separate rate structures)
#   local_jobs      — "Investing in local job creation and workforce development"
#   grid_resilience — "Contributing to electric and community resilience"
PLEDGE_PRINCIPLES: tuple[str, ...] = (
    "new_generation",
    "delivery_infra",
    "separate_rate",
    "local_jobs",
    "grid_resilience",
)
PLEDGE_PRINCIPLE_LABELS: dict[str, str] = {
    "new_generation": "Building, bringing, or buying new power supply",
    "delivery_infra": "Paying for new power delivery infrastructure upgrades",
    "separate_rate": "Paying whether they use the power or not",
    "local_jobs": "Investing in local job creation and workforce development",
    "grid_resilience": "Contributing to electric and community resilience",
}

# Per-principle fulfillment status for a given site:
#   met       — first-party statement or regulatory filing confirms compliance
#   partial   — covered by national pledge signature only (no site-specific evidence)
#   not_met   — credible independent evidence of non-compliance
#   unknown   — insufficient information captured
PLEDGE_PRINCIPLE_STATUSES: tuple[str, ...] = ("met", "partial", "not_met", "unknown")
PledgePrincipleStatus = Literal["met", "partial", "not_met", "unknown"]


# ---------------------------------------------------------------------------
# Core record types
# ---------------------------------------------------------------------------


class _StrictBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PledgePrincipleAssessment(_StrictBase):
    """Per-principle fulfillment assessment for a single pledge commitment at a single site.

    `status` is the editorial judgment; `note` is a 1-sentence plain-English
    explanation of WHY that status applies to THIS site specifically — the
    site-specific evidence or honest acknowledgement of a gap.
    """

    status: PledgePrincipleStatus
    note: str = Field(
        min_length=1,
        description=(
            "1-sentence site-specific explanation: what evidence backs 'met', "
            "what the gap is for 'partial'/'unknown', what the evidence is for "
            "'not_met'. NOT generic — every note must be specific to this site."
        ),
    )


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
    ratepayer_pledge_signatory: bool = Field(
        default=False,
        description=(
            "True if this company signed the White House Ratepayer Protection "
            "Pledge (2026-03-04). Fixed historical fact, not a curator judgment: "
            "the seven signatories are Amazon, Google, Meta, Microsoft, OpenAI, "
            "Oracle, xAI. Non-signatories (incl. Anthropic and the tracked "
            "non-hyperscalers) stay False even when they publish their own "
            "ratepayer commitments — the flag means 'signed THE pledge', and the "
            "Ratepayer view surfaces non-signatory commitments separately."
        ),
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


class Ratepayer(_StrictBase):
    """Curator assessment of how a data center reflects the Ratepayer Protection Pledge.

    Attached to a Project (not a Claim) because the unit of analysis in the
    Ratepayer view is the SITE: "for this data center announced since the
    pledge, is there a ratepayer-protection commitment, and how strong is it?"

    Editorial rules:
    - Only meaningful for projects whose company is a pledge signatory and that
      were announced on/after RATEPAYER_PLEDGE_DATE. Don't attach it to
      pre-pledge or non-signatory sites — absence is the honest signal there.
    - `status` is a curator judgment call (per Delivered/Stance precedent —
      explicitly NOT algorithmic).
    - Use `affirmed` only when a SITE-SPECIFIC first-party commitment exists;
      point `evidence_claim_id` at the backing verbatim Claim.
    - `pledge_only` is the honest default for a signatory site with no
      site-specific affirmation captured — it is NOT a failing grade, just
      "covered by the national signature, nothing site-specific yet."
    - `summary` is a NEUTRAL 1-sentence synthesis, not adversarial, not a quote.
    """

    status: RatepayerStatus
    summary: str = Field(
        min_length=1,
        description="1-sentence neutral synthesis of how this site reflects the pledge.",
    )
    evidence_claim_id: Optional[str] = Field(
        default=None,
        description=(
            "For `affirmed`: the id of the site-specific first-party Claim that "
            "backs the assessment. Required for `affirmed`; omit for "
            "`pledge_only`. Validated against claims.json in refresh.py."
        ),
    )
    assessed_at: Date
    principles: Optional[dict[str, PledgePrincipleAssessment]] = Field(
        default=None,
        description=(
            "Optional per-principle assessment keyed on PLEDGE_PRINCIPLES slugs "
            "(new_generation, delivery_infra, separate_rate, local_jobs, grid_resilience). "
            "Each value is a PledgePrincipleAssessment with a status + site-specific note. "
            "Absent field = principles not yet assessed. "
            "For pledge_only sites: status='partial', note explains the gap. "
            "For affirmed sites: status='met' for principles backed by the evidence_claim."
        ),
    )

    @field_validator("principles", check_fields=False)
    @classmethod
    def _principles_keys_valid(
        cls, v: Optional[dict]
    ) -> Optional[dict]:
        if v is None:
            return v
        unknown_keys = set(v.keys()) - set(PLEDGE_PRINCIPLES)
        if unknown_keys:
            raise ValueError(
                f"principles keys must be in PLEDGE_PRINCIPLES; unknown: {sorted(unknown_keys)}"
            )
        return v


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
    announced_date: Optional[Date] = Field(
        default=None,
        description=(
            "Exact announcement date when known. More precise than announced_year; "
            "used in the CSV export. Leave null when only the year is confirmed."
        ),
    )
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
    ratepayer: Optional[Ratepayer] = Field(
        default=None,
        description=(
            "Optional Ratepayer Protection Pledge assessment for this site. Set "
            "only for pledge-signatory projects announced on/after the pledge "
            "date (see Ratepayer docstring). Absent = out of cohort or not yet "
            "assessed; the Ratepayer view treats absence honestly, not as a fail."
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
    "RATEPAYER_PLEDGE_DATE",
    "RATEPAYER_PLEDGE_NAME",
    "RATEPAYER_PLEDGE_URL",
    "RATEPAYER_STATUSES",
    "RATEPAYER_LABELS",
    "PLEDGE_PRINCIPLES",
    "PLEDGE_PRINCIPLE_LABELS",
    "PLEDGE_PRINCIPLE_STATUSES",
    "Theme",
    "CompanySlug",
    "ProjectStatus",
    "Stance",
    "Constituency",
    "DeliveredStatus",
    "RatepayerStatus",
    "PledgePrincipleStatus",
    "PledgePrincipleAssessment",
    "Company",
    "Metric",
    "Delivered",
    "Ratepayer",
    "Claim",
    "Project",
    "CommunityResponse",
    "CompaniesPayload",
    "ClaimsPayload",
    "ProjectsPayload",
    "ResponsesPayload",
]
