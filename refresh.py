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
import json
import logging
import sys
from datetime import date
from pathlib import Path

from pydantic import ValidationError

from schema import (
    THEMES,
    ClaimsPayload,
    CompaniesPayload,
    ProjectsPayload,
    ResponsesPayload,
)

ROOT = Path(__file__).parent
SEED_DIR = ROOT / "data" / "seed"
OUT_DIR = ROOT / "docs" / "data"

PAYLOAD_FILES: dict[str, type] = {
    "companies": CompaniesPayload,
    "claims": ClaimsPayload,
    "projects": ProjectsPayload,
    "responses": ResponsesPayload,
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
) -> list[str]:
    """Cross-payload reference checks. Returns list of error messages (empty = OK)."""
    errors: list[str] = []

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


def _audit_missing_commitments(projects: ProjectsPayload) -> tuple[dict, dict]:
    """Audit projects for missing key commitment details.

    Returns: (critical_missing, medium_missing) dicts keyed by severity.
    """
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


def _write_audit_report(critical: dict, medium: dict) -> None:
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

    audit_file.write_text("".join(report_lines), encoding="utf-8")
    logger.info("Wrote audit report to ISSUES.md")


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
        critical, medium = _audit_missing_commitments(payloads["projects"])
        logger.warning(
            "Audit found %d critical + %d medium gaps in project commitment details",
            len(critical),
            len(medium),
        )
        _write_audit_report(critical, medium)
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
