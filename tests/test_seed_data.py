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
    DELIVERED_STATUSES,
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
    OPTIONAL_ENTITIES = {"wonder-valley", "qts", "nebius", "crusoe", "coreweave", "prologis"}

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


class TestDeliveredAssessments:
    """v1.13: Delivered-vs-promised assessments on Claim records.

    The Delivered field is optional and absent by default — only the subset
    of claims that the curator has assessed will have it. These tests guard
    the assessment quality bar: every assessed claim has corroborating
    evidence and a valid status; the dashboard ships with at least one of
    each of the four statuses so the legend reads.
    """

    def test_every_assessed_claim_has_valid_status(self, claims):
        for c in claims.claims:
            if c.delivered is None:
                continue
            assert c.delivered.status in DELIVERED_STATUSES, c.id

    def test_every_assessed_claim_has_evidence_url(self, claims):
        for c in claims.claims:
            if c.delivered is None:
                continue
            assert str(c.delivered.source_url).startswith("http"), c.id
            assert c.delivered.source_title, c.id

    def test_assessed_at_not_in_future(self, claims):
        today = date.today()
        for c in claims.claims:
            if c.delivered is None:
                continue
            assert c.delivered.assessed_at <= today, c.id

    def test_at_least_one_of_each_delivered_status(self, claims):
        # Demonstrative seed: ensure the legend reads with all four colors.
        # If a curator deletes all examples of a status, the dashboard's
        # legend still renders the chip but with no real examples behind
        # it — which is editorially dishonest. Block that.
        seen = {c.delivered.status for c in claims.claims if c.delivered}
        missing = set(DELIVERED_STATUSES) - seen
        assert not missing, (
            f"Delivered statuses with no example: {sorted(missing)}. "
            "Either add an example or document why this status is unused."
        )


class TestRatepayerPledge:
    """v1.15: White House Ratepayer Protection Pledge view.

    Guards the two data changes backing the new view: the seven signatory
    flags (fixed historical fact) and the per-project ratepayer assessments
    (curated, honest about the pledge-only vs site-specific distinction).
    """

    # The seven hyperscalers that signed on 2026-03-04 — fixed history.
    EXPECTED_SIGNATORIES = {
        "amazon", "google", "meta", "microsoft", "openai", "oracle", "xai",
    }

    def test_exactly_the_seven_signatories_flagged(self, companies):
        flagged = {
            c.slug for c in companies.companies if c.ratepayer_pledge_signatory
        }
        assert flagged == self.EXPECTED_SIGNATORIES, (
            f"Signatory roster drift: extra={flagged - self.EXPECTED_SIGNATORIES}, "
            f"missing={self.EXPECTED_SIGNATORIES - flagged}"
        )

    def test_anthropic_is_not_a_signatory(self, companies):
        # Anthropic publishes its own ratepayer commitment but did NOT sign the
        # pledge — the flag must not blur that distinction.
        anthropic = next(c for c in companies.companies if c.slug == "anthropic")
        assert anthropic.ratepayer_pledge_signatory is False

    def test_assessed_projects_belong_to_signatories(self, projects, companies):
        signatories = {
            c.slug for c in companies.companies if c.ratepayer_pledge_signatory
        }
        for p in projects.projects:
            if p.ratepayer is None:
                continue
            assert p.company_slug in signatories, (
                f"Project {p.id!r} has a ratepayer assessment but its company "
                f"{p.company_slug!r} is not a pledge signatory."
            )

    def test_assessed_projects_announced_on_or_after_pledge(self, projects):
        # The cohort is "data centers announced since the pledge" — an
        # assessment on a pre-2026 site would misrepresent the view.
        for p in projects.projects:
            if p.ratepayer is None:
                continue
            assert p.announced_year >= 2026, (
                f"Project {p.id!r} announced {p.announced_year} predates the "
                "2026 pledge but carries a ratepayer assessment."
            )

    def test_affirmed_assessments_cite_a_real_owned_claim(self, projects, claims):
        by_id = {c.id: c for c in claims.claims}
        for p in projects.projects:
            rp = p.ratepayer
            if rp is None:
                continue
            if rp.status == "affirmed":
                assert rp.evidence_claim_id is not None, (
                    f"Project {p.id!r} 'affirmed' but cites no evidence_claim_id"
                )
                assert rp.evidence_claim_id in by_id, (
                    f"Project {p.id!r} evidence_claim_id {rp.evidence_claim_id!r} "
                    "not found in claims.json"
                )
                assert by_id[rp.evidence_claim_id].project_id == p.id, (
                    f"Project {p.id!r} evidence claim belongs to a different project"
                )

    def test_pledge_only_assessments_have_no_evidence_claim(self, projects):
        # `pledge_only` means "no site-specific commitment captured" — it must
        # not carry an evidence claim (that would contradict the status).
        for p in projects.projects:
            rp = p.ratepayer
            if rp is None:
                continue
            if rp.status == "pledge_only":
                assert rp.evidence_claim_id is None, (
                    f"Project {p.id!r} is 'pledge_only' but cites an evidence "
                    "claim — use 'affirmed' if a site-specific commitment exists."
                )

    def test_at_least_one_affirmed_and_one_pledge_only(self, projects):
        # The view's value is the contrast; ship with both populated so the
        # legend reads. (No `contested` requirement — absence is honest.)
        seen = {p.ratepayer.status for p in projects.projects if p.ratepayer}
        assert "affirmed" in seen, "No 'affirmed' ratepayer assessment in seed"
        assert "pledge_only" in seen, "No 'pledge_only' ratepayer assessment in seed"


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
        # Cap history: 50KB (v1.0) → 100KB (v1.1, +68 claims) → 150KB (v1.6,
        # ~180 claims) → 200KB (v1.11, ~280 claims from comprehensive news
        # polling across 13 companies). The matrix view is the landing
        # surface so the budget stays tight, but real growth (more companies,
        # more claims, more verbatim quotes) justifies the bump. Minified
        # output is the contract; pretty mode is debug-only.
        first_paint = (OUT / "companies.json").stat().st_size + (
            OUT / "claims.json"
        ).stat().st_size
        assert first_paint < 200 * 1024, (
            f"First-paint payloads grew to {first_paint} bytes. "
            "Re-run `python refresh.py` (without --pretty) before shipping."
        )
