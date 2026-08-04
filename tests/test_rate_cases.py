"""Rate-case dataset integrity + wiring.

The rate cases are the proceeding layer under the tariffs (see CLAUDE.md).
These tests pin the editorial rules the schema can't express numerically and
the frontend wiring that renders them.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "seed" / "rate_cases.json"
APP_JS = ROOT / "docs" / "app.js"
INDEX_HTML = ROOT / "docs" / "index.html"


@pytest.fixture(scope="module")
def cases() -> list[dict]:
    return json.loads(SEED.read_text(encoding="utf-8"))["rate_cases"]


def test_seed_validates_against_schema() -> None:
    # Validates the full payload (generated_at + rate_cases), not just the
    # `cases` fixture's list — reads the file directly rather than taking an
    # unused fixture param shaped for a different check.
    from schema import RateCasesPayload

    RateCasesPayload.model_validate(
        json.loads(SEED.read_text(encoding="utf-8"))
    )


def test_every_case_cites_a_source(cases) -> None:
    for rc in cases:
        assert rc["source_url"].startswith("https://"), rc["id"]
        assert rc["source_title"], rc["id"]


def test_at_least_one_pending_case_has_a_next_milestone(cases) -> None:
    """The Home "What's next" list derives from these; a dataset with no
    forward-looking milestone renders an empty section on the landing page."""
    assert any(rc["status"] == "pending" and rc.get("next_milestone") for rc in cases)


def test_federal_cases_use_us_and_are_minority(cases) -> None:
    federal = [rc for rc in cases if rc.get("jurisdiction_level") == "federal"]
    for rc in federal:
        assert rc["state_code"] == "US", rc["id"]
    assert len(federal) < len(cases) / 2, "dataset should stay predominantly state-level"


def test_next_milestone_dates_only_accompany_text(cases) -> None:
    for rc in cases:
        if rc.get("next_milestone_date"):
            assert rc.get("next_milestone"), (
                f"{rc['id']} has a milestone date with no milestone text"
            )


def test_coverage_rollup_counts_rate_cases() -> None:
    cov = json.loads((ROOT / "docs" / "data" / "coverage.json").read_text())
    total = sum(s.get("rate_cases", 0) for s in cov["states"].values())
    seed = json.loads(SEED.read_text())["rate_cases"]
    state_level = [rc for rc in seed if rc.get("jurisdiction_level") != "federal"]
    assert total == len(state_level), (
        "coverage.json rate_cases counts drifted from the seed — re-run refresh.py"
    )


def test_index_html_has_rate_cases_section() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert 'id="rate-cases-section"' in html
    assert 'id="rate-cases-list"' in html
    assert 'id="whats-next-list"' in html, "Home What's-next list missing"


def test_app_js_wires_rate_cases() -> None:
    js = APP_JS.read_text(encoding="utf-8")
    assert "function loadRateCasesData()" in js
    assert "function renderRateCases()" in js
    assert "function renderWhatsNext()" in js
    # The state panel must include the rate-case section (the pairing the
    # dataset exists for).
    assert "Rate cases & proceedings" in js


def test_rate_cases_stay_out_of_first_paint() -> None:
    """Deferred tier, like responses.json: fetched by loadRatepayerView after
    first render, never preloaded."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "rate_cases.json" not in html
