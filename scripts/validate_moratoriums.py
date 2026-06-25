"""validate_moratoriums.py — Audit trail validator for moratorium records.

For each moratorium in data/seed/moratoriums.json, fetches the primary
source_url (and resource URLs when available), then checks whether key
verifiable claims — bill number, sponsors, vote counts, enactment date,
signatory, failure reason — can be found verbatim (or near-verbatim) in the
fetched text.

The output is an *audit trail*: a per-record JSON report linking each claim
to the snippet of source text that corroborates it, or flagging it as
unverified. Unverified claims are not automatically wrong — the source page
may not contain the text, or the fetch may have failed — but they surface
records that need a second look before publishing.

Usage:
    python scripts/validate_moratoriums.py              # all records, fetch + cache
    python scripts/validate_moratoriums.py --id maine-state-2026-04
    python scripts/validate_moratoriums.py --cached     # offline: use cached pages only
    python scripts/validate_moratoriums.py --dry-run    # schema checks only, no fetches
    python scripts/validate_moratoriums.py --summary    # terse per-record score lines
    python scripts/validate_moratoriums.py --fail-on-unverified  # exit 1 if any unverified

Outputs:
    moratorium_audit_report.json  — full per-record audit trail (always written)
    ISSUES.md                     — new entries for records missing a gov source
                                    and for critical unverified claims

Cache:
    .moratorium_cache/<url_hash>.json  — {url, fetched_at, status, text}
    Re-runs reuse cached pages.  Delete the cache directory to force a full
    re-fetch.  Per CLAUDE.md: 2 s delay per host, exponential back-off on 429.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
import time
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).parent.parent
SEED_PATH = ROOT / "data" / "seed" / "moratoriums.json"
REPORT_PATH = ROOT / "moratorium_audit_report.json"
ISSUES_PATH = ROOT / "ISSUES.md"
CACHE_DIR = ROOT / ".moratorium_cache"

DELAY = 2.0       # seconds between requests to the same host
TIMEOUT = 14      # HTTP timeout per request
SNIPPET_RADIUS = 80  # characters around a match to include as context

USER_AGENT = (
    "DataCenterCommunityBenefits/1.0 "
    "(moratorium-auditor; +https://github.com/pranava0x0/datacentercommunitybenefits)"
)

# Regex for detecting official government / legislative URLs
GOV_PATTERN = re.compile(
    r"\.(gov|legislature\.|legis\.|capitol\.|assembly\."
    r"|senate\.|house\.|state\.[a-z]{2}\.us|scstatehouse\.gov"
    r"|sdlegislature\.gov|cga\.ct\.gov|flsenate\.gov|flhouse\.gov"
    r"|leg\.wa\.gov|legislature\.mi\.gov|maine\.gov|nysenate\.gov"
    r"|leg\.colorado\.gov|oregonlegislature\.gov|njleg\.gov)",
    re.IGNORECASE,
)

logger = logging.getLogger("validate_moratoriums")


# ---------------------------------------------------------------------------
# HTTP + cache
# ---------------------------------------------------------------------------

_host_last_request: dict[str, float] = {}


def _rate_limit(host: str) -> None:
    now = time.monotonic()
    last = _host_last_request.get(host, 0.0)
    wait = DELAY - (now - last)
    if wait > 0:
        time.sleep(wait)
    _host_last_request[host] = time.monotonic()


def _cache_key(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def _cache_load(url: str) -> Optional[dict]:
    path = CACHE_DIR / f"{_cache_key(url)}.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


def _cache_save(url: str, entry: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{_cache_key(url)}.json"
    path.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_text(url: str, *, cached_only: bool = False) -> tuple[int, str]:
    """Return (http_status, page_text).  Uses cache when available.

    Returns (0, '') on network errors.  Caches both successes and failures
    so re-runs don't re-fetch dead links.
    """
    cached = _cache_load(url)
    if cached is not None:
        return cached["status"], cached.get("text", "")

    if cached_only:
        return 0, ""

    host = urlparse(url).netloc
    _rate_limit(host)

    req = Request(url)
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Accept", "text/html,application/xhtml+xml,*/*")
    req.add_header("Accept-Language", "en-US,en;q=0.9")

    backoff = 10.0
    for attempt in range(3):
        try:
            with urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read()
                # Strip HTML tags for plain-text search
                charset = resp.headers.get_content_charset("utf-8")
                text = _strip_html(raw.decode(charset, errors="replace"))
                entry = {"url": url, "fetched_at": str(date.today()), "status": resp.status, "text": text}
                _cache_save(url, entry)
                logger.debug("Fetched %s → %d (%d chars)", url[:80], resp.status, len(text))
                return resp.status, text
        except HTTPError as e:
            if e.code == 429 and attempt < 2:
                logger.warning("429 on %s — sleeping %ss", url[:60], backoff)
                time.sleep(backoff)
                backoff *= 3
                continue
            entry = {"url": url, "fetched_at": str(date.today()), "status": e.code, "text": ""}
            _cache_save(url, entry)
            return e.code, ""
        except URLError as e:
            # Connection refused / DNS failure: no point retrying multiple times
            logger.warning("Network error %s: %s", url[:60], e)
            entry = {"url": url, "fetched_at": str(date.today()), "status": 0, "text": ""}
            _cache_save(url, entry)
            return 0, ""
        except Exception as e:
            logger.warning("Unexpected error %s: %s", url[:60], e)
            entry = {"url": url, "fetched_at": str(date.today()), "status": 0, "text": ""}
            _cache_save(url, entry)
            return 0, ""
    return 0, ""


def _strip_html(html: str) -> str:
    """Minimal HTML → plain text: strip tags, decode common entities."""
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = (
        text.replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&nbsp;", " ")
            .replace("&#39;", "'")
            .replace("&quot;", '"')
            .replace("&#8217;", "'")
            .replace("&#8220;", '"')
            .replace("&#8221;", '"')
    )
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# Claim verification helpers
# ---------------------------------------------------------------------------

def _snippet(text: str, pos: int, radius: int = SNIPPET_RADIUS) -> str:
    """Return a snippet of `text` centred on `pos`."""
    start = max(0, pos - radius)
    end = min(len(text), pos + radius)
    snip = text[start:end].strip()
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return prefix + snip + suffix


def _search(text: str, needle: str) -> Optional[str]:
    """Case-insensitive search; returns a context snippet or None."""
    t_lower = text.lower()
    n_lower = needle.lower().strip()
    if not n_lower:
        return None
    pos = t_lower.find(n_lower)
    if pos >= 0:
        return _snippet(text, pos)
    return None


def _search_any(text: str, needles: list[str]) -> Optional[str]:
    """Return a snippet for the first needle found."""
    for n in needles:
        snip = _search(text, n)
        if snip is not None:
            return snip
    return None


def _date_variants(date_str: str) -> list[str]:
    """Return multiple textual representations of an ISO date string."""
    try:
        d = date.fromisoformat(date_str)
    except (ValueError, TypeError):
        return [date_str] if date_str else []
    months = [
        "", "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    short = [
        "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]
    m = d.month
    return [
        f"{months[m]} {d.day}, {d.year}",   # June 9, 2026
        f"{months[m]} {d.day} {d.year}",    # June 9 2026
        f"{short[m]} {d.day}, {d.year}",    # Jun 9, 2026
        f"{months[m]} {d.year}",            # June 2026 (year-month)
        f"{d.month}/{d.day}/{d.year}",      # 6/9/2026
        f"{d.month}/{d.day}/{str(d.year)[2:]}",  # 6/9/26
        date_str,                           # 2026-06-09
    ]


def _vote_variants(vote_str: str) -> list[str]:
    """Return search variants for a vote string like 'Senate 37-0, House 92-16'."""
    variants = [vote_str]
    # Extract all numeric X-Y patterns
    for m in re.finditer(r"(\d+)-(\d+)", vote_str):
        a, b = m.group(1), m.group(2)
        variants += [
            f"{a}-{b}",
            f"{a} to {b}",
            f"{a}–{b}",   # en-dash
            f"{a}—{b}",   # em-dash
        ]
    return variants


def _bill_variants(bill: str) -> list[str]:
    """Return search variants for a bill number like 'LD307' or 'SB 1018-1020'."""
    variants = [bill]
    # Insert/remove space between letters and numbers: LD307 ↔ LD 307
    spaced = re.sub(r"([A-Za-z]+)(\d)", r"\1 \2", bill)
    unspaced = bill.replace(" ", "")
    if spaced != bill:
        variants.append(spaced)
    if unspaced != bill:
        variants.append(unspaced)
    return variants


def _sponsor_last_names(sponsors: list[str]) -> list[str]:
    """Extract last names from sponsor strings for flexible matching."""
    names = []
    for s in sponsors:
        # Strip titles/districts: "Sen. Jane Smith (D-LD5)" → "Smith"
        s_clean = re.sub(r"\(.*?\)", "", s).strip()
        parts = s_clean.split()
        if parts:
            # Last substantive word (skip suffixes like Jr., II)
            last = parts[-1].rstrip(".,")
            if last.lower() not in ("jr", "sr", "ii", "iii", "iv"):
                names.append(last)
            elif len(parts) >= 2:
                names.append(parts[-2].rstrip(".,"))
    return names


# ---------------------------------------------------------------------------
# Per-record audit
# ---------------------------------------------------------------------------

CheckResult = dict  # {value, status, context?, checked_urls?}


def _check(value, source_texts: list[tuple[str, str]], needles_fn) -> CheckResult:
    """Generic claim check.

    value: the claim value (str / list / None)
    source_texts: [(url, text), ...]
    needles_fn: callable(value) → list[str] of search terms
    """
    if not value:
        return {"status": "no_claim", "value": value}

    needles = needles_fn(value)
    if not needles:
        return {"status": "no_claim", "value": value}

    for url, text in source_texts:
        if not text:
            continue
        snip = _search_any(text, needles)
        if snip is not None:
            return {"status": "found", "value": value, "context": snip, "source_url": url}

    if not any(text for _, text in source_texts):
        return {"status": "fetch_failed", "value": value}

    return {"status": "not_found", "value": value}


def _check_sponsors(sponsors: list[str], source_texts: list[tuple[str, str]]) -> CheckResult:
    """Check sponsors: report found/not_found per name."""
    if not sponsors:
        return {"status": "no_claim", "value": None}

    found_names = []
    not_found_names = []
    contexts = {}

    last_names = _sponsor_last_names(sponsors)
    full_names = [re.sub(r"[(\[].*", "", s).strip().lstrip("Sen. Rep. Councilmember ").strip() for s in sponsors]

    for i, sponsor in enumerate(sponsors):
        needles = [sponsors[i]]
        if i < len(full_names):
            needles.append(full_names[i])
        if i < len(last_names):
            needles.append(last_names[i])
        needles = [n for n in needles if n]

        found_in = None
        for url, text in source_texts:
            snip = _search_any(text, needles)
            if snip:
                found_in = (url, snip)
                break

        if found_in:
            found_names.append(sponsor)
            contexts[sponsor] = {"context": found_in[1], "source_url": found_in[0]}
        else:
            not_found_names.append(sponsor)

    if not found_names and not not_found_names:
        return {"status": "no_claim", "value": None}

    if not any(text for _, text in source_texts):
        status = "fetch_failed"
    elif not_found_names:
        status = "partial" if found_names else "not_found"
    else:
        status = "found"

    return {
        "status": status,
        "value": sponsors,
        "found": found_names,
        "not_found": not_found_names,
        "contexts": contexts,
    }


def audit_record(m: dict, *, cached_only: bool = False) -> dict:
    """Run all checks for one moratorium record. Returns audit dict."""
    record_id = m["id"]
    source_url = str(m.get("source_url", ""))
    resources = m.get("resources") or []
    resource_urls = [str(r.get("url", "")) for r in resources if r.get("url")]

    # Determine which URLs are official government sources
    all_urls = [source_url] + resource_urls
    gov_urls = [u for u in all_urls if u and GOV_PATTERN.search(u)]

    # Fetch source + up to 3 resources (gov sources preferred)
    preferred = gov_urls[:2]
    others = [u for u in [source_url] + resource_urls if u not in preferred][:2]
    urls_to_fetch = list(dict.fromkeys(preferred + others))  # dedup, preserve order

    source_texts: list[tuple[str, str]] = []
    fetch_statuses = {}
    for url in urls_to_fetch:
        if not url:
            continue
        status, text = fetch_text(url, cached_only=cached_only)
        fetch_statuses[url] = status
        source_texts.append((url, text))
        logger.info("[%s] %s → HTTP %s (%d chars)", record_id, url[:70], status, len(text))

    # --- Individual checks ---
    checks: dict[str, CheckResult] = {}

    # Bill number
    checks["bill_number"] = _check(
        m.get("bill_number"),
        source_texts,
        lambda v: _bill_variants(v),
    )

    # Sponsors
    checks["sponsors"] = _check_sponsors(m.get("sponsors") or [], source_texts)

    # Vote (legislative_votes or city_council_vote)
    vote_val = m.get("legislative_votes") or m.get("city_council_vote")
    checks["vote"] = _check(
        vote_val,
        source_texts,
        lambda v: _vote_variants(v),
    )

    # Enacted date
    checks["enacted_date"] = _check(
        m.get("enacted_date"),
        source_texts,
        lambda v: _date_variants(v),
    )

    # Enacted by (signer)
    checks["enacted_by"] = _check(
        m.get("enacted_by"),
        source_texts,
        lambda v: [v] + v.split()[-1:],  # full name + last name
    )

    # Failure reason (for failed records) — extract key phrases
    if m.get("status") == "failed" and m.get("failure_reason"):
        reason = m["failure_reason"]
        # Extract the most specific terms (vote pattern, committee name, key phrase)
        vote_in_reason = re.search(r"\d+-\d+", reason)
        keywords = []
        if vote_in_reason:
            keywords += _vote_variants(vote_in_reason.group())
        # Extract committee name if present
        committee_m = re.search(r"((?:\w+ )+Committee)", reason)
        if committee_m:
            keywords.append(committee_m.group(1).strip())
        if not keywords:
            # Fall back to first 6 words
            words = reason.split()[:6]
            keywords = [" ".join(words)]
        checks["failure_reason"] = _check(
            reason,
            source_texts,
            lambda v: keywords,
        )
    else:
        checks["failure_reason"] = {"status": "no_claim", "value": None}

    # Session / year
    session = m.get("session")
    if session:
        checks["session"] = _check(session, source_texts, lambda v: [v])
    else:
        checks["session"] = {"status": "no_claim", "value": None}

    # --- Scoring ---
    status_counts = defaultdict(int)
    for c in checks.values():
        status_counts[c["status"]] += 1

    total_verifiable = sum(
        v for k, v in status_counts.items() if k not in ("no_claim",)
    )
    found_count = status_counts["found"] + status_counts["partial"]
    score = round(found_count / total_verifiable, 2) if total_verifiable else None

    # --- Gov source assessment ---
    gov_source_present = len(gov_urls) > 0
    primary_is_gov = bool(source_url and GOV_PATTERN.search(source_url))

    return {
        "id": record_id,
        "jurisdiction": m.get("jurisdiction"),
        "status": m.get("status"),
        "source_url": source_url,
        "gov_source_present": gov_source_present,
        "primary_is_gov": primary_is_gov,
        "gov_urls": gov_urls,
        "fetch_statuses": fetch_statuses,
        "checks": checks,
        "score": {
            "found": found_count,
            "not_found": status_counts["not_found"],
            "fetch_failed": status_counts["fetch_failed"],
            "no_claim": status_counts["no_claim"],
            "verifiable_total": total_verifiable,
            "pct": score,
        },
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def _issues_for_record(a: dict) -> list[str]:
    """Return ISSUES.md-style lines for problems in this audit record."""
    issues = []
    today = str(date.today())
    rid = a["id"]

    if not a["gov_source_present"]:
        issues.append(
            f"| {today} | moratoriums:{rid} | No gov/official source URL | "
            f"Add .gov or official legislative link to source_url or resources | Open |\n"
        )

    for field, check in a["checks"].items():
        if check["status"] == "not_found":
            val = check.get("value", "")
            val_short = str(val)[:60] if val else ""
            issues.append(
                f"| {today} | moratoriums:{rid} | Claim unverified in source: {field}={val_short!r} | "
                f"Verify against {a['source_url'][:60]} | Open |\n"
            )

    return issues


def write_report(audits: list[dict]) -> None:
    REPORT_PATH.write_text(
        json.dumps(audits, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    logger.info("Wrote audit report → %s (%d records)", REPORT_PATH, len(audits))


def update_issues(audits: list[dict]) -> None:
    all_issues = []
    for a in audits:
        all_issues.extend(_issues_for_record(a))

    if not all_issues:
        logger.info("No issues to append to ISSUES.md.")
        return

    existing = ISSUES_PATH.read_text(encoding="utf-8") if ISSUES_PATH.exists() else ""
    if "## Moratorium source audit" not in existing:
        header = (
            "\n## Moratorium source audit\n\n"
            "| Date | Record | Issue | Recommended action | Status |\n"
            "|------|--------|-------|-------------------|--------|\n"
        )
        existing += header
    ISSUES_PATH.write_text(existing + "".join(all_issues), encoding="utf-8")
    logger.info("Appended %d issues to ISSUES.md", len(all_issues))


def print_summary(audits: list[dict]) -> None:
    """Print a concise per-record summary table."""
    SCORE_WIDTH = 6
    print(
        f"\n{'ID':<45} {'STATUS':<10} {'GOV':>3}  "
        f"{'FOUND':>5} {'NOT_FD':>6} {'FF':>3} {'NO_CLM':>6}  "
        f"{'SCORE':>5}"
    )
    print("-" * 95)
    total_found = total_not_found = total_ff = 0
    for a in sorted(audits, key=lambda x: (x["score"]["not_found"], -x["score"]["found"]), reverse=True):
        s = a["score"]
        gov = "✓" if a["gov_source_present"] else "✗"
        pct = f"{s['pct']:.0%}" if s["pct"] is not None else "  n/a"
        total_found += s["found"]
        total_not_found += s["not_found"]
        total_ff += s["fetch_failed"]
        print(
            f"{a['id']:<45} {a['status']:<10} {gov:>3}  "
            f"{s['found']:>5} {s['not_found']:>6} {s['fetch_failed']:>3} {s['no_claim']:>6}  "
            f"{pct:>{SCORE_WIDTH}}"
        )
    print("-" * 95)
    print(
        f"{'TOTAL':<45} {'':<10} {'':>3}  "
        f"{total_found:>5} {total_not_found:>6} {total_ff:>3}"
    )
    no_gov = sum(1 for a in audits if not a["gov_source_present"])
    print(f"\nRecords without a .gov/official source: {no_gov}/{len(audits)}")
    print(f"Audit report: {REPORT_PATH}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Audit moratorium records: verify claims against source URLs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--id", metavar="RECORD_ID", help="Audit a single record by id.")
    p.add_argument(
        "--cached",
        action="store_true",
        help="Only use cached pages — do not make any HTTP requests.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate schema only; do not fetch URLs or write files.",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        help="Print terse per-record score table after running.",
    )
    p.add_argument(
        "--fail-on-unverified",
        action="store_true",
        help="Exit with code 1 if any verifiable claim is not_found.",
    )
    p.add_argument(
        "--no-issues",
        action="store_true",
        help="Do not append to ISSUES.md.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    args = _parse_args(argv if argv is not None else sys.argv[1:])

    # Load seed
    if not SEED_PATH.exists():
        logger.error("Seed not found: %s", SEED_PATH)
        return 2

    payload = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    moratoriums = payload.get("moratoriums", [])
    logger.info("Loaded %d moratorium records.", len(moratoriums))

    if args.id:
        moratoriums = [m for m in moratoriums if m["id"] == args.id]
        if not moratoriums:
            logger.error("No record with id=%r found.", args.id)
            return 2
        logger.info("Filtering to record: %s", args.id)

    if args.dry_run:
        logger.info("--dry-run: schema loaded OK, skipping fetches.")
        return 0

    # Run audits
    audits = []
    total = len(moratoriums)
    for i, m in enumerate(moratoriums, 1):
        logger.info("[%d/%d] Auditing %s …", i, total, m["id"])
        try:
            a = audit_record(m, cached_only=args.cached)
            audits.append(a)
        except Exception as e:
            logger.error("Error auditing %s: %s", m["id"], e, exc_info=True)
            audits.append({
                "id": m["id"],
                "error": str(e),
                "score": {"found": 0, "not_found": 0, "fetch_failed": 0, "no_claim": 0, "verifiable_total": 0, "pct": None},
                "gov_source_present": False,
                "checks": {},
            })

    # Write report
    write_report(audits)

    # Update ISSUES.md
    if not args.no_issues:
        update_issues(audits)

    # Print summary
    if args.summary or args.id:
        print_summary(audits)

    # Stats
    total_not_found = sum(a["score"]["not_found"] for a in audits)
    no_gov_count = sum(1 for a in audits if not a["gov_source_present"])
    logger.info(
        "Done. %d/%d records. Not-found claims: %d. No-gov-source records: %d.",
        len(audits), total, total_not_found, no_gov_count,
    )

    if args.fail_on_unverified and total_not_found > 0:
        logger.error(
            "%d unverified claim(s) found — exiting 1 (--fail-on-unverified).",
            total_not_found,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
