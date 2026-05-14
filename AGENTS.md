# AGENTS.md — How to work in this repo as an AI agent

> Companion to [CLAUDE.md](CLAUDE.md). CLAUDE.md is the *what* (project
> intent, architecture, editorial rules); this file is the *how* (concrete
> agent workflow inside this codebase).

## Read these first, in order

1. **[CLAUDE.md](CLAUDE.md)** — universal principles + project-specific
   notes. The "Project intent" and "Editorial / sourcing rules" sections
   are load-bearing for every change.
2. **[DESIGN.md](DESIGN.md)** — design system + the editorial rubric for
   `stance` tagging. Touch this before changing community-response
   handling.
3. **[BACKLOG.md](BACKLOG.md)** — what's next. Pick from here, don't
   invent.
4. **[ISSUES.md](ISSUES.md)** — what's broken. Check before reporting a
   bug as new.

## The Explore → Plan → Code → Verify loop

This repo follows the loop CLAUDE.md describes. Concretely:

- **Explore.** Use `grep`, `find`, or the Explore agent to find relevant
  code. The codebase is small enough that a single read of `schema.py` +
  `docs/app.js` covers ~80% of the surface.
- **Plan.** For anything beyond a one-line fix, present 2–3 approaches
  with pros/cons before writing code. Editorial changes (theme taxonomy,
  stance rubric, what counts as a valid source) ALWAYS need a plan
  surface — they reshape the dataset.
- **Code.** Edit existing files first; only create new files when the
  task genuinely requires it. No new helpers for one-shot operations.
- **Verify.** Run the test suite (see "Verifying changes" below) before
  declaring done.

## Verifying changes

| Change kind                                      | Run                                            |
| ------------------------------------------------ | ---------------------------------------------- |
| Schema edit                                      | `pytest tests/test_schema.py`                  |
| Seed data edit                                   | `python refresh.py --check && pytest tests/test_seed_data.py` |
| Theme vocab change                               | `pytest tests/test_themes_match_frontend.py`   |
| Frontend (`docs/app.js`, `index.html`, `styles.css`) | `pytest tests/e2e/`                       |
| Refresh / connector change                       | `pytest tests/test_refresh.py`                 |
| Anything substantial                             | `pytest` (full suite, ~15s)                    |

For UI changes, **also** run the dashboard locally and click through both
views — type checking and tests verify code correctness, not feature
correctness.

```bash
cd docs && python -m http.server 8000
```

## Common tasks

### Adding a claim (most common)

1. Open `data/seed/claims.json`.
2. Append one record with: stable `id`, real `source_url`, verbatim
   `statement`, today's `captured_at`, and a `theme` from the canonical
   list in `schema.py`.
3. `python refresh.py` (validates + writes `docs/data/claims.json`).
4. `pytest tests/test_seed_data.py` to confirm.

### Adding a project + community responses

1. Add the project to `data/seed/projects.json`. Required: `id`,
   `company_slug`, `lat`, `lon`, `status`, `announced_year`, `source_url`.
2. Add 1–N community responses to `data/seed/responses.json`, each
   referencing `project_id`. Per [DESIGN.md](DESIGN.md), include both
   positive and negative voices when documented — single-source negative
   should set `single_source: true`.
3. `python refresh.py && pytest`.

### Adding a theme (RARE — requires migration)

This is a schema change. **Do not do this casually.** Steps:

1. File a [BACKLOG.md](BACKLOG.md) entry first.
2. Add to `THEMES` + `THEME_LABELS` in `schema.py`.
3. Mirror in `docs/app.js` (`THEMES` + `THEME_LABELS`).
4. Add a `--theme-<slug>` CSS var in both light and dark sections of
   `docs/styles.css`.
5. Re-tag existing claims that should map to the new theme (or
   intentionally leave them).
6. Run the full test suite — `test_themes_match_frontend.py` enforces
   parity.

### Adding a v2 connector (per-company scraper)

Not yet — v1 is curated. When v2 starts: subclass
`connectors.base.Connector`, register in `connectors/__init__.py`,
implement `fetch_claims()`. The driver in `refresh.py` will need a
companion `--source <slug>` flag (modeled on adjacent projects).

## What NOT to do

- **Don't paraphrase company claims into the `statement` field.** Quote
  verbatim. Tests catch obvious markers like "they claim that".
- **Don't add a record without a real `source_url`.** Schema rejects it,
  and reviewers will reject it harder.
- **Don't try to LLM-classify community-response stance.** It's the most
  adversarial editorial call in the project; a wrong tag undermines the
  whole frame. Curator-only.
- **Don't aggregate to a "trust score" or "greenwashing index."** Show
  the data; let users judge. See CLAUDE.md > "Editorial / sourcing rules".
- **Don't introduce a new framework.** Vanilla JS + Pydantic + Playwright
  is the whole stack. Adding React / Vue / Svelte / build tooling
  contradicts the static-first principle and adds maintenance debt.
- **Don't touch `docs/data/*.json` directly.** Edit `data/seed/*.json` and
  re-run `refresh.py`.
- **Don't expand scope inside a fix.** A bug fix doesn't need surrounding
  cleanup; a one-shot operation doesn't need a helper.

## Repo norms

- Type hints on every Python function.
- No `print()` for runtime output — use the `logging` module.
- Test alongside code, not after.
- Commit at natural checkpoints: per-feature, per-bug-fix, per-doc-update.
- Never commit `docs/data/*.json` and seed JSON in separate commits — they
  must move together so a future bisect doesn't land on a broken state.

## Escalate to a human when…

- The editorial frame would change (e.g. adding a 9th theme, changing the
  stance rubric, adding a non-named company).
- A community response is contested and you're unsure of the stance tag.
- A company source page goes 404 / paywalls — pause and ask before
  switching to a less-canonical source.
- Schema fields would change (cross-cuts seed + frontend + tests).
