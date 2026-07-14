---
name: refresh
description: >
  Regenerates the dashboard's static JSON output files by running python3 refresh.py in the
  project root. Validates all seed data (companies, claims, projects, responses, moratoriums,
  tariffs) against schema.py and writes output to docs/data/. Use when the user says
  "refresh", "refresh data", "run refresh", "regenerate output", "rebuild data",
  "rebuild the JSON", "update docs/data", or "python refresh.py".
---

# Refresh Build

Runs `python3 refresh.py` to validate seed data and write `docs/data/*.json`.

## Steps

1. Run from the project root (the active `.claude/worktrees/` path or the main project checkout).
2. Report: record counts per type, total payload size, and any validation errors.
3. If validation fails, read the error, identify the offending record in `data/seed/`, fix it, and re-run until clean.

## Commands

```bash
python3 refresh.py                  # validate + write docs/data/*.json (production)
python3 refresh.py --check          # validate only — no output written
python3 refresh.py --audit          # validate + write outputs + generate ISSUES.md
python3 refresh.py --audit --check  # validate + generate ISSUES.md only (no docs/data write)
python3 refresh.py --pretty         # validate + write pretty-printed JSON (human review)
```

## What a clean run looks like

```
INFO refresh: Validating companies.json …
INFO refresh: Validating claims.json …
INFO refresh: Validating projects.json …
INFO refresh: Validating responses.json …
INFO refresh: Validating moratoriums.json …
INFO refresh: Validating tariffs.json …
INFO refresh: Loaded: N companies, N claims, N projects, N responses
INFO refresh: Wrote companies.json …
…
INFO refresh: Total payload size: N KB
```

Any `ERROR` line means validation failed — fix the seed file and re-run.
A `WARNING` line from `--audit` means data gaps exist — review ISSUES.md.

## After a successful refresh

If seed data changed (not a no-op timestamp bump), commit both seed edits and generated outputs:

```bash
git add data/seed/ docs/data/ ISSUES.md
git commit -m "chore(data): refresh payloads — bump generated_at to $(date +%Y-%m-%d)"
```

## Known audit state (2026-06-30)

Running `python3 refresh.py --audit` currently reports **34 critical + 71 medium gaps**.
Most gaps require web research to fill (power_mw for older operational sites, site-level
investment figures for Stargate/AWS state-commitment sites). See `data-refresh.md` skill
for the full curation workflow including how to find and fill these gaps.
