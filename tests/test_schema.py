"""Schema-level invariants. Catches drift before seed data is even touched."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from schema import (
    COMPANY_SLUGS,
    CONSTITUENCIES,
    PROJECT_STATUSES,
    STANCES,
    THEME_LABELS,
    THEMES,
    Claim,
    ClaimsPayload,
    CommunityResponse,
    Company,
    Metric,
    Project,
    ProjectsPayload,
    ResponsesPayload,
)


def _company_kwargs(**over):
    base = dict(
        slug="meta",
        name="Meta",
        hq="Menlo Park, CA",
        dedicated_page_url="https://sustainability.atmeta.com/",
        last_reviewed=date(2026, 5, 14),
    )
    base.update(over)
    return base


def _claim_kwargs(**over):
    base = dict(
        id="meta-energy-1",
        company_slug="meta",
        theme="energy",
        statement="100% renewable energy.",
        source_url="https://example.com/sustainability",
        source_title="Meta Sustainability",
        captured_at=date(2026, 5, 14),
    )
    base.update(over)
    return base


def _project_kwargs(**over):
    base = dict(
        id="meta-prineville-or",
        company_slug="meta",
        name="Prineville Data Center",
        city="Prineville",
        state="OR",
        country="US",
        lat=44.3,
        lon=-120.83,
        status="operational",
        announced_year=2010,
        source_url="https://example.com/prineville",
        source_title="Meta — Prineville",
        captured_at=date(2026, 5, 14),
    )
    base.update(over)
    return base


def _response_kwargs(**over):
    base = dict(
        id="resp-1",
        project_id="meta-prineville-or",
        date=date(2024, 1, 1),
        stance="positive",
        constituency="local_government",
        summary="Local government welcomed the project.",
        source_url="https://example.com/news",
        source_title="Local News",
    )
    base.update(over)
    return base


# ---------------------------------------------------------------------------
# Vocabulary invariants
# ---------------------------------------------------------------------------


class TestVocabularies:
    def test_themes_are_unique(self):
        assert len(THEMES) == len(set(THEMES))

    def test_themes_have_labels(self):
        assert set(THEME_LABELS.keys()) == set(THEMES)
        for v in THEME_LABELS.values():
            assert isinstance(v, str) and v

    def test_company_slugs_unique_lowercase(self):
        assert len(COMPANY_SLUGS) == len(set(COMPANY_SLUGS))
        for s in COMPANY_SLUGS:
            assert s == s.lower()

    def test_project_statuses_fixed(self):
        # Locked vocabulary; adding a status is a schema change.
        assert PROJECT_STATUSES == ("announced", "construction", "operational")

    def test_stances_fixed(self):
        assert STANCES == ("positive", "mixed", "negative")

    def test_constituencies_fixed(self):
        assert CONSTITUENCIES == (
            "residents",
            "local_government",
            "ngo",
            "academic",
            "journalist",
            "regulator",
        )


# ---------------------------------------------------------------------------
# Company
# ---------------------------------------------------------------------------


class TestCompany:
    def test_minimum_valid(self):
        c = Company(**_company_kwargs(dedicated_page_url=None))
        assert c.slug == "meta"
        assert c.dedicated_page_url is None

    def test_unknown_slug_rejected(self):
        with pytest.raises(ValidationError):
            Company(**_company_kwargs(slug="not-a-real-company"))

    def test_extra_field_rejected(self):
        kwargs = _company_kwargs()
        kwargs["nickname"] = "FB"
        with pytest.raises(ValidationError):
            Company(**kwargs)

    def test_blank_name_rejected(self):
        with pytest.raises(ValidationError):
            Company(**_company_kwargs(name=""))


# ---------------------------------------------------------------------------
# Claim
# ---------------------------------------------------------------------------


class TestClaim:
    def test_round_trip_minimal(self):
        c = Claim(**_claim_kwargs())
        assert c.theme == "energy"
        assert c.metric is None

    def test_unknown_theme_rejected(self):
        with pytest.raises(ValidationError):
            Claim(**_claim_kwargs(theme="not-a-theme"))

    def test_invalid_url_rejected(self):
        with pytest.raises(ValidationError):
            Claim(**_claim_kwargs(source_url="not-a-url"))

    def test_metric_attached(self):
        c = Claim(
            **_claim_kwargs(
                metric=Metric(value=1000, unit="jobs", kind="construction")
            )
        )
        assert c.metric is not None
        assert c.metric.value == 1000


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------


class TestProject:
    def test_minimum_valid(self):
        p = Project(**_project_kwargs())
        assert p.lat == 44.3
        assert p.country == "US"

    def test_lat_out_of_range_rejected(self):
        with pytest.raises(ValidationError):
            Project(**_project_kwargs(lat=200))

    def test_lon_out_of_range_rejected(self):
        with pytest.raises(ValidationError):
            Project(**_project_kwargs(lon=-200))

    def test_negative_jobs_rejected(self):
        with pytest.raises(ValidationError):
            Project(**_project_kwargs(claimed_jobs=-1))

    def test_unknown_status_rejected(self):
        with pytest.raises(ValidationError):
            Project(**_project_kwargs(status="speculative"))

    def test_state_must_be_two_chars(self):
        with pytest.raises(ValidationError):
            Project(**_project_kwargs(state="Oregon"))


# ---------------------------------------------------------------------------
# CommunityResponse
# ---------------------------------------------------------------------------


class TestResponse:
    def test_round_trip(self):
        r = CommunityResponse(**_response_kwargs())
        assert r.stance == "positive"
        assert r.single_source is False

    def test_unknown_stance_rejected(self):
        with pytest.raises(ValidationError):
            CommunityResponse(**_response_kwargs(stance="furious"))

    def test_unknown_constituency_rejected(self):
        with pytest.raises(ValidationError):
            CommunityResponse(**_response_kwargs(constituency="aliens"))

    def test_single_source_marker_round_trips(self):
        r = CommunityResponse(**_response_kwargs(single_source=True))
        assert r.single_source is True


# ---------------------------------------------------------------------------
# Payload-level uniqueness
# ---------------------------------------------------------------------------


class TestPayloadUniqueness:
    def test_duplicate_claim_ids_rejected(self):
        c1 = Claim(**_claim_kwargs(id="dup"))
        c2 = Claim(**_claim_kwargs(id="dup"))
        with pytest.raises(ValidationError):
            ClaimsPayload(generated_at=date.today(), claims=[c1, c2])

    def test_duplicate_project_ids_rejected(self):
        p1 = Project(**_project_kwargs(id="dup"))
        p2 = Project(**_project_kwargs(id="dup", city="Forest City", state="NC"))
        with pytest.raises(ValidationError):
            ProjectsPayload(generated_at=date.today(), projects=[p1, p2])

    def test_duplicate_response_ids_rejected(self):
        r1 = CommunityResponse(**_response_kwargs(id="dup"))
        r2 = CommunityResponse(**_response_kwargs(id="dup"))
        with pytest.raises(ValidationError):
            ResponsesPayload(generated_at=date.today(), responses=[r1, r2])

    def test_unique_payload_accepted(self):
        c1 = Claim(**_claim_kwargs(id="a"))
        c2 = Claim(**_claim_kwargs(id="b"))
        cp = ClaimsPayload(generated_at=date.today(), claims=[c1, c2])
        assert len(cp.claims) == 2


# ---------------------------------------------------------------------------
# JSON serialization edge cases
# ---------------------------------------------------------------------------


class TestSerialization:
    def test_exclude_none_drops_optional_nulls(self):
        c = Claim(**_claim_kwargs())
        s = c.model_dump_json(exclude_none=True)
        # 'metric' and 'project_id' are None; should NOT appear in the output.
        assert '"metric"' not in s
        assert '"project_id"' not in s

    def test_metric_attached_serializes(self):
        c = Claim(
            **_claim_kwargs(
                metric=Metric(value=1000, unit="jobs", kind="construction")
            )
        )
        s = c.model_dump_json(exclude_none=True)
        assert '"metric"' in s
        assert '"jobs"' in s
