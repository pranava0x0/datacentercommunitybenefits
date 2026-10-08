"""merge_v5_refresh.py: apply the 2026-10-08 refresh to data/seed.

Inputs (agent outputs, git-ignored) under .agent_outputs/2026-10-08/:
  site_updates.jsonl / site_updates_b2.jsonl  local timeline events per site
  validation.jsonl / validation_b2.jsonl      per-event Haiku fact-check
  refresh_candidates.jsonl                    new policies / moratoriums / rate-case updates

Every event that ships here passed two gates: scripts/probe.py --evidence
(the verbatim is literally on the page) and a per-item validator that
re-read the page for the event date and the title's facts. Corrections the
validator made (relative-day dates, overstated titles) are applied by hand
in FIXES below rather than trusted blindly; DROP lists what didn't ship.

Idempotent: events dedupe by (date, source_url); records by id.

    python3 scripts/merge_v5_refresh.py && python3 refresh.py
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "seed"
OUT = ROOT / ".agent_outputs" / "2026-10-08"
CAPTURED = "2026-10-08"

log = logging.getLogger("merge_v5")

# (project_id, claimed_date) -> overrides. Applied after the agent's fields.
FIXES: dict[tuple[str, str], dict] = {
    # Batch 1 -------------------------------------------------------------
    ("wonder-valley-box-elder-ut", "2026-05-06"): {"date": "2026-05-05"},  # "On Tuesday", article Wed May 6
    ("aws-new-carlisle-in", "2025-08-14"): {
        "kind": "news",
        "title": "Amazon told to reapply for its New Carlisle wetland permit, report says",
    },
    ("aws-new-carlisle-in", "2026-07-09"): {"date": "2026-07-08"},  # "on Wednesday", article Thu Jul 9
    ("xai-memphis-tn", "2026-04-15"): {
        "date": "2026-04-14",  # "on Tuesday", posted Wed Apr 15
        "title": "NAACP sues xAI and MZX Tech alleging Clean Air Act violations at Colossus 2",
    },
    ("xai-southaven-ms", "2026-07-31"): {
        "kind": "news",
        "title": "xAI says it will remove all 69 turbines from its Southaven site",
        "authority": None,
    },
    ("qts-fayetteville-ga", "2026-05-11"): {
        "kind": "news",
        "title": "Records show ~$147,000 retroactive water bill to the QTS campus, which QTS later paid",
        "authority": None,
    },
    ("qts-fayetteville-ga", "2026-07-16"): {
        "title": "Report alleges 30M gallons of unbilled water; county cites a meter billing error",
    },
    ("meta-newton-ga", "2025-07-14"): {
        "title": "Neighbors say their well ran dry after construction began; Meta says its campus is an unlikely cause",
    },
    ("oracle-port-washington-wi", "2026-03-20"): {"date": "2026-03-19"},  # "Thursday night"
    ("oracle-port-washington-wi", "2026-04-07"): {
        "title": "Voters require a referendum for future TIF districts of $10M or more (66% yes)",
    },
    ("meta-richland-la", "2026-05-26"): {
        "kind": "news",
        "title": "Report: Louisiana ratepayers could bear billions in data center power costs",
    },
    ("ms-quincy-wa", "2026-01-27"): {
        "title": "Grant PUD approves rate increase; largest power users up 9.5% on average from April 1",
    },
    ("aws-loudoun-va", "2026-03-17"): {
        "project_id": "aws-ashburn-gwu-va",  # the GWU campus is its own tracked site
        "kind": "news",
        "title": "Amazon Data Services buys the GWU Ashburn campus for $427 million",
    },
}

# Events that did not ship, with the reason.
# Keyed (project_id, date) or, where two events share a date,
# (project_id, date, title prefix).
DROP: dict[tuple, str] = {
    ("google-linn-county-ia", "2026-05-15"): "verbatim is about water use, not the P&Z vote",
    ("meta-newton-ga", "2026-05-22"): "congressional hearing not tied to this site on the page",
    ("meta-richland-la", "2025-12-17"): "statewide PSC rule, not a site event",
    ("meta-richland-la", "2026-07-23"): "White House roundtable, not a site event",
    ("ms-quincy-wa", "2026-05-28"): "source blocked (429) for the gate",
    ("wonder-valley-box-elder-ut", "2026-05-29", "County attorney"): "podcast blurb gives no date for the denial",
    ("prologis-coweta-ga", "2026-05-12"): "article date only; the May 5 appeal already covers the suit",
}

# (events file, validator-fixes file). Fix/drop keys are "project_id|date"
# or "project_id|date|title prefix" where two events share a date.
BATCHES = [
    (OUT / "site_updates_b2.jsonl", OUT / "batch2_fixes.json"),
    (OUT / "site_updates_c1.jsonl", OUT / "batch_c_fixes.json"),
    (OUT / "site_updates_c2.jsonl", OUT / "batch_c_fixes.json"),
]


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def apply_site_updates(projects: list[dict]) -> int:
    by_id = {p["id"]: p for p in projects}
    # An event whose page already backs a community response at the same site
    # would render twice on the merged timeline; the response wins.
    responses = json.loads((SEED / "responses.json").read_text())["responses"]
    response_srcs = {(r["project_id"], r["source_url"]) for r in responses}
    fixes = dict(FIXES)
    drops = dict(DROP)
    # Later batches ship only once their validator's fixes file exists.
    batches = [OUT / "site_updates.jsonl"]
    for jsonl, fix_file in BATCHES:
        if not fix_file.exists():
            continue
        batches.append(jsonl)
        b = json.loads(fix_file.read_text())
        for k, v in b.get("fixes", {}).items():
            fixes[tuple(k.split("|"))] = v
        for k, why in b.get("drop", {}).items():
            drops[tuple(k.split("|"))] = why
    added = 0
    for p in projects:  # enforce the response-wins rule on events merged earlier too
        if p.get("updates"):
            kept = [u for u in p["updates"] if (p["id"], u["source_url"]) not in response_srcs]
            if len(kept) != len(p["updates"]):
                log.info("dedupe %s: %d event(s) duplicated a response", p["id"], len(p["updates"]) - len(kept))
            if kept:
                p["updates"] = kept
            else:
                p.pop("updates")
    for path in batches:
        for row in load_jsonl(path):
            for e in row["events"]:
                key = (row["project_id"], e["date"])
                why = drops.get(key) or next(
                    (w for k, w in drops.items() if len(k) == 3 and k[:2] == key and e["title"].startswith(k[2])),
                    None,
                )
                if why:
                    log.info("drop %s %s: %s", *key, why)
                    continue
                ev = {
                    "date": e["date"],
                    "kind": e["kind"],
                    "title": e["title"],
                    "summary": e.get("summary") or None,
                    "authority": e.get("authority") or None,
                    "upcoming": bool(e.get("upcoming")),
                    "source_url": e["source_url"],
                    "source_title": e["source_title"],
                }
                pid = row["project_id"]
                fix = fixes.get(key) or next(
                    (f for k, f in fixes.items() if len(k) == 3 and k[:2] == key and e["title"].startswith(k[2])),
                    {},
                )
                pid = fix.get("project_id", pid)
                ev.update({k: v for k, v in fix.items() if k != "project_id"})
                if (pid, ev["source_url"]) in response_srcs:
                    log.info("skip %s %s: same source as an existing response", pid, ev["date"])
                    continue
                p = by_id.get(pid)
                if p is None:
                    log.warning("unknown project %s", pid)
                    continue
                ups = p.setdefault("updates", [])
                if any(u["date"] == ev["date"] and u["source_url"] == ev["source_url"] for u in ups):
                    continue
                ups.append({k: v for k, v in ev.items() if v is not None})
                ups.sort(key=lambda u: u["date"])
                added += 1
    return added


# ---------------------------------------------------------------------------
# New records from refresh_candidates.jsonl, hand-finished from the agent rows
# plus the validator's notes (C-numbers are line indexes in that file).
# ---------------------------------------------------------------------------

NEW_MORATORIUMS = [
    {  # C2
        "id": "shawnee-county-ks-2026-08",
        "jurisdiction": "Shawnee County",
        "jurisdiction_type": "county",
        "state_code": "KS",
        "status": "enacted",
        "enacted_date": "2026-08-13",
        "duration_months": 6,
        "duration_description": "Six months; set to expire Feb. 17, 2027 unless changed.",
        "key_reasons": [],
        "summary": "Shawnee County commissioners approved a six-month pause at their Aug. 13, 2026 meeting: the county will not accept or process new applications for county land-use approval for a data center, and will not take final action on the pending Compass Datacenters application. The moratorium is set to expire Feb. 17, 2027.",
        "source_url": "https://www.ksnt.com/news/local-news/six-month-moratorium-approved-for-new-data-center-applications-in-shawnee-county/amp/",
        "source_title": "KSNT — Six-month moratorium approved for new data center applications in Shawnee County",
        "enacted_by": "Board of County Commissioners",
        "session": "2026",
    },
    {  # C3
        "id": "mesa-county-co-2026-09",
        "jurisdiction": "Mesa County",
        "jurisdiction_type": "county",
        "state_code": "CO",
        "status": "enacted",
        "enacted_date": "2026-09-29",
        "effective_date": "2026-09-29",
        "duration_months": 12,
        "duration_description": "12 months, effective immediately.",
        "key_reasons": [],
        "summary": "Mesa County commissioners unanimously approved a 12-month moratorium at a Sept. 29, 2026 public hearing, effective immediately. It pauses acceptance, processing and approval of land use applications for data center facilities in unincorporated Mesa County while staff update the land development code.",
        "source_url": "https://www.mesacounty.us/news/county-wide/commissioners-approve-data-center-moratorium",
        "source_title": "Mesa County — Commissioners approve data center moratorium",
        "enacted_by": "Board of County Commissioners",
        "session": "2026",
    },
    {  # C4
        "id": "pima-county-az-2026-09",
        "jurisdiction": "Pima County",
        "jurisdiction_type": "county",
        "state_code": "AZ",
        "status": "enacted",
        "enacted_date": "2026-09-22",
        "duration_months": 4,
        "duration_description": "120 days; returns to the board before it ends for a possible extension hearing.",
        "key_reasons": [],
        "summary": "The Pima County Board of Supervisors voted 3-2 on Sept. 22, 2026 to impose a 120-day moratorium on new data center development in unincorporated Pima County, applying to data centers whose site-improvement permits had not yet been submitted, while a zoning code text amendment on data centers is prepared.",
        "source_url": "https://tucsondailybrief.com/news-reports/pima-county-2026-09-22.html",
        "source_title": "Tucson Daily Brief — Pima County Board of Supervisors, Sept. 22, 2026",
        "enacted_by": "Board of Supervisors",
        "city_council_vote": "3-2",
        "session": "2026",
    },
    {  # C5
        "id": "oakland-ca-2026-09",
        "jurisdiction": "Oakland",
        "jurisdiction_type": "city",
        "state_code": "CA",
        "status": "proposed",
        "duration_description": "Proposed 45-day moratorium on approving land-use agreements or entitlements for new data centers.",
        "key_reasons": [],
        "summary": "Oakland's Life Enrichment Committee unanimously approved a proposed 45-day moratorium on Sept. 22, 2026 that would temporarily stop the city approving land-use agreements or entitlements for new data centers while it writes regulations. The full City Council was scheduled to take it up Oct. 6; that outcome is not yet recorded here.",
        "source_url": "https://oaklandside.org/2026/09/23/oakland-data-center-moratorium-committee-appoval/",
        "source_title": "The Oaklandside — Oakland data center moratorium clears committee",
        "session": "2026",
    },
    {  # C11
        "id": "tulare-county-ca-2026-09",
        "jurisdiction": "Tulare County",
        "jurisdiction_type": "county",
        "state_code": "CA",
        "status": "enacted",
        "enacted_date": "2026-09-22",
        "duration_months": 10,
        "duration_description": "Original 45-day pause (set to expire Oct. 2, 2026) extended by 10 months and 15 days.",
        "key_reasons": [],
        "policy_type": "Extension of an August 2026 45-day moratorium (the original pause is not separately recorded)",
        "summary": "Tulare County supervisors voted 5-0 to extend the county's original 45-day moratorium on new data center development in unincorporated Tulare County by another 10 months and 15 days. The original pause had been set to expire Oct. 2.",
        "source_url": "https://kmph.com/news/local/woman-removed-from-tulare-county-meeting-as-data-center-debate-erupts",
        "source_title": "KMPH — Tulare County extends data center moratorium",
        "enacted_by": "Board of Supervisors",
        "city_council_vote": "5-0",
        "session": "2026",
    },
    {  # C12
        "id": "raleigh-nc-2026-09",
        "jurisdiction": "Raleigh",
        "jurisdiction_type": "city",
        "state_code": "NC",
        "status": "proposed",
        "duration_description": "Proposed six-month moratorium; city attorney directed to draft it.",
        "key_reasons": [],
        "summary": "Raleigh City Council directed the city attorney to draft a six-month data center moratorium (reported Sept. 16, 2026), with discussion and a possible vote set for Oct. 6. That outcome is not yet recorded here.",
        "source_url": "https://www.wfae.org/2026-09-16/raleigh-cary-data-center-moratorium",
        "source_title": "WFAE — Raleigh, Cary weigh data center moratoriums",
        "session": "2026",
    },
    {  # C17
        "id": "marshall-county-ia-2026-09",
        "jurisdiction": "Marshall County",
        "jurisdiction_type": "county",
        "state_code": "IA",
        "status": "enacted",
        "enacted_date": "2026-09-23",
        "duration_months": 6,
        "duration_description": "Six months, on applications for data centers, AI computing, data mining and cryptocurrency mining.",
        "key_reasons": [],
        "summary": "The Marshall County Board of Supervisors adopted a six-month moratorium resolution on applications for data centers, AI computing facilities, data mining and cryptocurrency mining. The source article is inconsistent on the vote count, so none is recorded.",
        "source_url": "https://www.timesrepublican.com/news/todays-news/2026/09/supervisors-ok-six-month-data-center-moratorium-resolution/",
        "source_title": "Times-Republican — Supervisors OK six-month data center moratorium resolution",
        "enacted_by": "Board of Supervisors",
        "session": "2026",
    },
]

CA_RELEASE = "https://www.gov.ca.gov/2026/09/21/governor-newsom-signs-most-comprehensive-data-center-laws-in-the-nation-providing-communities-more-control-on-water-electricity-and-land-use/"
CA_TITLE = "Office of the Governor — Newsom signs data center laws (Sept. 21, 2026)"


def _ca(pid: str, ident: str, title: str, principles: list[str], themes: list[str], summary: str, terms: list[str]) -> dict:
    return {
        "id": pid, "title": title, "instrument": "legislation", "status": "in_effect",
        "scope": "state", "jurisdiction": "California", "state_code": "CA",
        "identifier": ident, "date": "2026-09-21", "benefit_themes": themes,
        "principles": principles, "community_benefits_framework": False,
        "key_terms": terms, "summary": summary,
        "source_url": CA_RELEASE, "source_title": CA_TITLE,
    }


NEW_POLICIES = [
    # C6-C9: the validator found each bill named as signed on the Governor's
    # release, but the descriptive sentences are package-level. Summaries say
    # exactly that; key_terms are only the bill names the page carries.
    _ca("ca-ab2383-2026", "AB 2383 (Chavez Zbur)", "Assembly Bill 2383 — electricity: data centers",
        ["pay_own_way"], ["energy"],
        "Signed Sept. 21, 2026 as part of the Governor's data center package, which the release describes as making data centers pay their fair share of grid costs. The release names the bill but does not detail its individual provisions.",
        ["AB 2383"]),
    _ca("ca-ab2619-2026", "AB 2619 (Papan)", "Assembly Bill 2619 — water resources: data centers",
        ["water"], ["water"],
        "Signed Sept. 21, 2026 as part of the Governor's data center package, which the release describes as requiring data centers to pay for water-supply upgrades they need. The release names the bill but does not detail its individual provisions.",
        ["AB 2619"]),
    _ca("ca-sb887-2026", "SB 887 (Padilla)", "Senate Bill 887 — CEQA streamlining and data centers",
        ["environmental_review"], ["energy", "water"],
        "Signed Sept. 21, 2026 as part of the Governor's data center package, which the release describes as narrowing blanket environmental-review exemptions for data centers. The release names the bill but does not detail its individual provisions.",
        ["SB 887"]),
    _ca("ca-sb1168-2026", "SB 1168 (McNerney)", "Senate Bill 1168 — data centers: rate structures",
        ["pay_own_way"], ["energy"],
        "Signed Sept. 21, 2026 as part of the Governor's data center package, which the release describes as preventing data centers from shifting electricity costs onto other ratepayers. The release names the bill but does not detail its individual provisions.",
        ["SB 1168"]),
    {  # C0
        "id": "nj-pl2026-c32",
        "title": "Data Center Fair Share Act (P.L. 2026, c.32) — large data center rate class",
        "instrument": "legislation", "status": "in_effect", "scope": "state",
        "jurisdiction": "New Jersey", "state_code": "NJ", "identifier": "P.L. 2026, c.32",
        "date": "2026-07-07", "benefit_themes": ["energy"], "principles": ["pay_own_way"],
        "community_benefits_framework": False,
        "key_terms": ["P.L. 2026, c.32"],
        "summary": "Signed July 7, 2026, the law has the Board of Public Utilities set a separate rate class and cost-allocation rules for large data centers so other customers do not subsidize them. The state's Local Finance Notice 2026-13 (Aug. 25, 2026) explains it to municipalities; the BPU is implementing it over the coming months. The tariff standards it sets are tracked on the Tariffs tab (A796/S731).",
        "source_url": "https://www.nj.gov/dca/dlgs/lfns/2026/2026-13.pdf",
        "source_title": "NJ Division of Local Government Services — Local Finance Notice 2026-13",
    },
    {  # C18 -- summary limited to what KATV reports (the veto and its reasons)
        "id": "pulaski-county-ar-ord-26-i-56b",
        "title": "Pulaski County Ordinance 26-I-56B on data centers (vetoed)",
        "instrument": "local_ordinance", "status": "failed", "scope": "county",
        "jurisdiction": "Pulaski County", "state_code": "AR", "identifier": "Ordinance No. 26-I-56B",
        "date": "2026-09-25", "benefit_themes": ["engagement"], "principles": ["local_control"],
        "community_benefits_framework": False,
        "key_terms": ["26-I-56B"],
        "summary": "County Judge Barry Hyde vetoed Ordinance No. 26-I-56B, a county data center ordinance, citing five reasons including unresolved questions about state law and existing property rights and appeal provisions that should be brought into compliance with Arkansas law.",
        "source_url": "https://katv.com/news/judge-barry-hyde-vetoes-data-center-ordinance-avaio-terri-hollingsworth-ordinance-no-26-i-56b-google-entergy-arkansas-law-economy-development",
        "source_title": "KATV — Judge Barry Hyde vetoes data center ordinance",
    },
    {  # C19
        "id": "volusia-county-fl-ban-2026",
        "title": "Volusia County ordinance prohibiting large-scale data centers (first reading)",
        "instrument": "local_ordinance", "status": "proposed", "scope": "county",
        "jurisdiction": "Volusia County", "state_code": "FL", "date": "2026-10-06",
        "benefit_themes": ["water", "energy"], "principles": ["local_control"],
        "community_benefits_framework": False,
        "key_terms": ["large-scale data centers"],
        "summary": "Volusia County Council voted unanimously on Oct. 6, 2026 to advance, after first reading, an ordinance prohibiting large-scale data centers in unincorporated areas. The Planning and Land Development Regulation Commission takes it up Oct. 15, with a second and final hearing Oct. 20.",
        "source_url": "https://mynews13.com/fl/orlando/news/2026/10/06/volusia-county-data-center-ban-heads-to-first-reading",
        "source_title": "Spectrum News 13 — Volusia County data center ban heads to first reading",
    },
]

TEXAS_TCEQ = (
    " On September 21, 2026 Abbott issued a third directive, ordering the Texas Commission on "
    "Environmental Quality (TCEQ) to issue no permits sought by data center projects until the "
    "audits are complete, with a TCEQ compliance report due to the Governor's office by October 19, 2026."
)
TEXAS_TCEQ_RESOURCE = {
    "url": "https://www.troutman.com/insights/governor-abbott-directs-tceq-to-halt-all-data-center-permits-pending-ercot-twdb-audits/",
    "title": "Troutman Pepper Locke — Governor Abbott directs TCEQ to halt all data center permits",
}

DUKE_SETTLEMENT = (
    " On October 7, 2026 Blue Ridge Public Radio reported that Duke Energy and data center operators "
    "had reached an agreement on a large-load tariff that repurposes an existing tariff and makes it "
    "mandatory for data centers and other high-load-factor customers; an NCUC order on it has not been announced."
)
DUKE_RESOURCE = {
    "url": "https://www.bpr.org/2026-10-07/duke-energy-comes-to-an-agreement-on-long-sought-large-load-tariff-for-data-centers-in-north-carolina",
    "title": "Blue Ridge Public Radio — Duke Energy reaches agreement on large-load tariff (Oct. 7, 2026)",
}


# Pre-existing record removed during this pass. It sat on google-new-florence-mo
# citing a Missouri Independent article that never mentions a lawsuit. ABC17
# reports the Feb 17, 2026 suit but names no company, so pinning it to either
# Montgomery County site would be the curator's inference. Lead in BACKLOG §3.
RESPONSES_REMOVED = ["resp-google-new-florence-preserve-lawsuit", "resp-amazon-montgomery-preserve-lawsuit"]


def upsert(records: list[dict], rec: dict) -> bool:
    """Insert-only: an id already in the seed is left alone, so a re-run never
    reverts a later edit (a daily refresh flipping Oakland to enacted)."""
    if any(r["id"] == rec["id"] for r in records):
        return False
    records.append({"captured_at": CAPTURED, **rec})
    return True


def find(records: list[dict], rid: str, kind: str) -> dict:
    rec = next((r for r in records if r["id"] == rid), None)
    if rec is None:
        raise SystemExit(f"{kind} {rid!r} not in the seed (renamed?); update this script")
    return rec


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    # One-shot replay of git-ignored agent outputs. On a clean checkout the
    # inputs are absent; fail rather than log "added: 0" and exit 0.
    if not (OUT / "site_updates.jsonl").exists():
        raise SystemExit(f"{OUT} is missing: this script replays the 2026-10-08 agent outputs "
                         "and only runs in the checkout that produced them")

    pj = json.loads((SEED / "projects.json").read_text())
    n = apply_site_updates(pj["projects"])
    (SEED / "projects.json").write_text(json.dumps(pj, indent=2, ensure_ascii=False) + "\n")
    log.info("site updates added: %d", n)

    mj = json.loads((SEED / "moratoriums.json").read_text())
    added = sum(upsert(mj["moratoriums"], m) for m in NEW_MORATORIUMS)
    tx = find(mj["moratoriums"], "texas-state-2026-08", "moratorium")
    if "September 21, 2026" not in tx["summary"]:
        tx["summary"] += TEXAS_TCEQ
        tx.setdefault("resources", None)
        tx["resources"] = (tx["resources"] or []) + [TEXAS_TCEQ_RESOURCE]
        tx["captured_at"] = CAPTURED
    (SEED / "moratoriums.json").write_text(json.dumps(mj, indent=2, ensure_ascii=False) + "\n")
    log.info("moratoriums added: %d (+ Texas TCEQ update)", added)

    polj = json.loads((SEED / "policies.json").read_text())
    added = sum(upsert(polj["policies"], p) for p in NEW_POLICIES)
    (SEED / "policies.json").write_text(json.dumps(polj, indent=2, ensure_ascii=False) + "\n")
    log.info("policies added: %d", added)

    rj = json.loads((SEED / "responses.json").read_text())
    rj["responses"] = [r for r in rj["responses"] if r["id"] not in RESPONSES_REMOVED]
    (SEED / "responses.json").write_text(json.dumps(rj, indent=2, ensure_ascii=False) + "\n")
    log.info("responses removed: %s", RESPONSES_REMOVED)

    rcj = json.loads((SEED / "rate_cases.json").read_text())
    duke = find(rcj["rate_cases"], "nc-ncuc-duke-settlement-2026", "rate case")
    if "October 7, 2026" not in duke["next_milestone"]:
        duke["next_milestone"] += DUKE_SETTLEMENT
        duke["resources"] = (duke.get("resources") or []) + [DUKE_RESOURCE]
        duke["captured_at"] = CAPTURED
    (SEED / "rate_cases.json").write_text(json.dumps(rcj, indent=2, ensure_ascii=False) + "\n")
    log.info("rate case updated: nc-ncuc-duke-settlement-2026")


if __name__ == "__main__":
    main()
