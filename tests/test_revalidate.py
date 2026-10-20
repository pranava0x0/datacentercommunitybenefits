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


# ---- review-fix regressions ------------------------------------------------

def _seed(tmp_path, monkeypatch, n=2):
    seed = tmp_path / "seed"
    seed.mkdir()
    (seed / "claims.json").write_text(json.dumps({"claims": [
        {"id": f"c{i}", "statement": "x" * 5, "source_url": f"https://a{i}.test/p"} for i in range(n)]}))
    monkeypatch.setattr(refresh, "SEED_DIR", seed)
    monkeypatch.setattr(refresh, "PAYLOAD_FILES", {"claims": None})


def test_empty_cache_is_not_a_clean_pass(tmp_path, monkeypatch, capsys):
    _seed(tmp_path, monkeypatch)
    nofetch = lambda u: (_ for _ in ()).throw(AssertionError("fetched"))
    code = rv.main(["--cached", "--fail-on-dead"], fetcher=nofetch, cache_dir=tmp_path / "c")
    assert code == 1
    assert "NOT CHECKED: 2 of 2 rows have no usable cached check" in capsys.readouterr().out
    # without a fail flag it still warns loudly but does not exit non-zero
    assert rv.main(["--cached"], fetcher=nofetch, cache_dir=tmp_path / "c") == 0
    # a lowered threshold lets partial coverage pass
    assert rv.main(["--cached", "--fail-on-dead", "--min-coverage", "0"],
                   fetcher=nofetch, cache_dir=tmp_path / "c") == 0


def test_full_coverage_has_no_banner(tmp_path, monkeypatch, capsys):
    _seed(tmp_path, monkeypatch)
    rv.main(["--delay", "0", "--fail-on-dead"], fetcher=lambda u: (200, u, LONG), cache_dir=tmp_path / "c")
    assert "NOT CHECKED" not in capsys.readouterr().out


def test_cache_saved_periodically_and_atomically(tmp_path):
    saves = []
    urls = [f"https://h{i}.test/x" for i in range(5)]
    rv.fetch_all(urls, {}, lambda u: (200, u, LONG), tmp_path, workers=1, sleep=lambda s: None,
                 save=lambda p: saves.append(len(p)), save_every=2)
    assert len(saves) == 2
    rv.save_cache(tmp_path, {"u": {"class": "live"}})
    assert json.loads((tmp_path / "pages.json").read_text()) == {"u": {"class": "live"}}
    assert not list(tmp_path.glob("pages.json.tmp*"))


def test_corrupt_cache_starts_fresh_with_backup(tmp_path):
    (tmp_path / "pages.json").write_text('{"truncated": ')
    assert rv.load_cache(tmp_path) == {}
    assert (tmp_path / "pages.json.corrupt").read_text() == '{"truncated": '


def test_exception_keeps_previous_fingerprint(tmp_path):
    pages = {}
    rv.fetch_all(["https://a.test/x"], pages, lambda u: (200, u, LONG), tmp_path, sleep=lambda s: None)
    fp = pages["https://a.test/x"]["fingerprint"]
    def boom(u):
        raise RuntimeError("x")
    rv.fetch_all(["https://a.test/x"], pages, boom, tmp_path, sleep=lambda s: None)
    assert pages["https://a.test/x"]["fingerprint"] == fp
    rv.fetch_all(["https://a.test/x"], pages, lambda u: (200, u, LONG + " Brand new lawsuit paragraph."),
                 tmp_path, sleep=lambda s: None)
    assert pages["https://a.test/x"]["changed"] is True


@pytest.mark.parametrize("url,final", [
    ("https://a.test/x", "https://a.test:443/x/"),
    ("http://a.test/x", "http://a.test:80/x"),
    ("https://a.test/x/", "https://www.a.test/x"),
])
def test_classify_ignores_default_port_and_slash(url, final):
    assert rv.classify(url, 200, final, LONG) == "live"


def test_classify_nondefault_port_is_redirect():
    assert rv.classify("https://a.test/x", 200, "https://a.test:8443/x", LONG) == "redirected"


@pytest.mark.parametrize("status,want", [(402, "blocked"), (405, "blocked"), (408, "blocked"),
                                         (418, "blocked"), (404, "dead"), (410, "dead")])
def test_classify_only_404_410_are_dead(status, want):
    assert rv.classify("https://a.test/x", status, "https://a.test/x", "") == want


def test_429_backs_off_exponentially_then_succeeds(tmp_path):
    seq = iter([(429, "u", ""), (429, "u", ""), (200, "https://a.test/x", LONG)])
    sleeps = []
    e = rv.check_url("https://a.test/x", None, lambda u: next(seq), tmp_path, sleep=sleeps.append)
    assert sleeps == [10.0, 20.0] and e["class"] == "live"


def test_429_retries_capped_at_three(tmp_path):
    calls, sleeps = [], []
    def f(u):
        calls.append(u)
        return 429, u, ""
    e = rv.check_url("https://a.test/x", None, f, tmp_path, sleep=sleeps.append)
    assert len(calls) == 4 and sleeps == [10.0, 20.0, 40.0] and e["class"] == "blocked"


def test_fingerprint_ignores_volatile_text():
    a = LONG + " Last updated: March 3, 2026. (c) 2025 Acme Corp. Posted 2026-03-03T10:00:00Z"
    b = LONG + " Last updated: October 19, 2026. (c) 2026 Acme Corp. Posted 2026-10-19T08:30:00Z"
    assert rv.fingerprint(a) == rv.fingerprint(b)
    assert rv.fingerprint(a) != rv.fingerprint(LONG + " The council added a new hearing.")


def test_changed_only_reported_for_urls_fetched_this_run(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, n=1)
    cache = tmp_path / "c"
    v = {"t": LONG}
    f = lambda u: (200, u, v["t"])
    out = tmp_path / "r.json"
    rv.main(["--delay", "0"], fetcher=f, cache_dir=cache)
    v["t"] = LONG + " A new paragraph about a lawsuit filed in the county court."
    rv.main(["--delay", "0", "--json", str(out)], fetcher=f, cache_dir=cache)
    assert len(json.loads(out.read_text())["changed_pages"]) == 1
    # replay from cache: the pending change must resurface until acknowledged
    rv.main(["--cached", "--json", str(out)], fetcher=f, cache_dir=cache)
    assert len(json.loads(out.read_text())["changed_pages"]) == 1
    rv.main(["--cached", "--ack-changes"], fetcher=f, cache_dir=cache)
    rv.main(["--cached", "--json", str(out)], fetcher=f, cache_dir=cache)
    assert json.loads(out.read_text())["changed_pages"] == []


def test_pending_change_survives_blocked_refetch_and_cached_run(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, n=1)
    cache, out = tmp_path / "c", tmp_path / "r.json"
    v = {"r": (200, LONG)}
    f = lambda u: (v["r"][0], u, v["r"][1])
    rv.main(["--delay", "0"], fetcher=f, cache_dir=cache)
    v["r"] = (200, LONG + " A new paragraph about a lawsuit filed in the county court.")
    rv.main(["--delay", "0"], fetcher=f, cache_dir=cache)
    v["r"] = (403, "")
    rv.main(["--delay", "0"], fetcher=f, cache_dir=cache)
    rv.main(["--cached", "--json", str(out)], fetcher=f, cache_dir=cache)
    assert len(json.loads(out.read_text())["changed_pages"]) == 1


def test_unchecked_entries_are_not_coverage(tmp_path, monkeypatch, capsys):
    _seed(tmp_path, monkeypatch, n=2)
    def f(u):
        if "a0" in u:
            raise RuntimeError("boom")
        return 200, u, LONG
    out = tmp_path / "r.json"
    code = rv.main(["--delay", "0", "--fail-on-dead", "--json", str(out)], fetcher=f, cache_dir=tmp_path / "c")
    text = capsys.readouterr().out
    assert code == 1 and "NOT CHECKED: 1 of 2" in text
    rep = json.loads(out.read_text())
    assert [u["id"] for u in rep["unchecked_urls"]] == ["c0"]
    assert rep["urls_checked"] == 1


def test_hearing_date_change_is_a_change_but_last_updated_is_not():
    base = LONG + " The public hearing is scheduled for March 3, 2026 at city hall."
    moved = base.replace("March 3, 2026", "April 14, 2026")
    assert rv.fingerprint(base) != rv.fingerprint(moved)
    a = LONG + " Last updated: March 3, 2026"
    b = LONG + " Last updated: October 19, 2026"
    assert rv.fingerprint(a) == rv.fingerprint(b)
    c = LONG + " Hearing 2026-03-03. Updated 2026-01-01"
    d = LONG + " Hearing 2026-03-03. Updated 2026-09-09"
    e = LONG + " Hearing 2026-04-04. Updated 2026-01-01"
    assert rv.fingerprint(c) == rv.fingerprint(d) != rv.fingerprint(e)


def test_save_cache_merges_with_a_concurrent_run(tmp_path) -> None:
    """Two runs at once used to erase each other's checks (last writer won)."""
    import json as _json
    rv.save_cache(tmp_path, {"https://a.example/": {"checked": "2026-10-19", "class": "live"}})
    rv.save_cache(tmp_path, {"https://b.example/": {"checked": "2026-10-19", "class": "dead"}})
    on_disk = _json.loads((tmp_path / "pages.json").read_text())
    assert set(on_disk) == {"https://a.example/", "https://b.example/"}
    # A newer check on disk is not overwritten by an older one held in memory.
    rv.save_cache(tmp_path, {"https://a.example/": {"checked": "2026-10-01", "class": "dead"}})
    assert _json.loads((tmp_path / "pages.json").read_text())["https://a.example/"]["class"] == "live"
