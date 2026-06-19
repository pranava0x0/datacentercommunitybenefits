"""Research accelerator CLI — fast, repeatable community-benefit data collection.

This automates the slow parts of the manual curation loop:

  status   — which sites still lack claims / community feedback (plan the work)
  queries  — emit ready-to-run web-search queries for those sites; paste them to
             the agent's WebSearch or drive them with the Chrome browser MCP
  harvest  — given the URLs those searches surface, fetch (cached + polite),
             auto-extract publication dates + candidate quotes, and write
             schema-shaped *candidate* records for curator review

Design guardrails (CLAUDE.md):
- Never auto-merges into data/seed/*. Output is candidates in data/candidates/.
- Never infers stance/constituency — those fields come out null with a TODO.
- Never paraphrases a Claim — it offers verbatim quote candidates to pick from.
- Every candidate carries its source_url; news candidates carry an auto date.

Examples:
    python -m connectors.research status
    python -m connectors.research queries --missing-feedback --limit 5
    python -m connectors.research harvest --project google-lenoir-nc \\
        https://datacenters.google/locations/north-carolina/
    python -m connectors.research harvest --urls-file urls.txt --out cand.json
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from connectors.extract import (
    extract_lede,
    extract_pub_date,
    extract_quotes,
    extract_title,
    first_party_company,
    is_first_party,
    needs_browser,
    outlet_for,
)
from connectors.http import CachedSession

log = logging.getLogger("connectors.research")

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "seed"
CANDIDATES_DIR = ROOT / "data" / "candidates"

# First-party page URL hints per company (where a per-site page usually lives).
FIRST_PARTY_HINTS: dict[str, str] = {
    "meta": "https://datacenters.atmeta.com/ (search 'Hello <City>' / location sheet)",
    "google": "https://datacenters.google/locations/<state-or-county>/",
    "microsoft": "https://local.microsoft.com/communities/americas/<region>/",
    "amazon": "https://www.aboutamazon.com/news/aws/ (economic-impact-of-aws-<state>)",
}

# Per-query templates. {co} {city} {state} filled per project.
FEEDBACK_QUERIES = [
    "{co} data center {city} {state} residents concerns water OR noise OR power",
    "{co} {city} {state} data center opposition OR lawsuit OR moratorium",
    "{co} {city} {state} data center community response local officials",
]
CLAIM_QUERIES = [
    "{co} {city} {state} data center investment jobs announcement first-party",
    "{co} {city} {state} data center renewable energy water community grants pledge",
]


def _load(name: str) -> list[dict]:
    data = json.loads((SEED / f"{name}.json").read_text())
    return data[name]


def _company_name(slug: str, companies: list[dict]) -> str:
    for c in companies:
        if c["slug"] == slug:
            return c["name"]
    return slug


# -- status ------------------------------------------------------------------
def _coverage() -> dict:
    projects = _load("projects")
    claims = _load("claims")
    responses = _load("responses")
    claim_pids = {c.get("project_id") for c in claims}
    resp_pids = {r["project_id"] for r in responses}
    no_feedback = [p for p in projects if p["id"] not in resp_pids]
    no_claims = [p for p in projects if p["id"] not in claim_pids]
    return {
        "projects": projects,
        "no_feedback": no_feedback,
        "no_claims": no_claims,
    }


def cmd_status(args: argparse.Namespace) -> int:
    cov = _coverage()
    n = len(cov["projects"])
    print(f"Projects: {n}")
    print(f"  without community feedback: {len(cov['no_feedback'])}")
    print(f"  without any project-tied claim: {len(cov['no_claims'])}")
    if args.list:
        print("\n-- sites missing community feedback --")
        for p in cov["no_feedback"]:
            print(f"  {p['id']:34} {p.get('city','?')}, {p.get('state','?')}")
    return 0


# -- queries -----------------------------------------------------------------
def cmd_queries(args: argparse.Namespace) -> int:
    cov = _coverage()
    companies = _load("companies")
    if args.missing_claims:
        targets, templates = cov["no_claims"], CLAIM_QUERIES
    else:
        targets, templates = cov["no_feedback"], FEEDBACK_QUERIES
    if args.limit:
        targets = targets[: args.limit]

    payload = []
    for p in targets:
        co = _company_name(p["company_slug"], companies)
        qs = [
            t.format(co=co, city=p.get("city", ""), state=p.get("state", ""))
            for t in templates
        ]
        payload.append(
            {
                "project_id": p["id"],
                "company": co,
                "first_party_hint": FIRST_PARTY_HINTS.get(p["company_slug"]),
                "queries": qs,
            }
        )
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for item in payload:
            print(f"\n# {item['project_id']}  ({item['company']})")
            if item["first_party_hint"]:
                print(f"  first-party: {item['first_party_hint']}")
            for q in item["queries"]:
                print(f"  search: {q}")
    return 0


# -- harvest -----------------------------------------------------------------
def _harvest_url(
    sess: CachedSession,
    url: str,
    project_id: str | None,
    page_override: str | None = None,
) -> dict:
    if page_override is not None:
        page, status, final = page_override, 200, url
    else:
        rec = sess.get(url)
        page, status, final = rec["text"], rec["status"], rec["final_url"]
    title = extract_title(page) if page else None
    base = {
        "source_url": url,
        "final_url": final,
        "http_status": status,
        "source_title": title,
        "project_id": project_id,
    }
    if status != 200 or not page:
        base["_note"] = f"non-200 or empty ({status}); cannot extract"
        base["kind"] = "error"
        return base

    # SPA shells (e.g. datacenters.google) need Chrome MCP — flag for re-fetch.
    if page_override is None and needs_browser(url, page):
        base["kind"] = "needs_browser"
        base["_todo"] = (
            "JS-rendered page; render with Chrome browser MCP "
            "(navigate + get_page_text/read_page), save the DOM HTML, then re-run: "
            f"harvest --html-file <saved.html> --as-url {url}"
            + (f" --project {project_id}" if project_id else "")
        )
        return base

    if is_first_party(url):
        base["kind"] = "claim_candidates"
        base["company_slug"] = first_party_company(url)
        base["captured_at"] = date.today().isoformat()
        base["quote_candidates"] = extract_quotes(page)
        base["_todo"] = "Pick a verbatim quote -> Claim.statement; set theme; set source_title."
    else:
        base["kind"] = "response_candidate"
        base["outlet"] = outlet_for(url)
        base["date"] = extract_pub_date(page)
        base["lede"] = extract_lede(page)
        base["stance"] = None
        base["constituency"] = None
        base["single_source"] = None
        base["_todo"] = (
            "Set stance/constituency (editorial); rewrite lede into neutral "
            "summary; confirm date" + ("" if base["date"] else " (NOT auto-detected!)")
        )
    return base


def cmd_harvest(args: argparse.Namespace) -> int:
    # Chrome-MCP bridge: extract from a locally-saved rendered DOM for one URL.
    if args.html_file:
        if not args.as_url:
            log.error("--html-file requires --as-url (the page's real URL)")
            return 2
        page = Path(args.html_file).read_text()
        out = [_harvest_url(None, args.as_url, args.project, page_override=page)]
        CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
        out_path = Path(args.out) if args.out else CANDIDATES_DIR / "harvest-latest.json"
        out_path.write_text(
            json.dumps({"harvested_at": date.today().isoformat(), "candidates": out}, indent=2)
        )
        quotes = sum(len(c.get("quote_candidates", [])) for c in out)
        print(f"Extracted from rendered HTML -> {out_path} ({quotes} quote candidate(s))")
        return 0

    urls: list[str] = list(args.urls)
    if args.urls_file:
        urls += [
            ln.strip()
            for ln in Path(args.urls_file).read_text().splitlines()
            if ln.strip() and not ln.startswith("#")
        ]
    if not urls:
        log.error("no URLs given (positional or --urls-file)")
        return 2
    for u in urls:
        if urlparse(u).scheme not in ("http", "https"):
            log.error("not an http(s) URL: %s", u)
            return 2

    if args.dry_run:
        print(f"[dry-run] would fetch {len(urls)} URL(s):")
        for u in urls:
            kind = "first-party" if is_first_party(u) else "feedback"
            print(f"  {kind:11} {u}")
        return 0

    sess = CachedSession(offline=args.offline)
    out = [_harvest_url(sess, u, args.project) for u in urls]

    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out) if args.out else CANDIDATES_DIR / "harvest-latest.json"
    out_path.write_text(json.dumps({"harvested_at": date.today().isoformat(), "candidates": out}, indent=2))

    ok = sum(1 for c in out if c.get("kind") != "error")
    dated = sum(1 for c in out if c.get("kind") == "response_candidate" and c.get("date"))
    quotes = sum(len(c.get("quote_candidates", [])) for c in out)
    print(f"Harvested {ok}/{len(out)} URL(s) -> {out_path}")
    print(f"  response candidates with auto-date: {dated}")
    print(f"  verbatim quote candidates surfaced: {quotes}")
    print("  Review + fill editorial fields, then merge into data/seed/ by hand.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="connectors.research",
        description="Fast, repeatable community-benefit data collection (candidate output only).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("status", help="coverage report: sites missing claims/feedback")
    s.add_argument("--list", action="store_true", help="list the missing-feedback sites")
    s.set_defaults(func=cmd_status)

    q = sub.add_parser("queries", help="emit web-search queries for under-covered sites")
    q.add_argument("--missing-feedback", action="store_true", help="(default) target sites w/o responses")
    q.add_argument("--missing-claims", action="store_true", help="target sites w/o project-tied claims")
    q.add_argument("--limit", type=int, default=0, help="cap number of sites")
    q.add_argument("--json", action="store_true", help="machine-readable output")
    q.set_defaults(func=cmd_queries)

    h = sub.add_parser("harvest", help="fetch URLs and emit candidate records")
    h.add_argument("urls", nargs="*", help="URLs to harvest")
    h.add_argument("--urls-file", help="file of URLs (one per line, # comments ok)")
    h.add_argument("--html-file", help="extract from a saved rendered DOM (Chrome-MCP bridge)")
    h.add_argument("--as-url", help="the real URL the --html-file corresponds to")
    h.add_argument("--project", help="project_id to attach candidates to")
    h.add_argument("--out", help="output JSON path (default data/candidates/harvest-latest.json)")
    h.add_argument("--offline", action="store_true", help="cache-only; never hit network")
    h.add_argument("--dry-run", action="store_true", help="show planned fetches, do nothing")
    h.set_defaults(func=cmd_harvest)
    return p


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
