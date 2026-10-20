"""scripts/revalidate.py: offline. Fetching is replaced by a fake fetcher."""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
_spec = importlib.util.spec_from_file_location("revalidate", ROOT / "scripts" / "revalidate.py")
rv = importlib.util.module_from_spec(_spec)
sys.modules["revalidate"] = rv
_spec.loader.exec_module(rv)

import refresh  # noqa: E402

LONG = "The council voted to approve the moratorium on new data centers for twelve months. " * 8


def test_enumeration_derives_from_every_payload_file():
    rows = rv.enumerate_sources()
    assert rows
    kinds = {r["kind"] for r in rows}
    # Every payload that holds a source_url shows up; none is hand-listed here.
    expected = set()
    for name in refresh.PAYLOAD_FILES:
        text = (refresh.SEED_DIR / f"{name}.json").read_text(encoding="utf-8")
        if '"source_url"' in text or '"url"' in text:
            expected.add(name)
    assert expected <= kinds
    assert all(r["url"].startswith("http") for r in rows)
    # international's nested record lists are walked too
    assert any(r["kind"] == "international" and r["list"] == "policies" for r in rows)


def test_enumeration_collects_nested_urls_and_quotes(tmp_path):
    (tmp_path / "claims.json").write_text(json.dumps({"claims": [
        {"id": "c1", "statement": "We will pay our own way.", "source_url": "https://a.test/x"}]}))
    (tmp_path / "policies.json").write_text(json.dumps({"policies": [
        {"id": "p1", "source_url": "https://b.test/p", "key_terms": ["Term one is here"],
         "resources": [{"url": "https://b.test/r", "title": "r"}]}]}))
    rows = rv.enumerate_sources(tmp_path, ["claims", "policies"])
    by = {(r["id"], r["url"]): r for r in rows}
    assert by[("c1", "https://a.test/x")]["quotes"] == ["We will pay our own way."]
    assert by[("p1", "https://b.test/p")]["quotes"] == ["Term one is here"]
    assert by[("p1", "https://b.test/r")]["role"] == "resource"
    assert by[("p1", "https://b.test/r")]["quotes"] == []


def test_filter_by_kind_list_and_id():
    rows = rv.enumerate_sources()
    assert {r["kind"] for r in rv.filter_rows(rows, only="claims")} >= {"claims"}
    assert {r["list"] for r in rv.filter_rows(rows, only="policies")} == {"policies"}
    one = rv.filter_rows(rows, rec_id=rows[0]["id"])
    assert one and all(r["id"] == rows[0]["id"] for r in one)


@pytest.mark.parametrize("status,final,text,want", [
    (200, "https://a.test/x", LONG, "live"),
    (404, "https://a.test/x", "", "dead"),
    (410, "https://a.test/x", "", "dead"),
    (403, "https://a.test/x", "", "blocked"),
    (429, "https://a.test/x", "", "blocked"),
    (503, "https://a.test/x", "", "blocked"),
    (200, "https://a.test/x", "Just a moment...", "blocked"),
    (0, "https://a.test/x", "FETCH-ERROR: Read timed out", "blocked"),
    (0, "https://a.test/x", "FETCH-ERROR: NameResolutionError", "dead"),
    (200, "https://other.test/x", LONG, "redirected"),
    (200, "https://a.test/", LONG, "redirected"),
])
def test_classify(status, final, text, want):
    assert rv.classify("https://a.test/x/y" if want == "redirected" and final.endswith("/") else "https://a.test/x",
                       status, final, text) == want


def test_fingerprint_change_detection(tmp_path):
    pages = {}
    pages_v = {"v": LONG}
    fetcher = lambda u: (200, u, pages_v["v"])
    rv.fetch_all(["https://a.test/x"], pages, fetcher, tmp_path, sleep=lambda s: None)
    assert pages["https://a.test/x"]["changed"] is False  # first sight is not a change
    rv.fetch_all(["https://a.test/x"], pages, fetcher, tmp_path, sleep=lambda s: None)
    assert pages["https://a.test/x"]["changed"] is False  # same text
    pages_v["v"] = LONG + " A new paragraph about a lawsuit filed in the county court."
    rv.fetch_all(["https://a.test/x"], pages, fetcher, tmp_path, sleep=lambda s: None)
    assert pages["https://a.test/x"]["changed"] is True


def test_blocked_day_keeps_last_fingerprint(tmp_path):
    pages = {}
    rv.fetch_all(["https://a.test/x"], pages, lambda u: (200, u, LONG), tmp_path, sleep=lambda s: None)
    fp = pages["https://a.test/x"]["fingerprint"]
    rv.fetch_all(["https://a.test/x"], pages, lambda u: (403, u, ""), tmp_path, sleep=lambda s: None)
    assert pages["https://a.test/x"]["class"] == "blocked"
    assert pages["https://a.test/x"]["fingerprint"] == fp
    assert pages["https://a.test/x"]["changed"] is False


def test_rate_limit_sleeps_between_same_host_only(tmp_path):
    sleeps = []
    rv.fetch_all(["https://a.test/1", "https://a.test/2", "https://b.test/1"], {},
                 lambda u: (200, u, LONG), tmp_path, delay=1.5, workers=1, sleep=sleeps.append)
    assert sleeps == [1.5]  # a.test twice -> one gap; b.test alone -> none


def test_fetch_exception_does_not_crash(tmp_path):
    def boom(u):
        raise RuntimeError("x")
    pages = rv.fetch_all(["https://a.test/1"], {}, boom, tmp_path, sleep=lambda s: None)
    assert pages["https://a.test/1"]["class"] == "unchecked"


def test_quote_check_hit_miss_and_unreadable(tmp_path):
    pages = {}
    rv.fetch_all(["https://a.test/x"], pages, lambda u: (200, u, LONG), tmp_path, sleep=lambda s: None)
    row = {"url": "https://a.test/x", "quotes": [
        "The council voted to approve the moratorium on new data centers for twelve months.",
        "The council also banned all cryptocurrency mining facilities in the county."]}
    misses = rv.check_quotes(row, pages["https://a.test/x"], tmp_path)
    assert len(misses) == 1 and "cryptocurrency" in misses[0]["quote"]
    blocked = {"class": "blocked"}
    assert rv.check_quotes(row, blocked, tmp_path) == []  # unreadable page: nothing was checked


def test_staleness_rules(tmp_path):
    today = date(2026, 10, 19)
    (tmp_path / "rate_cases.json").write_text(json.dumps({"rate_cases": [
        {"id": "rc-old", "status": "pending", "next_milestone_date": "2026-10-01"},
        {"id": "rc-future", "status": "pending", "next_milestone_date": "2026-12-01"},
        {"id": "rc-done", "status": "approved", "next_milestone_date": "2026-01-01"}]}))
    (tmp_path / "moratoriums.json").write_text(json.dumps({"moratoriums": [
        {"id": "m-prop-old", "status": "proposed", "captured_at": "2026-05-01"},
        {"id": "m-prop-new", "status": "proposed", "captured_at": "2026-10-10"},
        {"id": "m-ended", "status": "enacted", "effective_date": "2026-01-15", "duration_months": 6},
        {"id": "m-running", "status": "enacted", "effective_date": "2026-09-01", "duration_months": 6},
        {"id": "m-open", "status": "enacted", "effective_date": "2020-01-01"}]}))
    out = {s["id"] for s in rv.stale_statuses(tmp_path, today, 60, ["rate_cases", "moratoriums"])}
    assert out == {"rc-old", "m-prop-old", "m-ended"}


def test_add_months_clamps_month_end():
    assert rv.add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert rv.add_months(date(2026, 11, 15), 3) == date(2027, 2, 15)


def test_main_end_to_end_with_fake_fetcher(tmp_path, monkeypatch, capsys):
    seed = tmp_path / "seed"
    seed.mkdir()
    (seed / "claims.json").write_text(json.dumps({"claims": [
        {"id": "c-ok", "statement": "The council voted to approve the moratorium on new data centers.",
         "source_url": "https://a.test/ok"},
        {"id": "c-dead", "statement": "x" * 5, "source_url": "https://b.test/gone"}]}))
    monkeypatch.setattr(refresh, "SEED_DIR", seed)
    monkeypatch.setattr(refresh, "PAYLOAD_FILES", {"claims": None})
    fetcher = lambda u: (404, u, "") if "gone" in u else (200, u, LONG)
    cache = tmp_path / "cache"
    argv = ["--delay", "0", "--json", str(tmp_path / "r.json"), "--fail-on-dead"]
    assert rv.main(argv, fetcher=fetcher, cache_dir=cache) == 1
    rep = json.loads((tmp_path / "r.json").read_text())
    assert [d["id"] for d in rep["dead_links"]] == ["c-dead"]
    assert rep["quote_misses"] == []
    # --cached makes no fetches
    def nofetch(u):
        raise AssertionError("fetched in --cached mode")
    assert rv.main(["--cached"], fetcher=nofetch, cache_dir=cache) == 0
