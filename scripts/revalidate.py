#!/usr/bin/env python3
"""Token-free re-validation of every cited source in the seed payloads.

Spends no LLM tokens. It re-checks what a machine can check, so a refresh
only needs a model for the records this script puts on its worklist:

  * dead links          (404/410/DNS/refused, or a redirect to somewhere else)
  * quote misses        (claim `statement`, policy `key_terms` not on the page)
  * changed pages       (normalized-text fingerprint differs from last run)
  * stale statuses      (pending rate case past its milestone, old "proposed"
                         policy/moratorium, enacted moratorium past its end)

Usage:
    python scripts/revalidate.py --cached                 # offline, cache only
    python scripts/revalidate.py --limit 40               # oldest-checked first
    python scripts/revalidate.py --only moratoriums --json report.json
    python scripts/revalidate.py --id ny-state-eo62-2026-07 --fail-on-dead

Cache: .revalidate_cache/ (gitignored). pages.json holds status + fingerprint
per URL; text/<sha1>.txt holds the page text so --cached can re-run the quote
check offline. The first run for a URL records a fingerprint; "changed" only
appears from the second run on.

Fetching and quote matching are probe.py's (imported, not copied), so this
script and the evidence gate cannot disagree about what "on the page" means.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import fcntl
import json
import logging
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Optional
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import refresh  # noqa: E402  (PAYLOAD_FILES / SEED_DIR are the single source of truth)

_spec = importlib.util.spec_from_file_location("probe", ROOT / "scripts" / "probe.py")
probe = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("probe", probe)
_spec.loader.exec_module(probe)

log = logging.getLogger("revalidate")

CACHE_DIR = ROOT / ".revalidate_cache"
HOST_DELAY = 1.5
STALE_DAYS_DEFAULT = 60

LIVE, BLOCKED, DEAD, REDIRECTED, UNCHECKED = "live", "blocked", "dead", "redirected", "unchecked"
DEAD_STATUSES = {404, 410}
# Other 4xx (payment-required, method-not-allowed, request-timeout...) are
# almost always bot walls or flaky origins, never proof a page is gone.
BLOCKED_EXTRA = {402, 405, 408}
BACKOFF_START = 10.0   # CLAUDE.md network rules: 429 backs off from 10 s
MAX_429_RETRIES = 3
SAVE_EVERY = 50
MIN_COVERAGE_DEFAULT = 0.9
# A fetch that failed before any HTTP status: refused / DNS are dead, the rest
# (timeouts, SSL handshakes, resets) look like bot walls and stay "blocked".
_DEAD_ERROR_MARKERS = ("Name or service not known", "nodename nor servname", "getaddrinfo",
                       "NameResolutionError", "Connection refused", "No address associated")

CLASSIFIED = {LIVE, BLOCKED, DEAD, REDIRECTED}

Fetcher = Callable[[str], "tuple[int, str, str]"]


# --------------------------------------------------------------------------
# Enumeration
# --------------------------------------------------------------------------

def _iter_urls(node: Any) -> Iterator[str]:
    """Every http(s) URL held under a `source_url` or `url` key, at any depth."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("source_url", "url") and isinstance(v, str) and v.startswith("http"):
                yield v
            else:
                yield from _iter_urls(v)
    elif isinstance(node, list):
        for v in node:
            yield from _iter_urls(v)


def _records(payload: dict) -> Iterator["tuple[str, dict]"]:
    """(list_key, record) for every record list in a payload, one level deep
    (international.json nests its record lists under their own keys)."""
    for key, val in payload.items():
        if isinstance(val, list) and val and all(isinstance(x, dict) for x in val):
            for rec in val:
                yield key, rec


def enumerate_sources(seed_dir: Optional[Path] = None,
                      payload_names: Optional[list] = None) -> list:
    """One row per (record, url): kind, list, id, url, role, quotes.

    `quotes` is what must appear on the *record's own* source_url page: a
    claim's statement, a policy's key_terms. Resource / sub-record URLs carry
    no quotes. Derived from refresh.PAYLOAD_FILES, never a hand list."""
    seed_dir = seed_dir or refresh.SEED_DIR
    names = payload_names if payload_names is not None else list(refresh.PAYLOAD_FILES)
    rows = []
    for name in names:
        path = seed_dir / f"{name}.json"
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for list_key, rec in _records(payload):
            rid = rec.get("id") or rec.get("slug") or rec.get("name") or "?"
            quotes: list = []
            if list_key == "claims" and rec.get("statement"):
                quotes = [rec["statement"]]
            elif list_key == "policies":
                quotes = [t for t in rec.get("key_terms") or [] if isinstance(t, str)]
            primary = rec.get("source_url")
            seen = set()
            for url in _iter_urls(rec):
                if url in seen:
                    continue
                seen.add(url)
                rows.append({
                    "kind": name, "list": list_key, "id": rid, "url": url,
                    "role": "source" if url == primary else "resource",
                    "quotes": quotes if url == primary else [],
                })
    return rows


def filter_rows(rows: list, only: Optional[str] = None, rec_id: Optional[str] = None) -> list:
    out = rows
    if only:
        out = [r for r in out if only in (r["kind"], r["list"], f'{r["kind"]}.{r["list"]}')]
    if rec_id:
        out = [r for r in out if r["id"] == rec_id]
    return out


# --------------------------------------------------------------------------
# Classification + fingerprint
# --------------------------------------------------------------------------

def _path_of(url: str) -> str:
    return urlparse(url).path.rstrip("/")


def _host_of(url: str) -> str:
    """Lowercase host without www. and without a default port (:80/:443)."""
    p = urlparse(url)
    host = (p.hostname or "").lower().removeprefix("www.")
    if p.port and p.port not in (80, 443):
        host = f"{host}:{p.port}"
    return host


def classify(url: str, status: int, final_url: str, text: str) -> str:
    """live / blocked / dead / redirected. A 2xx whose final URL landed on a
    different host, or fell back to the site root from a deep path, is
    "redirected": the original page is gone even though something answered."""
    if status == 0:
        return DEAD if any(m in text for m in _DEAD_ERROR_MARKERS) else BLOCKED
    if status in DEAD_STATUSES:
        return DEAD
    if status in probe.BLOCKED_STATUSES or status in BLOCKED_EXTRA:
        return BLOCKED
    if status >= 500:
        return BLOCKED
    if 200 <= status < 300:
        host_a, host_b = _host_of(url), _host_of(final_url or url)
        if host_a != host_b or (_path_of(url) and not _path_of(final_url or url)):
            return REDIRECTED
        if len(text) < probe.MIN_TEXT:
            return BLOCKED  # a bot-wall interstitial is short
        return LIVE
    return DEAD if status in DEAD_STATUSES else BLOCKED


_MONTH = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?"
_DATE = (rf"(?:(?:19|20)\d\d-\d\d-\d\d(?:[t ]\d\d:\d\d(?::\d\d)?(?:\.\d+)?(?:z|[+-]\d\d:?\d\d)?)?"
         rf"|{_MONTH}\s+\d{{1,2}},?\s+(?:19|20)\d\d(?:,?\s+\d{{1,2}}:\d\d(?::\d\d)?\s*(?:[ap]\.?m\.?)?)?"
         rf"|\d{{1,2}}\s+{_MONTH}\s+(?:19|20)\d\d"
         rf"|\d{{1,2}}/\d{{1,2}}/(?:19|20)?\d\d)")
# Dates are removed ONLY in metadata contexts (a keyword introduces them) and in
# copyright notices. Every other date (hearing, vote, decision, deadline) stays
# in the fingerprint, because a changed hearing date is exactly what we want.
_VOLATILE = [
    re.compile(rf"\b(?:last\s+)?(?:updated|modified|published|posted|reviewed|revised)(?:\s+(?:on|at))?\s*:?\s*{_DATE}", re.I),
    re.compile(r"(?:\u00a9|\(c\)|copyright)\s*(?:19|20)\d\d(?:\s*[-\u2013]\s*(?:19|20)\d\d)?", re.I),
]


def strip_volatile(text: str) -> str:
    """Drop 'Updated/Posted/Reviewed: <date>' stamps and copyright years, so a
    page that only re-stamps itself does not read as changed. Other dates stay."""
    for rx in _VOLATILE:
        text = rx.sub(" ", text)
    return text


def fingerprint(text: str) -> str:
    return hashlib.sha1(probe.norm(strip_volatile(text)).lower().encode("utf-8")).hexdigest()


def _text_path(cache_dir: Path, url: str) -> Path:
    return cache_dir / "text" / (hashlib.sha1(url.encode()).hexdigest() + ".txt")


def load_cache(cache_dir: Path) -> dict:
    """Load pages.json. A corrupt file is moved to pages.json.corrupt and the
    run starts fresh; it never crashes the routine."""
    f = cache_dir / "pages.json"
    if not f.exists():
        return {}
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("pages.json is not an object")
        return data
    except (ValueError, OSError) as exc:
        backup = f.with_name("pages.json.corrupt")
        log.warning("corrupt cache %s (%s); starting fresh, backup at %s", f, exc, backup)
        try:
            os.replace(f, backup)
        except OSError as exc2:
            log.warning("could not back up corrupt cache: %s", exc2)
        return {}


def save_cache(cache_dir: Path, pages: dict) -> None:
    """Atomic: write a temp file, then os.replace, so a crash mid-write never
    leaves a truncated pages.json."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    final = cache_dir / "pages.json"
    # Merge with what is on disk rather than overwrite it. Two runs at once
    # (an --only run beside a full run) each held their own dict, and the last
    # writer erased the other's checks; a run killed before its final save
    # lost everything. Disk entries this run doesn't hold are kept, and a disk
    # entry checked later than ours wins.
    # Serialize the read-merge-replace: without a lock, two concurrent savers
    # each merge the same old file and the later os.replace drops the other's
    # entries.
    with open(cache_dir / "pages.json.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        _merge_and_replace(cache_dir, final, pages)


def _merge_and_replace(cache_dir: Path, final: Path, pages: dict) -> None:
    merged = dict(pages)
    if final.exists():
        try:
            on_disk = json.loads(final.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            log.warning("could not read existing cache for merge: %s", exc)
            on_disk = {}
        for url, entry in on_disk.items():
            mine = merged.get(url)
            if mine is None or entry.get("checked", "") > mine.get("checked", ""):
                merged[url] = entry
    tmp = cache_dir / f"pages.json.tmp.{os.getpid()}"
    tmp.write_text(json.dumps(merged, indent=1, sort_keys=True), encoding="utf-8")
    os.replace(tmp, final)


# --------------------------------------------------------------------------
# Fetching with per-host rate limit
# --------------------------------------------------------------------------

def check_url(url: str, prev: Optional[dict], fetcher: Fetcher, cache_dir: Path,
              now: Optional[str] = None,
              sleep: Callable[[float], None] = time.sleep) -> dict:
    """Fetch one URL, classify it, compare its fingerprint with the previous
    run's, and persist the text. Returns the new page entry."""
    status, final, text = fetcher(url)
    wait = BACKOFF_START
    for _ in range(MAX_429_RETRIES):
        if status != 429:
            break
        log.warning("429 from %s; backing off %.0fs", url, wait)
        sleep(wait)
        wait *= 2
        status, final, text = fetcher(url)
    cls = classify(url, status, final, text)
    entry = {"status": status, "final_url": final, "class": cls,
             "checked": now or datetime.now(timezone.utc).strftime("%Y-%m-%d")}
    prev = prev or {}
    if cls in (LIVE, REDIRECTED) and len(text) >= probe.MIN_TEXT:
        fp = fingerprint(text)
        entry["fingerprint"] = fp
        entry["fingerprint_prev"] = prev.get("fingerprint")
        entry["changed"] = bool(prev.get("fingerprint")) and prev["fingerprint"] != fp
        # A detected change stays pending across runs (incl. --cached) until acked.
        if entry["changed"]:
            entry["pending_change"] = True
            entry["changed_at"] = entry["checked"]
        elif prev.get("pending_change"):
            entry["pending_change"] = True
            if prev.get("changed_at"):
                entry["changed_at"] = prev["changed_at"]
        tp = _text_path(cache_dir, url)
        tp.parent.mkdir(parents=True, exist_ok=True)
        tp.write_text(text, encoding="utf-8")
    else:
        # Keep the last good fingerprint: a blocked day must not erase it.
        if "fingerprint" in prev:
            entry["fingerprint"] = prev["fingerprint"]
        entry["changed"] = False
        if prev.get("pending_change"):
            entry["pending_change"] = True
            if prev.get("changed_at"):
                entry["changed_at"] = prev["changed_at"]
    return entry


def fetch_all(urls: list, pages: dict, fetcher: Fetcher, cache_dir: Path,
              delay: float = HOST_DELAY, workers: int = 8,
              sleep: Callable[[float], None] = time.sleep,
              fetched: Optional[set] = None,
              save: Optional[Callable[[dict], None]] = None,
              save_every: int = SAVE_EVERY) -> dict:
    """Fetch urls, serial within a host (>= `delay` apart), parallel across hosts."""
    by_host: dict = {}
    for u in urls:
        by_host.setdefault(_host_of(u), []).append(u)
    lock = threading.Lock()
    done = [0]

    def run_host(host_urls: list) -> None:
        for i, u in enumerate(host_urls):
            if i:
                sleep(delay)
            try:
                entry = check_url(u, pages.get(u), fetcher, cache_dir, sleep=sleep)
            except Exception as exc:  # one URL must never crash the run
                log.error("check failed for %s: %s", u, exc)
                entry = {"status": 0, "final_url": u, "class": UNCHECKED, "error": str(exc),
                         "changed": False, "checked": date.today().isoformat()}
                # Carry the last good fingerprint so the next good fetch still
                # detects a change.
                prev = pages.get(u) or {}
                if "fingerprint" in prev:
                    entry["fingerprint"] = prev["fingerprint"]
                if prev.get("pending_change"):
                    entry["pending_change"] = True
                    if prev.get("changed_at"):
                        entry["changed_at"] = prev["changed_at"]
            with lock:
                pages[u] = entry
                if fetched is not None:
                    fetched.add(u)
                done[0] += 1
                if save and save_every and done[0] % save_every == 0:
                    save(pages)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(run_host, by_host.values()))
    return pages


# --------------------------------------------------------------------------
# Quote check
# --------------------------------------------------------------------------

def check_quotes(row: dict, page: Optional[dict], cache_dir: Path) -> list:
    """Misses for one row: quotes with a clause absent from a page that loaded.
    A page we could not read yields no misses (nothing was checked)."""
    if not row["quotes"] or not page or page.get("class") not in (LIVE, REDIRECTED):
        return []
    tp = _text_path(cache_dir, row["url"])
    if not tp.exists():
        return []
    text = tp.read_text(encoding="utf-8")
    misses = []
    for q in row["quotes"]:
        parts = probe.clauses(q)
        absent = [c for c in parts if not probe.find(text, c)]
        if parts and absent:
            misses.append({"quote": q, "missing_clauses": absent})
    return misses


# --------------------------------------------------------------------------
# Staleness
# --------------------------------------------------------------------------

def _d(s: Any) -> Optional[date]:
    try:
        return date.fromisoformat(str(s)[:10])
    except (ValueError, TypeError):
        return None


def add_months(d: date, months: int) -> date:
    y, m = divmod(d.month - 1 + months, 12)
    year, month = d.year + y, m + 1
    for day in (d.day, 30, 29, 28):
        try:
            return date(year, month, day)
        except ValueError:
            continue
    raise AssertionError("unreachable")


def stale_statuses(seed_dir: Optional[Path] = None, today: Optional[date] = None,
                   stale_days: int = STALE_DAYS_DEFAULT,
                   payload_names: Optional[list] = None) -> list:
    """Records whose stored status has probably moved on, by date arithmetic only."""
    seed_dir = seed_dir or refresh.SEED_DIR
    today = today or date.today()
    names = payload_names if payload_names is not None else list(refresh.PAYLOAD_FILES)
    out = []
    cutoff = today - timedelta(days=stale_days)
    for name in names:
        path = seed_dir / f"{name}.json"
        if not path.exists():
            continue
        for list_key, rec in _records(json.loads(path.read_text(encoding="utf-8"))):
            rid, status = rec.get("id"), rec.get("status")
            item = {"kind": name, "list": list_key, "id": rid, "status": status,
                    "url": rec.get("source_url")}
            if list_key == "rate_cases" and status == "pending":
                m = _d(rec.get("next_milestone_date"))
                if m and m < today:
                    out.append({**item, "reason": f"pending; next_milestone_date {m} has passed"})
            if list_key in ("policies", "moratoriums", "tariffs") and status == "proposed":
                cap = _d(rec.get("captured_at"))
                if cap and cap < cutoff:
                    out.append({**item, "reason": f"proposed; last captured {cap} (> {stale_days} days)"})
            if list_key == "moratoriums" and status == "enacted" and rec.get("duration_months"):
                start = _d(rec.get("effective_date")) or _d(rec.get("enacted_date"))
                if start:
                    end = add_months(start, int(rec["duration_months"]))
                    if end < today:
                        out.append({**item, "reason": f"enacted; {rec['duration_months']}-month term ended {end}"})
    return out


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------

def coverage_of(rows: list, pages: dict) -> "tuple[int, int]":
    """(rows with a CLASSIFIED cached check, total rows). An `unchecked` entry
    (check_url raised) is not coverage: nothing was learned about the page."""
    return sum(1 for r in rows if pages.get(r["url"], {}).get("class") in CLASSIFIED), len(rows)


def ack_changes(pages: dict, urls: Optional[set] = None) -> int:
    """Clear pending_change on `urls` (all if None); returns how many cleared."""
    n = 0
    for u, pg in pages.items():
        if pg.get("pending_change") and (urls is None or u in urls):
            pg["pending_change"] = False
            pg.pop("changed_at", None)
            n += 1
    return n


def build_report(rows: list, pages: dict, cache_dir: Path, stale: list,
                 fetched: Optional[set] = None) -> dict:
    """`changed_pages` lists every URL with a pending (unacknowledged) change,
    whether detected this run or an earlier one; `--ack-changes` clears them.
    `fetched` is kept for callers; it no longer gates changed pages."""
    dead, quote_misses, changed, unchecked = [], [], [], []
    for r in rows:
        pg = pages.get(r["url"])
        if not pg:
            continue
        ref = {k: r[k] for k in ("kind", "list", "id", "url", "role")}
        if pg["class"] in (DEAD, REDIRECTED):
            dead.append({**ref, "class": pg["class"], "status": pg["status"],
                         "final_url": pg.get("final_url")})
        if pg["class"] == UNCHECKED:
            unchecked.append({**ref, "error": pg.get("error")})
        if pg.get("pending_change") or (pg.get("changed") and r["url"] in (fetched or ())):
            changed.append({**ref, "changed_at": pg.get("changed_at") or pg.get("checked")})
        for miss in check_quotes(r, pg, cache_dir):
            quote_misses.append({**ref, **miss})
    blocked = sorted({r["url"] for r in rows if pages.get(r["url"], {}).get("class") == BLOCKED})
    return {"dead_links": dead, "quote_misses": quote_misses, "changed_pages": changed,
            "unchecked_urls": unchecked,
            "stale_statuses": stale, "blocked_urls": blocked,
            "urls_checked": coverage_of(rows, pages)[0],
            "rows_total": len(rows)}


def render_markdown(rep: dict) -> str:
    L = [f"# Revalidation worklist ({rep['urls_checked']} of {rep['rows_total']} source rows have a classified check)", ""]

    def section(title: str, items: list, fmt: Callable[[dict], str]) -> None:
        L.append(f"## {title} ({len(items)})")
        L.extend(fmt(i) for i in items) if items else L.append("None.")
        L.append("")

    section("Dead links", rep["dead_links"],
            lambda i: f"- `{i['kind']}.{i['list']}` **{i['id']}** [{i['class']} {i['status']}] {i['url']}"
                      + (f" -> {i['final_url']}" if i["class"] == REDIRECTED else ""))
    section("Quote misses", rep["quote_misses"],
            lambda i: f"- `{i['kind']}.{i['list']}` **{i['id']}** {i['url']}\n  - \"{i['quote'][:140]}\"\n"
                      f"  - missing: " + "; ".join(f'"{c[:80]}"' for c in i["missing_clauses"]))
    section("Changed pages (LLM work list)", rep["changed_pages"],
            lambda i: f"- `{i['kind']}.{i['list']}` **{i['id']}** {i['url']} (changed {i.get('changed_at')})")
    section("Unchecked (fetch raised; lowers coverage)", rep["unchecked_urls"],
            lambda i: f"- `{i['kind']}.{i['list']}` **{i['id']}** {i['url']} ({i.get('error')})")
    section("Stale statuses", rep["stale_statuses"],
            lambda i: f"- `{i['kind']}.{i['list']}` **{i['id']}** {i['reason']}")
    L.append(f"_Blocked (bot wall / timeout, not machine-verified): {len(rep['blocked_urls'])} URLs._")
    return "\n".join(L)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def select_urls(rows: list, pages: dict, limit: Optional[int]) -> list:
    """Unique URLs, never-checked first then oldest-checked, so successive
    --limit runs rotate through the whole set."""
    urls = list(dict.fromkeys(r["url"] for r in rows))
    urls.sort(key=lambda u: pages.get(u, {}).get("checked", ""))
    return urls[:limit] if limit else urls


def main(argv: Optional[list] = None, fetcher: Fetcher = probe.fetch,
         cache_dir: Path = CACHE_DIR) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cached", action="store_true", help="offline: use the cache only, fetch nothing")
    ap.add_argument("--only", help="payload (claims, international...) or list key (policies...)")
    ap.add_argument("--id", dest="rec_id", help="a single record id")
    ap.add_argument("--limit", type=int, help="check at most N URLs (oldest-checked first)")
    ap.add_argument("--json", dest="json_out", help="write the full report as JSON")
    ap.add_argument("--stale-days", type=int, default=STALE_DAYS_DEFAULT)
    ap.add_argument("--delay", type=float, default=HOST_DELAY)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--ack-changes", action="store_true",
                    help="after reporting, clear all pending changed-page flags (do this once the worklist is handled)")
    ap.add_argument("--fail-on-dead", action="store_true")
    ap.add_argument("--fail-on-miss", action="store_true")
    ap.add_argument("--min-coverage", type=float, default=MIN_COVERAGE_DEFAULT,
                    help="fail (under --fail-on-*) when fewer than this share of the selected rows has a cached check")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    rows = filter_rows(enumerate_sources(), args.only, args.rec_id)
    pages = load_cache(cache_dir)
    fetched: set = set()
    if not args.cached:
        urls = select_urls(rows, pages, args.limit)
        log.info("checking %d of %d unique URLs", len(urls), len({r['url'] for r in rows}))
        fetch_all(urls, pages, fetcher, cache_dir, delay=args.delay, workers=args.workers,
                  fetched=fetched, save=lambda p: save_cache(cache_dir, p))
        save_cache(cache_dir, pages)

    stale = [s for s in stale_statuses(stale_days=args.stale_days)
             if (not args.only or args.only in (s["kind"], s["list"]))
             and (not args.rec_id or s["id"] == args.rec_id)]
    rep = build_report(rows, pages, cache_dir, stale, fetched)
    have, total = coverage_of(rows, pages)
    coverage = have / total if total else 1.0
    if have < total:
        print(f"!! NOT CHECKED: {total - have} of {total} rows have no usable cached check "
              f"(coverage {coverage:.0%}). A clean report below does not mean clean.\n")
    print(render_markdown(rep))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(rep, indent=1), encoding="utf-8")
    if args.ack_changes:
        n = ack_changes(pages, {r["url"] for r in rows})
        save_cache(cache_dir, pages)
        log.info("acknowledged %d pending changes", n)
    code = 0
    if (args.fail_on_dead or args.fail_on_miss) and coverage < args.min_coverage:
        log.error("coverage %.0f%% is below --min-coverage %.0f%%", coverage * 100, args.min_coverage * 100)
        code = 1
    if args.fail_on_dead and rep["dead_links"]:
        code = 1
    if args.fail_on_miss and rep["quote_misses"]:
        code = 1
    return code


if __name__ == "__main__":
    sys.exit(main())
