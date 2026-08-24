"""Tests for connectors.dedupe and connectors.recheck -- the two accelerator
scripts added 2026-08-24 to formalize what a research agent used to redo by
hand every refresh session (a duplicate-check one-liner, a stale-record
search-query list). See connectors/README.md's "dedupe"/"recheck" sections
and REFRESH.md's 2026-08-24 entry for the incidents these replace.
"""

from __future__ import annotations

import json
from datetime import date, timedelta

import pytest

from connectors import dedupe, recheck


# -- dedupe --------------------------------------------------------------
@pytest.fixture
def seed(tmp_path, monkeypatch):
    d = tmp_path / "seed"
    d.mkdir()
    (d / "projects.json").write_text(json.dumps({"projects": [
        {"id": "google-new-florence-mo", "company_slug": "google", "city": "New Florence", "state": "MO", "name": "New Florence DC"},
        {"id": "meta-newton-ga", "company_slug": "meta", "city": "Social Circle", "state": "GA", "name": "Newton County DC"},
        {"id": "google-owasso-ok", "company_slug": "google", "city": "Owasso", "state": "OK", "name": "Project Clydesdale"},
    ]}))
    (d / "moratoriums.json").write_text(json.dumps({"moratoriums": [
        {"id": "fayetteville-ga-city-2026-03", "jurisdiction": "Fayetteville", "jurisdiction_type": "city", "status": "enacted", "state_code": "GA"},
        {"id": "seattle-city-2026-01", "jurisdiction": "Seattle", "jurisdiction_type": "city", "status": "enacted", "state_code": "WA"},
    ]}))
    (d / "tariffs.json").write_text(json.dumps({"tariffs": [
        {"id": "georgia-power-large-load-rules", "utility": "Georgia Power", "state": "GA", "status": "approved"},
    ]}))
    (d / "rate_cases.json").write_text(json.dumps({"rate_cases": [
        {"id": "ga-psc-rate-freeze-2025", "utility": "Georgia Power", "state_code": "GA", "status": "approved"},
    ]}))
    monkeypatch.setattr(dedupe, "SEED", d)
    return d


def test_projects_state_filter_is_case_insensitive(seed):
    """A curator typing '--state mo' (lowercase) must match the seed's 'MO'."""
    rows = dedupe._projects("mo", None)
    assert [r["id"] for r in rows] == ["google-new-florence-mo"]


def test_projects_state_filter_catches_the_named_incident(seed):
    """The exact regression this tool exists to prevent: a lead framed as
    'Montgomery County, MO' shares no substring with the seed's own
    'New Florence' city field. Filtering by STATE (not city-name matching)
    is what surfaces it for a human to eyeball."""
    rows = dedupe._projects("MO", None)
    ids = [r["id"] for r in rows]
    assert "google-new-florence-mo" in ids


def test_projects_company_filter(seed):
    rows = dedupe._projects(None, "google")
    assert {r["id"] for r in rows} == {"google-new-florence-mo", "google-owasso-ok"}


def test_projects_company_filter_is_case_insensitive(seed):
    """Regression: --state was normalized (.strip().upper()) but --company
    wasn't, so `--company Google` silently returned zero rows against a seed
    that has google-slug projects -- found by adversarial PR review,
    2026-08-24. A curator typing the company's display name instead of its
    lowercase slug should still get a match."""
    rows = dedupe._projects(None, "Google")
    assert {r["id"] for r in rows} == {"google-new-florence-mo", "google-owasso-ok"}


def test_projects_no_match_returns_empty_not_error(seed):
    assert dedupe._projects("ZZ", None) == []


def test_moratoriums_state_filter(seed):
    rows = dedupe._moratoriums("GA")
    assert [r["id"] for r in rows] == ["fayetteville-ga-city-2026-03"]


def test_all_covers_every_record_type_for_one_state(seed):
    """The 'all' command is the common case -- a lead might turn out to be
    any of the four record types, so every type gets checked in one pass."""
    assert dedupe._projects("GA", None) == [
        r for r in json.loads((seed / "projects.json").read_text())["projects"] if r["state"] == "GA"
    ]
    assert len(dedupe._moratoriums("GA")) == 1
    assert len(dedupe._tariffs("GA")) == 1
    assert len(dedupe._rate_cases("GA")) == 1


def test_cmd_all_requires_state(seed, caplog):
    # Error message goes through logging (not print/stdout) per AGENTS.md's
    # "no print() for runtime output" rule -- caplog, not capsys.
    ns = type("NS", (), {"state": None, "json": False})()
    rc = dedupe.cmd_all(ns)
    assert rc == 2
    assert "--state is required" in caplog.text


# -- recheck ---------------------------------------------------------------
def test_moratorium_queries_use_bill_number_when_present():
    row = {"jurisdiction": "Cleveland", "state_code": "OH", "bill_number": "Ord. 123-26"}
    qs = recheck._moratorium_queries(row)
    assert any("Ord. 123-26" in q for q in qs)
    assert any(q.startswith("Cleveland OH data center moratorium") for q in qs)


def test_moratorium_queries_omit_bill_number_when_absent():
    row = {"jurisdiction": "Greenfield", "state_code": "MA"}
    qs = recheck._moratorium_queries(row)
    assert not any("None" in q for q in qs)  # bill_number=None must never leak into a query string


def test_tariff_queries_include_docket_number():
    row = {"utility": "NV Energy", "state": "NV", "docket_number": "24-06014"}
    qs = recheck._tariff_or_rate_case_queries(row, "state")
    assert any("24-06014" in q for q in qs)


def test_docket_hint_falls_back_for_unknown_state():
    # No network/IO needed -- this is a pure dict lookup with a fallback.
    hint = recheck.DOCKET_SYSTEM_HINTS.get("ZZ", "state legislature bill tracker + local council agenda site")
    assert "ZZ" not in hint


@pytest.fixture
def stale_seed(tmp_path, monkeypatch):
    """A minimal but schema-valid seed (moratoriums/tariffs/rate_cases) with
    one genuinely stale proposed moratorium and one fresh (not-yet-stale) one,
    so cmd_stale's end-to-end filtering can be exercised against the real
    `refresh._audit_stale_pending` -- not a reimplementation of "what counts
    as stale" (see the module's single-source-of-truth rationale)."""
    import refresh as refresh_module

    d = tmp_path / "seed"
    d.mkdir()
    old_date = (date.today() - timedelta(days=recheck.STALE_PENDING_DAYS + 5)).isoformat()
    fresh_date = date.today().isoformat()

    (d / "moratoriums.json").write_text(json.dumps({
        "generated_at": fresh_date,
        "moratoriums": [
            {
                "id": "stale-city-2026-01", "jurisdiction": "Staleville", "jurisdiction_type": "city",
                "status": "proposed", "duration_description": "6 months", "summary": "A proposed pause.",
                "source_url": "https://example.com/a", "source_title": "Example", "captured_at": old_date,
                "state_code": "ZZ", "bill_number": "HB 42",
            },
            {
                "id": "fresh-city-2026-01", "jurisdiction": "Freshville", "jurisdiction_type": "city",
                "status": "proposed", "duration_description": "6 months", "summary": "A proposed pause.",
                "source_url": "https://example.com/b", "source_title": "Example", "captured_at": fresh_date,
                "state_code": "ZZ",
            },
        ],
    }))
    (d / "tariffs.json").write_text(json.dumps({"generated_at": fresh_date, "tariffs": []}))
    (d / "rate_cases.json").write_text(json.dumps({"generated_at": fresh_date, "rate_cases": []}))

    monkeypatch.setattr(refresh_module, "SEED_DIR", d)
    monkeypatch.setattr(recheck, "SEED", d)
    return d


def test_cmd_stale_only_flags_the_genuinely_stale_record(stale_seed, capsys):
    ns = type("NS", (), {"kind": None, "json": True})()
    rc = recheck.cmd_stale(ns)
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    ids = [it["id"] for it in out["items"]]
    assert ids == ["stale-city-2026-01"]  # fresh-city-2026-01 must NOT appear


def test_cmd_stale_query_uses_the_records_own_bill_number(stale_seed, capsys):
    ns = type("NS", (), {"kind": None, "json": True})()
    recheck.cmd_stale(ns)
    out = json.loads(capsys.readouterr().out)
    item = out["items"][0]
    assert any("HB 42" in q for q in item["queries"])
    assert item["kind"] == "moratorium"
    assert item["age_days"] >= recheck.STALE_PENDING_DAYS


def test_stale_moratorium_never_gets_a_puc_docket_hint(tmp_path, monkeypatch, capsys):
    """Regression: an earlier version applied DOCKET_SYSTEM_HINTS (a PUC/PSC
    docket-system map) to moratorium records too, purely because they share
    a `state_code` field with tariffs/rate_cases -- so a state constitutional-
    amendment moratorium in Ohio got told to check 'Ohio PUCO docketing',
    which is nonsense for a legislative/ballot instrument. 'OH' is
    deliberately IN DOCKET_SYSTEM_HINTS here (unlike the ZZ fixture above) so
    this actually exercises the bug rather than trivially passing because the
    dict has no entry to wrongly match."""
    import refresh as refresh_module

    d = tmp_path / "seed"
    d.mkdir()
    old_date = (date.today() - timedelta(days=recheck.STALE_PENDING_DAYS + 5)).isoformat()
    (d / "moratoriums.json").write_text(json.dumps({
        "generated_at": date.today().isoformat(),
        "moratoriums": [{
            "id": "ohio-state-amendment-2024", "jurisdiction": "Ohio", "jurisdiction_type": "state",
            "status": "proposed", "duration_description": "Permanent if adopted",
            "summary": "A proposed constitutional amendment.",
            "source_url": "https://example.com/oh", "source_title": "Example", "captured_at": old_date,
            "state_code": "OH",
        }],
    }))
    (d / "tariffs.json").write_text(json.dumps({"generated_at": date.today().isoformat(), "tariffs": []}))
    (d / "rate_cases.json").write_text(json.dumps({"generated_at": date.today().isoformat(), "rate_cases": []}))
    monkeypatch.setattr(refresh_module, "SEED_DIR", d)
    monkeypatch.setattr(recheck, "SEED", d)

    ns = type("NS", (), {"kind": None, "json": True})()
    recheck.cmd_stale(ns)
    out = json.loads(capsys.readouterr().out)
    item = out["items"][0]
    assert item["id"] == "ohio-state-amendment-2024"
    assert "PUCO" not in item["docket_hint"]
    assert "docket" not in item["docket_hint"].lower()
    assert item["docket_hint"] == "state legislature bill tracker + local council agenda site"
