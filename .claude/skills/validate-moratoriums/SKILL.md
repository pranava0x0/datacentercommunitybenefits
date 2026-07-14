---
name: validate-moratoriums
description: >-
  Validate the data-center moratorium dataset for source accuracy and live
  government links. Use whenever the user asks to "validate the moratoriums",
  "check the moratorium sources/links", "audit the moratorium data", "find dead
  links in the moratoriums", "verify the gov links", or before shipping new
  moratorium records. Wraps scripts/validate_moratoriums.py: a fast link-liveness
  pass (live/blocked/dead + gov-source presence) and a slower claim-verification
  pass (bill numbers, votes, dates, sponsors against the fetched source text).
---

# Validate moratoriums

The dataset (`data/seed/moratoriums.json`) is an audit-trail: every record must
carry a **live** source URL, and — per the project's "active links only, lean on
accuracy" rule — ideally an official **.gov / legislative** primary source. This
skill checks that and surfaces records that need a human fix.

## The two checks

1. **Link liveness (`--links-only`)** — fast, deterministic, the primary check.
   Probes every `source_url` + `resources[].url`, follows redirects with a
   browser User-Agent, and classifies each as:
   - **live** — 2xx/3xx. Good.
   - **blocked** — 401/403/406/429/503 or an SSL/timeout error. The site exists
     but bot-walls our fetcher. **Not** a broken link — spot-check in a browser
     if it's the only source.
   - **dead** — 404/410, DNS failure (a domain typo like `loudouncount.gov`), or
     connection refused. **Actionable**: replace or remove.
2. **Claim verification (full run)** — slower. Fetches the sources and searches
   the page text for the record's `bill_number`, `sponsors`, `legislative_votes`
   / `city_council_vote`, `enacted_date`, `enacted_by`, `failure_reason`,
   `session`, recording a verbatim snippet for each match. A `not_found` is a
   flag to re-check, not proof the fact is wrong (many gov pages are JS-rendered
   and return no text to a plain fetcher).

## Commands

```bash
# Fast liveness audit of every record (writes moratorium_link_report.json)
python scripts/validate_moratoriums.py --links-only

# Offline: reuse the .moratorium_cache from a prior run (no network)
python scripts/validate_moratoriums.py --links-only --cached

# CI gate: exit 1 if any record's PRIMARY source_url is dead
python scripts/validate_moratoriums.py --links-only --fail-on-dead-link --no-issues

# Full claim-verification audit (writes moratorium_audit_report.json)
python scripts/validate_moratoriums.py --summary

# One record
python scripts/validate_moratoriums.py --id maine-state-2026-04

# Schema-only, no fetches
python scripts/validate_moratoriums.py --dry-run
```

## Workflow

1. Run `--links-only`. Read the summary line: `primary-source dead`, `no-gov-source`, `total dead links`.
2. For each **dead primary**: find the correct live URL. Prefer the official
   legislature/city/county page (verify it returns 200 — use WebFetch, which
   gets through most bot-walls the script can't). Update `source_url`; move the
   old news link to `resources` only if it's still live.
3. For each **no-gov-source** record: add a `.gov`/legislative link to
   `resources` (or promote it to `source_url`) when one exists. Some local
   actions genuinely have no gov web presence — leave a live news source and note it.
4. For **blocked** links that are the only source: open in a browser to confirm
   they're real before trusting them.
5. Re-run `--links-only` until `primary-source dead` is 0.
6. Run the full audit and skim `not_found` claims for anything suspicious.

## Outputs & cache

- `moratorium_link_report.json` — per-record liveness (git-ignored run artifact).
- `moratorium_audit_report.json` — per-record claim trail (git-ignored).
- `ISSUES.md` — appended with actionable rows (unless `--no-issues`).
- `.moratorium_cache/` — fetched pages (git-ignored). Delete to force a re-fetch.

## Data-quality invariants (also enforced by `tests/test_validate_moratoriums.py`)

- Every `failed` record has a `failure_reason`; every `enacted` record has an `enacted_date`.
- IDs are unique; every record has the required schema fields.
- Don't fabricate a `.gov` URL to satisfy the gov-source check — a plausible-looking
  but non-existent path is worse than an honest live news link.
