# Data Center Community Benefits & Pushback Dashboard

A public-interest dashboard surfacing what the major hyperscalers — Meta,
Google, Microsoft, OpenAI, Anthropic, xAI, Oracle, Amazon — publicly
**claim** about community benefits from their data centers, alongside what
local communities, journalists, and regulators actually **report** back.

The dashboard is **neither a hit piece nor a corporate puff piece**. Both
company claims and community responses are presented with full source
attribution, dates, and clear visual distinction so users can evaluate the
gap between promised and delivered benefits themselves.

## Two views

1. **Company Comparison** — a thematic matrix of benefit claims across the
   eight companies, mapped to eight themes (jobs, tax revenue, energy,
   water, community grants, infrastructure, education, engagement). Click
   any cell to filter the claim list.
2. **Project Explorer** — individual data center sites with project info
   (location, status, claimed investment, claimed jobs), the company's
   claims, and any documented community responses (positive, mixed, or
   negative) with constituency tags.

## Architecture

- **Static-first.** No runtime backend. `refresh.py` validates curated seed
  data against a [Pydantic schema](schema.py) and emits four small JSON
  payloads to `docs/data/`; the frontend (`docs/`) is plain HTML/CSS/JS
  served by GitHub Pages.
- **Curated, not scraped (v1).** Each company's claims and projects are
  hand-seeded from publicly-known sources by a reviewer. v2 will introduce
  per-company connectors under `connectors/` for the pages that publish
  stable URLs. Community responses stay curated — no automated sentiment
  classification.
- **Single source of truth.** The theme vocabulary, company slugs, and
  enums live in [`schema.py`](schema.py); the frontend mirrors them in
  [`docs/app.js`](docs/app.js) and a test
  ([`tests/test_themes_match_frontend.py`](tests/test_themes_match_frontend.py))
  asserts they don't drift.

## Repo layout

```
.
├── schema.py                 # Pydantic models — single source of truth
├── refresh.py                # Validate seed → emit docs/data/*.json
├── connectors/               # Skeleton for v2 per-company scrapers
│   └── base.py
├── data/seed/                # Curator's working JSON
│   ├── companies.json
│   ├── claims.json
│   ├── projects.json
│   └── responses.json
├── docs/                     # GitHub Pages root
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── data/                 # Built payloads (output of refresh.py)
├── tests/                    # pytest unit + Playwright e2e
│   └── e2e/
├── CLAUDE.md                 # Project conventions (read first)
├── AGENTS.md                 # How AI agents should work in this repo
├── DESIGN.md                 # Design system + editorial rubric
├── ISSUES.md                 # Open / fixed bugs
└── BACKLOG.md                # Roadmap + ideas
```

## Quick start

```bash
# 1. Install deps
pip install -r requirements.txt
playwright install chromium      # only needed for e2e tests

# 2. Validate the curated seed and emit docs/data/*.json
python refresh.py --pretty

# 3. Serve the dashboard locally
cd docs && python -m http.server 8000
# → http://localhost:8000

# 4. Run tests
python -m pytest                 # unit + e2e (~15s)
python -m pytest tests/ --ignore=tests/e2e   # unit only (~0.2s)
```

## Adding a claim or project (curator workflow)

1. Open the relevant file in `data/seed/`.
2. Append a record. Every record needs a real source URL, a verbatim quote
   (for claims), and a capture date. See [DESIGN.md](DESIGN.md) for the
   editorial rubric.
3. Run `python refresh.py` — it validates against the schema (`extra="forbid"`)
   and updates `docs/data/`.
4. Run `pytest` — every record is exercised by `tests/test_seed_data.py`.

## Editorial principles (the load-bearing ones)

- **Quote, don't paraphrase.** Claims field `statement` carries the
  company's own wording. Tests catch paraphrase markers like "they claim
  that".
- **Source attribution is non-negotiable.** Every record carries
  `source_url` + `source_title`; schema rejects records without them, and
  the frontend renders a "view source" link on every card.
- **Stance is a human judgment call.** Don't try to LLM-classify community
  responses; the rubric for `positive` / `mixed` / `negative` is in
  [DESIGN.md](DESIGN.md).
- **No "trust score."** The dashboard shows the data; it doesn't synthesize
  a numeric "greenwashing index."

See [CLAUDE.md](CLAUDE.md) for the full project conventions.

## License

Code: MIT. Data: each record carries its own source attribution; refer to
the source URL for terms.
