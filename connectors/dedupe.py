"""Dedupe accelerator -- mechanical pre-flight check before adding a new record.

Fixes a specific, recurring failure mode documented in REFRESH.md's "Learned
patterns": a research pass pre-flights a lead by substring-matching the
headline's place name against the seed ("missouri", "aurora", "Montgomery
County") and misses an exact duplicate filed under a differently-worded name
-- `google-new-florence-mo` was already in the seed under a city name that
shares no substring with the headline's "Montgomery County" framing. It was
only caught by schema validation's duplicate-id check, and it recurred a
WEEK LATER when a second agent re-flagged the same lead -- "prose reminders
[in REFRESH.md] aren't sticking across sessions." The prescribed fix was
always a mechanical check ("eyeball every row in that state"), never a
remembered habit; this script IS that mechanical check, so it doesn't have
to be re-typed as an ad-hoc `python3 -c "..."` one-liner every single time
(and can be updated in one place as new record types/fields are added).

    python -m connectors.dedupe projects --state OK
    python -m connectors.dedupe projects --company google
    python -m connectors.dedupe moratoriums --state SC
    python -m connectors.dedupe all --state GA        # every record type at once

This is a LISTING tool, not a matcher -- unlike `connectors.scout`'s
token-overlap heuristic, it does no fuzzy comparison at all. It prints every
existing record for the state/company you're about to add to, on the theory
that a human (or agent) eyeballing ~5-15 rows will catch a duplicate a
substring match misses, and that a short, honest list beats a heuristic that
can be silently wrong in either direction. Read every row before deciding a
lead is new -- an empty result means "no existing record in this state",
not "definitely not a duplicate" (a project can be recorded under a
different state if the seed has a data entry error).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from connectors.scout import _load as _load_seed

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "seed"


def _load(name: str) -> list[dict]:
    """Thin wrapper around scout._load, pointed at THIS module's `SEED` (kept
    as its own constant so tests can monkeypatch it independently of scout's).
    See scout._load's docstring for why the fallback logic lives there once."""
    return _load_seed(name, seed_dir=SEED)


def _filter_state(rows: list[dict], state_field: str, state: str) -> list[dict]:
    want = state.strip().upper()
    return [r for r in rows if (r.get(state_field) or "").strip().upper() == want]


# -- per-type listings --------------------------------------------------------
def _projects(state: str | None, company: str | None) -> list[dict]:
    rows = _load("projects")
    if state:
        rows = _filter_state(rows, "state", state)
    if company:
        # company_slug values are lowercase-hyphenated; normalize the same way
        # --state already is (--state was case-insensitive, --company wasn't --
        # found by adversarial PR review, 2026-08-24: `--company Google` silently
        # returned zero rows against a seed that has 32 google-slug projects).
        want = company.strip().lower()
        rows = [r for r in rows if (r.get("company_slug") or "").strip().lower() == want]
    return rows


def _moratoriums(state: str | None) -> list[dict]:
    rows = _load("moratoriums")
    if state:
        rows = _filter_state(rows, "state_code", state)
    return rows


def _tariffs(state: str | None) -> list[dict]:
    rows = _load("tariffs")
    if state:
        rows = _filter_state(rows, "state", state)
    return rows


def _rate_cases(state: str | None) -> list[dict]:
    rows = _load("rate_cases")
    if state:
        rows = _filter_state(rows, "state_code", state)
    return rows


# -- output --------------------------------------------------------------
def _print_table(rows: list[dict], columns: list[tuple[str, str]]) -> None:
    """columns: list of (field, header). Missing/None renders as '-'."""
    if not rows:
        print("  (none in the seed -- no existing record to collide with)")
        return
    widths = [max(len(header), *(len(str(r.get(f) or "-")) for r in rows)) for f, header in columns]
    header_line = "  ".join(h.ljust(w) for (f, h), w in zip(columns, widths))
    print(f"  {header_line}")
    print(f"  {'-' * len(header_line)}")
    for r in rows:
        line = "  ".join(str(r.get(f) or "-").ljust(w) for (f, _), w in zip(columns, widths))
        print(f"  {line}")


def _report(label: str, rows: list[dict], columns: list[tuple[str, str]], as_json: bool) -> dict:
    if as_json:
        return {"type": label, "count": len(rows), "records": rows}
    print(f"\n-- {label} ({len(rows)}) --")
    _print_table(rows, columns)
    return {}


PROJECT_COLS = [("id", "id"), ("company_slug", "company"), ("city", "city"), ("state", "st"), ("name", "name")]
MORATORIUM_COLS = [("id", "id"), ("jurisdiction", "jurisdiction"), ("jurisdiction_type", "type"), ("status", "status")]
TARIFF_COLS = [("id", "id"), ("utility", "utility"), ("state", "st"), ("status", "status")]
RATE_CASE_COLS = [("id", "id"), ("utility", "utility"), ("state_code", "st"), ("status", "status")]


def cmd_projects(args: argparse.Namespace) -> int:
    rows = _projects(args.state, args.company)
    if args.json:
        print(json.dumps(_report("projects", rows, PROJECT_COLS, True), indent=2))
    else:
        _report("projects", rows, PROJECT_COLS, False)
    return 0


def cmd_moratoriums(args: argparse.Namespace) -> int:
    rows = _moratoriums(args.state)
    if args.json:
        print(json.dumps(_report("moratoriums", rows, MORATORIUM_COLS, True), indent=2))
    else:
        _report("moratoriums", rows, MORATORIUM_COLS, False)
    return 0


def cmd_tariffs(args: argparse.Namespace) -> int:
    rows = _tariffs(args.state)
    if args.json:
        print(json.dumps(_report("tariffs", rows, TARIFF_COLS, True), indent=2))
    else:
        _report("tariffs", rows, TARIFF_COLS, False)
    return 0


def cmd_rate_cases(args: argparse.Namespace) -> int:
    rows = _rate_cases(args.state)
    if args.json:
        print(json.dumps(_report("rate_cases", rows, RATE_CASE_COLS, True), indent=2))
    else:
        _report("rate_cases", rows, RATE_CASE_COLS, False)
    return 0


def cmd_all(args: argparse.Namespace) -> int:
    """Every record type for one state in one pass -- the common case: a lead
    might turn out to be a project, a moratorium, a tariff, or a rate case,
    and it's cheaper to check all four than to guess which one first."""
    if not args.state:
        print("--state is required for 'all' (state is the only field every record type shares)")
        return 2
    results = {
        "projects": _projects(args.state, None),
        "moratoriums": _moratoriums(args.state),
        "tariffs": _tariffs(args.state),
        "rate_cases": _rate_cases(args.state),
    }
    if args.json:
        print(json.dumps(results, indent=2))
        return 0
    _report("projects", results["projects"], PROJECT_COLS, False)
    _report("moratoriums", results["moratoriums"], MORATORIUM_COLS, False)
    _report("tariffs", results["tariffs"], TARIFF_COLS, False)
    _report("rate_cases", results["rate_cases"], RATE_CASE_COLS, False)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="connectors.dedupe",
        description="List existing seed records for a state/company -- eyeball before adding a new one.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("projects", help="list existing projects")
    pr.add_argument("--state", help="2-letter state code")
    pr.add_argument("--company", help="company_slug")
    pr.add_argument("--json", action="store_true")
    pr.set_defaults(func=cmd_projects)

    mo = sub.add_parser("moratoriums", help="list existing moratoriums")
    mo.add_argument("--state", help="2-letter state code")
    mo.add_argument("--json", action="store_true")
    mo.set_defaults(func=cmd_moratoriums)

    ta = sub.add_parser("tariffs", help="list existing tariffs")
    ta.add_argument("--state", help="2-letter state code")
    ta.add_argument("--json", action="store_true")
    ta.set_defaults(func=cmd_tariffs)

    rc = sub.add_parser("rate-cases", help="list existing rate cases")
    rc.add_argument("--state", help="2-letter state code")
    rc.add_argument("--json", action="store_true")
    rc.set_defaults(func=cmd_rate_cases)

    al = sub.add_parser("all", help="list every record type for one state")
    al.add_argument("--state", help="2-letter state code (required)")
    al.add_argument("--json", action="store_true")
    al.set_defaults(func=cmd_all)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
