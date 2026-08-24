"""Recheck accelerator -- ready-to-run search queries for stale pending records.

`refresh.py --audit` already identifies WHICH `proposed`/`pending` moratoriums,
tariffs, and rate cases are stale (not re-verified in `STALE_PENDING_DAYS`) and
writes them to ISSUES.md -- see `refresh._audit_stale_pending`, imported here
directly rather than re-implemented, so the two can never drift on what
"stale" means (CLAUDE.md's single-source-of-truth rule). What ISSUES.md does
NOT do is turn that list into something to act on -- a curator/agent still has
to hand-write a search query per record from the id and jurisdiction. This
turns that into one command:

    python -m connectors.recheck stale
    python -m connectors.recheck stale --kind moratorium --json

For each stale record it emits ready-to-run search strings (using the record's
own bill/docket number when present -- much higher-precision than a bare
jurisdiction name) plus a docket-system hint for the record's state, so a
curator/agent can go straight to WebSearch or the regulator's own docket
search instead of guessing where to look.

This does NOT verify anything itself -- same guardrail as `connectors.research`
and `connectors.scout`: running the searches, reading the results, and
deciding whether status changed stays a human/agent judgment call. Follow
REFRESH.md's "Status re-check checklist" when acting on the output:
  - status changed -> update status + enacted_date/failure_reason, bump
    captured_at to today
  - re-confirmed unchanged -> bump captured_at to today (so it doesn't
    re-flag for another STALE_PENDING_DAYS)
  - could NOT verify (paywall/403/no fresh coverage) -> leave the record
    COMPLETELY untouched, including captured_at -- a bumped date on an
    unverified record silently retires it from the audit
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # so `import refresh` / `import schema` resolve when run via -m

SEED = ROOT / "data" / "seed"

from refresh import STALE_PENDING_DAYS, _audit_stale_pending, _load_payload  # noqa: E402
from schema import MoratoriumsPayload, RateCasesPayload, TariffsPayload  # noqa: E402

# Best-effort docket-system hints for states that have shown up in this
# dataset's tariff/rate-case records so far -- not exhaustive. Unknown states
# fall back to a generic "check the state PUC/PSC docket search" hint. Add an
# entry here as a new state's docket system gets used in a real record,
# rather than letting this list silently go stale relative to the seed.
DOCKET_SYSTEM_HINTS: dict[str, str] = {
    "MO": "Missouri PSC EFIS docket search (efis.psc.mo.gov)",
    "AZ": "Arizona Corp. Commission eDocket (edocket.azcc.gov)",
    "NC": "NC Utilities Commission starw1 docket search (starw1.ncuc.gov)",
    "NV": "Nevada PUC PUCN docket search (puc.nv.gov)",
    "US": "FERC eLibrary (elibrary.ferc.gov)",
    "CO": "Colorado PUC e-filings (dora.colorado.gov/puc)",
    "VA": "Virginia SCC Clerk's Information System (scc.virginia.gov/docketsearch)",
    "OH": "Ohio PUCO docketing (dis.puc.state.oh.us)",
    "MN": "Minnesota PUC eDockets (edockets.puc.state.mn.us)",
}


def _load(name: str) -> dict[str, dict]:
    """Raw seed rows keyed by id, for fields _audit_stale_pending doesn't carry
    (bill_number, docket_number, state, utility) -- the audit summary only has
    id/jurisdiction/captured_at/age_days, not enough to build a good query."""
    payload = json.loads((SEED / f"{name}.json").read_text())
    key = name if name in payload else next(k for k, v in payload.items() if isinstance(v, list))
    return {r["id"]: r for r in payload[key]}


def _moratorium_queries(row: dict) -> list[str]:
    bill = row.get("bill_number")
    jurisdiction = row.get("jurisdiction", "")
    state = row.get("state_code") or ""
    base = f"{jurisdiction} {state} data center moratorium".strip()
    qs = [base]
    if bill:
        qs.append(f"{jurisdiction} {state} {bill} data center".strip())
    qs.append(f"{jurisdiction} {state} data center ordinance vote 2026".strip())
    return qs


def _tariff_or_rate_case_queries(row: dict, state_field: str) -> list[str]:
    utility = row.get("utility", "")
    state = row.get(state_field) or ""
    docket = row.get("docket_number")
    qs = [f"{utility} {state} data center tariff large load docket".strip()]
    if docket:
        qs.append(f"{docket} {utility} PUC PSC order".strip())
    return qs


def cmd_stale(args: argparse.Namespace) -> int:
    moratoriums = _load_payload("moratoriums", MoratoriumsPayload)
    tariffs = _load_payload("tariffs", TariffsPayload)
    rate_cases = _load_payload("rate_cases", RateCasesPayload)
    stale = _audit_stale_pending(moratoriums, tariffs, rate_cases)

    if args.kind:
        stale = [s for s in stale if s["kind"] == args.kind]

    raw = {
        "moratorium": _load("moratoriums"),
        "tariff": _load("tariffs"),
        "rate_case": _load("rate_cases"),
    }

    items = []
    for s in stale:
        row = raw[s["kind"]].get(s["id"], {})
        if s["kind"] == "moratorium":
            queries = _moratorium_queries(row)
            state = row.get("state_code") or ""
            docket_hint = DOCKET_SYSTEM_HINTS.get(state, "state legislature bill tracker + local council agenda site")
        elif s["kind"] == "tariff":
            queries = _tariff_or_rate_case_queries(row, "state")
            state = row.get("state") or ""
            docket_hint = DOCKET_SYSTEM_HINTS.get(state, f"state PUC/PSC docket search for {state}")
        else:  # rate_case
            queries = _tariff_or_rate_case_queries(row, "state_code")
            state = row.get("state_code") or ""
            docket_hint = DOCKET_SYSTEM_HINTS.get(state, f"state PUC/PSC docket search for {state}")
        items.append(
            {
                "id": s["id"],
                "kind": s["kind"],
                "jurisdiction": s["jurisdiction"],
                "status": row.get("status"),
                "captured_at": s["captured_at"],
                "age_days": s["age_days"],
                "docket_hint": docket_hint,
                "queries": queries,
            }
        )

    if args.json:
        print(json.dumps({"stale_pending_days": STALE_PENDING_DAYS, "items": items}, indent=2))
        return 0

    print(f"{len(items)} stale record(s) (proposed/pending, not re-checked in {STALE_PENDING_DAYS}+ days)\n")
    for it in items:
        print(f"# {it['id']}  [{it['kind']}]  captured {it['captured_at']} ({it['age_days']}d ago)")
        print(f"  docket hint: {it['docket_hint']}")
        for q in it["queries"]:
            print(f"  search: {q}")
        print()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="connectors.recheck",
        description="Ready-to-run search queries for stale pending moratoriums/tariffs/rate cases.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("stale", help="emit queries for every stale-pending record")
    s.add_argument("--kind", choices=["moratorium", "tariff", "rate_case"], help="filter to one record type")
    s.add_argument("--json", action="store_true", help="machine-readable output")
    s.set_defaults(func=cmd_stale)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
