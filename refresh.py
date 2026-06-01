"""Refresh driver — validates `data/seed/*.json` and emits `docs/data/*.json`.

In v1, the seed is the source of truth (curated by hand); this script's job is
to validate it against `schema.py` and copy validated payloads to `docs/data/`
for the frontend.

Usage:
    python refresh.py                 # validate + emit all four payloads
    python refresh.py --check         # validate only; do NOT write outputs
    python refresh.py --pretty        # emit pretty-printed JSON (default: minified)

Per CLAUDE.md:
- Schema enforces `extra="forbid"` so any seed drift fails fast here.
- All four payload IDs must be unique within their type (enforced in schema).
- Cross-record references (claim.project_id, response.project_id, claim.company_slug)
  are checked here as a post-validation pass — Pydantic doesn't know about
  cross-payload joins.
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


def refresh(*, check_only: bool = False, pretty: bool = False) -> int:
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
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    return refresh(check_only=args.check, pretty=args.pretty)


if __name__ == "__main__":
    raise SystemExit(main())
