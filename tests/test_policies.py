"""Policies & agreements dataset integrity + Python↔JS vocabulary parity (v3.1).

See SPEC_POLICIES_TAB.md. The schema enforces shape; these tests pin the
editorial rules and the frontend mirrors that nothing else would catch.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tests.test_themes_match_frontend import (
    _extract_array,
    _extract_object_keys,
    _extract_object_values,
)

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "seed" / "policies.json"
APP_JS = ROOT / "docs" / "app.js"
CSS = ROOT / "docs" / "styles.css"
INDEX = ROOT / "docs" / "index.html"


@pytest.fixture(scope="module")
def policies() -> list[dict]:
    return json.loads(SEED.read_text(encoding="utf-8"))["policies"]


@pytest.fixture(scope="module")
def js() -> str:
    return APP_JS.read_text(encoding="utf-8")


def test_seed_validates_against_schema() -> None:
    from schema import PoliciesPayload

    PoliciesPayload.model_validate(json.loads(SEED.read_text(encoding="utf-8")))


def test_seed_is_not_empty(policies) -> None:
    assert len(policies) >= 20


def test_every_record_cites_an_https_source(policies) -> None:
    for p in policies:
        assert p["source_url"].startswith("https://"), p["id"]
        for r in p.get("resources", []):
            assert r["url"].startswith("https://"), p["id"]


def test_related_ids_resolve(policies) -> None:
    projects = {
        x["id"]
        for x in json.loads((ROOT / "data/seed/projects.json").read_text())["projects"]
    }
    moratoriums = {
        x["id"]
        for x in json.loads((ROOT / "data/seed/moratoriums.json").read_text())["moratoriums"]
    }
    for p in policies:
        for pid in p.get("related_project_ids", []):
            assert pid in projects, (p["id"], pid)
        if p.get("related_moratorium_id"):
            assert p["related_moratorium_id"] in moratoriums, p["id"]


def test_state_codes_are_real_states(policies, js) -> None:
    import re

    body = re.search(r"const STATE_NAMES = \{(.*?)\};", js, re.DOTALL).group(1)
    codes = set(re.findall(r"\b([A-Z]{2}):", body))
    for p in policies:
        if p.get("state_code"):
            assert p["state_code"] in codes, (p["id"], p["state_code"])


def test_both_halves_of_the_tab_are_populated(policies) -> None:
    """The tab exists to put public instruments beside negotiated agreements."""
    kinds = {p["instrument"] for p in policies}
    assert kinds & {"executive_order", "legislation", "regulation"}
    assert kinds & {"benefit_agreement", "company_plan", "local_ordinance"}
    assert any(p["community_benefits_framework"] for p in policies)


def test_value_usd_only_with_a_community_benefit(policies) -> None:
    """A stated dollar value is the value of committed community benefits."""
    for p in policies:
        if p.get("value_usd") is not None:
            assert p["community_benefits_framework"] or "community_grants" in p["benefit_themes"], p["id"]


# --- schema edge cases ------------------------------------------------------

BASE = {
    "id": "x",
    "title": "X",
    "instrument": "legislation",
    "status": "in_effect",
    "scope": "state",
    "jurisdiction": "Texas",
    "state_code": "tx",
    "benefit_themes": ["energy"],
    "key_terms": ["term"],
    "summary": "s",
    "source_url": "https://example.gov/x",
    "source_title": "t",
    "captured_at": "2026-09-23",
}


def _policy(**over):
    from schema import Policy

    return Policy.model_validate({**BASE, **over})


def test_state_code_is_uppercased() -> None:
    assert _policy().state_code == "TX"


@pytest.mark.parametrize("scope", ["state", "county", "city"])
def test_local_scopes_need_a_state_code(scope) -> None:
    with pytest.raises(ValidationError):
        _policy(scope=scope, state_code=None)


def test_federal_scope_needs_no_state() -> None:
    assert _policy(scope="federal", state_code=None, jurisdiction="Federal")


def test_company_plan_rules() -> None:
    ok = dict(instrument="company_plan", scope="company", state_code=None,
              jurisdiction="Meta (company-wide)", company_slugs=["meta"])
    assert _policy(**ok)
    with pytest.raises(ValidationError):  # no company named
        _policy(**{**ok, "company_slugs": None})
    with pytest.raises(ValidationError):  # plan at a jurisdiction scope
        _policy(**{**ok, "scope": "state", "state_code": "TX"})
    with pytest.raises(ValidationError):  # company scope, public instrument
        _policy(**{**ok, "instrument": "legislation"})


@pytest.mark.parametrize("terms", [[], ["  "]])
def test_key_terms_required_and_non_blank(terms) -> None:
    with pytest.raises(ValidationError):
        _policy(key_terms=terms)


def test_themes_required_and_frozen() -> None:
    with pytest.raises(ValidationError):
        _policy(benefit_themes=[])
    with pytest.raises(ValidationError):
        _policy(benefit_themes=["housing"])


def test_negative_value_rejected() -> None:
    with pytest.raises(ValidationError):
        _policy(value_usd=-1)


def test_duplicate_ids_rejected() -> None:
    from schema import PoliciesPayload

    with pytest.raises(ValidationError):
        PoliciesPayload.model_validate(
            {"generated_at": "2026-09-23", "policies": [BASE, BASE]}
        )


def test_refresh_flags_unknown_related_ids() -> None:
    import refresh
    from schema import Policy, PoliciesPayload

    pl = refresh._load_payload
    projects = pl("projects", refresh.PAYLOAD_FILES["projects"])
    bad = PoliciesPayload(
        generated_at="2026-09-23",
        policies=[Policy.model_validate(
            {**BASE, "related_project_ids": ["nope"], "related_moratorium_id": "nope"}
        )],
    )
    errors = refresh._check_cross_refs(
        pl("companies", refresh.PAYLOAD_FILES["companies"]),
        pl("claims", refresh.PAYLOAD_FILES["claims"]),
        projects,
        pl("responses", refresh.PAYLOAD_FILES["responses"]),
        policies=bad,
        moratoriums=pl("moratoriums", refresh.PAYLOAD_FILES["moratoriums"]),
    )
    assert any("related_project_id 'nope'" in e for e in errors)
    assert any("related_moratorium_id 'nope'" in e for e in errors)


def test_coverage_totals_count_policies() -> None:
    cov = json.loads((ROOT / "docs/data/coverage.json").read_text())
    n = len(json.loads(SEED.read_text())["policies"])
    assert cov["totals"]["policies"] == n


# --- Python ↔ JS parity -----------------------------------------------------

def test_instrument_vocab_matches(js) -> None:
    from schema import POLICY_INSTRUMENT_LABELS, POLICY_INSTRUMENTS

    assert tuple(_extract_array(js, "POLICY_INSTRUMENTS")) == POLICY_INSTRUMENTS
    assert _extract_object_keys(js, "POLICY_INSTRUMENT_LABELS") == set(POLICY_INSTRUMENTS)
    assert _extract_object_values(js, "POLICY_INSTRUMENT_LABELS") == set(POLICY_INSTRUMENT_LABELS.values())


def test_status_vocab_matches(js) -> None:
    from schema import POLICY_STATUS_LABELS, POLICY_STATUSES

    assert tuple(_extract_array(js, "POLICY_STATUSES")) == POLICY_STATUSES
    assert _extract_object_keys(js, "POLICY_STATUS_LABELS") == set(POLICY_STATUSES)
    assert _extract_object_values(js, "POLICY_STATUS_LABELS") == set(POLICY_STATUS_LABELS.values())


def test_scope_vocab_matches(js) -> None:
    from schema import POLICY_SCOPES

    assert tuple(_extract_array(js, "POLICY_SCOPES")) == POLICY_SCOPES
    assert _extract_object_keys(js, "POLICY_SCOPE_LABELS") == set(POLICY_SCOPES)


def test_status_badge_classes_exist_in_css(js) -> None:
    """Values, not just keys — the RATE_CASE_BADGE_CLASS lesson (CLAUDE.md)."""
    from schema import POLICY_STATUSES

    assert _extract_object_keys(js, "POLICY_STATUS_BADGE_CLASS") == set(POLICY_STATUSES)
    css = CSS.read_text(encoding="utf-8")
    for cls in _extract_object_values(js, "POLICY_STATUS_BADGE_CLASS"):
        assert f".{cls}" in css, cls


def test_tab_is_wired(js) -> None:
    html = INDEX.read_text(encoding="utf-8")
    assert 'id="tab-policies"' in html and 'id="view-policies"' in html
    assert '"#policies"' in js
    assert 'data-path-target="policies"' in html
