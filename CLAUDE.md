# CLAUDE.md — Universal Development Principles

> Distilled from patterns across multiple projects. Apply universally; skip sections irrelevant to the current project type.

---

## Agent Workflow: Explore → Plan → Code → Verify

Never blindly write code. Always follow this loop:

1. **Explore** — Search the codebase. Find relevant files, understand existing patterns before touching anything.
2. **Plan** — Assess the blast radius (how many files touched, how long it takes). For significant changes, present 2–3 high-level approaches with pros/cons and ask for human approval before writing code.
3. **Code** — Implement following the rules below.
4. **Verify** — Run tests. Fix all failures before declaring the task complete.

**Read before edit:** Always read a file before editing it, even if it was read earlier in the conversation.

**Ask for options first.** On non-trivial tasks, propose approaches before writing code. The human needs to evaluate options — don't assume the first plausible approach is the right one.

---

## Communication Style

- **Concise output.** No filler, no apologies, no moralizing. Skip generic advice.
- **Show your work.** Use short internal monologues to break down complex problems.
- **Fail loud.** Never use catch-all exception handlers that silently swallow errors. Always raise or log explicitly.

---

## Architecture Principles

- **No over-engineering.** Only make changes directly requested or clearly necessary. Keep solutions simple.
- **Single source of truth.** Constants, configs, and shared types derive from one place.
- **Modular design.** Separate concerns: data fetching, processing, storage, and presentation are distinct layers.
- **Idempotent operations.** Re-running any operation should be safe and produce the same result. Use `INSERT OR IGNORE` patterns, cache checks, or deduplication by unique key.
- **Static when possible.** Prefer baked-in data over runtime backends when the data update cycle allows it.
- **Cost-optimized.** Stay on free tiers and use the cheapest resources that meet requirements.
- **CLI-first.** Build CLI entry points before UI. Agents can invoke CLIs directly to self-validate output, closing the feedback loop without human intervention.
- **Minimize page weight and request count.** Audit total payload size and number of requests. Content-focused sites should be lightweight — aim for fewest requests and smallest payload possible.
- **Tree-shake and code-split.** Don't bundle every controller/feature for every page. Use code-splitting and lazy loading so pages only load the code they actually need.
- **Benchmark against best-in-class.** Compare your site/app against well-optimized reference points. If the simplest site in your org is orders of magnitude lighter, your build process needs review.
- **Document subsystems.** Maintain a `docs/` folder with notes on non-obvious subsystems, design decisions, and correct CLI invocations. One line of documentation prevents repeated mistakes.

---

## Error Resilience

- **Never let a single item failure crash the pipeline.** Wrap individual record processing in try/except. Log and continue.
- **Log aggressively.** Every request, parse, API call, cache hit/miss, and filter decision should be logged.
- **Cache everything.** Re-runs should be fast and cheap. Multi-layer caching where appropriate.
- **Validate everything.** Invalid responses from external services → log and skip, never crash.
- **Track errors visibly.** Use an `issues.md` file or errors array — failures must be visible, not silent.

---

## Security & Credential Handling

- **Never commit secrets.** API keys, tokens, and passwords must never appear in committed code.
- Read credentials from environment variables only (e.g., `os.environ["API_KEY"]`). Halt with a clear error if missing.
- Never log or print credential values.
- Always `.gitignore`: `.env`, `.env.local`, `credentials.json`, `secrets/`, `node_modules/`, `__pycache__/`, `dist/`, `*.pyc`.
- Before committing: `git diff --cached | grep -iE "apikey|password|token|secret"`.
- **Respect user privacy choices.** Don't circumvent ad blockers or privacy tools by proxying tracking SDKs through your own domain. This erodes user trust.
- **Check the dependency-advisory feed before suggesting any install.** Before recommending `npm install`, `pip install`, `pip install -r requirements.txt`, `pnpm add`, `yarn add`, `uv add`, `poetry add`, or any equivalent that pulls third-party packages — fetch the curated advisory list at <https://pranava0x0.github.io/vibe-coding-security/llms-ctx.txt> (compact, ~12 KB) and scan it for the package name and any closely-matched pattern. If a match exists, surface the warning + advisory link to the user BEFORE running or recommending the install. If the fetch fails (offline, 404), say so explicitly and let the user decide whether to proceed; **don't** silently skip the check. This applies to one-off installs in the terminal, edits to `requirements.txt` / `package.json` / `pyproject.toml`, and any CI workflow that resolves new packages.

---

## Testing & Validation

- **Write tests alongside code, not as an afterthought.** Every new module or bug fix includes corresponding tests.
- Write a regression test for every bug fix.
- Validate output data against expected schemas before writing to disk.
- **Cover edge cases, not just happy paths:**
  - Empty input: `[]`, `{}`, `""`
  - Null/undefined for every optional field
  - Boundary values (first/last page, exact date boundaries, zero counts)
  - Combined states (e.g., multiple filters active simultaneously)
- Run the full test suite before committing to catch regressions.
- **Never ship test files to production.** Ensure build pipelines exclude test files, dev fixtures, and debug artifacts from production bundles. Use build exclusions and CI checks to enforce this.

---

## Git Discipline

- **Commit often** at natural checkpoints — small, focused commits over large monolithic ones.
  - After each new module/feature is built
  - After fixing a bug or resolving a failing test
  - After updating documentation
- Write descriptive commit messages explaining *what* and *why*.
- Never commit large binary files, downloaded data, or API keys.

---

## Data Handling

- **Append-only data.** Append new records rather than overwriting. Deduplicate via unique keys.
- **Source attribution.** Every data record must include its origin (source URL, connector name, etc.). Users must be able to trace data back to its source.
- **Defensive optional field handling.** Null-check every optional field before rendering or processing.
- Null values show explicit placeholders ("N/A", "TBD", "Value TBD") — never blank UI elements or missing fields.

---

## Issue Tracking (`issues.md`)

Maintain a living `issues.md` in the project root as an audit trail.

- Log bugs with: date, module/area, description, root cause (**code bug** vs. **test bug**), and status (Open / Fixed).
- Update entries when resolved: what the fix was + the commit that resolved it.
- After every bug fix, check whether a new regression test is needed.

---

## Backlog (`backlog.md`)

Maintain a `backlog.md` for ideas, features, and enhancements.

- When ideas come up during development, add them immediately — don't lose them.
- Each item: brief description + priority (low / medium / high).
- Review and reprioritize periodically.

---

## Python Standards

*(Apply when the project uses Python)*

- Type hints on all functions.
- Use `pathlib.Path` for file paths.
- Use the `logging` module — no bare `print` for runtime output.
- All constants in a single config module.
- Pin dependencies in `requirements.txt`.
- Use Pydantic for data validation.
- Python 3.9+ compatible unless specified otherwise.

---

## Frontend Standards

*(Apply when the project has a web frontend)*

- Functional components + hooks only. No class components.
- Colors, enums, and constants in a dedicated constants file — never hardcoded inline.
- Data transforms belong in hooks or utility functions, not in components.
- Proper loading, error, and empty states on every view.
- All interactive elements must have visible focus indicators for accessibility.
- **Mobile-first responsive design.** All features must work on both mobile and desktop.
- Use TypeScript strict mode when the project uses TypeScript. No `any` types.
- **Deduplicate image assets.** Serve each image exactly once. Use `<picture>` with `srcset` so the browser selects the best format (AVIF > WebP > PNG) rather than downloading all variants.
- **Serve optimized image formats.** Always use an image CDN or optimization pipeline. Never serve uncompressed PNGs for content images in production.
- **Only load libraries used on the page.** Don't let backend-only dependencies leak into read-only frontend pages.
- **Write descriptive `alt` attributes.** Every content image needs meaningful alt text for accessibility — never leave `alt=""`.
- **Use responsive CSS, not duplicate DOM trees.** Handle mobile/desktop layouts with CSS media queries — never render the same content twice in the DOM.
- **The `[hidden]` trap.** Writing `display: inline-flex` / `display: block` on an element that uses the `hidden` HTML attribute makes the CSS rule win and the attribute become a no-op. Always pair `display: ...` overrides with an explicit `[hidden] { display: none }` rule.

---

## Network Ethics & Rate Limiting

*(Apply when the project fetches from external sources)*

- Minimum 1.5–2s delay between requests to any single host.
- Set an informative `User-Agent` header.
- Handle 429 responses with exponential backoff (start at 10s).
- Cache all fetched content to disk. Re-runs should never re-download already-cached content.
- If a service persistently blocks after retries, log to `issues.md` and gracefully skip. Never crash.
- Start small when testing scrapers — validate against a handful of pages before scaling to full runs.
- **Use an image CDN or optimization pipeline.** Never serve raw, uncompressed images directly from object storage. Compress and convert to modern formats (WebP/AVIF) before delivery.

---

## AI/API Cost Optimization

*(Apply when the project uses LLM APIs)*

- Use the cheapest model that meets quality requirements by default (e.g., Haiku before Opus).
- Apply keyword pre-filtering to skip irrelevant content before sending to expensive APIs.
- Truncate/excerpt input text to reduce token usage.
- Cache API responses by content hash. Never re-classify identical content.
- Log cost impact at each optimization layer. Print a cost summary at the end of each run.
- `--dry-run` and `--fetch-only` modes must work without an API key.

---

## Working with AI Agents

*Meta-principles for getting the most out of AI-assisted development.*

- **Context engineering over prompt engineering.** Fill the context window with exactly what's needed — no more, no less. Watch for three failure modes: *context poisoning* (early errors that compound), *context distraction* (irrelevant content that buries what matters), and *context clash* (contradictory instructions).
- **Start fresh on topic switches.** Use `/clear` when moving to an unrelated problem. Long mixed-topic contexts degrade quality. Break complex tasks into small steps and commit between them.
- **AI has no taste.** Actively review output for: excessive try/catch blocks, unnecessary abstractions, code bloat instead of refactoring, and poor judgment on simplicity vs. structure. These are recurring failure modes that require human correction.
- **AI is a tool, not a substitute for engineering discipline.** Always apply fundamentals to AI-generated code: performance auditing, bundle analysis, code review, and optimization passes. High LOC output is meaningless if the code is bloated, duplicated, and unoptimized. Shipping fast doesn't mean shipping well.
- **Closed-loop validation.** Build projects so the agent can compile, lint, run tests, and verify its own output without human intervention. When the agent can close the loop itself, you can trust the result.
- **Efficient-first, deep-later.** Before spawning a sub-agent or starting a multi-step research loop, exhaust cheap options: `grep`, `find`, `python3 -c "import json..."`, `Read` on a known file path. A sub-agent for research costs 10–100× more tokens than a targeted shell command. Only reach for an agent when the task genuinely requires it — many parallel fetches, cross-repo synthesis, or a query that can't be answered with local data. A "find new sites" task should first run a python one-liner to see what's already in the seed; only then go wide.
- **Token gate at 50K.** If you estimate a task will consume more than 50K tokens — or if you've already burned 50K in a single turn — stop and present the user with options before continuing: (a) proceed as planned, (b) scope down to a lighter approach, (c) abort. Never silently burn a large token budget. The user deserves the choice.
- **URL fetch gate at 10.** Never fetch more than 10 URLs in a single turn (whether via workflow, parallel agents, or sequential WebFetch calls) without explicit user approval. When a research request would exceed 10 URLs: list the proposed URLs, estimate token cost, and ask "proceed with all N, or start with the top 3–5?" Fetching 1–2 pages to spot-check before going wide is always the right default.
- **Keep this file current.** When something unexpected happens — a pattern that failed, a correct CLI invocation, a library quirk — add a concise note here. This file should grow incrementally as organizational scar tissue, not be rewritten from scratch.
- **Write big plans to files.** For large tasks, write the spec to a `docs/` markdown file and review it before executing. This persists context across sessions and allows a second-opinion review before building.
- **Sweep for orphaned wrapper shells after every commit / push.** Bash `run_in_background` calls that wrap long-running data refreshes — especially polling-loop wrappers like `until ps -p $(pgrep -f "...") >/dev/null; do sleep N; done` — can outlive the process they were watching. Once the watched PID exits, `pgrep` returns empty, `$(pgrep)` is `""`, `ps -p ""` always fails, and the `until` loop can never resolve, so the wrapper shell sleeps forever. Run `pgrep -fl "<project-path>"` (or check `jobs -l`) before declaring a session done; `kill` any lingering wrappers. Two design fixes: (1) prefer the `Monitor` tool over inline `until`+`sleep` polling — `Monitor` cleans up when its body exits; (2) if you must use Bash, invert the test to `while pgrep -f "..."; do sleep N; done` so the loop exits *when* the process disappears, instead of the unsatisfiable `until ps -p $(pgrep)` shape.

---

## Project-specific notes (Data Center Community Benefits Dashboard)

### Project intent (v1.5+: blueprint framing)

Dashboard surfacing the **community-benefit commitments** major data-center operators have published — and how those commitments are playing out on the ground at real sites. Use it as a **blueprint of solutions** for future data-center projects: what's possible to ask for, what's working in practice, and where the gaps still are.

Two stakeholders:
- **Policymakers / community advocates** evaluating what to ask for in permit, tax-abatement, or PPA negotiations.
- **Researchers / journalists / project developers** comparing what's been offered + delivered across companies, looking for the playbook patterns to replicate.

**Editorial frame (v1.5).** Reframed from prior "neither hit piece nor puff piece" framing to a positive blueprint orientation: lead with the solutions/commitments being offered, treat on-the-ground feedback as case-study evidence ("here's what happened when X tried Y"), not as adversarial pushback. **Keep** all data including critical responses — they're load-bearing for "lessons learned" and showing where commitments fell short. **Don't** delete or hide negative-stance feedback; it's the field-evidence that makes the blueprint usable rather than aspirational. **Don't** soften verbatim quotes to make them sound nicer — quote-as-published is still the rule.

The earlier "neither hit piece nor puff piece" framing was load-bearing in v1.0–v1.4; v1.5 deliberately lets the framing slide toward solutions/blueprint while preserving the underlying data integrity. If a future contributor wants to revert to the strict balanced framing, the dataset supports it — only the hero copy + tab labels + summary verbiage need to change.

### Companies in scope (v1.4)

**Eight original hyperscalers** (locked, `REQUIRED_HYPERSCALERS` in tests): Meta, Google, Microsoft, OpenAI, Anthropic, xAI, Oracle, Amazon (AWS).

**Non-hyperscaler entities** added when both gates are met: (1) the entity has announced a project at hyperscaler scale (≥1 GW), and (2) the entity publishes its own community-impact framing (so we have first-party claims to quote). Tracked entities:
- **Wonder Valley** (O'Leary Digital, Box Elder County UT) — added v1.1.
- **QTS** (Blackstone subsidiary) — added v1.4. The Cedar Rapids IA campus is the canonical "Ratepayer Protection Pledge" reference site (QTS pays 100% of its energy costs so grid upgrades don't shift to existing utility ratepayers); the Richmond VA campus (RIC5) is the first-ever data center to receive FAST-41 federal-permitting coverage. Both are first-party-substantive enough to clear the gates; v1.0–v1.3 had QTS on the explicit "out of scope" list, but v1.4 reverses that based on the substance of QTS's published commitments.

The slugs (`wonder-valley`, `qts`) live in `COMPANY_SLUGS` + the `CompanySlug` Literal in [schema.py](schema.py); `TestSeedCoverage.OPTIONAL_ENTITIES` in [tests/test_seed_data.py](tests/test_seed_data.py) is the test-side ledger. When adding a new non-hyperscaler entity:
1. Add the slug to all four locations above (schema Literal + COMPANY_SLUGS tuple, app.js COMPANY_SLUGS array, OPTIONAL_ENTITIES set).
2. Add a `--co-<slug>` CSS color in both light and dark `:root` blocks.
3. Add the company entry to `data/seed/companies.json` with a curated `summary`.

Hyperscaler-adjacent colocation operators not yet tracked (Equinix, Digital Realty, CoreWeave) remain **out of scope** unless they meet the same two-gate test. The QTS addition is the precedent for evaluating future operators.

### Source publication date vs capture date (v1.4)

`Claim.captured_at` is the date the **curator** recorded the claim. `Claim.published_at` (Optional, added v1.4) is the **source's** own publication date — the day the press release went out, the news article was filed, the FERC order was issued. Frontend displays `published_at` if present, falling back to `captured_at`. The two often differ by days or years (e.g., a Dec 2024 Meta press release captured in May 2026).

The merge script in `.agent_outputs/merge_v14.py` auto-extracts publication dates from URLs that include `/YYYY/MM/DD/` path segments — common shape for newsroom CMSes (news.microsoft.com, fox8live.com, bendbulletin.com, ppc.land, etc.). Agent-supplied `published_at` always wins over auto-extraction. **Don't** fabricate publication dates for evergreen company pages without one — leave `published_at` null and the curator's `captured_at` is what gets shown.

`CommunityResponse.date` is already the publication / event date by convention — no schema change needed there.

### `Project.at_a_glance` per-theme summary (v1.4)

Optional `dict[str, str]` field on `Project` mapping canonical theme keys (jobs, tax_revenue, energy, water, community_grants, infrastructure, education, engagement) to one-line plain-English phrases — e.g., `{"water": "Air-cooled, low water use", "jobs": "5,000 construction / 500 ops"}`. Surfaced in the project Overview tab's "At a glance" section.

When `at_a_glance` is **set** for a theme, the curator-written copy wins. When it's **not set**, the frontend auto-derives from the project's project-tied claims:
- If any claim for the theme has a structured `metric`, format the top 1–2 metrics joined by ` · `.
- Otherwise truncate the first claim's `statement` to ~90 chars.

Field validator in [schema.py](schema.py) rejects unknown theme keys at refresh time. **Don't** invent themes here that aren't in the canonical 8 — adding a theme is still a deliberate schema migration (CLAUDE.md > "Theme taxonomy"). The auto-derivation path means most projects need no manual `at_a_glance` work; reach for the override only when the auto-summary buries something important (e.g., a notable air-cooling design that the metrics don't surface).

### Draft banner (v1.4)

A thin top strip (`.draft-banner` in [docs/styles.css](docs/styles.css), `<div class="draft-banner">` at the top of `<body>` in [docs/index.html](docs/index.html)) signals to readers that the dataset is under active curation. The banner says "Draft · Data collection in progress · Last refresh: YYYY-MM-DD". The date is a `<span id="draft-date">` so it can be wired to a build-time stamp later if we want — for now it's hardcoded to the current refresh date. **Don't** remove the banner without explicit user direction; it sets reader expectations about completeness ("if your favorite site isn't here, it's because we haven't gotten to it yet, not because it doesn't matter"). Test `test_draft_banner_present` guards visibility + content.

### Two views

**Company Comparison view (default landing).** A thematic matrix of benefit claims across the eight companies. Rows = companies, columns = themes (see Theme Taxonomy below). Cell content shows claim count + a representative claim quote. Surfaces patterns at a glance: which companies have formalized pledges vs ad-hoc claims, which themes are universal vs niche, which companies surface community engagement as a theme at all.

**Project Explorer view.** Individual data center sites. Each project carries: company, location (city/state, lat/lon), status (`announced` / `construction` / `operational`), claimed investment, claimed jobs, the company's stated benefits for that site, AND any documented community responses (positive, mixed, negative) with constituency tags. Geo-tagged on a map; filterable by company, theme, stance, status.

### Theme taxonomy (frozen for v1)

A small fixed vocabulary every claim gets mapped to so the comparison view is meaningful:

1. **Jobs** — construction, operational, indirect/induced.
2. **Tax revenue** — local property/sales tax contributions, abatement framing.
3. **Energy** — renewable PPAs, efficiency claims, grid investment.
4. **Water** — usage, recycling, watershed restoration.
5. **Community grants** — direct philanthropy / community funds.
6. **Infrastructure** — roads, fiber, utilities investment beyond the site fence.
7. **Education** — STEM programs, scholarships, workforce training.
8. **Engagement** — community input during siting, transparency commitments.

Adding a 9th theme requires a [BACKLOG.md](BACKLOG.md) entry + migration of all existing claim records. **Don't** add a theme inline — the comparison view's value depends on a stable cross-company vocabulary; ad-hoc theme additions silently break the matrix narrative for older claims that pre-date the new theme.

### Data model

Four record types in [schema.py](schema.py), all with required `source_url` + `captured_at`:

- **`Company`** — `slug` (e.g. `"meta"`), `name`, `hq`, `dedicated_page_url` (their published community-impact page if one exists), `last_reviewed`.
- **`Claim`** — `id`, `company_slug`, `theme` (one of the 8 above), `statement` (the original quote, NOT paraphrased), `source_url`, `source_title`, `captured_at`, optional `metric` (e.g. `{"value": 1000, "unit": "jobs", "kind": "construction"}` for structured comparison).
- **`Project`** — `id`, `company_slug`, `name`, `city`, `state`, `country`, `lat`, `lon`, `status` (`announced` / `construction` / `operational`), `announced_year`, `claimed_investment_usd`, `claimed_jobs`, `notes`, `source_url`.
- **`CommunityResponse`** — `id`, `project_id`, `date`, `stance` (`positive` / `mixed` / `negative`), `constituency` (`residents` / `local_government` / `ngo` / `academic` / `journalist` / `regulator`), `summary` (1–2 sentences, neutral phrasing), `source_url`, `source_title`.

All four payload types live in `data/seed/` (the curator's working copy) and are mirrored to `docs/data/` on `refresh.py` for the frontend to fetch. **Don't** edit the `docs/data/*.json` files directly — they're build outputs; edit the seed and re-run.

### Editorial / sourcing rules

- **Quote claims; don't paraphrase.** A company's "we will" matters; restating as "they claim X" loses the original wording that's often the most-quoted-by-critics part. The `statement` field is for the verbatim quote; the surrounding UI provides any framing.
- **Every record carries a source URL and capture date.** No exceptions. If a claim has no source, it doesn't ship. Schema enforces this; the frontend renders a "view source" link on every card.
- **What counts as "first-party" (v1.6.1 expansion).** First-party means the statement comes from the company or a named executive — not the venue.
  - **Always first-party:** company-published material (sustainability page, blog post, press release, regulatory filing, S-1 / annual report).
  - **Acceptable as first-party:** a news article that contains a direct verbatim quote from a named company executive (e.g., *"'We will pay our way for electricity,' Brad Smith told Bloomberg."*). The quote is first-party even if the venue is a third-party outlet — the `source_title` should name both the speaker and the outlet (e.g., `"Bloomberg — Smith on Microsoft's Cheyenne pledge"`).
  - **NOT acceptable:** a news article paraphrasing the company without quotation marks. ("Microsoft says it will pay…" without a quote attached.) Skip rather than paraphrase.
  - **NOT acceptable:** an analyst report or NGO summary describing the company's commitment. Those are `CommunityResponse` records, not `Claim` records.
  - **NOT acceptable:** something an executive said in a context where they were not speaking for the company (a personal podcast take that wasn't picked up as a corporate position).
- **Stance is editorial, not algorithmic.** Stance tagging on community responses is a human judgment call — the rubric is in [DESIGN.md](DESIGN.md). **Don't** try to LLM-classify stance; it's the most adversarial part of the editorial frame and a wrong tag undermines the whole dashboard.
- **Constituency matters.** A negative stance from a state regulator is a different signal than a negative stance from a Twitter thread; the `constituency` field lets users weight accordingly.
- **Capture dates over "current" framing.** Company pages change frequently; a claim is always presented as "as of YYYY-MM-DD" in the UI. Re-capture quarterly. Old captures stay in the dataset (append-only) so historical drift is visible.
- **News-source diversity.** For each negative-stance project, prefer at least two independent sources from different outlets before flagging. Single-source claims get a `single_source: true` marker in the response record and a small badge in the UI.
- **Don't aggregate to a "trust score."** Surfacing a numeric "greenwashing index" would be both editorially indefensible and operationally fragile. Show the data; let users judge.

### Data acquisition strategy

v1 is **curated**, not auto-scraped. Each company's claims and projects are seeded from publicly-known sources by a human reviewer, validated against the schema, and shipped as JSON. This trades coverage for accuracy — the dashboard's value is editorial selection, not exhaustiveness. ~10 claims and ~3 projects per company is the v1 target; not 100 of each.

v2 will introduce **connector-based refresh** for the company pages that publish stable URLs (Meta's data centers page at `metadatacenters.com`, Google's data centers page, Microsoft's Datacenter Community Pledge). Connectors live under `connectors/` with the same base-class pattern as adjacent projects: rate-limited HTTP, disk cache, normalize to schema, idempotent re-runs. **Ad-hoc news / community-response sources stay curated** — no automated sentiment classification (see editorial rules above).

### Architectural intent

- **Static-first.** Connectors emit JSON to `docs/data/`; frontend is vanilla JS hosted on GitHub Pages; no runtime backend.
- **Single source of truth in [schema.py](schema.py).** Pydantic models with `extra="forbid"` so any drift in the curated JSON fails fast at refresh time, not at runtime in the browser.
- **Theme constants live in one place.** Currently `THEMES` in [schema.py](schema.py) (Python) + the `THEMES` constant in [docs/app.js](docs/app.js) (frontend). A test (`test_themes_match_frontend`) reads both and asserts they're identical so they can't drift silently. **Don't** add a theme to one without the other.
- **Two payloads, not one.** `companies.json` + `claims.json` (small — preloads on first paint for the comparison view). `projects.json` + `responses.json` (lazy-loads when the user opens the Project Explorer tab). Keeps first paint snappy; the project view is heavier because of the map and per-project detail rendering.
- **Map only on the project view.** **Don't** pull Leaflet's CSS/JS in on the comparison-only view. The frontend code-splits — the map module loads only when the Project Explorer tab is activated.
- **Color tokens are CSS-var-driven.** Per-company brand-adjacent color (NOT exact brand colors — we're not affiliated and don't want to imply endorsement), per-stance color (positive / mixed / negative) — single palette in `:root`, dark-mode override in `[data-theme="dark"]`. **Don't** hard-code colors in JS; read via `getComputedStyle()`.
- **No connector-side aggregation.** Connectors emit raw records; aggregation (claim counts per theme, project counts per company) happens at frontend ingest. Keeps the JSON close to source and lets the frontend re-aggregate as filters change.

### What's explicitly OUT of scope (v1)

- Real-time scraping or alerts.
- Social-media sentiment mining (too noisy; constituency tagging would be meaningless).
- Predictive scoring of "trustworthy" vs "greenwashing" claims.
- Non-US data centers (US sites have richer public-record coverage; revisit in v2).
- Hyperscaler-adjacent colocation operators (Equinix, Digital Realty, etc.).
- Per-claim "delivered vs promised" verification (would need 5–10 years of historical claims to compare meaningfully).
- Automated stance classification on community responses.

### Cross-project lessons carried forward

- **Source attribution is non-negotiable.** Every record must include its origin URL. If a record lacks a source, it doesn't ship.
- **Defensive optional field handling.** Null values in the UI render as explicit placeholders ("N/A", "Not disclosed"), never blank cells.
- **Schema is the contract.** Pydantic `extra="forbid"` catches drift before write; tests cover normalize/edge cases.
- **The `[hidden]` trap.** See Frontend Standards above — pair every `display: ...` override with `[hidden] { display: none }`.
- **Static-first deployment.** GitHub Pages serving `docs/` with no runtime backend; same pattern as adjacent projects in this org.

### Project-detail tab strip (v1.1)

The project pop-out in the Explorer view is split into three tabs — Overview / Claims / Community — generated from `DETAIL_TABS = ["overview", "claims", "responses"]` in [docs/app.js](docs/app.js). Three drift-safe rules:

- **Iterate `DETAIL_TABS` everywhere.** `setActiveDetailTab()`, `wireDetailTabs()`, and any future code that enumerates tabs MUST loop over the constant — same drift-safe iteration pattern as `THEMES`. When a 4th tab ships, drop it into the array and the wiring picks it up for free.
- **Last-clicked tab persists within session, resets on reload.** Module-level `_lastDetailTab` (default `"overview"`) records the user's last explicit click; `resetDetailTabs()` restores it on every `selectProject()`. **Don't** snap back to Overview on every selection — a user scanning Claims across multiple projects shouldn't have to re-click on every project. **Don't** persist to `localStorage` either: a returning user reloading the page should land on the structured Overview, not whatever lighter pane they last visited.
- **Tab-count badges hide via `[hidden]`.** `updateDetailTabCounts(claims, responses)` sets `badge.hidden = (count === 0)`. The `[hidden]` global rule has `!important` so the inline `display: inline-block` on `.dtab-count` doesn't override. Test `test_count_badges_hidden_when_no_data` guards against the trap regression.

### Playwright `wait_for_selector` on hidden-by-default panes (v1.1)

The Community pane is `[hidden]` by default (Overview is the landing tab). Tests that target elements inside that pane MUST pass `state="attached"` to `wait_for_selector`, e.g. `page.wait_for_selector("#d-responses .response-card", state="attached")`. Default `state="visible"` would time out because the parent's `display: none` removes children from the bounding box. Same lesson as adjacent projects — when you waited for visibility but the selector targets a `[hidden]`-conditional element, the wait races a CSS transition or an attribute toggle and flakes on slow runners. Locator `count()` and attribute reads work fine without the wait — they query the DOM, not the layout box.

### Delivered-vs-promised assessments on Claims (v1.13)

The dashboard's blueprint framing implicitly assumed commitments translate to delivery; v1.13 adds a `delivered` Optional sub-object on `Claim` so the curator can attach independent-reporting evidence of how a commitment actually played out. Four-status vocabulary, frozen for v1: `delivered` / `partial` / `contested` / `shortfall`. Schema in [schema.py](schema.py) (`Delivered` class + `DELIVERED_STATUSES` Literal); frontend mirror is `DELIVERED_STATUSES` + `DELIVERED_LABELS` in [docs/app.js](docs/app.js), guarded by `test_delivered_statuses_match` parity tests. Render lives in `renderDeliveredPanel()`, appended to `renderClaimCard()` only when `c.delivered` is set.

Four drift-safe rules:

- **Absence is editorially valuable.** A claim WITHOUT a delivered assessment means "the curator hasn't done the work yet," NOT "implied delivery." **Don't** auto-fill any default status; **don't** add a 5th "unknown" status to fill rows. Leave the panel off and the claim card reads exactly as it did pre-v1.13.
- **Status is a curator judgment call**, exactly like `Stance` on `CommunityResponse`. **Don't** try to LLM-classify it. Use `shortfall` only with strong corroboration (≥2 independent sources or a clear, citable regulator/court finding). `contested` is the right choice when the company maintains delivery and a credible third party documents shortfall — surface both, don't pick a side.
- **Summary is NEUTRAL synthesis** — not a quote, not adversarial framing. Cite the underlying evidence in `source_url`. Existing `claim.source_url` is the company's quote source; `claim.delivered.source_url` is the assessment source — they will almost always differ.
- **Adding a 5th status requires a BACKLOG entry + migration**, exactly like adding a theme. Add to `DELIVERED_STATUSES` tuple + `DeliveredStatus` Literal + `DELIVERED_LABELS` dict (Python), then the same three constants in `app.js`, then per-status color tokens in `:root` and `[data-theme="dark"]` blocks. The `test_delivered_status_vocabulary_frozen` test guards the four-status assumption.

A test (`test_at_least_one_of_each_delivered_status`) asserts the seed dataset ships with at least one example of each of the four statuses so the legend reads with all four colors backed by real records. **Don't** silently delete all examples of a status — the legend would render an empty chip.

The CSS palette mirrors stance hues (delivered ↔ positive, shortfall ↔ negative, partial / contested ↔ mixed-adjacent) so reading the dashboard's color signal stays consistent across the Claims tab and the Community tab.

### Ratepayer Protection Pledge view (v1.15)

A **third top-level tab** (`view-ratepayer`) built around a real-world anchor: the White House Ratepayer Protection Pledge, signed 2026-03-04 at the White House by seven hyperscalers (Amazon, Google, Meta, Microsoft, OpenAI, Oracle, xAI); QTS became the eighth signatory via the DOE companion track on 2026-04-24 (`RATEPAYER_PLEDGE_DOE_DATE`). The view answers "who signed, and is it showing up at the data centers they've announced since?" — top-level stat tiles, a signatory roster, and a per-site scorecard. Lazy-loads the projects/responses payload (NOT Leaflet — that stays Explorer-only) via the shared `loadProjectData()` extracted from `loadExplorerData()`. Deep-linkable at `#ratepayer`.

Two data structures back it, both in [schema.py](schema.py):
- **`Company.ratepayer_pledge_signatory`** (bool, default False) — the eight signatories (seven White House 2026-03-04 + QTS via DOE track 2026-04-24). This is **fixed historical fact, not a curator judgment** — don't flip it for companies that publish their own ratepayer commitment but didn't sign (Anthropic stays False). The roster note distinguishes tracks ("Signed at White House on March 4, 2026" vs "Signed with DOE on April 24, 2026", driven by `RATEPAYER_DOE_TRACK_SIGNATORIES` in app.js). `test_exactly_the_eight_signatories_flagged` guards the roster.
- **`Project.ratepayer`** (Optional `Ratepayer` sub-object) — a curated per-site assessment with a 3-status vocab: `affirmed` (site-specific pay-our-own-way commitment exists; `evidence_claim_id` points at the backing verbatim Claim) / `pledge_only` (signatory + post-pledge, no site-specific commitment captured) / `contested` (third party documents the site shifting costs despite the pledge). Frozen for v1.

Drift-safe rules (same spirit as the delivered block):
- **Only attach `ratepayer` to signatory projects announced on/after 2026-03-04.** Pre-pledge or non-signatory sites get nothing — `test_assessed_projects_belong_to_signatories` and `test_assessed_projects_announced_on_or_after_pledge` enforce the cohort boundary. Absence is honest.
- **`pledge_only` is NOT a failing grade.** It means "covered by the national signature, nothing site-specific captured." Don't write it as criticism; don't attach an `evidence_claim_id` to it (`test_pledge_only_assessments_have_no_evidence_claim`).
- **`affirmed` MUST cite a real, project-owned claim** in `evidence_claim_id`. refresh.py's cross-ref pass validates the id exists AND belongs to the same project; `test_affirmed_assessments_cite_a_real_owned_claim` mirrors it.
- **No forced one-of-each-status.** Unlike delivered, only `affirmed` + `pledge_only` are required (`test_at_least_one_affirmed_and_one_pledge_only`); the frontend legend (`renderRatepayerLegend`) only renders chips for statuses actually present in the cohort. The first `contested` examples landed 2026-06-11: the three post-pledge Amazon Mississippi sites (`amazon-clinton-ms`, `amazon-vicksburg-ms`, `aws-ridgeland-ms`), based on the May 2026 Synapse Energy Economics report (commissioned by Earthjustice / Environmental Advocates Mississippi; covered by Mississippi Today and independently by Vicksburg Daily News) estimating ~$38M in data-center-related costs already charged to Entergy Mississippi residential ratepayers — while Amazon/Entergy maintain full-cost payment and invoke the pledge. That's the canonical `contested` shape: surface both sides, don't pick one. Each contested site keeps its `evidence_claim_id` (the company's affirmation is the other half of the dispute), flips the `delivery_infra` principle to `not_met` with a dispute-aware note, and carries a paired negative `CommunityResponse` (constituency `ngo`) citing the report coverage. **Don't** mark `contested` from criticism of a rate *structure* alone (e.g. NIPSCO GenCo skepticism in Indiana) — it requires documented cost-shifting at/serving the site.
- **Status vocab mirrors to `app.js`** as `RATEPAYER_STATUSES` + `RATEPAYER_LABELS`, guarded by `test_ratepayer_statuses_match` / `test_ratepayer_labels_keys_match`. Adding a status = BACKLOG entry + the Python/JS constants + `--ratepayer-<status>` color tokens in both `:root` blocks, same drill as delivered/themes.

The roster's non-signatory flagging (Anthropic surfaces as "Own commitment") is **frontend-derived** via a keyword scan (`RATEPAYER_CLAIM_KEYWORDS` in app.js) over each company's claims — it's a discovery affordance, not a stored field, so it stays in sync as claims land. The `"100% of the grid"` keyword was added when QTS moved into the signatory group so Anthropic's "pay for 100% of the grid upgrades" keeps the non-signatory group populated (the flag surfaces the *clearest* non-signatory commitments, it isn't a census). The CSS palette reuses the delivered hues: `affirmed ↔ delivered green`, `pledge_only ↔ partial blue-grey`, `contested ↔ amber`.

### Comparison view is summary-pop-out, not claims-list (v1.3)

The Comparison view's job is to surface "what does each company actually publish about community engagement?" — not to be a global claim browser. v1.0–v1.2 had a global claims list under the matrix that filtered when you clicked a cell; v1.3 removed that entirely. The matrix now opens a per-company pop-out (`#company-detail`) on row / cell click, showing:

- A curated 1–2 paragraph `summary` (new optional field on `Company`, see `schema.py`) describing how the company frames data-center community engagement.
- A link to `dedicated_page_url` (the company's main community/engagement page on their own site).
- Counts of recorded claims + tracked projects for that company.
- Last-reviewed date.
- A "View this company's projects →" CTA that switches to the Explorer view with the company filter pre-set (via `state.explorerFilters.company` + `syncExplorerFilterUIToState()`).

**Don't** restore the global claims list. The user explicitly cut it because the matrix should answer "does this company speak to this theme at all?" + "what's their overall framing?", not "scroll a wall of every claim by every company". Claim-level browsing happens in the Project Explorer's per-project Claims tab. **Don't** make the company summary an aggregation of the per-company claims either — the summary's editorial value is meta-commentary on the company's framework / page structure / gaps (e.g. "Anthropic has no published framework — they don't operate their own data centers"), which is information that doesn't fall out of the claim records.

The `summary` field is **Optional** in the schema. An empty summary surfaces a muted "No community-impact summary captured for this company yet" placeholder — that's editorially honest for a future entity we haven't researched yet. **Don't** lazy-fill summaries by templating from the claims; spend the curation time.

### Matrix is checkmark-only (v1.2)

`renderMatrix()` in [docs/app.js](docs/app.js) emits `<span class="count check">✓</span>` for **every** populated cell, regardless of the underlying claim count. The matrix answers a binary question — "does this company speak to this theme at all?" — and volume goes in the claims list below, not the matrix itself. The `aria-label` still carries the precise integer (`"6 Meta Jobs claims — click to filter"`) so screen readers get the count even when the visual is a glyph. **Don't** restore the digit-count branch: the v1.1 implementation surfaced volume in the matrix and the user explicitly cut it because the matrix should read at a glance. **Don't** drop the `aria-label` numeric — the visual is intentionally lossy. Tests `test_all_populated_cells_render_check`, `test_no_digit_only_cells_remain`, and `test_check_cell_aria_label_carries_numeric_count` guard the contract.

### `project_page_url` is distinct from `source_url` (v1.1)

`Project.project_page_url` (Optional[HttpUrl], schema.py) is the canonical project page on the company's official site (e.g. `https://datacenters.atmeta.com/2021/03/hello-georgia/` for `meta-newton-ga`). `Project.source_url` is where THIS RECORD was sourced — often a press release or news article. They overlap when the project page is also the announcement source (Meta does this); they diverge when the source is a Reuters / Bloomberg / company-blog post that links *out* to the project page. The detail panel's Overview tab renders both as separate KV rows ("Project page" + "Record source"). When adding a project, fill `project_page_url` if a canonical project page exists; leave null if not (e.g., Stargate Abilene has no public OpenAI page yet that returns 200 to scrapers).

### Physical / operational project fields (v1.2)

Four new optional fields on `Project` capture the physical scale and tenant arrangement of each campus:

- **`acreage`** (Optional[float], acres) — physical site size. Cumulative across phases for sites that have expanded (e.g. Meta Richland 2,250 ac, AWS Project Rainier 1,200 ac). Null when the site is too distributed for a single canonical figure (e.g. AWS Loudoun spans 50+ parcels).
- **`power_mw`** (Optional[float], megawatts) — total announced electrical capacity. Latest known number — pre-Cox-scaleback Wonder Valley would have been 7,500 MW (7.5 GW); the seed uses the post-scaleback 1,500 MW (1.5 GW) figure. Null when the company hasn't disclosed (Microsoft Quincy and Mt. Pleasant are intentionally null — neither has a clean Microsoft-disclosed total).
- **`gpu_count`** (Optional[int]) — total announced AI accelerators (NVIDIA H100/H200/GB200, AMD MI300, AWS Trainium 2, Google TPU). **Almost always null for owner-operator hyperscaler sites** — Meta, Google, MS, AWS owner-operator campuses don't publish GPU counts. Where it IS public: Stargate Abilene (450K GB200), Project Rainier (500K Trainium2), Memphis Colossus (230K H100/H200/GB200).
- **`offtaker`** (Optional[str]) — the workload owner. For owner-operator sites this is the operating company itself ("Meta", "Google", "Microsoft", "AWS"). The field's real value is in **colocation arrangements**: `oracle-abilene-tx` shows `OpenAI` (Oracle hosts, OpenAI uses); `aws-new-carlisle-in` shows `Anthropic` (AWS operates Project Rainier, Anthropic is the primary tenant). Null for `wonder-valley-box-elder-ut` because the developer hasn't named tenants.

Frontend formatters in [docs/app.js](docs/app.js): `formatAcreage` (rounds to whole acres ≥10, one decimal below), `formatPower` (auto-converts ≥1000 MW to GW with one decimal), `formatGpuCount` (compresses to "K" / "M"). The Overview tab renders all four under the existing investment/jobs rows; null values use the standard `setKv()` "Not disclosed" placeholder. **Don't** display the offtaker as a separate badge if it equals the company — the redundancy is fine in the KV grid (always present, easy to scan), but a badge would just be noise for the 12 owner-operator sites where they match.

### Compact claim card variant (v1.1)

Claim cards have two visual modes driven by an opt-in `.compact` class on the parent `<ol class="claims-list">`:
- **Default** (Comparison view's main claims list) — full padding, 0.92rem font, box-shadow, large typographic curly quotes (`\201C` / `\201D`) wrapping the verbatim quote. The serif font on the quote is load-bearing — it signals "this is a quoted statement," not body copy.
- **Compact** (Project detail's Claims tab) — tighter padding, 0.85rem font, no shadow, same serif quote treatment but at 0.88rem. The card is supporting context for a project, not the headline read; visual weight should drop accordingly.

**Don't** drop the serif on `.claim-quote` in either mode — that's the editorial signal. **Don't** add the `compact` class to the comparison view's main list — that view IS the read.
