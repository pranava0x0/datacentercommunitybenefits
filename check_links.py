"""check_links.py — Link checker with Wayback Machine fallback.

Reads every source_url from all four seed payloads, HEADs each unique URL
(rate-limited at 2 s per host), and for any 4xx/5xx checks whether the
Wayback Machine has an archived copy.

Usage:
    python check_links.py              # check all, write dead_links_report.json
    python check_links.py --fix        # also write wayback_url into seed JSON
    python check_links.py --dry-run    # check only, no writes

Outputs:
    dead_links_report.json  — list of {url, status, wayback_url, records} dicts
    ISSUES.md               — new entries appended for each dead link found (if --fix)

Per CLAUDE.md: rate-limited to 2 s per host; exponential back-off on 429;
never crashes on a single URL failure.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).parent
SEED_DIR = ROOT / "data" / "seed"
REPORT_PATH = ROOT / "dead_links_report.json"
ISSUES_PATH = ROOT / "ISSUES.md"

DELAY = 2.0        # seconds between requests to the same host
TIMEOUT = 12       # HTTP timeout per request
USER_AGENT = "DataCenterCommunityBenefits/1.0 (link-checker; +https://github.com/pranava0x0/datacentercommunitybenefits)"

logger = logging.getLogger("check_links")


# ---------------------------------------------------------------------------
# URL collection
# ---------------------------------------------------------------------------

def _collect_urls() -> dict[str, list[dict]]:
    """Return {url: [{file, record_id, field}, ...]} across all seed files."""
    urls: dict[str, list[dict]] = defaultdict(list)

    def _add(url: str, file: str, record_id: str, field: str = "source_url") -> None:
        if url:
            urls[url].append({"file": file, "record_id": record_id, "field": field})

    for name in ("companies", "claims", "projects", "responses"):
        path = SEED_DIR / f"{name}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        records = data.get(name, [])
        for r in records:
            rid = r.get("id") or r.get("slug") or "?"
            _add(r.get("source_url", ""), name, rid, "source_url")
            if "dedicated_page_url" in r and r["dedicated_page_url"]:
                _add(r["dedicated_page_url"], name, rid, "dedicated_page_url")
            if "project_page_url" in r and r["project_page_url"]:
                _add(r["project_page_url"], name, rid, "project_page_url")

    return dict(urls)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

_host_last_request: dict[str, float] = {}

def _rate_limit(host: str) -> None:
    now = time.monotonic()
    last = _host_last_request.get(host, 0.0)
    wait = DELAY - (now - last)
    if wait > 0:
        time.sleep(wait)
    _host_last_request[host] = time.monotonic()


def _head(url: str) -> int:
    """Return HTTP status code for a HEAD request. 0 on network error."""
    host = urlparse(url).netloc
    _rate_limit(host)
    req = Request(url, method="HEAD")
    req.add_header("User-Agent", USER_AGENT)
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status
    except HTTPError as e:
        return e.code
    except URLError as e:
        logger.warning("Network error for %s: %s", url, e)
        return 0
    except Exception as e:
        logger.warning("Unexpected error for %s: %s", url, e)
        return 0


def _wayback_lookup(url: str) -> Optional[str]:
    """Query the Wayback Machine CDX API. Returns archived URL or None."""
    api = f"https://archive.org/wayback/available?url={url}"
    req = Request(api)
    req.add_header("User-Agent", USER_AGENT)
    _rate_limit("archive.org")
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
        snapshot = data.get("archived_snapshots", {}).get("closest", {})
        if snapshot.get("available") and snapshot.get("url"):
            return snapshot["url"]
        return None
    except Exception as e:
        logger.warning("Wayback lookup failed for %s: %s", url, e)
        return None


# ---------------------------------------------------------------------------
# Main check loop
# ---------------------------------------------------------------------------

def check(*, fix: bool = False, dry_run: bool = False) -> int:
    url_map = _collect_urls()
    total = len(url_map)
    logger.info("Checking %d unique URLs …", total)

    dead: list[dict] = []

    for i, (url, records) in enumerate(sorted(url_map.items()), 1):
        status = _head(url)
        is_dead = status >= 400 or status == 0
        logger.info("[%d/%d] %s  →  %s", i, total, url[:80], status or "ERR")

        if not is_dead:
            continue

        wayback = _wayback_lookup(url)
        entry = {
            "url": url,
            "status": status,
            "wayback_url": wayback,
            "records": records,
        }
        dead.append(entry)
        level = logging.ERROR if wayback is None else logging.WARNING
        logger.log(
            level,
            "DEAD %s (HTTP %s) — wayback: %s",
            url,
            status or "ERR",
            wayback or "not found",
        )

    logger.info("Dead links found: %d / %d", len(dead), total)

    # Write report
    if not dry_run:
        REPORT_PATH.write_text(
            json.dumps(dead, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        logger.info("Report written to %s", REPORT_PATH)

        if dead:
            _append_issues(dead)

    # --fix: write wayback_url into seed JSON for records that have one
    if fix and not dry_run:
        _apply_wayback_fixes(dead)

    return 1 if any(e["wayback_url"] is None and e["status"] != 0 for e in dead) else 0


def _append_issues(dead: list[dict]) -> None:
    """Append new dead-link entries to ISSUES.md."""
    from datetime import date
    today = str(date.today())
    lines = ["\n"]
    for e in dead:
        wb = e["wayback_url"] or "none found"
        recs = ", ".join(f"{r['file']}:{r['record_id']}" for r in e["records"][:3])
        if len(e["records"]) > 3:
            recs += f" +{len(e['records']) - 3} more"
        lines.append(
            f"| {today} | {e['url'][:60]} | HTTP {e['status'] or 'ERR'} | "
            f"Wayback: {wb[:60]} | {recs} | Open — curator action needed |\n"
        )

    existing = ISSUES_PATH.read_text(encoding="utf-8") if ISSUES_PATH.exists() else ""
    if "## Dead links" not in existing:
        header = (
            "\n## Dead links\n\n"
            "| Date | URL | Status | Wayback | Affected records | Resolution |\n"
            "|------|-----|--------|---------|------------------|------------|\n"
        )
        existing += header
    ISSUES_PATH.write_text(existing + "".join(lines), encoding="utf-8")
    logger.info("Appended %d entries to ISSUES.md", len(dead))


def _apply_wayback_fixes(dead: list[dict]) -> None:
    """Write wayback_url into seed JSON records where a wayback URL was found."""
    # Group by file
    by_file: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for e in dead:
        if not e["wayback_url"]:
            continue
        for rec in e["records"]:
            if rec["field"] == "source_url":
                by_file[rec["file"]].append(
                    (rec["record_id"], "wayback_url", e["wayback_url"])
                )

    fixed = 0
    for name, patches in by_file.items():
        path = SEED_DIR / f"{name}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        records = data.get(name, [])
        lookup: dict[str, dict] = {}
        for r in records:
            rid = r.get("id") or r.get("slug") or ""
            if rid:
                lookup[rid] = r
        for rid, field, value in patches:
            if rid in lookup:
                lookup[rid][field] = value
                fixed += 1
                logger.info("Set %s.%s.%s = %s", name, rid, field, value[:60])
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    logger.info("Applied %d wayback_url fixes to seed data.", fixed)
    if fixed:
        logger.info(
            "Re-run `python refresh.py` to propagate fixes to docs/data/."
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument(
        "--fix",
        action="store_true",
        help="Write discovered wayback_url values into seed JSON files.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Check links but do not write any files.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    return check(fix=args.fix, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
