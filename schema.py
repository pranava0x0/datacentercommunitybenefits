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
# ratepayers. QTS became the eighth signatory via the DOE companion track on
# 2026-04-24 (Energy Secretary Chris Wright's Cedar Rapids tour; KCRG / The
# Gazette coverage) — the first colocation operator to sign. This is the
# real-world anchor for the "Ratepayer Protection Pledge" view. Facts (dates +
# signatory roster) are fixed history, not a curator judgment call.
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
# Date QTS signed the DOE companion commitment (the eighth signatory). The
# frontend mirrors this for the roster note ("Signed with DOE on …").
RATEPAYER_PLEDGE_DOE_DATE: str = "2026-04-24"

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
# The Ratepayer Protection Pledge roster (v2, from the 2026-07-23 expansion).
#
# Categories mirror the stakeholder groups the White House page itself uses,
# with one deliberate split: the page lumps the 7 hyperscalers in with the
# data-center developers under a single "DATA CENTER" chip, but the two behave
# very differently for our purposes (hyperscalers are electricity BUYERS who
# signed in the March round; developers are builders who signed in July). The
# builder re-tags a roster row as `hyperscaler` when it resolves to a tracked
# Company that was already a March signatory.
#
# Frozen for v2 — adding a category = BACKLOG entry + the app.js mirror +
# a `--sig-<category>` color token in BOTH `:root` blocks, same drill as
# THEMES / DELIVERED_STATUSES / RATEPAYER_STATUSES.
SIGNATORY_CATEGORIES: tuple[str, ...] = (
    "hyperscaler",
    "utility",
    "cooperative",
    "developer",
    "governor",
)
SIGNATORY_CATEGORY_LABELS: dict[str, str] = {
    "hyperscaler": "Hyperscaler / AI company",
    "utility": "Utility",
    "cooperative": "Cooperative",
    "developer": "Data-center developer",
    "governor": "Governor",
}

# Which signing event a roster row belongs to. `signed_date` carries the exact
# day; the track is what makes the cohort legible ("March round" vs "July
# expansion") and drives pledge-era eligibility in the scorecard.
SIGNATORY_TRACKS: tuple[str, ...] = (
    "white-house-2026-03-04",  # the original 7 hyperscalers
    "doe-2026-04-24",  # QTS, via the DOE companion track
    "expansion-2026-07-23",  # the EPA-HQ event cohort + governors' addendum
    "rolling",  # added to the roster after 7/23 (e.g. TVA-style adds)
)
SIGNATORY_TRACK_LABELS: dict[str, str] = {
    "white-house-2026-03-04": "White House, March 4, 2026",
    "doe-2026-04-24": "DOE companion track, April 24, 2026",
    "expansion-2026-07-23": "Expansion, July 23, 2026",
    "rolling": "Added to the roster after July 23, 2026",
}
# The day the pledge expanded from 8 organizations to 200+.
RATEPAYER_PLEDGE_EXPANSION_DATE: str = "2026-07-23"

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
            "True if this company signed the Ratepayer Protection Pledge. "
            "Fixed historical fact, not a curator judgment: seven signed at the "
            "White House on 2026-03-04 (Amazon, Google, Meta, Microsoft, OpenAI, "
            "Oracle, xAI) and QTS signed via the DOE companion track on "
            "2026-04-24 (RATEPAYER_PLEDGE_DOE_DATE) — eight signatories total. "
            "Non-signatories (incl. Anthropic) stay False even when they publish "
            "their own ratepayer commitments — the flag means 'signed THE "
            "pledge', and the Ratepayer view surfaces non-signatory commitments "
            "separately."
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
    formal_agreement: bool = Field(
        default=False,
        description=(
            "True when this claim is backed by a formally published pledge, "
            "signed community benefit agreement (CBA), or binding regulatory "
            "commitment — not just an aspirational executive statement. "
            "Examples: Microsoft Datacenter Community Pledge (named document), "
            "QTS Ratepayer Protection Pledge (signed pledge), a CBA between "
            "developer and municipal authority. NOT for verbal commitments or "
            "press-release aspirations. Surfaced as a 'Formal agreement' badge "
            "on the claim card."
        ),
    )
    wayback_url: Optional[HttpUrl] = Field(
        default=None,
        description=(
            "If the original source_url is dead (4xx/5xx), a Wayback Machine "
            "archived URL preserving the original content. Set by the "
            "check_links.py curator tool. The frontend falls back to this URL "
            "on the 'view source' link when present. Absence means the link "
            "hasn't been checked or is still live."
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
    lat: Optional[float] = Field(
        default=None,
        ge=-90,
        le=90,
        description="Latitude. Null for infrastructure partnerships without a physical site.",
    )
    lon: Optional[float] = Field(
        default=None,
        ge=-180,
        le=180,
        description="Longitude. Null for infrastructure partnerships without a physical site.",
    )
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
    wayback_url: Optional[HttpUrl] = Field(
        default=None,
        description=(
            "Wayback Machine fallback URL if the original source_url is dead. "
            "Set by the check_links.py curator tool."
        ),
    )


# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Data center moratoriums (v1.16)
# ---------------------------------------------------------------------------
# Tracks city, county, state, and federal moratoriums on data center development.
# Status: enacted (in effect), proposed (introduced), failed (voted down/died).
#
# Captured timestamps show when a moratorium's status was verified; recurring
# quarterly refreshes will show policy momentum over time.

MORATORIUM_STATUSES: tuple[str, ...] = ("enacted", "proposed", "failed")
MoratoriumStatus = Literal["enacted", "proposed", "failed"]

MORATORIUM_REASON_TYPES: tuple[str, ...] = (
    "energy",           # Grid strain, power demand concerns
    "water",            # Water usage, aquifer depletion
    "air_quality",      # Air pollution, emissions, air quality impacts
    "noise",            # Noise from cooling fans, turbines, operations
    "transparency",     # NDA concerns, lack of community input, secrecy
    "equity",           # Ratepayer burden, cost-shifting to residents
)
MoratoriumReasonType = Literal["energy", "water", "air_quality", "noise", "transparency", "equity"]

MORATORIUM_REASON_LABELS: dict[str, str] = {
    "energy": "Grid & Power",
    "water": "Water & Depletion",
    "air_quality": "Air Quality",
    "noise": "Noise & Turbines",
    "transparency": "Community Process & Transparency",
    "equity": "Ratepayer Protection",
}


class Moratorium(_StrictBase):
    """A data center moratorium or ban enacted or proposed by a jurisdiction."""

    id: str = Field(min_length=1)
    jurisdiction: str = Field(
        min_length=1,
        description="City, County, State, or 'Federal' — the level at which the moratorium is set.",
    )
    jurisdiction_type: Literal["city", "county", "state", "federal"] = Field(
        description="Geographic scope of the moratorium.",
    )
    status: MoratoriumStatus = Field(
        description=(
            "enacted = law/regulation in effect as of capture date. "
            "proposed = bill introduced but not yet passed. "
            "failed = voted down or died in committee."
        ),
    )
    enacted_date: Optional[Date] = Field(
        default=None,
        description=(
            "Date the moratorium was signed/enacted. Null if proposed or failed. "
            "Used to sort the timeline."
        ),
    )
    effective_date: Optional[Date] = Field(
        default=None,
        description="Date the moratorium takes effect (may be after enacted_date).",
    )
    duration_months: Optional[int] = Field(
        default=None,
        ge=1,
        description="Length of the moratorium in months. Null for permanent bans or unknown durations.",
    )
    duration_description: str = Field(
        min_length=1,
        description=(
            "Human-readable duration. Prefer a short label ('6 months', '1 year', "
            "'18 months', 'Permanent ban'); a brief qualifier is fine ('Up to 2 years, "
            "until zoning adopted'). Keep the lede the actual duration — the directory "
            "table shows a truncated form (shortDuration() in app.js) and the full "
            "text renders in the detail modal + cell tooltip."
        ),
    )
    power_threshold_mw: Optional[float] = Field(
        default=None,
        ge=0,
        description=(
            "If the moratorium applies only to data centers above a certain power threshold, "
            "set that threshold in megawatts (e.g., 20 for a '20 MW or higher' threshold). "
            "Null if no threshold / all sizes covered."
        ),
    )
    key_reasons: list[MoratoriumReasonType] = Field(
        default_factory=list,
        description=(
            "Documented reasons behind the moratorium. Curators identify these from the "
            "bill text, legislative debate, or news. Order by prominence."
        ),
    )
    summary: str = Field(
        min_length=1,
        description=(
            "1–2 sentence plain-English summary of what the moratorium does. "
            "Neutral phrasing — not advocacy language."
        ),
    )
    source_url: HttpUrl
    source_title: str = Field(
        min_length=1,
        description="e.g., 'Denver City Council Bill #...' or 'New York S09144'.",
    )
    resources: Optional[list[dict]] = Field(
        default=None,
        description=(
            "Optional list of additional reputable sources. "
            "Each item: {'url': 'https://...', 'title': 'Source name'}. "
            "Prioritize government links, then major news outlets."
        ),
    )
    bill_number: Optional[str] = Field(
        default=None,
        description=(
            "Legislative bill designation. Convention: no space between chamber "
            "prefix and number (e.g., 'HB620', 'LD307', 'SB5982', not 'SB 5982'); "
            "companion bills joined with ' / ' (e.g., 'HF4888 / SF4298'). Exception: "
            "preserve a jurisdiction's own citation style verbatim when it differs "
            "structurally, not just by spacing — e.g. Vermont's period-separated "
            "'H.149', or a city ordinance's 'Bill No. 3927'. Optional, for enhanced "
            "entries."
        ),
    )
    sponsors: Optional[list[str]] = Field(
        default=None,
        description="Named legislative sponsors. Optional, for enhanced entries.",
    )
    key_stakeholders: Optional[dict] = Field(
        default=None,
        description=(
            "Optional breakdown of stakeholder positions by category. "
            "Keys: 'environmental', 'utility', 'community', 'labor', 'opposed', etc. "
            "Values: lists of organization names."
        ),
    )
    policy_type: Optional[str] = Field(
        default=None,
        description="Type of policy (e.g., 'traditional moratorium', 'cost-allocation rule'). Optional.",
    )
    enacted_by: Optional[str] = Field(
        default=None,
        description="Who enacted the moratorium (e.g., 'Governor Janet Mills', 'City Council'). Optional.",
    )
    legislative_votes: Optional[str] = Field(
        default=None,
        description="Vote counts if available (e.g., 'Senate 26-23, House 57-41'). Optional.",
    )
    city_council_vote: Optional[str] = Field(
        default=None,
        description="City council vote count if applicable (e.g., '11-2 in favor'). Optional.",
    )
    failure_reason: Optional[str] = Field(
        default=None,
        description="If status is 'failed', the reason (e.g., 'Died in House Energy Committee'). Optional.",
    )
    session: Optional[str] = Field(
        default=None,
        description="Legislative session year (e.g., '2024', '2026'). Optional.",
    )
    captured_at: Date = Field(
        description="Date this record was curated / moratorium status was verified."
    )


class ThemeRecommendation(BaseModel):
    """Evidence-based recommendations for addressing a moratorium theme, backed by actual moratorium text."""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(description="Short label for the theme (e.g., 'Grid & Power')")
    description: str = Field(description="One-line description of the theme")
    evidence: list[dict] = Field(
        description="List of moratorium-backed examples with text excerpts and proposals, keyed by moratorium name, text excerpt, and proposals list"
    )


class MoratoriumsPayload(_StrictBase):
    generated_at: Date
    moratoriums: list[Moratorium]
    china_anti_datacenter_messaging: dict | None = None
    theme_recommendations: dict[str, ThemeRecommendation] | None = None

    @field_validator("moratoriums")
    @classmethod
    def _ids_unique(cls, v: list[Moratorium]) -> list[Moratorium]:
        ids = [m.id for m in v]
        if len(ids) != len(set(ids)):
            dup = [i for i in ids if ids.count(i) > 1]
            raise ValueError(f"Duplicate moratorium ids: {sorted(set(dup))}")
        return v


# ---------------------------------------------------------------------------
# State large-load utility tariffs (v1.17)
# ---------------------------------------------------------------------------
# Tracks state-regulated electricity tariffs / rate designs that utilities have
# proposed, that regulators have approved, or that were rejected/withdrawn, for
# large-load customers (primarily data centers). Each tariff is scored against
# the design-element taxonomy from the DOE / Berkeley Lab (LBL) technical brief
# "Electricity Rate Designs for Large Loads: Evolving Practices and
# Opportunities" (January 2025), plus any additional terms OUTSIDE that study,
# plus the state legislation that authorizes or influenced it.
#
# The parameter taxonomy (TARIFF_PARAMETERS) is FROZEN for v1 and mirrors the
# LBL brief's five element groups. Adding a parameter requires a BACKLOG entry +
# the JS mirror (TARIFF_PARAMETERS in docs/app.js) — same drift-safe discipline
# as THEMES / DELIVERED_STATUSES. A test asserts Python/JS parity.

# Regulatory status. Maps the user-facing "passed / proposed / rejected" to the
# regulator's vocabulary: approved = order issued / in effect; proposed = filed
# or settlement pending a decision; rejected = denied, withdrawn, or died.
TARIFF_STATUSES: tuple[str, ...] = ("approved", "proposed", "rejected")
TariffStatus = Literal["approved", "proposed", "rejected"]
TARIFF_STATUS_LABELS: dict[str, str] = {
    "approved": "Approved",
    "proposed": "Proposed",
    "rejected": "Rejected / Withdrawn",
}

# Regulatory level. 'state' = state PUC/PSC tariff (the dataset's focus);
# 'federal' = a FERC co-location / interconnection case, included for context
# but kept out of the state-tariff stat counts (see Tariff.jurisdiction_level).
TARIFF_JURISDICTION_LEVELS: tuple[str, ...] = ("state", "federal")
TariffJurisdictionLevel = Literal["state", "federal"]

SignatoryCategory = Literal[
    "hyperscaler",
    "utility",
    "cooperative",
    "developer",
    "governor",
]
SignatoryTrack = Literal[
    "white-house-2026-03-04",
    "doe-2026-04-24",
    "expansion-2026-07-23",
    "rolling",
]

# The five LBL element groups, in the brief's order. (group_key, label).
TARIFF_PARAMETER_GROUPS: tuple[tuple[str, str], ...] = (
    ("eligibility", "Eligibility & Applicability"),
    ("contract_size", "Contract Size"),
    ("duration", "Contract Duration & Exit"),
    ("energy_source", "Energy Source"),
    ("other", "Other Elements"),
)

# The 17 large-load tariff design elements from the LBL brief, in the brief's
# order, grouped by the categories above. Keys are stable identifiers; labels
# are display text. FROZEN for v1.
TARIFF_PARAMETERS: tuple[str, ...] = (
    # Eligibility & applicability
    "min_load",
    "monthly_demand_charge",
    "customer_type",
    "study_cost_recovery",
    "credit_collateral",
    # Contract size
    "contracted_capacity",
    "resize_reassign",
    "btm_backup",
    "load_factor",
    # Contract duration & exit
    "contract_duration",
    "ramp_times",
    "duration_flexibility",
    "exit_fee",
    # Energy source
    "clean_energy",
    "specific_generation",
    # Other elements
    "marginal_pricing",
    "econ_dev_payments",
)

TARIFF_PARAMETER_LABELS: dict[str, str] = {
    "min_load": "Minimum load requirement",
    "monthly_demand_charge": "Minimum demand charge",
    "customer_type": "Customer-type applicability",
    "study_cost_recovery": "Study-cost recovery",
    "credit_collateral": "Credit rating / collateral",
    "contracted_capacity": "Contracted capacity & energy",
    "resize_reassign": "Resizing / reassignment",
    "btm_backup": "Behind-the-meter backup",
    "load_factor": "Minimum load factor",
    "contract_duration": "Contract duration",
    "ramp_times": "Ramp times",
    "duration_flexibility": "Duration flexibility",
    "exit_fee": "Exit fee",
    "clean_energy": "Clean-energy requirements",
    "specific_generation": "Specific generation technologies",
    "marginal_pricing": "Marginal pricing / cost-sharing",
    "econ_dev_payments": "Economic-development payments",
}

# One-line plain-English description of each LBL element (for tooltips / detail).
TARIFF_PARAMETER_DESCRIPTIONS: dict[str, str] = {
    "min_load": "A lower-bound MW load threshold to qualify for the tariff.",
    "monthly_demand_charge": "Minimum charge tied to a percentage of forecasted maximum demand.",
    "customer_type": "Tariff scoped to a specific large-load customer type (e.g., data centers).",
    "study_cost_recovery": "Customer pays for interconnection / system-impact studies.",
    "credit_collateral": "Minimum credit rating and/or collateral / deposit requirements.",
    "contracted_capacity": "Defined MW / MWh the customer is obligated to buy.",
    "resize_reassign": "Terms to resize, reassign, or sell unused contracted capacity / energy.",
    "btm_backup": "Treatment of behind-the-meter generation / storage as backup or supplemental power.",
    "load_factor": "A minimum average-to-peak load ratio the customer must maintain.",
    "contract_duration": "Minimum contract term to back long-lived utility investment.",
    "ramp_times": "An extended period to reach full contracted load.",
    "duration_flexibility": "Modifications / renewals to the contract term.",
    "exit_fee": "Charge for exiting the tariff or terminating service early.",
    "clean_energy": "Requirements / options to serve the load with clean or renewable energy.",
    "specific_generation": "Utility procures specific named generation on the customer's behalf.",
    "marginal_pricing": "Marginal-cost pricing / cost-sharing to limit cross-subsidization.",
    "econ_dev_payments": "Direct payments for workforce, community, or low-income programs.",
}

# Maps each parameter key to its group key (for grouped rendering / parity test).
TARIFF_PARAMETER_GROUP_OF: dict[str, str] = {
    "min_load": "eligibility",
    "monthly_demand_charge": "eligibility",
    "customer_type": "eligibility",
    "study_cost_recovery": "eligibility",
    "credit_collateral": "eligibility",
    "contracted_capacity": "contract_size",
    "resize_reassign": "contract_size",
    "btm_backup": "contract_size",
    "load_factor": "contract_size",
    "contract_duration": "duration",
    "ramp_times": "duration",
    "duration_flexibility": "duration",
    "exit_fee": "duration",
    "clean_energy": "energy_source",
    "specific_generation": "energy_source",
    "marginal_pricing": "other",
    "econ_dev_payments": "other",
}

# Per-parameter coverage status. "included" = the tariff addresses this element;
# "partial" = addresses it in a limited / conditional way. A parameter the
# tariff does NOT address is simply OMITTED from Tariff.parameters (sparse) — the
# frontend iterates the full TARIFF_PARAMETERS list and renders the gap, so
# "not met" is shown to the reader without storing a row for it.
TARIFF_COVERAGE_STATUSES: tuple[str, ...] = ("included", "partial")
TariffCoverageStatus = Literal["included", "partial"]


class TariffParameter(_StrictBase):
    """How a single tariff addresses one LBL design element.

    `detail` must be concrete and specific to THIS tariff — the value, threshold,
    or mechanism, not a restatement of the generic element. Cite a specific
    `source_url` only when it differs from the tariff's main source.
    """

    status: TariffCoverageStatus = "included"
    detail: str = Field(
        min_length=1,
        description="What the tariff specifies for this element (1 sentence, concrete).",
    )
    source_url: Optional[HttpUrl] = Field(
        default=None,
        description="Source for THIS element if different from the tariff's main source_url.",
    )


class TariffLegislation(_StrictBase):
    """A state law / bill that authorizes or influenced this tariff."""

    title: str = Field(
        min_length=1, description="e.g., 'Ohio HB 15 (2025)' or 'Texas SB 6 (2025)'."
    )
    url: HttpUrl
    citation: Optional[str] = Field(
        default=None, description="Bill number / statutory citation."
    )
    status: Optional[str] = Field(
        default=None, description="e.g., 'Enacted 2025', 'Pending in committee'."
    )
    summary: Optional[str] = Field(
        default=None,
        description="1 sentence on how the legislation relates to the tariff.",
    )


class TariffAdditionalTerm(_StrictBase):
    """A material term in the tariff that is NOT one of the LBL design elements."""

    term: str = Field(min_length=1, description="Short label for the term.")
    detail: str = Field(min_length=1, description="1 sentence describing it.")
    source_url: Optional[HttpUrl] = None


class SourceResource(_StrictBase):
    """A typed {url, title} source link.

    Replaces the loose `list[dict]` shape so refresh.py fails fast on a missing
    URL/title or a non-HTTP value — the frontend's detail renderer assumes both
    fields exist, and a broken source link is exactly the traceability failure
    this dataset must not ship.
    """

    url: HttpUrl
    title: str = Field(min_length=1)


class Tariff(_StrictBase):
    """A state-regulated large-load / data-center electricity tariff or rate design."""

    id: str = Field(min_length=1)
    utility: str = Field(min_length=1, description="Utility filing / holding the tariff.")
    state: str = Field(
        min_length=2,
        max_length=2,
        description="Two-letter US state / 'federal' code where the tariff is filed (primary).",
    )
    jurisdiction_level: TariffJurisdictionLevel = Field(
        default="state",
        description=(
            "'state' for a state-regulated (PUC/PSC) tariff; 'federal' for a FERC "
            "co-location / interconnection case. Federal cases are included for "
            "context (the LBL brief covers co-location) but are EXCLUDED from the "
            "state-tariff stat counts and badged separately so they don't read as "
            "a state tariff. Almost always 'state'."
        ),
    )
    tariff_name: str = Field(
        min_length=1, description="Official tariff / rider / service-agreement name."
    )
    tariff_type: Optional[str] = Field(
        default=None,
        description=(
            "e.g., 'Data center tariff', 'Clean transition tariff', "
            "'Special contract / ESA', 'Large-load rider'."
        ),
    )
    status: TariffStatus
    status_detail: Optional[str] = Field(
        default=None,
        description="Nuance, e.g. 'Settlement pending PUCO approval' or 'Withdrawn 2025'.",
    )
    regulator: str = Field(
        min_length=1, description="The approving PUC / PSC / commission (with acronym)."
    )
    docket_number: Optional[str] = Field(
        default=None, description="PUC docket / case number, e.g. '24-508-EL-ATA'."
    )
    filed_date: Optional[Date] = None
    decision_date: Optional[Date] = Field(
        default=None,
        description="Date approved / rejected. Null while still proposed.",
    )
    min_load_mw: Optional[float] = Field(
        default=None,
        ge=0,
        description="Headline minimum-load threshold (MW), surfaced in the directory row.",
    )
    customers: Optional[list[str]] = Field(
        default=None,
        description="Named large-load customers served under the tariff (e.g., 'Google').",
    )
    summary: str = Field(
        min_length=1,
        description="1–2 sentence neutral description of what the tariff does.",
    )
    parameters: dict[str, TariffParameter] = Field(
        default_factory=dict,
        description=(
            "LBL design elements the tariff addresses, keyed by TARIFF_PARAMETERS "
            "key. Sparse: omit elements the tariff does not address."
        ),
    )
    additional_terms: list[TariffAdditionalTerm] = Field(
        default_factory=list,
        description="Material terms not covered by the LBL element taxonomy.",
    )
    legislation: list[TariffLegislation] = Field(
        default_factory=list,
        description="State legislation that authorizes or influenced the tariff.",
    )
    source_url: HttpUrl
    source_title: str = Field(min_length=1)
    resources: Optional[list[SourceResource]] = Field(
        default=None,
        description=(
            "Additional reputable {url, title} sources. Prioritize government "
            "(PUC / legislature) links, then major trade press."
        ),
    )
    captured_at: Date = Field(
        description="Date this record was curated / the tariff status was verified."
    )

    @field_validator("state")
    @classmethod
    def _state_upper(cls, v: str) -> str:
        return v.upper()

    @field_validator("parameters")
    @classmethod
    def _params_known(cls, v: dict) -> dict:
        unknown = [k for k in v if k not in TARIFF_PARAMETERS]
        if unknown:
            raise ValueError(
                f"Unknown tariff parameter key(s): {sorted(unknown)}. "
                f"Valid keys: {list(TARIFF_PARAMETERS)}"
            )
        return v


class TariffsPayload(_StrictBase):
    generated_at: Date
    tariffs: list[Tariff]

    @field_validator("tariffs")
    @classmethod
    def _ids_unique(cls, v: list[Tariff]) -> list[Tariff]:
        ids = [t.id for t in v]
        if len(ids) != len(set(ids)):
            dup = [i for i in ids if ids.count(i) > 1]
            raise ValueError(f"Duplicate tariff ids: {sorted(set(dup))}")
        return v


class Signatory(_StrictBase):
    """One organization (or governor) on the Ratepayer Protection Pledge roster.

    Deliberately a THIN record, unlike Company. The dashboard has two tiers:

      Company    — deep coverage. 13 slugs, each with curated claims, projects,
                   a hand-written summary. Adding one requires the two-gate
                   editorial test (CLAUDE.md > "Companies in scope").
      Signatory  — breadth. Every name on the White House roster, carrying only
                   what the roster itself publishes (name, category, domain)
                   plus who signed when.

    `matched_company_slug` is the bridge: the handful of signatories we also
    track deeply point at their Company record. Everything else is roster-only,
    and that is the honest state — we are not implying we have researched 279
    cooperatives because we listed them.

    Editorial rules:
    - The roster is a SNAPSHOT, not a live mirror. Counts are always rendered
      "as of <roster_as_of>". The White House page's own header chips disagree
      with its own list (it advertised 281/69 while listing 279/68 on
      2026-07-25) — store what the LIST shows and record the advertised numbers
      separately in `roster_counts_stated`. Never silently reconcile the two.
    - Governors are signatory records too (category "governor", `state`
      required, sourced to the RGA release). One vocabulary, one payload — the
      state panel then gets its governor row for free.
    - Signing a pledge is a fact, not an assessment. Nothing here is a curator
      judgment call, and no per-signatory compliance is scored: for the vast
      majority we have no site data at all, and absence stays honest.
    """

    id: str = Field(
        min_length=1,
        description="Stable slug: 'aep-ohio', 'gov-tx', 'tva'. Governors use 'gov-<state>'.",
    )
    name: str = Field(
        min_length=1,
        description="Exact spelling as it appears on the roster ('AEP Ohio', not 'AEP-Ohio').",
    )
    category: SignatoryCategory
    signed_track: SignatoryTrack
    signed_date: Optional[Date] = Field(
        default=None,
        description=(
            "Date this signatory joined. Null ONLY for `rolling` adds whose date "
            "the roster does not publish — never guessed."
        ),
    )
    state: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=2,
        description="Two-letter state code. REQUIRED for governors; optional HQ state otherwise.",
    )
    website_domain: Optional[str] = Field(
        default=None,
        description="Bare domain as published on the roster ('aepohio.com'), no scheme.",
    )
    source_url: HttpUrl
    source_title: str = Field(min_length=1)
    captured_at: Date
    matched_company_slug: Optional[CompanySlug] = Field(
        default=None,
        description="Bridges a roster row to a deeply-tracked Company record.",
    )
    utility_aliases: list[str] = Field(
        default_factory=list,
        description=(
            "Other spellings this organization appears under in tariffs.json "
            "`utility` — e.g. 'AEP Ohio (Ohio Power Company)'. Used for exact-id "
            "joins ONLY; never fuzzy-match utility names (AEP Ohio vs AEP Texas)."
        ),
    )
    notes: Optional[str] = None

    @field_validator("state")
    @classmethod
    def _state_upper(cls, v: Optional[str]) -> Optional[str]:
        return v.upper() if v else v

    @field_validator("website_domain")
    @classmethod
    def _domain_is_bare(cls, v: Optional[str]) -> Optional[str]:
        if v and ("://" in v or v.startswith("www.")):
            raise ValueError(f"website_domain must be a bare domain, got {v!r}")
        return v


class SignatoriesPayload(_StrictBase):
    """The pledge roster as captured on a given day."""

    generated_at: Date
    roster_as_of: Date = Field(
        description="The day the White House roster was captured. Displayed with every count.",
    )
    roster_counts_stated: dict[str, int] = Field(
        default_factory=dict,
        description=(
            "Counts as ADVERTISED by the source page's own filter chips on "
            "`roster_as_of`. Kept alongside the derived counts precisely because "
            "the two drift; the UI shows ours and footnotes theirs."
        ),
    )
    pledge_url: str
    pledge_pdf_url: Optional[str] = None
    drift_note: Optional[str] = Field(
        default=None,
        description="Plain-English description of any stated-vs-listed count mismatch.",
    )
    signatories: list[Signatory]

    @field_validator("signatories")
    @classmethod
    def _ids_unique(cls, v: list[Signatory]) -> list[Signatory]:
        ids = [s.id for s in v]
        if len(ids) != len(set(ids)):
            dup = [i for i in ids if ids.count(i) > 1]
            raise ValueError(f"Duplicate signatory ids: {sorted(set(dup))}")
        return v

    @field_validator("signatories")
    @classmethod
    def _governors_have_state(cls, v: list[Signatory]) -> list[Signatory]:
        bad = [s.id for s in v if s.category == "governor" and not s.state]
        if bad:
            raise ValueError(f"Governor signatories missing `state`: {sorted(bad)}")
        return v

    @field_validator("signatories")
    @classmethod
    def _import_not_truncated(cls, v: list[Signatory]) -> list[Signatory]:
        """Fail loudly on a half-parsed roster rather than shipping a short list."""
        counts: dict[str, int] = {}
        for s in v:
            counts[s.category] = counts.get(s.category, 0) + 1
        floors = {
            "hyperscaler": 1,
            "utility": 1,
            "cooperative": 1,
            "developer": 1,
            "governor": 23,
        }
        short = {
            cat: (counts.get(cat, 0), floor)
            for cat, floor in floors.items()
            if counts.get(cat, 0) < floor
        }
        if short:
            raise ValueError(
                "Signatory roster looks truncated — "
                + ", ".join(f"{c}: {got} < {want}" for c, (got, want) in sorted(short.items()))
            )
        return v


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
    "RATEPAYER_PLEDGE_DOE_DATE",
    "RATEPAYER_PLEDGE_NAME",
    "RATEPAYER_PLEDGE_URL",
    "RATEPAYER_STATUSES",
    "RATEPAYER_LABELS",
    "PLEDGE_PRINCIPLES",
    "PLEDGE_PRINCIPLE_LABELS",
    "PLEDGE_PRINCIPLE_STATUSES",
    "MORATORIUM_STATUSES",
    "MORATORIUM_REASON_TYPES",
    "MORATORIUM_REASON_LABELS",
    "TARIFF_STATUSES",
    "TARIFF_STATUS_LABELS",
    "TARIFF_JURISDICTION_LEVELS",
    "TARIFF_PARAMETERS",
    "TARIFF_PARAMETER_LABELS",
    "TARIFF_PARAMETER_DESCRIPTIONS",
    "TARIFF_PARAMETER_GROUPS",
    "TARIFF_PARAMETER_GROUP_OF",
    "TARIFF_COVERAGE_STATUSES",
    "SIGNATORY_CATEGORIES",
    "SIGNATORY_CATEGORY_LABELS",
    "SIGNATORY_TRACKS",
    "SIGNATORY_TRACK_LABELS",
    "RATEPAYER_PLEDGE_EXPANSION_DATE",
    "Theme",
    "CompanySlug",
    "ProjectStatus",
    "Stance",
    "Constituency",
    "DeliveredStatus",
    "RatepayerStatus",
    "MoratoriumStatus",
    "MoratoriumReasonType",
    "TariffStatus",
    "TariffCoverageStatus",
    "TariffJurisdictionLevel",
    "SignatoryCategory",
    "SignatoryTrack",
    "PledgePrincipleStatus",
    "PledgePrincipleAssessment",
    "Company",
    "Metric",
    "Delivered",
    "Ratepayer",
    "Moratorium",
    "TariffParameter",
    "TariffLegislation",
    "TariffAdditionalTerm",
    "SourceResource",
    "Tariff",
    "Claim",
    "Project",
    "CommunityResponse",
    "CompaniesPayload",
    "ClaimsPayload",
    "ProjectsPayload",
    "ResponsesPayload",
    "MoratoriumsPayload",
    "TariffsPayload",
    "Signatory",
    "SignatoriesPayload",
]
