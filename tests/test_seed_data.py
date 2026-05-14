"""End-to-end validation of `data/seed/*.json` and the `docs/data/*.json` build outputs.

These are the contract tests for the curated dataset. They fail loudly if a
curator edits seed files into a state the schema rejects, the cross-references
break, or the build is stale.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from schema import (
    THEMES,
    ClaimsPayload,
    CompaniesPayload,
    ProjectsPayload,
    ResponsesPayload,
)

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "seed"
OUT = ROOT / "docs" / "data"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def companies() -> CompaniesPayload:
    return CompaniesPayload.model_validate_json((SEED / "companies.json").read_text())


@pytest.fixture(scope="module")
def claims() -> ClaimsPayload:
    return ClaimsPayload.model_validate_json((SEED / "claims.json").read_text())


@pytest.fixture(scope="module")
def projects() -> ProjectsPayload:
    return ProjectsPayload.model_validate_json((SEED / "projects.json").read_text())


@pytest.fixture(scope="module")
def responses() -> ResponsesPayload:
    return ResponsesPayload.model_validate_json((SEED / "responses.json").read_text())


# ---------------------------------------------------------------------------
# Seed validation
# ---------------------------------------------------------------------------


class TestSeedValidates:
    def test_companies_valid(self, companies):
        assert len(companies.companies) >= 1

    def test_claims_valid(self, claims):
        assert len(claims.claims) >= 1

    def test_projects_valid(self, projects):
        assert len(projects.projects) >= 1

    def test_responses_valid(self, responses):
        assert len(responses.responses) >= 1


class TestSeedCoverage:
    # The eight original hyperscalers — these MUST be present.
    REQUIRED_HYPERSCALERS = {
        "meta", "google", "microsoft", "amazon",
        "openai", "anthropic", "xai", "oracle",
    }

    # Non-hyperscaler entities tracked from v1.1 onward when they announce
    # at hyperscaler scale + publish their own community-impact framing.
    OPTIONAL_ENTITIES = {"wonder-valley", "qts"}

    def test_all_required_hyperscalers_present(self, companies):
        slugs = {c.slug for c in companies.companies}
        missing = self.REQUIRED_HYPERSCALERS - slugs
        assert not missing, f"Missing required hyperscalers: {missing}"

    def test_no_unrecognized_companies(self, companies):
        # Guard against typos sneaking through the Literal narrow.
        slugs = {c.slug for c in companies.companies}
        recognized = self.REQUIRED_HYPERSCALERS | self.OPTIONAL_ENTITIES
        unknown = slugs - recognized
        assert not unknown, (
            f"Unknown company slugs: {unknown}. Expand "
            "TestSeedCoverage.OPTIONAL_ENTITIES if intentional."
        )

    def test_each_major_hyperscaler_has_at_least_one_project(self, projects):
        # The four "big four" hyperscalers should each have at least one project.
        # OpenAI/Anthropic/xAI/Oracle may have 0–2 because they're newer to direct DC ops.
        major = {"meta", "google", "microsoft", "amazon"}
        present = {p.company_slug for p in projects.projects}
        missing = major - present
        assert not missing, f"Missing projects for major hyperscalers: {missing}"

    def test_each_company_with_a_project_has_at_least_one_claim(
        self, projects, claims
    ):
        co_with_projects = {p.company_slug for p in projects.projects}
        co_with_claims = {c.company_slug for c in claims.claims}
        missing = co_with_projects - co_with_claims
        assert (
            not missing
        ), f"Companies with projects but no claims: {missing} — every project should be backed by at least one source claim."

    def test_at_least_one_response_per_stance(self, responses):
        stances = {r.stance for r in responses.responses}
        # Avoid a hit-piece bias: if we only have negative responses,
        # the editorial frame is broken.
        assert "positive" in stances, "Seed has no positive community responses"
        assert "negative" in stances, "Seed has no negative community responses"


# ---------------------------------------------------------------------------
# Cross-reference integrity
# ---------------------------------------------------------------------------


class TestCrossReferences:
    def test_claims_reference_known_companies(self, claims, companies):
        slugs = {c.slug for c in companies.companies}
        for c in claims.claims:
            assert c.company_slug in slugs, f"Claim {c.id} references unknown company {c.company_slug!r}"

    def test_claims_reference_known_projects(self, claims, projects):
        ids = {p.id for p in projects.projects}
        for c in claims.claims:
            if c.project_id is not None:
                assert c.project_id in ids, f"Claim {c.id} references unknown project {c.project_id!r}"

    def test_projects_reference_known_companies(self, projects, companies):
        slugs = {c.slug for c in companies.companies}
        for p in projects.projects:
            assert p.company_slug in slugs

    def test_responses_reference_known_projects(self, responses, projects):
        ids = {p.id for p in projects.projects}
        for r in responses.responses:
            assert r.project_id in ids, f"Response {r.id} references unknown project {r.project_id!r}"


# ---------------------------------------------------------------------------
# Per-record sanity
# ---------------------------------------------------------------------------


class TestRecordSanity:
    def test_every_claim_has_source_url(self, claims):
        for c in claims.claims:
            assert str(c.source_url).startswith("http"), c.id

    def test_every_project_has_source_url(self, projects):
        for p in projects.projects:
            assert str(p.source_url).startswith("http"), p.id

    def test_every_response_has_source_url(self, responses):
        for r in responses.responses:
            assert str(r.source_url).startswith("http"), r.id

    def test_capture_dates_not_in_future(self, claims, projects):
        today = date.today()
        # Allow today as the upper bound; future-dated captures are a curator typo.
        for c in claims.claims:
            assert c.captured_at <= today, f"Claim {c.id} captured_at in the future"
        for p in projects.projects:
            assert p.captured_at <= today, f"Project {p.id} captured_at in the future"

    def test_lat_lon_in_us_or_neighbors(self, projects):
        # v1 is US-only; allow a wide margin for CONUS + AK/HI/PR.
        for p in projects.projects:
            assert -180 <= p.lon <= -60, f"Project {p.id} lon {p.lon} outside US range"
            assert 18 <= p.lat <= 72, f"Project {p.id} lat {p.lat} outside US range"

    def test_claim_themes_in_vocabulary(self, claims):
        for c in claims.claims:
            assert c.theme in THEMES

    def test_no_claim_statement_is_a_paraphrase_marker(self, claims):
        # Tripwire: catch curator paraphrases like "they say that..." which
        # violate the verbatim-quote rule (CLAUDE.md > Editorial sourcing).
        for c in claims.claims:
            s = c.statement.lower()
            for marker in (
                "the company claims",
                "they claim that",
                "they say that",
                "the company says that",
            ):
                assert (
                    marker not in s
                ), f"Claim {c.id} appears to be a paraphrase, not a verbatim quote: {marker!r}"


# ---------------------------------------------------------------------------
# Build-output parity (docs/data/*.json must match validated seed)
# ---------------------------------------------------------------------------


class TestBuildOutputs:
    """If these fail, the curator forgot to re-run `python refresh.py`."""

    def test_companies_json_built(self):
        path = OUT / "companies.json"
        assert path.exists(), "Run `python refresh.py` to emit docs/data/companies.json"
        # Parse and re-validate to catch any divergence from the schema.
        CompaniesPayload.model_validate_json(path.read_text())

    def test_claims_json_built(self):
        path = OUT / "claims.json"
        assert path.exists(), "Run `python refresh.py`"
        ClaimsPayload.model_validate_json(path.read_text())

    def test_projects_json_built(self):
        path = OUT / "projects.json"
        assert path.exists(), "Run `python refresh.py`"
        ProjectsPayload.model_validate_json(path.read_text())

    def test_responses_json_built(self):
        path = OUT / "responses.json"
        assert path.exists(), "Run `python refresh.py`"
        ResponsesPayload.model_validate_json(path.read_text())

    def test_built_claims_match_seed_count(self):
        seed = json.loads((SEED / "claims.json").read_text())
        built = json.loads((OUT / "claims.json").read_text())
        assert len(seed["claims"]) == len(built["claims"]), "Build is stale — re-run refresh.py"

    def test_payload_sizes_under_budget(self):
        # Frontend perf budget: combined first-paint payloads (companies + claims).
        # Headroom: the matrix view is the landing surface, so the budget should
        # be tight. v1.1 raised the cap from 50KB to 100KB after the data fill
        # took claims.json from ~25 records to ~93 records — minified is well
        # under the cap, pretty mode goes over (don't ship pretty in production).
        first_paint = (OUT / "companies.json").stat().st_size + (
            OUT / "claims.json"
        ).stat().st_size
        assert first_paint < 100 * 1024, (
            f"First-paint payloads grew to {first_paint} bytes. "
            "Re-run `python refresh.py` (without --pretty) before shipping."
        )
