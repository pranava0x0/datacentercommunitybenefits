"""Daily-refresh work queue: which site, company or state to review next.

Units are DERIVED, never listed by hand:
- every project in projects.json is a `site:<id>`,
- every company in companies.json is a `company:<slug>`,
- every key of `STATE_NAMES` in docs/app.js, plus `US` for federal records,
  is a `state:<XX>`.

`data/refresh_ledger.json` records only when each unit was last reviewed, what
the review found, and dated follow-ups ("Oct 6: Manatee County second
hearing"). It never enumerates units. A project added tomorrow joins the queue
by existing (CLAUDE.md: a hand-written list that mirrors a registry rots).

Some follow-ups are derived from the data rather than stored, so they can't
drift from it:
- a pending rate case's `next_milestone_date` falls due the day after;
- an enacted moratorium with `duration_months` falls due when its computed
  end date passes. Did it lapse, get extended, or become a permanent rule?
A derived follow-up goes away when the record changes. A new milestone date,
a new duration, or a later `captured_at` than the due date all count as
"handled".

Run plan (`--next N`):
1. Units with a follow-up due on or before today, earliest first. These are
   quick, targeted checks ("did the Oct 6 hearing adopt it?").
2. Then full reviews in a fixed rhythm: a site; then a state on odd days or a
   company on even days; then another site; then whichever kind skipped its
   turn. Within a kind, the most overdue unit goes first: days since its last
   review over the kind's target interval (site 90 days, state 120, company
   30). A never-reviewed site counts from its record's `captured_at`, and a
   never-reviewed company from companies.json `last_reviewed`. A
   never-reviewed state counts as exactly due, busiest first.
Sites get about two reviews a day and states and companies one every other
day. At two to three units per run that is roughly one pass over all sites
per quarter and over companies per month.

Usage:
    python3 scripts/refresh_queue.py                    # top of the queue, readable
    python3 scripts/refresh_queue.py --next 3 --json    # what the routine works on
    python3 scripts/refresh_queue.py --unit state:GA    # one unit's records + leads
    python3 scripts/refresh_queue.py --mark site:meta-newton-ga \\
        --summary "Status + figures re-verified; 1 county approval added" \\
        --follow-up 2026-11-04 "Nov 3 ballot measure outcome"
    python3 scripts/refresh_queue.py --write-backlog    # regenerate BACKLOG.md §1
    python3 scripts/refresh_queue.py --check            # validate the ledger (CI/tests)

`--mark` clears follow-ups that were due on or before the review date (the
review handled them) unless `--keep-due` is passed, and appends any new
`--follow-up`s. Every write is immediate. The routine marks each unit as soon
as it finishes it, so a killed run loses at most the unit in progress.
"""

from __future__ import annotations

import argparse
import calendar
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "seed"
LEDGER = ROOT / "data" / "refresh_ledger.json"
BACKLOG = ROOT / "BACKLOG.md"
APP_JS = ROOT / "docs" / "app.js"

TARGET_DAYS = {"site": 90, "state": 120, "company": 30}
KIND_ORDER = {"site": 0, "state": 1, "company": 2}
START = "<!-- refresh-queue:start -->"
END = "<!-- refresh-queue:end -->"
FEDERAL = "US"


def _load(name: str, key: str) -> list[dict]:
    return json.loads((SEED / name).read_text())[key]


def state_names() -> dict[str, str]:
    """`STATE_NAMES` from docs/app.js: the frontend's registry, reused so the
    queue and the state strip can't disagree about which states exist."""
    js = APP_JS.read_text()
    block = re.search(r"const STATE_NAMES = \{(.*?)\};", js, re.S)
    if not block:
        raise SystemExit("STATE_NAMES not found in docs/app.js")
    return dict(re.findall(r'\b([A-Z]{2}):\s*"([^"]+)"', block.group(1)))


@dataclass
class Unit:
    key: str
    kind: str
    label: str
    baseline: Optional[date]  # when the record was last curated, if never reviewed
    records: dict[str, list[str]] = field(default_factory=dict)
    last_reviewed: Optional[date] = None
    summary: str = ""
    follow_ups: list[dict] = field(default_factory=list)
    last_check: Optional[dict] = None

    def due_follow_ups(self, today: date) -> list[dict]:
        return sorted(
            (f for f in self.follow_ups if date.fromisoformat(f["due"]) <= today),
            key=lambda f: f["due"],
        )

    def overdue_ratio(self, today: date) -> float:
        ref = self.last_reviewed or self.baseline
        if ref is None:  # never-reviewed state: exactly due, busiest first
            return 1.0 + min(sum(map(len, self.records.values())), 99) / 1000
        return (today - ref).days / TARGET_DAYS[self.kind]


def derive_units() -> dict[str, Unit]:
    projects = _load("projects.json", "projects")
    claims = _load("claims.json", "claims")
    responses = _load("responses.json", "responses")
    companies = _load("companies.json", "companies")
    names = state_names()

    units: dict[str, Unit] = {}
    by_project: dict[str, dict[str, list[str]]] = {}
    for c in claims:
        if c.get("project_id"):
            by_project.setdefault(c["project_id"], {}).setdefault("claims", []).append(c["id"])
    for r in responses:
        by_project.setdefault(r["project_id"], {}).setdefault("responses", []).append(r["id"])

    for p in projects:
        key = f"site:{p['id']}"
        units[key] = Unit(
            key, "site", f"{p['name']} ({p['city']}, {p['state']}; {p['status']})",
            date.fromisoformat(p["captured_at"]), by_project.get(p["id"], {}),
        )
    for c in companies:
        n_projects = sum(p["company_slug"] == c["slug"] for p in projects)
        units[f"company:{c['slug']}"] = Unit(
            f"company:{c['slug']}", "company", f"{c['name']} ({n_projects} tracked sites)",
            date.fromisoformat(c["last_reviewed"]),
            {"projects": [p["id"] for p in projects if p["company_slug"] == c["slug"]]},
        )
    for code, name in list(names.items()) + [(FEDERAL, "Federal (FERC, Congress, agencies)")]:
        units[f"state:{code}"] = Unit(f"state:{code}", "state", name, None, {})

    def add(code: Optional[str], payload: str, rid: str) -> None:
        u = units.get(f"state:{code}") if code else None
        if u is not None:
            u.records.setdefault(payload, []).append(rid)

    for p in projects:
        add(p["state"], "projects", p["id"])
    for m in _load("moratoriums.json", "moratoriums"):
        add(FEDERAL if m["jurisdiction_type"] == "federal" else m.get("state_code"), "moratoriums", m["id"])
    for t in _load("tariffs.json", "tariffs"):
        add(FEDERAL if t.get("jurisdiction_level") == "federal" else t.get("state"), "tariffs", t["id"])
    for rc in _load("rate_cases.json", "rate_cases"):
        add(rc.get("state_code"), "rate_cases", rc["id"])
    for pol in _load("policies.json", "policies"):
        add(pol.get("state_code"), "policies", pol["id"])
    for s in _load("signatories.json", "signatories"):
        if s["category"] == "governor":
            add(s.get("state"), "governor", s["id"])
    return units


def _add_months(d: date, months: int) -> date:
    y, m = divmod(d.month - 1 + months, 12)
    y += d.year
    return date(y, m + 1, min(d.day, calendar.monthrange(y, m + 1)[1]))


def derived_follow_ups() -> dict[str, list[dict]]:
    """Follow-ups implied by the records themselves (see module docstring)."""
    out: dict[str, list[dict]] = {}
    for rc in _load("rate_cases.json", "rate_cases"):
        d = rc.get("next_milestone_date")
        if rc["status"] == "pending" and d:
            due = date.fromisoformat(d) + timedelta(days=1)
            if date.fromisoformat(rc["captured_at"]) < due:
                out.setdefault(f"state:{rc.get('state_code') or FEDERAL}", []).append({
                    "due": due.isoformat(),
                    "what": f"rate case `{rc['id']}`: {d} milestone passed; record the outcome "
                            "and the next announced step",
                    "derived": True,
                })
    for m in _load("moratoriums.json", "moratoriums"):
        start = m.get("effective_date") or m.get("enacted_date")
        if m["status"] != "enacted" or not m.get("duration_months") or not start:
            continue
        end = _add_months(date.fromisoformat(start), m["duration_months"])
        if date.fromisoformat(m["captured_at"]) < end:
            code = FEDERAL if m["jurisdiction_type"] == "federal" else m.get("state_code")
            out.setdefault(f"state:{code}", []).append({
                "due": end.isoformat(),
                "what": f"moratorium `{m['id']}` ({m['jurisdiction']}) reaches its computed end "
                        f"date {end}: lapsed, extended, or replaced by a permanent rule?",
                "derived": True,
            })
    return out


def load_ledger() -> dict:
    if not LEDGER.exists():
        return {"units": {}}
    return json.loads(LEDGER.read_text())


def save_ledger(ledger: dict) -> None:
    ledger["units"] = dict(sorted(ledger["units"].items()))
    LEDGER.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n")


def merged_units() -> dict[str, Unit]:
    units = derive_units()
    for key, entry in load_ledger()["units"].items():
        u = units.get(key)
        if u is None:
            continue  # reported by --check; a removed record shouldn't crash the queue
        if entry.get("last_reviewed"):
            u.last_reviewed = date.fromisoformat(entry["last_reviewed"])
        u.summary = entry.get("summary", "")
        u.follow_ups = list(entry.get("follow_ups", []))
        u.last_check = entry.get("last_check")
    for key, items in derived_follow_ups().items():
        if key in units:
            units[key].follow_ups.extend(items)
    return units


def ranked(units: dict[str, Unit], today: date) -> list[tuple[Unit, str]]:
    due, rest = [], []
    for u in units.values():
        d = u.due_follow_ups(today)
        if d:
            due.append((d[0]["due"], u, f"follow-up due {d[0]['due']}: {d[0]['what']}"))
        else:
            ratio = u.overdue_ratio(today)
            ref = u.last_reviewed or u.baseline
            if u.last_reviewed:
                why = f"reviewed {u.last_reviewed} ({ratio:.1f}x its {TARGET_DAYS[u.kind]}-day target)"
            elif ref:
                why = f"never reviewed; record curated {ref} ({ratio:.1f}x target)"
            else:
                n = sum(map(len, u.records.values()))
                why = f"never reviewed; {n} records"
            rest.append((ratio, u, why))
    due.sort(key=lambda t: (t[0], KIND_ORDER[t[1].kind], t[1].key))
    rest.sort(key=lambda t: (-t[0], KIND_ORDER[t[1].kind], t[1].key))
    return [(u, why) for _, u, why in due] + [(u, why) for _, u, why in rest]


def run_plan(units: dict[str, Unit], today: date, n: int) -> list[tuple[Unit, str]]:
    """What one run should work through, in order (see module docstring)."""
    order = ranked(units, today)
    due = [t for t in order if t[0].due_follow_ups(today)]
    by_kind = {k: [t for t in order if t[0].kind == k and not t[0].due_follow_ups(today)]
               for k in TARGET_DAYS}
    alt = ("state", "company") if today.toordinal() % 2 else ("company", "state")
    rhythm = ["site", alt[0], "site", alt[1]]
    plan = due[:n]
    i = 0
    while len(plan) < n and any(by_kind.values()):
        kind = rhythm[i % len(rhythm)]
        i += 1
        if by_kind[kind]:
            plan.append(by_kind[kind].pop(0))
    return plan


def backlog_leads(unit_key: str) -> str:
    """The hand-curated lead section for this unit in BACKLOG.md §2, if any.
    Headings there start with the unit key (e.g. `#### state:GA — Georgia`)."""
    if not BACKLOG.exists():
        return ""
    text = BACKLOG.read_text()
    m = re.search(rf"^(#{{3,4}}) {re.escape(unit_key)}\b.*?$(.*?)(?=^#{{2,4}} |\Z)", text, re.S | re.M)
    return m.group(2).strip() if m else ""


def unit_json(u: Unit, why: str, today: date) -> dict:
    return {
        "unit": u.key,
        "kind": u.kind,
        "label": u.label,
        "why_now": why,
        "last_reviewed": u.last_reviewed.isoformat() if u.last_reviewed else None,
        "last_summary": u.summary or None,
        "last_check": u.last_check,
        "due_follow_ups": u.due_follow_ups(today),
        "upcoming_follow_ups": [f for f in u.follow_ups if f not in u.due_follow_ups(today)],
        "records": u.records,
        "backlog_leads": backlog_leads(u.key) or None,
    }


def coverage_line(units: dict[str, Unit], today: date) -> str:
    parts = []
    for kind in ("site", "company", "state"):
        us = [u for u in units.values() if u.kind == kind]
        fresh = sum(
            1 for u in us
            if u.last_reviewed and (today - u.last_reviewed).days <= TARGET_DAYS[kind]
        )
        parts.append(f"{fresh} of {len(us)} {kind if kind != 'company' else 'companie'}s "
                     f"reviewed within {TARGET_DAYS[kind]} days")
    return "; ".join(parts) + "."


def render_backlog_block(units: dict[str, Unit], today: date) -> str:
    order = ranked(units, today)
    lines = [
        START,
        f"_Generated by `python3 scripts/refresh_queue.py --write-backlog` on {today}. "
        "Do not edit between the markers: review dates and follow-ups live in "
        "`data/refresh_ledger.json`, and units come from the data itself._",
        "",
        f"**Coverage:** {coverage_line(units, today)}",
        "",
    ]
    due = [(u, f) for u in units.values() for f in u.due_follow_ups(today)]
    lines.append(f"**Due now ({len(due)})**")
    lines.append("")
    if due:
        lines += ["| Due | Unit | Check |", "|---|---|---|"]
        for u, f in sorted(due, key=lambda t: (t[1]["due"], t[0].key)):
            lines.append(f"| {f['due']} | `{u.key}` | {f['what']} |")
    else:
        lines.append("Nothing due.")
    plan = run_plan(units, today, 4)
    lines += ["", "**Next run works through**", ""]
    for i, (u, why) in enumerate(plan, 1):
        lines.append(f"{i}. `{u.key}` ({u.label}): {why}")
    for kind, n in (("site", 6), ("state", 4), ("company", 4)):
        queue = [t for t in order if t[0].kind == kind and t not in plan][:n]
        lines += ["", f"**Then, {kind if kind != 'company' else 'companie'}s**", "",
                  "| Unit | What | Why now |", "|---|---|---|"]
        for u, why in queue:
            lines.append(f"| `{u.key}` | {u.label} | {why} |")
    horizon = today + timedelta(days=30)
    upcoming = sorted(
        ((f, u) for u in units.values() for f in u.follow_ups
         if today < date.fromisoformat(f["due"]) <= horizon),
        key=lambda t: (t[0]["due"], t[1].key),
    )
    lines += ["", f"**Coming up in the next 30 days ({len(upcoming)})**", ""]
    if upcoming:
        lines += ["| Due | Unit | Check |", "|---|---|---|"]
        for f, u in upcoming:
            lines.append(f"| {f['due']} | `{u.key}` | {f['what']} |")
    else:
        lines.append("No dated follow-ups in the next 30 days.")
    recent = []
    for u in units.values():
        if u.last_reviewed and (today - u.last_reviewed).days <= 14:
            recent.append((u.last_reviewed, u.key, "review", u.summary or "(no summary)"))
        lc = u.last_check
        if lc and (today - date.fromisoformat(lc["date"])).days <= 14:
            recent.append((date.fromisoformat(lc["date"]), u.key, "check", lc["summary"]))
    recent.sort(reverse=True)
    lines += ["", f"**Reviewed or checked in the last 14 days ({len(recent)})**", ""]
    if recent:
        for when, key, kind, text in recent[:15]:
            lines.append(f"- {when} `{key}` ({kind}): {text}")
        if len(recent) > 15:
            lines.append(f"- …and {len(recent) - 15} more (see `data/refresh_ledger.json`).")
    else:
        lines.append("None yet.")
    lines.append(END)
    return "\n".join(lines)


def write_backlog(units: dict[str, Unit], today: date) -> bool:
    text = BACKLOG.read_text()
    if START not in text or END not in text:
        raise SystemExit(f"BACKLOG.md is missing the {START} / {END} markers")
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    new = head + render_backlog_block(units, today) + tail
    if new != text:
        BACKLOG.write_text(new)
        return True
    return False


def check_ledger() -> list[str]:
    problems = []
    units = derive_units()
    ledger = load_ledger()
    if set(ledger) - {"about", "units"}:
        problems.append(f"unexpected top-level keys: {sorted(set(ledger) - {'about', 'units'})}")
    for key, entry in ledger.get("units", {}).items():
        if key not in units:
            problems.append(f"{key}: not a unit (record renamed or removed?)")
        if not entry.get("last_reviewed") and not entry.get("follow_ups") and not entry.get("last_check"):
            problems.append(f"{key}: empty entry (no review, check or follow-ups)")
        lc = entry.get("last_check")
        if lc is not None:
            if not isinstance(lc, dict) or not lc.get("summary"):
                problems.append(f"{key}: last_check needs a summary: {lc}")
            try:
                date.fromisoformat((lc or {}).get("date", "") if isinstance(lc, dict) else "")
            except ValueError:
                problems.append(f"{key}: last_check needs an ISO date: {lc}")
        extra = set(entry) - {"last_reviewed", "summary", "follow_ups", "last_check"}
        if extra:
            problems.append(f"{key}: unexpected fields {sorted(extra)}")
        try:
            if entry.get("last_reviewed"):
                date.fromisoformat(entry["last_reviewed"])
        except ValueError:
            problems.append(f"{key}: last_reviewed is not an ISO date")
        for f in entry.get("follow_ups", []):
            if set(f) - {"due", "what", "hint"} or not f.get("what"):
                problems.append(f"{key}: follow-up needs due + what (+ optional hint): {f}")
            try:
                date.fromisoformat(f.get("due", ""))
            except ValueError:
                problems.append(f"{key}: follow-up due is not an ISO date: {f}")
    return problems


def mark(key: str, summary: str, follow_ups: list[list[str]], on: date,
         keep_due: bool, hint: Optional[str], followups_only: bool = False) -> None:
    units = derive_units()
    if key not in units:
        close = [k for k in units if k.split(":", 1)[-1] in key or key.split(":", 1)[-1] in k][:5]
        raise SystemExit(f"unknown unit {key!r}. Similar: {close}")
    ledger = load_ledger()
    entry = ledger["units"].setdefault(key, {})
    if followups_only:  # a quick follow-up check is not a full review...
        # ...but what it found must survive the run, not only its commit message.
        entry["last_check"] = {"date": on.isoformat(), "summary": summary.strip()}
    else:
        entry["last_reviewed"] = on.isoformat()
        entry["summary"] = summary.strip()
    kept = [
        f for f in entry.get("follow_ups", [])
        if keep_due or date.fromisoformat(f["due"]) > on
    ]
    for due, what in follow_ups:
        date.fromisoformat(due)
        item = {"due": due, "what": what.strip()}
        if hint:
            item["hint"] = hint
        if item not in kept:
            kept.append(item)
    if kept:
        entry["follow_ups"] = sorted(kept, key=lambda f: (f["due"], f["what"]))
    else:
        entry.pop("follow_ups", None)
    if not entry.get("last_reviewed") and not entry.get("follow_ups") and not entry.get("last_check"):
        # A `--followups-only` mark whose unit had no *stored* follow-ups (the
        # due item was purely derived — see module docstring) both skips
        # last_reviewed/summary and clears the (empty) follow_ups list, so the
        # entry setdefault'd above would otherwise be left as a bare `{}`: an
        # empty ledger entry that carries no information and fails
        # check_ledger(). Drop it — a unit with nothing stored is exactly a
        # never-reviewed unit, which is already how a MISSING key is read.
        ledger["units"].pop(key, None)
    save_ledger(ledger)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--today", type=date.fromisoformat, default=date.today())
    ap.add_argument("--next", type=int, metavar="N")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--unit", metavar="KEY", help="show one unit: records, ledger entry, backlog leads")
    ap.add_argument("--mark", metavar="KEY")
    ap.add_argument("--summary", default="")
    ap.add_argument("--follow-up", nargs=2, action="append", default=[], metavar=("YYYY-MM-DD", "WHAT"))
    ap.add_argument("--hint", help="URL or note attached to the --follow-up(s) given")
    ap.add_argument("--keep-due", action="store_true")
    ap.add_argument("--followups-only", action="store_true",
                    help="with --mark: clear due follow-ups and add new ones without "
                         "counting it as a full review (last_reviewed unchanged)")
    ap.add_argument("--write-backlog", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args(argv)

    if args.check:
        problems = check_ledger()
        for p in problems:
            print("LEDGER:", p)
        print("ledger ok" if not problems else f"{len(problems)} ledger problem(s)")
        return 1 if problems else 0
    if args.mark:
        if not args.summary:
            raise SystemExit("--mark needs --summary (what was checked, what changed)")
        mark(args.mark, args.summary, args.follow_up, args.today, args.keep_due, args.hint,
             args.followups_only)
        print(f"{args.mark}: follow-ups updated" if args.followups_only
              else f"{args.mark}: marked reviewed {args.today}")
        if not args.write_backlog:
            return 0
    units = merged_units()
    if args.write_backlog:
        changed = write_backlog(units, args.today)
        print("BACKLOG.md queue block " + ("updated" if changed else "unchanged"))
        return 0
    if args.unit:
        u = units.get(args.unit)
        if u is None:
            raise SystemExit(f"unknown unit {args.unit!r}")
        why = dict((x.key, w) for x, w in ranked(units, args.today))[u.key]
        print(json.dumps(unit_json(u, why, args.today), indent=2, ensure_ascii=False))
        return 0
    order = ranked(units, args.today)
    if args.next is not None:
        picked = run_plan(units, args.today, args.next)
        if args.json:
            print(json.dumps([unit_json(u, why, args.today) for u, why in picked], indent=2, ensure_ascii=False))
        else:
            for u, why in picked:
                print(f"{u.key:48} {why}")
        return 0
    print(coverage_line(units, args.today))
    for i, (u, why) in enumerate(order[: args.top], 1):
        print(f"{i:3} {u.key:48} {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
