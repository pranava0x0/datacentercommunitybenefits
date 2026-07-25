#!/usr/bin/env python3
"""Build data/seed/signatories.json from the White House Ratepayer Protection Pledge roster.

The roster is a LIVING list — organizations kept joining after the July 23, 2026
expansion event. This script captures it as a dated snapshot and is idempotent:
re-running against an unchanged page produces an identical file, so a real diff
always means the roster actually moved.

    python scripts/build_signatories.py --diff     # show adds/removals, write nothing
    python scripts/build_signatories.py            # write data/seed/signatories.json
    python scripts/build_signatories.py --cached   # parse the cached HTML, no network

Then: python refresh.py

Two things this script deliberately does NOT do:

  * It does not reconcile the page's own numbers. On 2026-07-25 the filter chips
    advertised 281 organizations / 69 utilities while the list underneath held
    279 / 68. Both numbers are recorded — ours from the list, theirs verbatim —
    and the drift is described in `drift_note`. Silently picking one would be
    inventing a fact.
  * It does not auto-delete. A removal from the roster is news, so `--diff`
    surfaces it for a curator to act on rather than quietly dropping the record.

Governors are not on the White House roster; they signed a separate addendum
announced by the RGA. They are hand-curated in GOVERNORS below (23 records,
verified against the RGA release) and merged into the same payload so the state
panel gets its governor row for free.
"""
from __future__ import annotations

import argparse
import gzip
import html as html_mod
import json
import pathlib
import re
import ssl
import sys
import urllib.request
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEED = ROOT / "data" / "seed" / "signatories.json"
CACHE = ROOT / ".signatory_cache"

PLEDGE_ROSTER_URL = "https://www.whitehouse.gov/ratepayer-protection-pledge/"
PLEDGE_URL = "https://www.whitehouse.gov/releases/2026/03/ratepayer-protection-pledge/"
PLEDGE_PDF_URL = (
    "https://www.whitehouse.gov/wp-content/uploads/2026/07/"
    "Ratepayer-Protection-Pledge-Signed.pdf"
)
RGA_URL = (
    "https://www.rga.org/republican-governors-sign-president-trumps-"
    "ratepayer-protection-pledge/"
)

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Roster chip -> our category. The page files all data-center companies under a
# single "dc" chip; HYPERSCALER_SLUGS below re-tags the March-round buyers out
# of that bucket, because a hyperscaler buying power and a developer building
# the shell are different actors in every question this dashboard asks.
CHIP_TO_CATEGORY = {"coop": "cooperative", "utility": "utility", "dc": "developer"}

# Roster name -> tracked Company slug. Hand-curated: an exact-name bridge, never
# a fuzzy match. Names must match the roster's own spelling exactly, so a
# renamed row shows up as unmatched instead of silently binding to the wrong
# company.
COMPANY_MATCHES = {
    "Amazon": "amazon",
    "Google": "google",
    "Meta": "meta",
    "Microsoft": "microsoft",
    "OpenAI": "openai",
    "Oracle": "oracle",
    "xAI": "xai",
    "QTS": "qts",
    "CoreWeave": "coreweave",
    "Crusoe": "crusoe",
    "Prologis": "prologis",
}

# The seven electricity BUYERS from the March 4 round. Everything else in the
# roster's "dc" bucket is a July developer signatory.
HYPERSCALER_SLUGS = {"amazon", "google", "meta", "microsoft", "openai", "oracle", "xai"}

# QTS signed via the DOE companion track, not the White House event.
DOE_TRACK_SLUGS = {"qts"}

WH_TRACK = "white-house-2026-03-04"
DOE_TRACK = "doe-2026-04-24"
EXPANSION_TRACK = "expansion-2026-07-23"

TRACK_DATES = {
    WH_TRACK: "2026-03-04",
    DOE_TRACK: "2026-04-24",
    EXPANSION_TRACK: "2026-07-23",
}

# Names in tariffs.json `utility` that resolve to a roster row. Curated, exact,
# and one-directional — the utility layer joins on these ids only.
#
# Parent-company entries are marked in the value comment: when a holding company
# signed and the operating utility on the tariff is its subsidiary, the pledge
# does cover the subsidiary, but the roster row is the PARENT. That distinction
# is surfaced in the UI rather than flattened, so nobody reads "NV Energy signed
# the pledge" off a row that actually says Berkshire Hathaway Energy.
UTILITY_ALIASES: dict[str, list[str]] = {
    "AEP Ohio": ["AEP Ohio (Ohio Power Company)"],
    "Arizona Public Service Company": ["Arizona Public Service (APS)"],
    "Black Hills": ["Black Hills Energy"],
    "Dominion Energy": ["Dominion Energy Virginia"],
    "Duke Energy": [
        "Duke Energy Carolinas / Duke Energy Progress",
        "Duke Energy Indiana",
    ],
    "Entergy Corporation": ["Entergy Mississippi"],
    "Georgia Power; Mississippi Power; Alabama Power": ["Georgia Power"],
    "Idaho Power": ["Idaho Power"],
    "Indiana Michigan Power": ["Indiana Michigan Power (I&M, an AEP utility)"],
    "Portland General Electric": ["Portland General Electric (PGE)"],
    "Xcel Energy": [
        "Public Service Company of Colorado (Xcel Energy)",
        "Xcel Energy (Northern States Power — Minnesota)",
    ],
    # --- parent-company relationships ---
    "WEC Energy Group": ["We Energies (Wisconsin Electric Power Company)"],
    "Berkshire Hathaway Energy": [
        "NV Energy",
        "NV Energy (tariff proposed by Microsoft)",
    ],
    "Exelon Corporation": ["Commonwealth Edison (ComEd)"],
    "MDU Resources Group": ["Montana-Dakota Utilities (MDU)"],
}

PARENT_ALIAS_NAMES = {
    "WEC Energy Group",
    "Berkshire Hathaway Energy",
    "Exelon Corporation",
    "MDU Resources Group",
}

# The 23 governors who signed the addendum, from the RGA release (2026-07-23).
# Hand-curated because the White House roster does not list them.
GOVERNORS: list[tuple[str, str]] = [
    ("Kay Ivey", "AL"),
    ("Mike Dunleavy", "AK"),
    ("Sarah Huckabee Sanders", "AR"),
    ("Brian Kemp", "GA"),
    ("Brad Little", "ID"),
    ("Mike Braun", "IN"),
    ("Kim Reynolds", "IA"),
    ("Jeff Landry", "LA"),
    ("Tate Reeves", "MS"),
    ("Mike Kehoe", "MO"),
    ("Greg Gianforte", "MT"),
    ("Jim Pillen", "NE"),
    ("Joe Lombardo", "NV"),
    ("Kelly Armstrong", "ND"),
    ("Mike DeWine", "OH"),
    ("Kevin Stitt", "OK"),
    ("Henry McMaster", "SC"),
    ("Larry Rhoden", "SD"),
    ("Bill Lee", "TN"),
    ("Greg Abbott", "TX"),
    ("Spencer Cox", "UT"),
    ("Patrick Morrisey", "WV"),
    ("Mark Gordon", "WY"),
]

ROW_RE = re.compile(
    r'<li class="row" data-name="[^"]*" data-domain="([^"]*)" data-cat="([^"]*)">'
    r'<span class="row-name">(.*?)</span>',
    re.S,
)
CHIP_RE = re.compile(r'data-cat="(\w+)">[^<]*<span class="chip-count">(\d+)</span>')


def slugify(name: str) -> str:
    s = name.lower()
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def fetch(url: str, *, cached_only: bool = False) -> str:
    CACHE.mkdir(exist_ok=True)
    path = CACHE / (slugify(url) + ".html")
    if cached_only or path.exists():
        if not path.exists():
            raise SystemExit(f"--cached given but no cache at {path}")
        return path.read_text()
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=45, context=ctx) as resp:
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        text = raw.decode("utf-8", "replace")
    path.write_text(text)
    return text


def parse_roster(html: str, captured: str) -> tuple[list[dict], dict[str, int]]:
    rows = ROW_RE.findall(html)
    if not rows:
        raise SystemExit(
            "Parsed zero roster rows — the page markup changed. Inspect the cached "
            f"HTML in {CACHE} and update ROW_RE before trusting any output."
        )

    stated = {}
    for cat, n in CHIP_RE.findall(html):
        key = {"all": "all", "coop": "cooperative", "utility": "utility", "dc": "data_center"}
        stated[key.get(cat, cat)] = int(n)

    out: list[dict] = []
    seen: set[str] = set()
    for domain, chip, raw_name in rows:
        name = html_mod.unescape(raw_name).strip()
        slug = COMPANY_MATCHES.get(name)
        category = CHIP_TO_CATEGORY.get(chip)
        if category is None:
            raise SystemExit(f"Unknown roster chip {chip!r} on row {name!r} — map it first.")
        if slug in HYPERSCALER_SLUGS:
            category = "hyperscaler"
            track = WH_TRACK
        elif slug in DOE_TRACK_SLUGS:
            track = DOE_TRACK
        else:
            track = EXPANSION_TRACK

        # Distinct organizations can share a name — the roster carries two
        # separate "Southeastern Electric Cooperative" rows on different
        # domains. Disambiguate by domain rather than dropping one, which
        # would silently lose a real signatory.
        sid = slugify(name)
        if sid in seen:
            if not domain:
                raise SystemExit(
                    f"Duplicate roster name {name!r} with no domain to disambiguate on."
                )
            sid = f"{sid}-{slugify(domain.split('.')[0])}"
            if sid in seen:
                raise SystemExit(f"Cannot disambiguate duplicate roster row {name!r}.")
        seen.add(sid)

        rec = {
            "id": sid,
            "name": name,
            "category": category,
            "signed_track": track,
            "signed_date": TRACK_DATES[track],
            "state": None,
            "website_domain": domain or None,
            "source_url": PLEDGE_ROSTER_URL,
            "source_title": "White House — Ratepayer Protection Pledge signatory roster",
            "captured_at": captured,
            "matched_company_slug": slug,
            "utility_aliases": UTILITY_ALIASES.get(name, []),
            "notes": None,
        }
        if name in PARENT_ALIAS_NAMES:
            rec["notes"] = (
                "Roster row is the parent holding company; the tariffs tracked here "
                "are filed by its operating utility."
            )
        out.append(rec)
    return out, stated


def build_governors(captured: str) -> list[dict]:
    return [
        {
            "id": f"gov-{code.lower()}",
            "name": f"Gov. {name}",
            "category": "governor",
            "signed_track": EXPANSION_TRACK,
            "signed_date": TRACK_DATES[EXPANSION_TRACK],
            "state": code,
            "website_domain": None,
            "source_url": RGA_URL,
            "source_title": (
                "Republican Governors Association — Republican governors sign "
                "President Trump's Ratepayer Protection Pledge"
            ),
            "captured_at": captured,
            "matched_company_slug": None,
            "utility_aliases": [],
            "notes": (
                "Signed an addendum to the pledge, not the corporate pledge itself — "
                "a commitment to apply its principles in the governor's own role."
            ),
        }
        for name, code in GOVERNORS
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--diff", action="store_true", help="report adds/removals, write nothing")
    ap.add_argument("--cached", action="store_true", help="use cached HTML, no network")
    ap.add_argument("--as-of", default=date.today().isoformat(), help="roster_as_of date")
    args = ap.parse_args()

    html = fetch(PLEDGE_ROSTER_URL, cached_only=args.cached)
    orgs, stated = parse_roster(html, args.as_of)
    govs = build_governors(args.as_of)
    records = sorted(orgs + govs, key=lambda r: (r["category"], r["id"]))

    derived: dict[str, int] = {}
    for r in records:
        derived[r["category"]] = derived.get(r["category"], 0) + 1
    org_total = len(orgs)

    drift = None
    stated_all = stated.get("all")
    if stated_all is not None and stated_all != org_total:
        drift = (
            f"The White House page advertised {stated_all} organizations when this "
            f"roster was captured, but the list it published held {org_total}. The "
            "counts shown here are taken from the list itself; the page's own "
            "figures are recorded alongside them rather than reconciled away."
        )

    payload = {
        "generated_at": args.as_of,
        "roster_as_of": args.as_of,
        "roster_counts_stated": stated,
        "pledge_url": PLEDGE_URL,
        "pledge_pdf_url": PLEDGE_PDF_URL,
        "drift_note": drift,
        "signatories": records,
    }

    if args.diff:
        if not SEED.exists():
            print(f"No existing seed at {SEED}; {len(records)} records would be written.")
            return 0
        old = {s["id"]: s for s in json.loads(SEED.read_text())["signatories"]}
        new = {s["id"]: s for s in records}
        added = sorted(set(new) - set(old))
        removed = sorted(set(old) - set(new))
        changed = sorted(i for i in set(old) & set(new) if old[i] != new[i])
        print(f"adds ({len(added)}): {added}")
        print(f"REMOVALS ({len(removed)}): {removed}   <- review before accepting")
        print(f"changed ({len(changed)}): {changed}")
        return 0

    SEED.parent.mkdir(parents=True, exist_ok=True)
    SEED.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {SEED} — {len(records)} records ({org_total} orgs + {len(govs)} governors)")
    print(f"  by category: {json.dumps(derived, sort_keys=True)}")
    print(f"  page stated: {json.dumps(stated, sort_keys=True)}")
    if drift:
        print(f"  drift: {drift}")
    matched = [r["id"] for r in records if r["matched_company_slug"]]
    print(f"  matched to tracked companies ({len(matched)}): {matched}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
