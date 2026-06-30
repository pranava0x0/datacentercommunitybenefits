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

1. Run the command from the project root (the active `.claude/worktrees/` path).
2. Report: record counts per type, total payload size, and any validation errors.
3. If validation fails, read the error message, identify the offending seed file in `data/seed/`, fix it, and re-run until clean.

## Command

```bash
python3 refresh.py
```

No flags needed for standard production output. Useful flags:

| Flag | Effect |
|------|--------|
| *(none)* | Validate + write `docs/data/*.json` (minified) |
| `--check` | Validate only — no output written |
| `--pretty` | Validate + write pretty-printed JSON (for human review) |
| `--audit` | Include data-gap audit; also writes `ISSUES.md` |
| `--audit --check` | Audit only, no output |

## What a clean run looks like

```
INFO refresh: Validating companies.json …
INFO refresh: Validating claims.json …
INFO refresh: Validating projects.json …
INFO refresh: Validating responses.json …
INFO refresh: Validating moratoriums.json …
INFO refresh: Validating tariffs.json …
INFO refresh: Loaded: N companies, N claims, N projects, N responses
INFO refresh: Wrote companies.json (N bytes)
…
INFO refresh: Total payload size: N KB
```

Any line starting with `ERROR` means a validation failure — fix the seed file and re-run.

## After a successful refresh

If seed data changed (not just a no-op re-run), commit both the seed edits and the generated `docs/data/` files together:

```bash
git add data/seed/ docs/data/
git commit -m "chore(data): refresh payloads — bump generated_at to $(date +%Y-%m-%d)"
```
