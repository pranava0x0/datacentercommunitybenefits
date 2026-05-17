# Data Center Community Benefits — A Blueprint

A public-interest dashboard cataloguing the **community-benefit
commitments** major data-center operators have published — and how those
commitments are playing out on the ground at real sites.

The framing as of v1.5 is **positive / blueprint-oriented**: this is meant
as a starting menu of what's possible to ask for in future data-center
projects, with on-the-ground feedback (positive, mixed, and the lessons
learned) as case-study evidence for what's working and where the gaps
still are. Every commitment links to its first-party source. Every
on-the-ground response cites who said it and where.

→ **Live dashboard:** <https://pranava0x0.github.io/datacentercommunitybenefits/>

---

## What the dashboard shows

### View 1 — Company Comparison
A 9 × 8 thematic matrix. Rows are companies; columns are the eight
benefit themes ([jobs, tax revenue, energy, water, community grants,
infrastructure, education, engagement](DESIGN.md#theme-assignment)).

- A `✓` in a cell means the company has at least one recorded claim
  against that theme; an `—` means none recorded. The matrix answers a
  binary question — "does this company speak to this theme at all?"
- Click any company row (or populated cell) to open a per-company
  summary pop-out with:
  - A curated 1–2 paragraph synthesis of how the company frames data-
    center community engagement (including honest "no published
    framework" gaps where they exist).
  - A link to the company's main community / engagement page on their
    own site.
  - Counts of recorded claims + tracked projects for that company.
  - A "View this company's projects →" CTA that switches to the
    Project Explorer with the company filter pre-set.

### View 2 — Project Explorer
The 16 individual data center projects on a Leaflet map (lazy-loaded —
the comparison view doesn't pull Leaflet at all).

Filterable by company, status (announced / construction / operational),
and community stance. Click any marker or list card to open the project
pop-out, which has three tabs:

- **Overview** — investment, jobs, **acreage, power capacity (MW/GW),
  GPU/accelerator count, offtaker (workload owner)**, project page
  link, record source link, notes.
- **Claims** — site-specific quotes for that project (with a count
  badge on the tab). Claims that the curator has assessed against
  independent reporting carry a **Delivered-vs-promised** panel
  (v1.13+) — one of `Delivered` / `Partial` / `Contested` / `Shortfall`
  with the evidence link and a short neutral synthesis. Absence of the
  panel means no assessment has been captured yet (treated as honest
  gap, not implied success).
- **Community** — documented responses tagged
  positive/mixed/negative with constituency
  (residents / local government / NGO / academic / journalist / regulator).

The **offtaker** field is what disambiguates colocation arrangements
from owner-operator sites: Stargate Abilene's `oracle-abilene-tx`
record carries `OpenAI` as offtaker (Oracle hosts, OpenAI uses); AWS
New Carlisle (Project Rainier) carries `Anthropic`. For owner-operator
campuses, offtaker equals the operating company.

The active tab persists across project selections within a session so
scanning one tab across multiple projects doesn't force a re-click.

---

## What's in the dataset (as of v1.13)

| Record type        | Count | What it tracks                                                          |
| ------------------ | ----- | ----------------------------------------------------------------------- |
| Companies          | 13    | 8 hyperscalers + Wonder Valley + QTS + Crusoe + CoreWeave + Nebius      |
| Claims             | 276   | Verbatim first-party quotes (incl. exec quotes in news), mapped to 8 themes |
| Projects           | 74    | Sites with location, status, investment, acreage, power, GPUs, offtaker |
| On-the-ground feedback | 194 | Reactions from residents / officials / NGOs / journalists / regulators  |
| Delivered-vs-promised assessments | 12  | Curator judgment on whether the claim was actually met (4 status types) |
| **Matrix coverage** | **98/104 (94%)** | 7 of 13 companies have full 8-theme coverage; 6 honest gaps remain |

**First-paint payload:** `companies.json` (~7 KB) + `claims.json`
(~70 KB) preload on first paint. `projects.json` (~20 KB) +
`responses.json` (~34 KB) lazy-load when the user opens the Project
Explorer tab. Map JS/CSS (Leaflet, ~150 KB) only loads on the Explorer
view.

**Date fields:** `Claim.captured_at` is when the curator recorded the
record. `Claim.published_at` (optional, v1.4+) is the source's own
publication date when known — frontend prefers it. `CommunityResponse.date`
is always the publication / event date.

### Companies tracked

**Eight hyperscalers (locked):** Meta, Google, Microsoft, Amazon (AWS),
OpenAI, Anthropic, xAI, Oracle.

**Non-hyperscaler entities (v1.1+):**
- Wonder Valley / O'Leary Digital (Box Elder County, UT) — added v1.1.
- QTS (Blackstone subsidiary) — added v1.4. Cedar Rapids IA is the
  canonical Ratepayer Protection Pledge site; Richmond VA RIC5 is the
  first-ever data center to receive FAST-41 federal-permitting
  coverage.
- Crusoe — added v1.6. Operates the Stargate Abilene campus
  (1.2 GW, OpenAI/Oracle/Microsoft offtake) with site-specific
  community framing (5,600 daily construction workers, 32% of
  Abilene FY25 property tax, closed-loop cooling).
- CoreWeave — added v1.6. Hammond IN site has a $4M/yr Community
  Impact Payment funding the College Bound scholarship program.
- Nebius — added v1.6. Independence MO 800 MW campus with first-party
  ratepayer-protection commitments via Independence Power and Light.

The two-gate rule for adding more: ≥1 GW announced + first-party
community-impact framing. See
[CLAUDE.md](CLAUDE.md#companies-in-scope-v14) for the rule + the slug-
addition checklist.

---

## Architecture

- **Static-first.** No runtime backend, no database. `refresh.py`
  validates the curated seed data against a [Pydantic schema](schema.py)
  and emits four small JSON payloads to `docs/data/`. The frontend
  (`docs/`) is plain HTML/CSS/JS served by GitHub Pages.
- **Single source of truth.** Theme vocabulary, company slugs, project
  statuses, stances, and constituencies live in [`schema.py`](schema.py).
  The frontend mirrors the slugs/themes in [`docs/app.js`](docs/app.js);
  [`tests/test_themes_match_frontend.py`](tests/test_themes_match_frontend.py)
  asserts the two never drift.
- **Curated, not scraped (v1).** Each claim, project, and response is
  hand-seeded from publicly-known sources by a reviewer. The v1.1 data-
  fill pass used four parallel research sub-agents to walk each
  company's published material and pull verbatim quotes — but the
  output went through human review, not directly to disk. Community
  responses stay curated forever; no automated sentiment classification.
- **Schema is the contract.** Pydantic `extra="forbid"` catches any
  drift in seed JSON before write. Cross-references (`Claim.project_id`
  → `Project.id`, `CommunityResponse.project_id` → `Project.id`,
  `*.company_slug` → `Company.slug`) are checked in `refresh.py`.

---

## Repo layout

```
.
├── schema.py                   # Pydantic models — single source of truth
├── refresh.py                  # CLI: validate seed → emit docs/data/*.json
├── connectors/                 # Skeleton for v2 per-company scrapers
│   ├── __init__.py             # (v1: empty; v2: connector registry)
│   └── base.py                 # Connector ABC for v2 fetchers
├── data/seed/                  # Curator's working JSON (the source of truth)
│   ├── companies.json          # 9 companies
│   ├── claims.json             # 93 verbatim benefit claims
│   ├── projects.json           # 16 data center sites
│   └── responses.json          # 16 community responses
├── docs/                       # GitHub Pages root
│   ├── index.html              # Two-view shell + tab strip
│   ├── styles.css              # CSS-var-driven palette + dark mode
│   ├── app.js                  # View rendering + Leaflet code-split
│   └── data/                   # Built JSON payloads (output of refresh.py)
├── tests/
│   ├── test_schema.py          # Schema-level invariants (30 tests)
│   ├── test_seed_data.py       # Seed validation + cross-references (26 tests)
│   ├── test_refresh.py         # refresh.py CLI behavior (8 tests)
│   ├── test_themes_match_frontend.py   # Python ↔ JS parity (3 tests)
│   └── e2e/
│       ├── conftest.py         # Spins up local server for Playwright
│       └── test_views.py       # End-to-end browser tests (41 tests)
├── requirements.txt            # pydantic, requests, pytest, playwright
├── pytest.ini                  # Test config
├── CLAUDE.md                   # Project conventions (read first)
├── AGENTS.md                   # How AI agents should work in this repo
├── DESIGN.md                   # Design system + editorial rubric
├── ISSUES.md                   # Open / fixed bugs
├── BACKLOG.md                  # Roadmap + done log
└── README.md                   # ← you are here
```

---

## Quick start

```bash
# 1. Install deps
pip install -r requirements.txt
playwright install chromium      # only needed for e2e tests

# 2. Validate the curated seed and emit docs/data/*.json
python refresh.py                # minified output (production)
python refresh.py --pretty       # indented output (better for diffing)
python refresh.py --check        # validate only; do NOT write outputs

# 3. Serve the dashboard locally
cd docs && python -m http.server 8000
# → http://localhost:8000

# 4. Run tests
python -m pytest                                # full suite (108 tests, ~15 s)
python -m pytest tests/ --ignore=tests/e2e      # unit only (67 tests, ~0.2 s)
python -m pytest tests/e2e/                     # Playwright e2e only (~13 s)
```

---

## Curator workflow

### Adding a claim

1. Open `data/seed/claims.json`.
2. Append a record. Required fields:
   - `id` — `<company>-<theme>-<short>` for company-level claims, or
     `<project_id>-<theme>-<short>` for project-tied claims.
   - `company_slug` — must match a slug in `companies.json` (and the
     `CompanySlug` Literal in `schema.py`).
   - `theme` — one of the 8 themes (frozen vocabulary).
   - `statement` — the **verbatim quote**. Don't paraphrase.
     (`tests/test_seed_data.py` flags obvious paraphrase markers.)
   - `source_url` — must be a real, resolving HTTPS URL.
   - `source_title` — short, descriptive page title.
   - `captured_at` — ISO date you (or the source) captured the claim.
3. Optional: `project_id` if the claim is tied to a specific project.
4. Optional: `metric` — `{"value": N, "unit": "usd"|"jobs"|…, "kind": "…"}`
   when the quote contains a structured number.
5. Run `python refresh.py` — Pydantic validates the schema, cross-refs
   are checked, and `docs/data/*.json` is regenerated.
6. Run `pytest` — every record is exercised.

### Adding a project

1. Open `data/seed/projects.json`.
2. Required: `id`, `company_slug`, `name`, `city`, `state` (2-letter),
   `lat`, `lon`, `status`, `announced_year`, `source_url`, `source_title`,
   `captured_at`.
3. Optional but valuable: `claimed_investment_usd`, `claimed_jobs`,
   `notes`, `project_page_url` (the canonical page on the company's own
   site, distinct from `source_url`).
4. Once the project exists, you can add `Claim` records that reference
   `project_id`, and `CommunityResponse` records that reference it too.

### Adding a non-hyperscaler company

Two editorial gates ([CLAUDE.md](CLAUDE.md#companies-in-scope-v11)):
1. The entity has announced a project at hyperscaler scale (≥1 GW).
2. The entity publishes its own community-impact framing — so we have
   first-party material to quote.

Then:
1. Add the slug to `COMPANY_SLUGS` + the `CompanySlug` Literal in
   [`schema.py`](schema.py).
2. Mirror in [`docs/app.js`](docs/app.js)'s `COMPANY_SLUGS` array
   (test `test_company_slugs_match` enforces parity).
3. Add a `--co-<slug>` color token to both light + dark sections in
   [`docs/styles.css`](docs/styles.css).
4. Add to `TestSeedCoverage.OPTIONAL_ENTITIES` in
   [`tests/test_seed_data.py`](tests/test_seed_data.py).
5. Append the company entry to `data/seed/companies.json`, then add
   claims / projects / responses as above.

---

## Editorial principles (the load-bearing ones)

- **Quote, don't paraphrase.** The `statement` field carries the
  company's own wording. Tests catch markers like "they claim that".
  Restating a claim editorially is the fastest way to lose credibility
  with a reader who clicks through to the source.
- **Source attribution is non-negotiable.** Every record carries
  `source_url` + `source_title`; the schema rejects records without
  them; the frontend renders a "view source" link on every card.
- **Stance is a human judgment call.** The rubric for `positive` /
  `mixed` / `negative` lives in [DESIGN.md](DESIGN.md). Don't try to
  LLM-classify community responses — it's the most adversarial
  editorial call in the project, and a wrong tag undermines the whole
  frame. When in doubt, use `mixed`.
- **Capture dates over "current" framing.** Company pages change. A
  claim is always "as of YYYY-MM-DD"; the frontend surfaces the date
  on every card so historical drift is visible.
- **No "trust score."** The dashboard shows the data; it doesn't
  synthesize a numeric "greenwashing index." Aggregating into a single
  number would be both editorially indefensible and operationally
  fragile.

See [CLAUDE.md](CLAUDE.md) for the full project conventions and
[DESIGN.md](DESIGN.md) for the design system + stance rubric.

---

## What's explicitly OUT of scope (v1)

- Real-time scraping or alerts.
- Social-media sentiment mining.
- Predictive scoring of "trustworthy" vs "greenwashing" claims.
- Non-US data centers (US sites have richer public-record coverage;
  revisit in v2).
- Hyperscaler-adjacent **colocation** operators (Equinix, Digital
  Realty, QTS) — they don't run their own AI workloads at hyperscaler
  scale.
- Per-claim "delivered vs promised" verification.
- Automated stance classification on community responses.

See [BACKLOG.md](BACKLOG.md) for the v2+ roadmap.

---

## License

Code: MIT. Data: each record carries its own source attribution and
links to the original publication; refer to the source URL for the
publisher's terms.
