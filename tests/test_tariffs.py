"""Contract tests for the state large-load utility tariff dataset (v1.17).

Covers: schema validation of the seed, the frozen LBL parameter taxonomy, the
passed/proposed/rejected status coverage, source-link integrity ("every claim
links to a source"), legislation links, and the docs/data build parity.

Also guards the v1.17 ratepayer fix: every ratepayer card must surface a source
link (the rpCardSourcesHtml helper is defined and called in both renderers).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from schema import (
    TARIFF_COVERAGE_STATUSES,
    TARIFF_PARAMETER_GROUP_OF,
    TARIFF_PARAMETER_GROUPS,
    TARIFF_PARAMETER_LABELS,
    TARIFF_PARAMETERS,
    TARIFF_STATUSES,
    TariffsPayload,
)

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "seed"
OUT = ROOT / "docs" / "data"
APP_JS = ROOT / "docs" / "app.js"
INDEX_HTML = ROOT / "docs" / "index.html"


@pytest.fixture(scope="module")
def tariffs() -> TariffsPayload:
    return TariffsPayload.model_validate_json((SEED / "tariffs.json").read_text())


# --- Schema + taxonomy --------------------------------------------------------


def test_seed_validates(tariffs: TariffsPayload) -> None:
    assert len(tariffs.tariffs) >= 10, "Expected a substantive tariff dataset."


def test_parameter_taxonomy_frozen() -> None:
    # The LBL brief catalogues 17 design elements across 5 groups. Frozen for v1;
    # changing this is a deliberate migration (BACKLOG + JS mirror + colors).
    assert len(TARIFF_PARAMETERS) == 17
    assert len(set(TARIFF_PARAMETERS)) == 17, "Parameter keys must be unique."
    assert len(TARIFF_PARAMETER_GROUPS) == 5


def test_every_parameter_has_label_and_group() -> None:
    group_keys = {g[0] for g in TARIFF_PARAMETER_GROUPS}
    for key in TARIFF_PARAMETERS:
        assert key in TARIFF_PARAMETER_LABELS, f"{key} missing a label"
        assert key in TARIFF_PARAMETER_GROUP_OF, f"{key} missing a group"
        assert TARIFF_PARAMETER_GROUP_OF[key] in group_keys, (
            f"{key} maps to unknown group {TARIFF_PARAMETER_GROUP_OF[key]!r}"
        )


def test_every_group_has_at_least_one_parameter() -> None:
    used = set(TARIFF_PARAMETER_GROUP_OF.values())
    for group_key, _label in TARIFF_PARAMETER_GROUPS:
        assert group_key in used, f"Group {group_key!r} has no parameters."


def test_all_data_parameter_keys_are_known(tariffs: TariffsPayload) -> None:
    for t in tariffs.tariffs:
        for key in t.parameters:
            assert key in TARIFF_PARAMETERS, (
                f"Tariff {t.id!r} uses unknown parameter key {key!r}"
            )


def test_coverage_statuses_valid(tariffs: TariffsPayload) -> None:
    for t in tariffs.tariffs:
        for key, pc in t.parameters.items():
            assert pc.status in TARIFF_COVERAGE_STATUSES, (
                f"Tariff {t.id!r} element {key!r} has bad status {pc.status!r}"
            )
            assert pc.detail.strip(), f"Tariff {t.id!r} element {key!r} has empty detail"


# --- Status coverage (passed / proposed / rejected) ---------------------------


def test_all_three_statuses_present(tariffs: TariffsPayload) -> None:
    """The user asked for passed/proposed/rejected — each must have an example so
    the directory legend reads with all three states backed by real records."""
    present = {t.status for t in tariffs.tariffs}
    for status in TARIFF_STATUSES:
        assert status in present, (
            f"No tariff with status {status!r}; the directory needs at least one "
            "example of each of approved / proposed / rejected."
        )


def test_ids_unique(tariffs: TariffsPayload) -> None:
    ids = [t.id for t in tariffs.tariffs]
    assert len(ids) == len(set(ids))


def test_no_empty_tariffs(tariffs: TariffsPayload) -> None:
    # Every tariff should address at least one LBL element — otherwise the
    # "X / 17 elements" cell and detail checklist would be empty.
    for t in tariffs.tariffs:
        assert len(t.parameters) >= 1, f"Tariff {t.id!r} addresses no LBL elements."


def test_state_codes_are_two_letter(tariffs: TariffsPayload) -> None:
    for t in tariffs.tariffs:
        assert re.fullmatch(r"[A-Z]{2}", t.state), f"Bad state code {t.state!r} on {t.id!r}"


# --- Source-link integrity ("links for every claim") --------------------------


def test_every_tariff_has_source(tariffs: TariffsPayload) -> None:
    for t in tariffs.tariffs:
        assert str(t.source_url).startswith("http"), f"{t.id!r} missing source_url"
        assert t.source_title.strip(), f"{t.id!r} missing source_title"


def test_every_legislation_entry_has_url(tariffs: TariffsPayload) -> None:
    any_legislation = False
    for t in tariffs.tariffs:
        for leg in t.legislation:
            any_legislation = True
            assert str(leg.url).startswith("http"), (
                f"{t.id!r} legislation {leg.title!r} missing a URL"
            )
            assert leg.title.strip()
    assert any_legislation, (
        "At least one tariff should link to the state legislation behind it."
    )


def test_additional_terms_have_detail(tariffs: TariffsPayload) -> None:
    for t in tariffs.tariffs:
        for term in t.additional_terms:
            assert term.term.strip() and term.detail.strip(), (
                f"{t.id!r} has an additional term missing label/detail"
            )


def test_prioritizes_gov_sources(tariffs: TariffsPayload) -> None:
    """Most primary sources should be government (.gov) or the DOE/LBL brief —
    the editorial rule is to prefer authoritative sources."""
    gov = 0
    for t in tariffs.tariffs:
        url = str(t.source_url)
        if ".gov" in url or "lbl.gov" in url or "capitol.texas.gov" in url:
            gov += 1
    assert gov >= len(tariffs.tariffs) * 0.6, (
        f"Only {gov}/{len(tariffs.tariffs)} primary sources are .gov/LBL; "
        "prioritize authoritative sources."
    )


# --- Build parity -------------------------------------------------------------


def test_docs_build_exists_and_validates() -> None:
    path = OUT / "tariffs.json"
    assert path.exists(), "Run `python refresh.py` to emit docs/data/tariffs.json"
    TariffsPayload.model_validate_json(path.read_text())


def test_docs_build_matches_seed_ids() -> None:
    seed = json.loads((SEED / "tariffs.json").read_text())
    built = json.loads((OUT / "tariffs.json").read_text())
    seed_ids = {t["id"] for t in seed["tariffs"]}
    built_ids = {t["id"] for t in built["tariffs"]}
    assert seed_ids == built_ids, "Build is stale — re-run `python refresh.py`."


# --- Frontend wiring ----------------------------------------------------------


def test_index_html_has_tariffs_tab() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert 'id="tab-tariffs"' in html
    assert 'id="view-tariffs"' in html
    assert 'id="tariffs-tbody"' in html
    assert 'id="tariff-detail"' in html


def test_app_js_wires_tariffs_view() -> None:
    js = APP_JS.read_text(encoding="utf-8")
    assert "loadTariffsData" in js
    assert "renderTariffsView" in js
    assert "showTariffDetail" in js
    # The view must be registered in the VIEWS table so the tab activates.
    assert re.search(r'name:\s*"tariffs"', js), "tariffs view not registered in VIEWS"


# --- Ratepayer fix guard (v1.17): every card surfaces a source link -----------


def test_ratepayer_cards_have_sources_helper() -> None:
    """The fix adds rpCardSourcesHtml and calls it from BOTH card renderers so
    every site (incl. pledge_only / pre-pledge with no evidence claim) links to
    a source. Guards against silent regression of that fix."""
    js = APP_JS.read_text(encoding="utf-8")
    assert "function rpCardSourcesHtml(" in js, "rpCardSourcesHtml helper missing"
    # Must be invoked in the assessed card and the pre-pledge/unassessed card.
    calls = len(re.findall(r"\$\{rpCardSourcesHtml\(p\)\}", js))
    assert calls >= 2, (
        f"rpCardSourcesHtml is only invoked {calls} time(s); expected it in both "
        "renderRatepayerCard and renderPrePledgeCard."
    )
