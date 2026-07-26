"""Contract tests for the Ratepayer Protection Pledge roster (`signatories.json`).

The roster is the breadth tier of the dashboard's two-tier model — 300+ thin
records against 13 deeply-tracked companies. These tests guard the things that
would quietly corrupt it: a truncated import, a fabricated governor list, a
fuzzy utility join binding a tariff to the wrong company, or the source page's
own count drift being silently "fixed".
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from schema import (
    COMPANY_SLUGS,
    RATEPAYER_PLEDGE_DATE,
    RATEPAYER_PLEDGE_DOE_DATE,
    RATEPAYER_PLEDGE_EXPANSION_DATE,
    SIGNATORY_CATEGORIES,
    SIGNATORY_TRACKS,
    SignatoriesPayload,
)

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "seed"
OUT = ROOT / "docs" / "data"

# The 23 states whose governors signed the addendum announced 2026-07-23.
# Fixed historical fact, not a curator judgment — sourced to the RGA release.
GOVERNOR_STATES = {
    "AL", "AK", "AR", "GA", "ID", "IN", "IA", "LA", "MS", "MO", "MT", "NE",
    "NV", "ND", "OH", "OK", "SC", "SD", "TN", "TX", "UT", "WV", "WY",
}

# The seven electricity buyers from the March 4 round.
MARCH_HYPERSCALERS = {"amazon", "google", "meta", "microsoft", "openai", "oracle", "xai"}


@pytest.fixture(scope="module")
def roster() -> SignatoriesPayload:
    return SignatoriesPayload.model_validate_json((SEED / "signatories.json").read_text())


# ---------------------------------------------------------------------------
# Shape + vocabulary
# ---------------------------------------------------------------------------


def test_seed_validates(roster: SignatoriesPayload) -> None:
    assert roster.signatories, "roster is empty"


def test_categories_are_in_vocabulary(roster: SignatoriesPayload) -> None:
    bad = {s.category for s in roster.signatories} - set(SIGNATORY_CATEGORIES)
    assert not bad, f"unknown categories: {bad}"


def test_tracks_are_in_vocabulary(roster: SignatoriesPayload) -> None:
    bad = {s.signed_track for s in roster.signatories} - set(SIGNATORY_TRACKS)
    assert not bad, f"unknown tracks: {bad}"


def test_ids_are_unique(roster: SignatoriesPayload) -> None:
    ids = [s.id for s in roster.signatories]
    assert len(ids) == len(set(ids))


def test_every_record_is_sourced(roster: SignatoriesPayload) -> None:
    """No source, no ship — the rule holds for thin records too."""
    unsourced = [s.id for s in roster.signatories if not s.source_url or not s.source_title]
    assert not unsourced, f"signatories missing a source: {unsourced}"


# ---------------------------------------------------------------------------
# Import integrity — a truncated parse must fail loudly, not ship short
# ---------------------------------------------------------------------------


def test_roster_is_not_truncated(roster: SignatoriesPayload) -> None:
    """The July expansion was 200+ organizations; a short list means a broken parse."""
    orgs = [s for s in roster.signatories if s.category != "governor"]
    assert len(orgs) >= 200, (
        f"only {len(orgs)} organizations on the roster — the White House page "
        "markup probably changed and build_signatories.py parsed a partial list"
    )


def test_all_five_categories_are_populated(roster: SignatoriesPayload) -> None:
    present = {s.category for s in roster.signatories}
    assert present == set(SIGNATORY_CATEGORIES), (
        f"missing categories: {set(SIGNATORY_CATEGORIES) - present}"
    )


def test_exactly_the_23_governor_states(roster: SignatoriesPayload) -> None:
    govs = [s for s in roster.signatories if s.category == "governor"]
    assert len(govs) == 23, f"expected 23 governors, got {len(govs)}"
    assert {g.state for g in govs} == GOVERNOR_STATES


def test_governors_are_dated_to_the_expansion(roster: SignatoriesPayload) -> None:
    for g in (s for s in roster.signatories if s.category == "governor"):
        assert g.signed_date and g.signed_date.isoformat() == RATEPAYER_PLEDGE_EXPANSION_DATE
        assert g.signed_track == "expansion-2026-07-23"


def test_governors_are_not_conflated_with_corporate_signatories(
    roster: SignatoriesPayload,
) -> None:
    """A governor signed an addendum, not the corporate pledge. Keep it visible."""
    for g in (s for s in roster.signatories if s.category == "governor"):
        assert g.notes and "addendum" in g.notes.lower(), (
            f"{g.id} must record that governors signed an addendum, not the pledge itself"
        )
        assert g.matched_company_slug is None


# ---------------------------------------------------------------------------
# The bridge to deeply-tracked companies
# ---------------------------------------------------------------------------


def test_matched_slugs_are_real_companies(roster: SignatoriesPayload) -> None:
    for s in roster.signatories:
        if s.matched_company_slug:
            assert s.matched_company_slug in COMPANY_SLUGS, (
                f"{s.id} points at unknown company slug {s.matched_company_slug!r}"
            )


def test_matched_slugs_are_unique(roster: SignatoriesPayload) -> None:
    """Two roster rows claiming the same company would double-count the scorecard."""
    slugs = [s.matched_company_slug for s in roster.signatories if s.matched_company_slug]
    assert len(slugs) == len(set(slugs)), f"duplicate company matches: {slugs}"


def test_the_original_seven_are_hyperscalers_on_the_march_track(
    roster: SignatoriesPayload,
) -> None:
    by_slug = {s.matched_company_slug: s for s in roster.signatories if s.matched_company_slug}
    for slug in MARCH_HYPERSCALERS:
        assert slug in by_slug, f"{slug} missing from the roster"
        rec = by_slug[slug]
        assert rec.category == "hyperscaler", f"{slug} categorised as {rec.category}"
        assert rec.signed_track == "white-house-2026-03-04"
        assert rec.signed_date.isoformat() == RATEPAYER_PLEDGE_DATE


def test_qts_is_on_the_doe_companion_track(roster: SignatoriesPayload) -> None:
    qts = next(s for s in roster.signatories if s.matched_company_slug == "qts")
    assert qts.signed_track == "doe-2026-04-24"
    assert qts.signed_date.isoformat() == RATEPAYER_PLEDGE_DOE_DATE


def test_anthropic_is_not_on_the_roster(roster: SignatoriesPayload) -> None:
    """Anthropic publishes its own commitment but never signed. Don't imply it did."""
    matched = {s.matched_company_slug for s in roster.signatories}
    assert "anthropic" not in matched


def test_coreweave_signed_in_the_july_expansion(roster: SignatoriesPayload) -> None:
    """The v1.21 non-signatory toggle predates this; CoreWeave is a signatory now."""
    cw = next(
        (s for s in roster.signatories if s.matched_company_slug == "coreweave"), None
    )
    assert cw is not None, "CoreWeave is on the July roster and must be matched"
    assert cw.signed_date.isoformat() == RATEPAYER_PLEDGE_EXPANSION_DATE


# ---------------------------------------------------------------------------
# Utility aliases — exact joins only
# ---------------------------------------------------------------------------


def test_utility_aliases_are_unique_across_the_roster() -> None:
    """One tariff utility name must never resolve to two different signatories."""
    payload = SignatoriesPayload.model_validate_json(
        (SEED / "signatories.json").read_text()
    )
    seen: dict[str, str] = {}
    for s in payload.signatories:
        for alias in s.utility_aliases:
            assert alias not in seen, (
                f"alias {alias!r} claimed by both {seen[alias]} and {s.id}"
            )
            seen[alias] = s.id


def test_utility_aliases_resolve_to_real_tariff_records(roster: SignatoriesPayload) -> None:
    """An alias that matches no tariff is dead weight — and usually a typo."""
    tariffs = json.loads((SEED / "tariffs.json").read_text())["tariffs"]
    known = {t.get("utility") for t in tariffs}
    for s in roster.signatories:
        for alias in s.utility_aliases:
            assert alias in known, (
                f"{s.id} aliases {alias!r}, which appears in no tariff record. "
                "Aliases are exact-match joins; fix the spelling rather than "
                "loosening the match."
            )


def test_only_utilities_carry_aliases(roster: SignatoriesPayload) -> None:
    for s in roster.signatories:
        if s.utility_aliases:
            assert s.category == "utility", (
                f"{s.id} ({s.category}) carries utility_aliases — only utilities join tariffs"
            )


# ---------------------------------------------------------------------------
# Snapshot honesty
# ---------------------------------------------------------------------------


def test_roster_records_the_source_pages_own_counts(roster: SignatoriesPayload) -> None:
    assert roster.roster_counts_stated, (
        "roster_counts_stated must record what the source page advertised, so the "
        "UI can footnote the difference instead of quietly picking a number"
    )


def test_count_drift_is_described_when_it_exists(roster: SignatoriesPayload) -> None:
    """If our list and the page's advertised total disagree, say so in words."""
    stated = roster.roster_counts_stated.get("all")
    listed = len([s for s in roster.signatories if s.category != "governor"])
    if stated is not None and stated != listed:
        assert roster.drift_note, (
            f"page advertised {stated} orgs, list holds {listed}, but drift_note is empty"
        )


def test_signed_dates_are_never_in_the_future_of_capture(roster: SignatoriesPayload) -> None:
    for s in roster.signatories:
        if s.signed_date:
            assert s.signed_date <= s.captured_at, (
                f"{s.id} claims to have signed after it was captured"
            )


def test_only_rolling_adds_may_omit_a_signed_date(roster: SignatoriesPayload) -> None:
    """Every dated track has a known date; never guess one to fill the column."""
    for s in roster.signatories:
        if s.signed_date is None:
            assert s.signed_track == "rolling", (
                f"{s.id} is on track {s.signed_track} with no signed_date"
            )


# ---------------------------------------------------------------------------
# Build output
# ---------------------------------------------------------------------------


def test_build_output_matches_seed(roster: SignatoriesPayload) -> None:
    built = SignatoriesPayload.model_validate_json((OUT / "signatories.json").read_text())
    assert len(built.signatories) == len(roster.signatories)
    assert built.roster_as_of == roster.roster_as_of


def test_roster_is_lazy_loaded_not_preloaded() -> None:
    """The roster is the biggest payload; it must never touch first paint."""
    index = (ROOT / "docs" / "index.html").read_text()
    assert "signatories.json" not in index, (
        "signatories.json must not be preloaded in index.html — it is lazy-loaded "
        "by the Ratepayer view (perf baseline: first paint stays under the budget)"
    )


# ---------------------------------------------------------------------------
# Serving-utility joins (P5)
# ---------------------------------------------------------------------------


def test_serving_utility_ids_resolve_to_the_roster(roster: SignatoriesPayload) -> None:
    """A typo here fails silently in the browser: the utility lens just shows
    no sites, which reads as 'this utility serves nothing we track'."""
    ids = {s.id for s in roster.signatories}
    projects = json.loads((SEED / "projects.json").read_text())["projects"]
    for p in projects:
        sid = p.get("serving_utility_signatory_id")
        if sid:
            assert sid in ids, f"{p['id']} points at unknown signatory {sid!r}"


def test_serving_utility_id_always_has_a_display_name() -> None:
    """The id is the join key; the name is what a reader sees."""
    projects = json.loads((SEED / "projects.json").read_text())["projects"]
    for p in projects:
        if p.get("serving_utility_signatory_id"):
            assert p.get("serving_utility"), (
                f"{p['id']} sets a serving-utility id with no display name"
            )


def test_serving_utility_points_at_a_utility(roster: SignatoriesPayload) -> None:
    """A data center is not served by a governor or a hyperscaler."""
    by_id = {s.id: s for s in roster.signatories}
    projects = json.loads((SEED / "projects.json").read_text())["projects"]
    for p in projects:
        sid = p.get("serving_utility_signatory_id")
        if sid:
            cat = by_id[sid].category
            assert cat in ("utility", "cooperative"), (
                f"{p['id']} is 'served by' {sid} which is a {cat}"
            )


def test_serving_utility_backfill_is_not_empty() -> None:
    """Guards against the field silently reverting to all-null, which would
    make the utility lens look broken rather than unpopulated."""
    projects = json.loads((SEED / "projects.json").read_text())["projects"]
    filled = [p for p in projects if p.get("serving_utility")]
    assert len(filled) >= 10, f"only {len(filled)} projects name a serving utility"
