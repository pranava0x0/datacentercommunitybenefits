"""Refresh driver — validates `data/seed/*.json` and emits `docs/data/*.json`.

In v1, the seed is the source of truth (curated by hand); this script's job is
to validate it against `schema.py` and copy validated payloads to `docs/data/`
for the frontend.

Usage:
    python refresh.py                 # validate + emit all four payloads
    python refresh.py --check         # validate only; do NOT write outputs
    python refresh.py --pretty        # emit pretty-printed JSON (default: minified)
    python refresh.py --audit         # flag projects missing key commitment details

Per CLAUDE.md:
- Schema enforces `extra="forbid"` so any seed drift fails fast here.
- All four payload IDs must be unique within their type (enforced in schema).
- Cross-record references (claim.project_id, response.project_id, claim.company_slug)
  are checked here as a post-validation pass — Pydantic doesn't know about
  cross-payload joins.
- Commitment audit (--audit) identifies projects missing key fields based on status.
"""

from __future__ import annotations

import argparse
import calendar
import json
import logging
import sys
from datetime import date
from pathlib import Path

from pydantic import ValidationError

from schema import (
    RATEPAYER_PLEDGE_DATE,
    THEMES,
    ClaimsPayload,
    CompaniesPayload,
    MoratoriumsPayload,
    PoliciesPayload,
    ProjectsPayload,
    RateCasesPayload,
    ResponsesPayload,
    SignatoriesPayload,
    TariffsPayload,
)

RATEPAYER_PLEDGE_YEAR = int(RATEPAYER_PLEDGE_DATE[:4])
RATEPAYER_PLEDGE_DATE_OBJ = date.fromisoformat(RATEPAYER_PLEDGE_DATE)

ROOT = Path(__file__).parent
SEED_DIR = ROOT / "data" / "seed"
OUT_DIR = ROOT / "docs" / "data"

PAYLOAD_FILES: dict[str, type] = {
    "companies": CompaniesPayload,
    "claims": ClaimsPayload,
    "projects": ProjectsPayload,
    "responses": ResponsesPayload,
    "moratoriums": MoratoriumsPayload,
    "tariffs": TariffsPayload,
    "signatories": SignatoriesPayload,
    "rate_cases": RateCasesPayload,
    "policies": PoliciesPayload,
}


logger = logging.getLogger("refresh")


def _load_payload(name: str, model: type):
    """Load + validate one seed payload. Raises on schema drift."""
    src = SEED_DIR / f"{name}.json"
    if not src.exists():
        raise FileNotFoundError(f"Seed file missing: {src}")
    raw = json.loads(src.read_text(encoding="utf-8"))
    try:
        return model.model_validate(raw)
    except ValidationError as e:
        logger.error("Validation failed for %s.json:\n%s", name, e)
        raise


def _check_cross_refs(
    companies: CompaniesPayload,
    claims: ClaimsPayload,
    projects: ProjectsPayload,
    responses: ResponsesPayload,
    signatories=None,
    tariffs=None,
    rate_cases=None,
    policies=None,
    moratoriums=None,
) -> list[str]:
    """Cross-payload reference checks. Returns list of error messages (empty = OK)."""
    errors: list[str] = []

    # Policies link to tracked sites and to the moratorium record that carries
    # the same instrument; a broken id would render as a dead link.
    if policies is not None:
        project_ids = {p.id for p in projects.projects}
        moratorium_ids = (
            {m.id for m in moratoriums.moratoriums} if moratoriums is not None else None
        )
        for pol in policies.policies:
            for pid in pol.related_project_ids or []:
                if pid not in project_ids:
                    errors.append(
                        f"policies.json: {pol.id!r} references unknown "
                        f"related_project_id {pid!r}"
                    )
            mid = pol.related_moratorium_id
            if mid is not None and moratorium_ids is not None and mid not in moratorium_ids:
                errors.append(
                    f"policies.json: {pol.id!r} references unknown "
                    f"related_moratorium_id {mid!r}"
                )

    # Rate cases join onto tariffs and projects; a broken id renders as a dead
    # link in the state panel, so it must fail here, not in the browser.
    if rate_cases is not None:
        # tariffs is None means "not passed to this check", not "no tariffs
        # exist" — treating it as an empty set would flag every non-null
        # related_tariff_id as unknown. Skip the check rather than false-fail.
        tariff_ids = {t.id for t in tariffs.tariffs} if tariffs is not None else None
        rc_project_ids = {p.id for p in projects.projects}
        for rc in rate_cases.rate_cases:
            if (
                tariff_ids is not None
                and rc.related_tariff_id is not None
                and rc.related_tariff_id not in tariff_ids
            ):
                errors.append(
                    f"rate_cases.json: case {rc.id!r} references unknown "
                    f"related_tariff_id {rc.related_tariff_id!r}"
                )
            for pid in rc.related_project_ids or []:
                if pid not in rc_project_ids:
                    errors.append(
                        f"rate_cases.json: case {rc.id!r} references unknown "
                        f"related_project_id {pid!r}"
                    )

    # serving_utility_signatory_id must resolve to a real roster row. A typo
    # here fails silently in the browser — the utility lens simply shows no
    # sites, which reads as "this utility serves nothing we track".
    if signatories is not None:
        roster_ids = {s.id for s in signatories.signatories}
        for p in projects.projects:
            sid = p.serving_utility_signatory_id
            if sid and sid not in roster_ids:
                errors.append(
                    f"projects.json: project {p.id!r} serving_utility_signatory_id "
                    f"{sid!r} not found in signatories.json"
                )
            if sid and not p.serving_utility:
                errors.append(
                    f"projects.json: project {p.id!r} sets serving_utility_signatory_id "
                    "without serving_utility — the display name is what readers see"
                )

    company_slugs = {c.slug for c in companies.companies}
    project_ids = {p.id for p in projects.projects}
    claim_ids = {c.id for c in claims.claims}

    for c in claims.claims:
        if c.company_slug not in company_slugs:
            errors.append(
                f"claims.json: claim {c.id!r} references unknown company_slug {c.company_slug!r}"
            )
        if c.project_id is not None and c.project_id not in project_ids:
            errors.append(
                f"claims.json: claim {c.id!r} references unknown project_id {c.project_id!r}"
            )
        if c.theme not in THEMES:
            errors.append(
                f"claims.json: claim {c.id!r} has theme {c.theme!r} not in THEMES vocabulary"
            )

    for p in projects.projects:
        if p.company_slug not in company_slugs:
            errors.append(
                f"projects.json: project {p.id!r} references unknown company_slug {p.company_slug!r}"
            )
        # Ratepayer assessment integrity (v1.15): `affirmed` must cite a backing
        # claim; the cited claim must exist and belong to this project.
        rp = p.ratepayer
        if rp is not None:
            if rp.status == "affirmed":
                if rp.evidence_claim_id is None:
                    errors.append(
                        f"projects.json: project {p.id!r} ratepayer status 'affirmed' "
                        "requires evidence_claim_id"
                    )
                elif rp.evidence_claim_id not in claim_ids:
                    errors.append(
                        f"projects.json: project {p.id!r} ratepayer.evidence_claim_id "
                        f"{rp.evidence_claim_id!r} not found in claims.json"
                    )
            if rp.evidence_claim_id is not None and rp.evidence_claim_id in claim_ids:
                claim = next(c for c in claims.claims if c.id == rp.evidence_claim_id)
                if claim.project_id != p.id:
                    errors.append(
                        f"projects.json: project {p.id!r} ratepayer.evidence_claim_id "
                        f"{rp.evidence_claim_id!r} belongs to project "
                        f"{claim.project_id!r}, not this one"
                    )

    for r in responses.responses:
        if r.project_id not in project_ids:
            errors.append(
                f"responses.json: response {r.id!r} references unknown project_id {r.project_id!r}"
            )

    return errors


def _signatory_dates(signatories) -> dict[str, date]:
    """company slug -> the date that company joined the pledge.

    Read from the roster rather than assumed, because the July 2026 expansion
    made the join date vary by company: the original seven signed 2026-03-04,
    QTS 2026-04-24, and CoreWeave / Crusoe / Prologis 2026-07-23.
    """
    out: dict[str, date] = {}
    for s in signatories.signatories:
        if s.matched_company_slug and s.signed_date:
            out[s.matched_company_slug] = s.signed_date
    return out


def _is_ratepayer_eligible(p, signed_dates: dict[str, date]) -> bool:
    """Mirror docs/app.js's isPrePledgeProject.

    A site is expected to carry a ratepayer assessment only when its operator
    had ALREADY SIGNED when the site was announced. Before v2 this compared
    every project against the single White House date; that silently mislabeled
    the July cohort, whose sites announced in (say) May 2026 predate their own
    operator's signature by two months and cannot reasonably be assessed
    against a pledge that company had not yet made.

    A year-only announcement is treated as pledge-era when the year is at or
    after the signing year: a bare "2026" cannot be placed either side of a
    specific day, so it stays in the awaiting-assessment bucket rather than
    being confidently mislabeled pre-pledge.
    """
    signed = signed_dates.get(p.company_slug)
    if signed is None:
        return False
    if p.announced_date:
        return p.announced_date >= signed
    return p.announced_year >= signed.year


def _audit_missing_commitments(
    projects: ProjectsPayload, signatories
) -> tuple[dict, dict]:
    """Audit projects for missing key commitment details.

    Returns: (critical_missing, medium_missing) dicts keyed by severity.
    """
    signed_dates = _signatory_dates(signatories)

    # Key commitment fields to check
    EXPECTATIONS = {
        "operational": {
            "required": ["claimed_investment_usd", "power_mw"],
            "important": ["claimed_jobs", "at_a_glance", "ratepayer"],
        },
        "construction": {
            "required": ["claimed_investment_usd"],
            "important": ["claimed_jobs", "power_mw", "at_a_glance", "ratepayer"],
        },
        "announced": {
            "required": [],
            "important": ["claimed_investment_usd", "claimed_jobs", "power_mw", "at_a_glance"],
        },
    }

    critical = {}
    medium = {}

    for p in projects.projects:
        status = p.status
        expectations = EXPECTATIONS.get(status, {})
        required = expectations.get("required", [])
        important = expectations.get("important", [])

        missing_critical = []
        missing_medium = []

        for field in required:
            if getattr(p, field, None) is None:
                missing_critical.append(field)

        for field in important:
            if field == "ratepayer" and not _is_ratepayer_eligible(p, signed_dates):
                continue
            if getattr(p, field, None) is None:
                missing_medium.append(field)

        if missing_critical:
            critical[p.id] = {
                "company": p.company_slug,
                "name": p.name,
                "status": status,
                "missing": missing_critical,
            }
        elif missing_medium:
            medium[p.id] = {
                "company": p.company_slug,
                "name": p.name,
                "status": status,
                "missing": missing_medium,
            }

    return critical, medium


STALE_PENDING_DAYS = 21  # matches the skill's "3-week research window" cadence


def _audit_stale_pending(
    moratoriums: MoratoriumsPayload,
    tariffs: TariffsPayload,
    rate_cases: RateCasesPayload | None = None,
    policies: PoliciesPayload | None = None,
) -> list[dict]:
    """Flag proposed/pending public records not re-checked in STALE_PENDING_DAYS.

    A `proposed` bill or docket is a moving target (it can be signed, vetoed,
    or fail in committee at any time) — unlike an `enacted`/`approved` record,
    which is stable once captured. Don't flag those; only pending ones go stale.
    """
    today = date.today()
    stale: list[dict] = []

    for m in moratoriums.moratoriums:
        if m.status == "proposed":
            age = (today - m.captured_at).days
            if age >= STALE_PENDING_DAYS:
                stale.append(
                    {
                        "kind": "moratorium",
                        "id": m.id,
                        "jurisdiction": m.jurisdiction,
                        "captured_at": str(m.captured_at),
                        "age_days": age,
                    }
                )

    for t in tariffs.tariffs:
        if t.status == "proposed":
            age = (today - t.captured_at).days
            if age >= STALE_PENDING_DAYS:
                stale.append(
                    {
                        "kind": "tariff",
                        "id": t.id,
                        "jurisdiction": t.state,
                        "captured_at": str(t.captured_at),
                        "age_days": age,
                    }
                )

    for rc in rate_cases.rate_cases if rate_cases is not None else []:
        if rc.status == "pending":
            age = (today - rc.captured_at).days
            if age >= STALE_PENDING_DAYS:
                stale.append(
                    {
                        "kind": "rate_case",
                        "id": rc.id,
                        "jurisdiction": rc.state_code,
                        "captured_at": str(rc.captured_at),
                        "age_days": age,
                    }
                )

    for policy in policies.policies if policies is not None else []:
        if policy.status == "proposed":
            age = (today - policy.captured_at).days
            if age >= STALE_PENDING_DAYS:
                stale.append(
                    {
                        "kind": "policy",
                        "id": policy.id,
                        "jurisdiction": policy.jurisdiction,
                        "captured_at": str(policy.captured_at),
                        "age_days": age,
                    }
                )

    return stale


def _write_audit_report(
    critical: dict, medium: dict, stale_pending: list[dict] | None = None
) -> None:
    """Write audit report to ISSUES.md."""
    audit_file = ROOT / "ISSUES.md"

    report_lines = [
        "# ISSUES.md — Data Audit Report\n",
        f"Generated: {date.today()}\n",
        f"Total projects needing attention: {len(critical) + len(medium)}\n",
        "\n## Critical Missing Commitment Details\n",
        f"({len(critical)} projects)\n",
        "\nProjects missing required fields based on status:\n",
    ]

    for proj_id in sorted(critical.keys()):
        p = critical[proj_id]
        report_lines.append(f"- **{proj_id}** ({p['status']}): {', '.join(p['missing'])}\n")

    report_lines.extend([
        "\n## Medium Priority Missing Details\n",
        f"({len(medium)} projects)\n",
        "\nProjects with important gaps:\n",
    ])

    for proj_id in sorted(medium.keys()):
        p = medium[proj_id]
        report_lines.append(f"- **{proj_id}** ({p['status']}): {', '.join(p['missing'])}\n")

    if stale_pending:
        report_lines.extend([
            "\n## Stale Pending Records\n",
            f"({len(stale_pending)} {'record' if len(stale_pending) == 1 else 'records'})\n",
            f"\n`proposed` moratoriums/tariffs/policies or `pending` rate cases not re-verified in "
            f"{STALE_PENDING_DAYS}+ days — status may have changed "
            "(signed/vetoed/enacted/rejected). Re-check source and update:\n",
        ])
        for rec in sorted(stale_pending, key=lambda r: -r["age_days"]):
            report_lines.append(
                f"- **{rec['id']}** ({rec['kind']}, {rec['jurisdiction']}): "
                f"captured {rec['captured_at']}, {rec['age_days']} days ago\n"
            )

    audit_file.write_text("".join(report_lines), encoding="utf-8")
    logger.info("Wrote audit report to ISSUES.md")


# "XX" is the sentinel for virtual / multi-site partnerships with no physical
# location. It is not a place and must never become a state.
NON_GEOGRAPHIC_STATE = "XX"


def _build_coverage(projects, tariffs, moratoriums, rate_cases=None, policies=None) -> dict:
    """Per-state record counts for the landing page's coverage surfaces.

    Precomputed here rather than derived in the browser because the landing view
    would otherwise have to download moratoriums.json + tariffs.json (~50 KB
    gzipped) just to draw a state grid. Without this, the strip silently reported
    site counts only: a state with a moratorium and no tracked site rendered as
    "No records yet", which is precisely the opposite of what that chip is for.

    ~2 KB, so it can join first paint without troubling the budget.
    """
    states: dict[str, dict[str, int]] = {}

    def bucket(code):
        if not code:
            return None
        key = str(code).upper()
        if key == NON_GEOGRAPHIC_STATE:
            return None
        return states.setdefault(
            key, {"projects": 0, "tariffs": 0, "moratoriums": 0, "rate_cases": 0, "policies": 0}
        )

    for p in projects.projects:
        b = bucket(p.state)
        if b is not None:
            b["projects"] += 1
    for t in tariffs.tariffs:
        b = bucket(t.state)
        if b is not None:
            b["tariffs"] += 1
    for m in moratoriums.moratoriums:
        b = bucket(m.state_code)
        if b is not None:
            b["moratoriums"] += 1
    if rate_cases is not None:
        for rc in rate_cases.rate_cases:
            if rc.jurisdiction_level == "federal":
                continue  # "US" is not a state cell
            b = bucket(rc.state_code)
            if b is not None:
                b["rate_cases"] += 1
    if policies is not None:
        for pol in policies.policies:
            b = bucket(pol.state_code)  # company-wide / federal have none
            if b is not None:
                b["policies"] += 1

    # Whole-record totals for the Home numbers band. NOT the sum of the state
    # cells: federal records (a FERC rate case, a federal moratorium) are
    # excluded from state cells by design, so summing the grid client-side
    # undercounts. len() of each payload is the honest total.
    totals = {
        "projects": len(projects.projects),
        "tariffs": len(tariffs.tariffs),
        "moratoriums": len(moratoriums.moratoriums),
        "rate_cases": len(rate_cases.rate_cases) if rate_cases is not None else 0,
        "policies": len(policies.policies) if policies is not None else 0,
    }

    return {"states": dict(sorted(states.items())), "totals": totals}


def _write_coverage(payloads, *, pretty: bool) -> int:
    """Emit the derived coverage rollup alongside the validated payloads."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = _build_coverage(
        payloads["projects"],
        payloads["tariffs"],
        payloads["moratoriums"],
        payloads.get("rate_cases"),
        payloads.get("policies"),
    )
    data["generated_at"] = payloads["projects"].generated_at.isoformat()
    out = OUT_DIR / "coverage.json"
    text = json.dumps(data, indent=2) + "\n" if pretty else json.dumps(data, separators=(",", ":"))
    out.write_text(text, encoding="utf-8")
    return len(text.encode("utf-8"))


# ---------------------------------------------------------------------------
# Home digest (v6, 2026-10-08)
# ---------------------------------------------------------------------------
# Home used to load projects + the pledge roster + coverage (~90 KB gzipped) to
# show six numbers, and its "Recent changes" feed only knew about the roster.
# This ~4 KB digest is everything Home renders: whole-record numbers, the
# latest dated events across every record type, and announced dates ahead.

HOME_LATEST_MAX = 12
HOME_LATEST_PER_TYPE = 4  # so a burst of one record type can't fill the feed
HOME_UPCOMING_MAX = 8
HOME_UPCOMING_PER_TYPE = 3


def _is_contested(p, neg_projects: set, disputed_projects: set) -> bool:
    """Mirror of contestedReasons() in docs/app.js (parity-tested in e2e):
    a critical community response, a contested ratepayer assessment, a
    contested/shortfall delivery finding, or a lawsuit on the timeline."""
    return (
        p.id in neg_projects
        or (p.ratepayer is not None and p.ratepayer.status == "contested")
        or p.id in disputed_projects
        or any(u.kind == "lawsuit" for u in (p.updates or []))
    )


def _is_agreement(pol) -> bool:
    """Mirror of isAgreementRecord in app.js: a developer-community deal, or a
    company's pledge to one host community. Company-wide plans are not."""
    if not pol.community_benefits_framework:
        return False
    if pol.instrument == "benefit_agreement":
        return True
    return pol.instrument == "company_plan" and pol.scope != "company"


def _place(city: str | None, state: str | None) -> str:
    return ", ".join(x for x in (city, state) if x)


def _build_home(payloads, today: date) -> dict:
    projects = payloads["projects"].projects
    responses = payloads["responses"].responses
    claims = payloads["claims"].claims
    morats = payloads["moratoriums"].moratoriums
    policies = payloads["policies"].policies
    tariffs = payloads["tariffs"].tariffs
    rate_cases = payloads["rate_cases"].rate_cases
    sig = payloads["signatories"]

    neg = {r.project_id for r in responses if r.stance == "negative"}
    disputed = {
        c.project_id for c in claims
        if c.project_id and c.delivered and c.delivered.status in ("contested", "shortfall")
    }
    contested = [p for p in projects if _is_contested(p, neg, disputed)]
    orgs = [s for s in sig.signatories if s.category != "governor"]

    totals = {
        "sites": len(projects),
        "contested_sites": len(contested),
        "companies": len(payloads["companies"].companies),
        "moratoriums": len(morats),
        "moratoriums_enacted": sum(m.status == "enacted" for m in morats),
        "policies": len(policies),
        "policies_in_effect": sum(p.status == "in_effect" for p in policies),
        "agreements": sum(_is_agreement(p) for p in policies),
        "agreements_signed": sum(
            p.instrument == "benefit_agreement" and p.status == "in_effect"
            for p in policies
        ),
        "tariffs": len(tariffs),
        "rate_cases": len(rate_cases),
        "rate_cases_pending": sum(r.status == "pending" for r in rate_cases),
        "pledge_organizations": len(orgs),
        "pledge_governors": len(sig.signatories) - len(orgs),
        "roster_as_of": sig.roster_as_of.isoformat() if sig.roster_as_of else None,
    }

    latest: list[dict] = []
    for m in morats:
        if m.status == "enacted" and m.enacted_date and m.enacted_date <= today:
            latest.append({
                "date": m.enacted_date.isoformat(), "type": "Moratorium",
                "title": f"{m.jurisdiction} enacts a data center moratorium",
                "place": m.state_code or "", "target": {"kind": "moratorium", "id": m.id},
            })
    for pol in policies:
        if pol.date and pol.date <= today:
            verb = {"in_effect": "", "proposed": " (proposed)", "failed": " (failed)"}[pol.status]
            if "(" in pol.title:  # "(vetoed)", "(first reading)" already say it
                verb = ""
            agreement = _is_agreement(pol)
            latest.append({
                "date": pol.date.isoformat(),
                "type": "Agreement" if agreement else "Local policy",
                "title": pol.title + verb,
                "place": pol.state_code or "",
                "target": {"kind": "agreement" if agreement else "policy", "id": pol.id},
            })
    for rc in rate_cases:
        d = rc.decided_date if rc.status != "pending" else rc.filed_date
        if d and d <= today:
            what = {"pending": "filed", "approved": "approved", "rejected": "rejected"}[rc.status]
            latest.append({
                "date": d.isoformat(), "type": "Rate case",
                "title": f"{rc.title} ({what})",
                "place": rc.state_code or "", "target": {"kind": "ratecase", "id": rc.id},
            })
    for p in projects:
        for u in p.updates or []:
            if not u.upcoming and u.date <= today:
                latest.append({
                    "date": u.date.isoformat(), "type": "Site", "subtype": u.kind,
                    "title": u.title, "place": _place(p.city, p.state),
                    "target": {"kind": "site", "id": p.id},
                })
    joined = [x for x in sig.signatories if x.signed_track == "expansion-2026-07-23"]
    if joined:
        govs = sum(x.category == "governor" for x in joined)
        latest.append({
            "date": "2026-07-23", "type": "Pledge",
            "title": f"{len(joined) - govs} organizations and {govs} governors join the Ratepayer Protection Pledge",
            "place": "", "target": {"kind": "roster"},
        })
    rolling = sum(x.signed_track == "rolling" for x in sig.signatories)
    if rolling and sig.roster_as_of and sig.roster_as_of <= today:
        latest.append({
            "date": sig.roster_as_of.isoformat(), "type": "Pledge",
            "title": f"{rolling} more organizations appear on the pledge roster (join dates unpublished)",
            "place": "", "target": {"kind": "roster"},
        })
    latest.sort(key=lambda x: x["date"], reverse=True)
    picked: list[dict] = []
    per_type: dict[str, int] = {}
    for item in latest:
        if per_type.get(item["type"], 0) >= HOME_LATEST_PER_TYPE:
            continue
        per_type[item["type"]] = per_type.get(item["type"], 0) + 1
        picked.append(item)
        if len(picked) == HOME_LATEST_MAX:
            break

    upcoming: list[dict] = []
    for rc in rate_cases:
        d = rc.next_milestone_date  # regulator-announced; any status can have one
        if d and d >= today:
            upcoming.append({
                "date": d.isoformat(), "type": "Rate case", "title": rc.title,
                "place": rc.state_code or "", "target": {"kind": "ratecase", "id": rc.id},
            })
    for p in projects:
        for u in p.updates or []:
            if u.upcoming and u.date >= today:
                upcoming.append({
                    "date": u.date.isoformat(), "type": "Site", "subtype": u.kind, "title": u.title,
                    "place": _place(p.city, p.state), "target": {"kind": "site", "id": p.id},
                })
    for m in morats:
        start = m.effective_date or m.enacted_date
        if m.status == "enacted" and m.duration_months and start:
            y, mo = divmod(start.month - 1 + m.duration_months, 12)
            year, month = start.year + y, mo + 1
            end = date(year, month, min(start.day, calendar.monthrange(year, month)[1]))
            if end >= today:
                upcoming.append({
                    "date": end.isoformat(), "type": "Moratorium",
                    "title": f"{m.jurisdiction} moratorium reaches its end date",
                    "place": m.state_code or "", "target": {"kind": "moratorium", "id": m.id},
                })
    upcoming.sort(key=lambda x: x["date"])
    soon: list[dict] = []
    per_type = {}
    for item in upcoming:  # 107 moratorium end dates would otherwise fill it
        if per_type.get(item["type"], 0) >= HOME_UPCOMING_PER_TYPE:
            continue
        per_type[item["type"]] = per_type.get(item["type"], 0) + 1
        soon.append(item)
        if len(soon) == HOME_UPCOMING_MAX:
            break

    return {
        "totals": totals,
        "latest": picked,
        "upcoming": soon,
    }


def _write_home(payloads, *, pretty: bool) -> int:
    today = payloads["projects"].generated_at
    data = _build_home(payloads, today)
    data["generated_at"] = today.isoformat()
    out = OUT_DIR / "home.json"
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n" if pretty else json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    out.write_text(text, encoding="utf-8")
    return len(text.encode("utf-8"))


def _write_payload(name: str, model_obj, *, pretty: bool) -> int:
    """Emit one payload to docs/data/<name>.json. Returns bytes written."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{name}.json"
    if pretty:
        text = model_obj.model_dump_json(exclude_none=True, indent=2) + "\n"
    else:
        text = model_obj.model_dump_json(exclude_none=True)
    out.write_text(text, encoding="utf-8")
    return len(text.encode("utf-8"))


def refresh(*, check_only: bool = False, pretty: bool = False, audit: bool = False) -> int:
    """Validate seed and (optionally) write payloads. Returns exit code."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    payloads = {}
    for name, model in PAYLOAD_FILES.items():
        logger.info("Validating %s.json …", name)
        payloads[name] = _load_payload(name, model)

    cross_errors = _check_cross_refs(
        payloads["companies"],
        payloads["claims"],
        payloads["projects"],
        payloads["responses"],
        payloads.get("signatories"),
        payloads.get("tariffs"),
        payloads.get("rate_cases"),
        payloads.get("policies"),
        payloads.get("moratoriums"),
    )
    if cross_errors:
        for err in cross_errors:
            logger.error(err)
        logger.error("Cross-reference validation failed: %d error(s)", len(cross_errors))
        return 1

    logger.info(
        "Loaded: %d companies, %d claims, %d projects, %d responses",
        len(payloads["companies"].companies),
        len(payloads["claims"].claims),
        len(payloads["projects"].projects),
        len(payloads["responses"].responses),
    )

    # Audit missing commitment details if requested
    if audit:
        critical, medium = _audit_missing_commitments(
            payloads["projects"], payloads["signatories"]
        )
        stale_pending = _audit_stale_pending(
            payloads["moratoriums"], payloads["tariffs"],
            payloads.get("rate_cases"), payloads.get("policies"),
        )
        logger.warning(
            "Audit found %d critical + %d medium gaps in project commitment details; "
            "%d stale pending bills/tariffs/rate cases/policies",
            len(critical),
            len(medium),
            len(stale_pending),
        )
        _write_audit_report(critical, medium, stale_pending)
        if check_only:
            return 0

    # Stamp generated_at on the emitted payloads (always today).
    today = date.today()
    for p in payloads.values():
        p.generated_at = today

    if check_only:
        logger.info("--check passed; no outputs written.")
        return 0

    total = 0
    for name, payload in payloads.items():
        nbytes = _write_payload(name, payload, pretty=pretty)
        total += nbytes
        logger.info("Wrote %s.json (%d bytes)", name, nbytes)
    nbytes = _write_coverage(payloads, pretty=pretty)
    total += nbytes
    logger.info("Wrote coverage.json (%d bytes)", nbytes)
    nbytes = _write_home(payloads, pretty=pretty)
    total += nbytes
    logger.info("Wrote home.json (%d bytes)", nbytes)
    logger.info("Total payload size: %.1f KB", total / 1024)
    return 0


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument(
        "--check",
        action="store_true",
        help="Validate seed without writing outputs.",
    )
    p.add_argument(
        "--pretty",
        action="store_true",
        help="Emit indented JSON (default: minified).",
    )
    p.add_argument(
        "--audit",
        action="store_true",
        help="Audit projects for missing key commitment details (generates ISSUES.md).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    return refresh(check_only=args.check, pretty=args.pretty, audit=args.audit)


if __name__ == "__main__":
    raise SystemExit(main())
