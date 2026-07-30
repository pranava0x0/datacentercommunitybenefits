"""Scout accelerator -- mechanical "is there anything new?" sweeps.

Complements `connectors.research` (which finds GAPS in records that already
exist) by finding CANDIDATES for records that don't exist yet: new project
announcements, new moratorium/tariff bills. It automates the fetch-and-diff
mechanics that a research agent otherwise has to redo by hand every refresh --
see REFRESH.md's "Finding New Announcements" and "Moratoriums & Tariffs
Refresh" sections for the manual version this replaces.

    python -m connectors.scout projects
    python -m connectors.scout moratoriums
    python -m connectors.scout all --json

What this CAN do:
- Fetch a fixed list of index/listing pages (politely, cached, rate-limited --
  the same CachedSession as connectors.research) and extract headline/link
  candidates.
- Filter to data-center-relevant headlines by keyword.
- Diff each candidate against the existing seed by state/city/company/
  jurisdiction token overlap, to separate "probably already tracked" from
  "no match found in the seed".

What this CANNOT do (each of these bit a human or an agent during past
refresh sessions -- see REFRESH.md's "Learned patterns" for the incidents):
- Confirm a fact is actually ON a page vs. only in a search engine's
  synthesized summary -- every candidate here still needs a direct fetch +
  read before it becomes a record (2026-07-14 lesson).
- Tell a real moratorium from a "voted to study" resolution, or a headline's
  loaded word ("ban") from the underlying legal instrument -- that is a
  reading-comprehension judgment call, not a keyword match (the Loudoun
  County lesson, hit three separate times).
- Disambiguate a place name against a differently-named existing seed record
  (a "Montgomery County" headline vs. a seed row filed under "New Florence").
  The token-overlap heuristic here is best-effort. A "NO MATCH" is a lead to
  check by hand, not proof of novelty; a "MATCH" is not proof of an actual
  duplicate either.
- Extract or verify first-party verbatim quotes, judge the two-gate editorial
  test for a new company, or make any stance/constituency call -- fully out
  of scope, same as `connectors.research`.
- Fetch a source that bot-walls a plain HTTP client but allows a real browser
  or an agent's WebFetch tool. `--offline`-free runs report these as
  "blocked", not silently drop them -- see the "blocked sources" note in the
  report output. Several known-good sources for this project
  (datacenterdynamics.com article pages, citizenportal.ai, some .gov docket
  search UIs) fall in this bucket; this script can still fetch their *index*
  pages some of the time even when individual article pages 403.

In short: this turns "spend an agent run fetching ~15 known sources and
manually cross-checking headlines against the seed" into "run one command and
read a shortlist of leads." It does not turn "verify and curate a new
record" into a zero-judgment task -- see CLAUDE.md's editorial rules for why
that stays a human/agent job.
"""

from __future__ import annotations

import argparse
import html as _html
import json
import logging
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

from connectors.http import CachedSession, FetchError

log = logging.getLogger("connectors.scout")

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "seed"

# -- sources ------------------------------------------------------------------
# Mirrors REFRESH.md's "Finding New Announcements" + "Moratoriums & Tariffs
# Refresh" source lists. This is now the single source of truth for what a
# `scout` sweep checks -- add/remove a source here, not just in REFRESH.md's
# prose, or the two will drift (CLAUDE.md's single-source-of-truth rule).
PROJECT_SOURCES: dict[str, str] = {
    "dcd_construction": "https://www.datacenterdynamics.com/en/news/?term=construction-site-selection",
    "meta": "https://datacenters.atmeta.com/",
    "google": "https://blog.google/innovation-and-ai/infrastructure-and-cloud/",
    "microsoft": "https://news.microsoft.com/source/topics/datacenters/",
    "amazon": "https://www.aboutamazon.com/news/aws",
    "openai": "https://openai.com/news/",
    "oracle": "https://www.oracle.com/news/announcement/",
    "xai": "https://x.ai/news",
    "qts": "https://q.com/news/",
    "coreweave": "https://www.coreweave.com/news",
    "crusoe": "https://www.crusoe.ai/resources/blog",
    "sb_energy": "https://sbenergy.com/communities/",
    "brookfield": "https://bam.brookfield.com/views-news/newsroom",
    "doe_hub": "https://www.energy.gov/powering-americas-ai-future-data-center-resource-hub",
}

MORATORIUM_TARIFF_SOURCES: dict[str, str] = {
    "datacenterbans": "https://www.datacenterbans.com/",
    "interconnected_capital": "https://www.interconnectedcapital.com/research/data-center-moratoriums",
    "good_jobs_first": "https://www.goodjobsfirst.org/",
    "halcyon_tariffs": "https://halcyon.io/large-load-tariff-tracker",
}

# An extracted headline must contain at least one of these (case-insensitive)
# to be reported as a candidate -- cuts index-page chrome (nav links, unrelated
# stories) down to on-topic items only.
RELEVANCE_KEYWORDS = [
    "data center", "datacenter", "data centre", "hyperscale", "ai campus",
    "gigawatt", "megawatt", " gw ", " mw ", "moratorium", "tariff",
    "large load", "large-load", "rate case", "ratepayer",
]

MIN_DISTINCTIVE_LEN = 4  # a token this long or longer can match on its own
_WORD = re.compile(r"[a-z0-9]+")


def _words(text: str) -> set[str]:
    """Punctuation-stripped lowercase word set, e.g. 'LaGrange, Georgia' -> {'lagrange', 'georgia'}."""
    return set(_WORD.findall(text.lower()))

# -- HTML link extraction ------------------------------------------------------
_A_TAG = re.compile(r'<a\b[^>]*href=(["\'])(.*?)\1[^>]*>(.*?)</a>', re.I | re.S)
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def _clean(fragment: str) -> str:
    return _WS.sub(" ", _html.unescape(_TAG.sub(" ", fragment))).strip()


def extract_links(page: str, base_url: str) -> list[dict]:
    """Every `<a href>` on the page as `{title, url}`, resolved to absolute URLs.

    No relevance filtering here -- that's `relevant()`'s job. Dedupes by
    (title, url) since index pages often repeat a headline as both an image
    link and a text link.
    """
    seen: set[tuple[str, str]] = set()
    out: list[dict] = []
    for m in _A_TAG.finditer(page):
        href, inner = m.group(2), m.group(3)
        title = _clean(inner)
        if not title or len(title) < 8:
            continue
        if href.startswith(("#", "mailto:", "javascript:", "tel:")):
            continue
        url = urljoin(base_url, href)
        if urlparse(url).scheme not in ("http", "https"):
            continue
        key = (title.lower(), url)
        if key in seen:
            continue
        seen.add(key)
        out.append({"title": title, "url": url})
    return out


def _padded(text: str) -> str:
    """Lowercase with runs of non-alphanumerics collapsed to a single space,
    padded at both ends -- so a phrase match isn't defeated by a trailing
    comma/period ('LaGrange, Georgia' -> ' lagrange georgia ')."""
    return " " + _WS.sub(" ", re.sub(r"[^a-z0-9]+", " ", text.lower())) + " "


def relevant(title: str) -> bool:
    t = _padded(title)
    # _padded() both normalizes the title AND the keyword the same way, so a
    # plain `_padded(keyword) in t` is already word-boundary-safe -- no raw
    # substring fallback needed. An earlier version had one (`k.strip() in
    # t`) to work around a padding bug of its own; that fallback is exactly
    # what let "gw" match inside "Edgware" (unrelated headline), since a raw
    # substring check ignores word boundaries entirely. Fixed by padding the
    # keyword's own whitespace away first (`k.strip()`) instead of adding a
    # second, unsafe check.
    return any(_padded(k.strip()) in t for k in RELEVANCE_KEYWORDS)


# -- seed fingerprints ----------------------------------------------------
def _load(name: str) -> list[dict]:
    payload = json.loads((SEED / f"{name}.json").read_text())
    key = name if name in payload else next(k for k, v in payload.items() if isinstance(v, list))
    return payload[key]


# Generic words that show up inside company/utility names (SB "Energy",
# "Brookfield" Asset Management "Group", "Duke Energy", Big Rivers "Electric"
# Power Corporation) but are common enough in unrelated headlines to produce
# false-positive matches on their own -- e.g. an unrelated ESIG "Large Load
# Task Force" headline matched "sb-energy" purely on "energy" + "group"
# before this list existed, and a generic Indiana rate-case headline matched
# a Duke Energy Indiana tariff purely on "energy" + "indiana" before this
# list was applied to utility names too (2026-07-30 review). Applied to
# EVERY fingerprint source below -- company names, utility names -- not just
# companies; a city/county/jurisdiction name is assumed distinctive enough
# not to need it.
_GENERIC_WORDS = {
    "energy", "group", "power", "electric", "systems", "corp", "corporation",
    "inc", "llc", "company", "holdings", "partners", "capital", "solutions",
    "cooperative", "co", "utilities", "utility",
}

# US utilities routinely embed their state in their own name ("Duke Energy
# Indiana", "AEP Ohio", "Entergy Mississippi") -- found via a test failure
# 2026-07-30: after _GENERIC_WORDS strips "Energy", "Duke Energy Indiana"
# left {"duke", "indiana"}, and "indiana" (7 letters) alone is "distinctive"
# by length even though a state name is the opposite of distinctive -- it is
# a legitimate word in nearly every headline about that state, regardless of
# subject. Spelled-out state names are excluded from fingerprint tokens
# entirely (the 2-letter code already covers the "same state" signal, at the
# lower "not enough alone" weight that short tokens get).
_STATE_NAMES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "hampshire", "jersey", "mexico", "york", "carolina", "dakota", "ohio",
    "oklahoma", "oregon", "pennsylvania", "rhode", "island", "tennessee",
    "texas", "utah", "vermont", "virginia", "washington", "wisconsin",
    "wyoming",
}


def project_fingerprints() -> list[dict]:
    """One fingerprint per seed project: city/state + company-name tokens."""
    companies = {c["slug"]: c["name"] for c in _load("companies")}
    out = []
    for p in _load("projects"):
        tokens = _words(p.get("city", "")) | _words(p.get("state", ""))
        tokens |= _words(companies.get(p["company_slug"], "")) - _GENERIC_WORDS - _STATE_NAMES
        out.append({"id": p["id"], "tokens": tokens})
    return out


def moratorium_fingerprints() -> list[dict]:
    # NOTE: _STATE_NAMES is intentionally NOT applied here -- a jurisdiction
    # can legitimately be named after a state word ("Washington County"),
    # unlike a company/utility name where the state is incidental to the
    # brand. Stripping it would make exactly those jurisdictions unmatchable
    # by their most distinctive word.
    out = []
    for r in _load("moratoriums"):
        tokens = _words(r.get("jurisdiction", "")) | _words(r.get("state_code", "") or "")
        out.append({"id": r["id"], "tokens": tokens})
    return out


def tariff_fingerprints() -> list[dict]:
    out = []
    for r in _load("tariffs"):
        utility_tokens = _words(r.get("utility", "")) - _GENERIC_WORDS - _STATE_NAMES
        tokens = utility_tokens | _words(r.get("state", ""))
        out.append({"id": r["id"], "tokens": tokens})
    return out


def match_existing(title: str, fingerprints: list[dict]) -> str | None:
    """Best-effort: does this headline share enough words with an existing
    record's city/state/company/jurisdiction tokens to call it a match?

    A match needs EITHER one "distinctive" token (length >= MIN_DISTINCTIVE_LEN,
    e.g. a city or company name) OR two shorter tokens together (so a bare
    2-letter state code never matches alone). The distinctive/short split
    matters: an earlier version required 2 tokens unconditionally, which
    filtered out state-code tokens (length 2) as too short to count at all --
    meaning a single-word jurisdiction like "Denver" could NEVER clear the
    bar even with an exact headline match, because "denver" (1 token) plus
    "co" (filtered) never reached 2. Confirmed against the live seed
    2026-07-30: that version left 57 of 111 moratorium records structurally
    unmatchable regardless of headline wording.

    Returns the best-matching record id, or None. Read the module docstring
    before trusting either outcome -- this is a heuristic, not a verdict.
    """
    title_words = _words(title)
    best_id, best_score = None, 0
    for fp in fingerprints:
        hits = [tok for tok in fp["tokens"] if tok in title_words]
        distinctive = sum(1 for tok in hits if len(tok) >= MIN_DISTINCTIVE_LEN)
        if distinctive >= 1 or len(hits) >= 2:
            score = distinctive * 2 + len(hits)  # for picking the BEST match only
            if score > best_score:
                best_id, best_score = fp["id"], score
    return best_id


# -- sweep ------------------------------------------------------------------
def sweep(sources: dict[str, str], fingerprints: list[dict], sess: CachedSession) -> dict:
    """Fetch every source and diff its headlines against the fingerprints.

    Index/listing pages are live documents -- new headlines appear at the
    SAME url every refresh. `sess.get(..., refresh=not sess.offline)` forces
    a live re-fetch on every non-offline run; the alternative (the default
    `refresh=False`) would silently keep serving the first run's cached
    snapshot forever, defeating the entire point of a repeatable "is there
    anything new?" sweep (caught by review, 2026-07-30, before this ever
    shipped as a false sense of "checked"). `--offline` runs still want the
    cache-only behavior, so honor `sess.offline` rather than hardcoding True.
    """
    fetched, blocked, candidates = [], [], []
    for name, url in sources.items():
        try:
            rec = sess.get(url, refresh=not sess.offline)
        except FetchError as exc:
            log.warning("fetch failed for %s (%s): %s", name, url, exc)
            blocked.append({"source": name, "url": url, "error": str(exc)})
            continue
        if rec["status"] != 200:
            blocked.append({"source": name, "url": url, "status": rec["status"]})
            continue
        fetched.append(name)
        for link in extract_links(rec["text"], rec["final_url"]):
            if not relevant(link["title"]):
                continue
            candidates.append(
                {
                    "source": name,
                    "title": link["title"],
                    "url": link["url"],
                    "existing_match": match_existing(link["title"], fingerprints),
                }
            )
    return {"fetched": fetched, "blocked": blocked, "candidates": candidates}


def _report(results: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(results, indent=2))
        return
    total = len(results["fetched"]) + len(results["blocked"])
    print(f"Fetched {len(results['fetched'])}/{total} sources")
    if results["blocked"]:
        print("\nBlocked/failed (need a browser-backed fetch instead -- see module docstring):")
        for b in results["blocked"]:
            print(f"  {b['source']:22} {b.get('status', b.get('error'))}")
    no_match = [c for c in results["candidates"] if not c["existing_match"]]
    matched = [c for c in results["candidates"] if c["existing_match"]]
    print(f"\nNo seed match ({len(no_match)}) -- check these first:")
    for c in no_match:
        print(f"  [{c['source']}] {c['title']}\n      {c['url']}")
    if not no_match:
        print("  (none -- consistent with a recently-refreshed dataset)")
    print(f"\nMatches an existing record ({len(matched)}) -- probably already tracked:")
    for c in matched:
        print(f"  [{c['source']}] {c['title']}  ~ {c['existing_match']}")


def _run_projects(args: argparse.Namespace) -> dict:
    sess = CachedSession(offline=args.offline)
    return sweep(PROJECT_SOURCES, project_fingerprints(), sess)


def _run_moratoriums(args: argparse.Namespace) -> dict:
    sess = CachedSession(offline=args.offline)
    fps = moratorium_fingerprints() + tariff_fingerprints()
    return sweep(MORATORIUM_TARIFF_SOURCES, fps, sess)


def cmd_projects(args: argparse.Namespace) -> int:
    _report(_run_projects(args), args.json)
    return 0


def cmd_moratoriums(args: argparse.Namespace) -> int:
    _report(_run_moratoriums(args), args.json)
    return 0


def cmd_all(args: argparse.Namespace) -> int:
    """Run both sweeps and report once.

    `--json` must emit exactly ONE JSON document (a `{"projects": ...,
    "moratoriums": ...}` object) -- printing two separate JSON objects with a
    text separator between them, as an earlier version did, produces output
    that isn't valid JSON at all and can't be piped into anything (caught by
    review, 2026-07-30).
    """
    projects_results = _run_projects(args)
    moratoriums_results = _run_moratoriums(args)
    if args.json:
        print(json.dumps({"projects": projects_results, "moratoriums": moratoriums_results}, indent=2))
    else:
        _report(projects_results, as_json=False)
        print("\n" + "=" * 78 + "\n")
        _report(moratoriums_results, as_json=False)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="connectors.scout",
        description="Mechanical 'is there anything new?' sweep (candidate leads only, never auto-adds).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn, help_ in (
        ("projects", cmd_projects, "sweep company newsrooms + DCD for new site announcements"),
        ("moratoriums", cmd_moratoriums, "sweep trackers for new moratorium/tariff activity"),
        ("all", cmd_all, "run both sweeps"),
    ):
        s = sub.add_parser(name, help=help_)
        s.add_argument("--json", action="store_true", help="machine-readable output")
        s.add_argument("--offline", action="store_true", help="cache-only; never hit network")
        s.set_defaults(func=fn)
    return p


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
