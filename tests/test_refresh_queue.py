"""The daily-refresh queue (scripts/refresh_queue.py).

The queue decides what the unattended daily routine works on, so the failure
modes worth pinning are the silent ones: a unit that never comes up, a
follow-up that never clears, a ledger entry pointing at a renamed record, a
review that forgets it was only a quick check. Expected sets are derived from
the payloads, never written out, so the tests can't go stale as data grows.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "seed"

_spec = importlib.util.spec_from_file_location("refresh_queue", ROOT / "scripts" / "refresh_queue.py")
rq = importlib.util.module_from_spec(_spec)
sys.modules["refresh_queue"] = rq  # dataclasses resolve annotations via sys.modules
_spec.loader.exec_module(rq)


@pytest.fixture
def tmp_ledger(tmp_path, monkeypatch):
    path = tmp_path / "refresh_ledger.json"
    path.write_text(json.dumps({"units": {}}))
    monkeypatch.setattr(rq, "LEDGER", path)
    return path


def _write(path: Path, units: dict) -> None:
    path.write_text(json.dumps({"units": units}))


# --- the real files ------------------------------------------------------------

def test_committed_ledger_is_valid() -> None:
    """Every ledger key must still name a unit. A renamed project id would
    otherwise orphan its review history without anyone noticing."""
    assert rq.check_ledger() == []


def test_backlog_carries_the_generated_queue_block() -> None:
    text = (ROOT / "BACKLOG.md").read_text()
    assert text.count(rq.START) == 1 and text.count(rq.END) == 1
    assert text.index(rq.START) < text.index(rq.END)


def test_every_record_owner_is_a_unit() -> None:
    units = rq.derive_units()
    projects = json.loads((SEED / "projects.json").read_text())["projects"]
    companies = json.loads((SEED / "companies.json").read_text())["companies"]
    for p in projects:
        assert f"site:{p['id']}" in units
    for c in companies:
        assert f"company:{c['slug']}" in units
    states = {k.split(":", 1)[1] for k, u in units.items() if u.kind == "state"}
    assert states == set(rq.state_names()) | {rq.FEDERAL}


def test_every_moratorium_lands_in_a_state_unit() -> None:
    """A record whose state never reaches a unit is a record the routine
    never re-checks."""
    units = rq.derive_units()
    placed = {rid for u in units.values() if u.kind == "state"
              for rid in u.records.get("moratoriums", [])}
    moratoriums = json.loads((SEED / "moratoriums.json").read_text())["moratoriums"]
    assert placed == {m["id"] for m in moratoriums}


def test_every_claim_and_policy_lands_in_a_unit() -> None:
    """Claims belong to a site (project_id) or, company-wide, to their company.
    Policies belong to a state, or, when company-scoped, to each company they
    name. A record outside every unit is one the routine never re-checks
    (Codex review, PR #49)."""
    units = rq.derive_units()
    placed = {(payload, rid) for u in units.values()
              for payload, ids in u.records.items() for rid in ids}
    claims = json.loads((SEED / "claims.json").read_text())["claims"]
    for c in claims:
        if c.get("project_id"):
            assert c["id"] in units[f"site:{c['project_id']}"].records.get("claims", []), c["id"]
        else:
            assert ("claims", c["id"]) in placed, c["id"]
    policies = json.loads((SEED / "policies.json").read_text())["policies"]
    assert {p["id"] for p in policies} <= {rid for payload, rid in placed if payload == "policies"}


# --- ranking ---------------------------------------------------------------------

def test_due_follow_ups_come_first(tmp_ledger) -> None:
    site = next(k for k in rq.derive_units() if k.startswith("site:"))
    _write(tmp_ledger, {site: {"follow_ups": [{"due": "2026-01-02", "what": "check the vote"}]}})
    plan = rq.run_plan(rq.merged_units(), date(2026, 9, 25), 3)
    assert plan[0][0].key == site
    assert "check the vote" in plan[0][1]


def test_rhythm_gives_states_and_companies_alternate_days(tmp_ledger, monkeypatch) -> None:
    monkeypatch.setattr(rq, "derived_follow_ups", lambda: {})
    units = rq.merged_units()
    odd, even = date(2026, 9, 25), date(2026, 9, 26)
    assert odd.toordinal() % 2 != even.toordinal() % 2
    kinds_odd = [u.kind for u, _ in rq.run_plan(units, odd, 4)]
    kinds_even = [u.kind for u, _ in rq.run_plan(units, even, 4)]
    assert kinds_odd[0] == kinds_even[0] == "site"
    assert {kinds_odd[1], kinds_even[1]} == {"state", "company"}
    assert sorted(kinds_odd) == sorted(kinds_even) == ["company", "site", "site", "state"]


def test_a_fresh_review_moves_a_unit_down(tmp_ledger, monkeypatch) -> None:
    monkeypatch.setattr(rq, "derived_follow_ups", lambda: {})
    today = date(2026, 9, 25)
    first_site = rq.run_plan(rq.merged_units(), today, 1)[0][0].key
    rq.mark(first_site, "reviewed", [], today, False, None)
    assert rq.run_plan(rq.merged_units(), today, 1)[0][0].key != first_site


# --- marking ---------------------------------------------------------------------

def test_mark_clears_due_follow_ups_and_keeps_future_ones(tmp_ledger) -> None:
    site = next(k for k in rq.derive_units() if k.startswith("site:"))
    _write(tmp_ledger, {site: {"follow_ups": [
        {"due": "2026-09-01", "what": "past"},
        {"due": "2026-12-01", "what": "future"},
    ]}})
    rq.mark(site, "checked", [["2027-01-15", "new"]], date(2026, 9, 25), False, None)
    entry = json.loads(tmp_ledger.read_text())["units"][site]
    assert entry["last_reviewed"] == "2026-09-25"
    assert [f["what"] for f in entry["follow_ups"]] == ["future", "new"]


def test_followups_only_mark_is_not_a_full_review(tmp_ledger) -> None:
    state = "state:GA"
    _write(tmp_ledger, {state: {"last_reviewed": "2026-06-01", "summary": "old",
                                "follow_ups": [{"due": "2026-09-20", "what": "vote"}]}})
    rq.mark(state, "vote was held", [], date(2026, 9, 25), False, None, followups_only=True)
    entry = json.loads(tmp_ledger.read_text())["units"][state]
    assert entry["last_reviewed"] == "2026-06-01" and entry["summary"] == "old"
    assert "follow_ups" not in entry


def test_followups_only_check_is_recorded_not_lost(tmp_ledger) -> None:
    """A derived follow-up (no stored ones) checked with --followups-only must
    leave its finding in the ledger: not a bare {}, and not nothing at all.
    The 2026-09-25 dry run hit both failure shapes."""
    rq.mark("state:MO", "St. Charles made its ban permanent", [], date(2026, 9, 25),
            False, None, followups_only=True)
    entry = json.loads(tmp_ledger.read_text())["units"]["state:MO"]
    assert entry == {"last_check": {"date": "2026-09-25", "summary": "St. Charles made its ban permanent"}}
    assert rq.check_ledger() == []


def test_check_flags_a_malformed_last_check(tmp_ledger) -> None:
    _write(tmp_ledger, {"state:MO": {"last_check": {"date": "soon"}}})
    assert any("last_check" in p for p in rq.check_ledger())


def test_mark_rejects_an_unknown_unit(tmp_ledger) -> None:
    with pytest.raises(SystemExit):
        rq.mark("site:not-a-real-project", "x", [], date(2026, 9, 25), False, None)


def test_check_flags_an_orphaned_entry(tmp_ledger) -> None:
    _write(tmp_ledger, {"site:renamed-away": {"last_reviewed": "2026-09-01", "summary": "x"}})
    assert any("not a unit" in p for p in rq.check_ledger())


# --- derived follow-ups -----------------------------------------------------------

def _fake_loader(moratoriums: list[dict], rate_cases: list[dict]):
    real = rq._load

    def load(name: str, key: str):
        if name == "moratoriums.json":
            return moratoriums
        if name == "rate_cases.json":
            return rate_cases
        return real(name, key)
    return load


def test_moratorium_end_date_is_due_until_the_record_is_recaptured(monkeypatch) -> None:
    rec = {"id": "x-2026-01", "jurisdiction": "X", "jurisdiction_type": "city", "state_code": "OH",
           "status": "enacted", "effective_date": "2026-01-31", "duration_months": 6,
           "captured_at": "2026-02-01"}
    monkeypatch.setattr(rq, "_load", _fake_loader([rec], []))
    items = rq.derived_follow_ups()["state:OH"]
    assert items[0]["due"] == "2026-07-31"  # month arithmetic clamps, doesn't overflow
    rec["captured_at"] = "2026-08-02"  # re-checked after it ended
    assert "state:OH" not in rq.derived_follow_ups()


def test_rate_case_milestone_is_due_the_day_after(monkeypatch) -> None:
    rc = {"id": "rc-1", "state_code": "NC", "status": "pending",
          "next_milestone_date": "2026-09-30", "captured_at": "2026-09-22"}
    monkeypatch.setattr(rq, "_load", _fake_loader([], [rc]))
    assert rq.derived_follow_ups()["state:NC"][0]["due"] == "2026-10-01"
    rc["status"] = "approved"
    assert rq.derived_follow_ups() == {}


# --- the generated backlog block ---------------------------------------------------

def test_write_backlog_is_idempotent(tmp_ledger, tmp_path, monkeypatch) -> None:
    backlog = tmp_path / "BACKLOG.md"
    backlog.write_text(f"# B\n\nintro\n\n{rq.START}\nstale\n{rq.END}\n\n## After\n")
    monkeypatch.setattr(rq, "BACKLOG", backlog)
    today = date(2026, 9, 25)
    assert rq.write_backlog(rq.merged_units(), today) is True
    first = backlog.read_text()
    assert rq.write_backlog(rq.merged_units(), today) is False
    assert backlog.read_text() == first
    assert first.startswith("# B\n\nintro\n\n") and first.endswith("\n\n## After\n")
    assert "stale" not in first


def test_backlog_leads_are_found_by_exact_unit_heading(tmp_path, monkeypatch) -> None:
    backlog = tmp_path / "BACKLOG.md"
    backlog.write_text("## Leads\n\n#### state:GA — Georgia\n- Hall County vote\n\n"
                       "#### state:GAX — nope\n- wrong\n\n## Next\n")
    monkeypatch.setattr(rq, "BACKLOG", backlog)
    assert rq.backlog_leads("state:GA") == "- Hall County vote"
    assert rq.backlog_leads("state:G") == ""
