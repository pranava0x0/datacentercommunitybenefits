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
- **Single source of truth.** Constants, configs, and shared types derive from one place. **A hand-written list that mirrors a registry rots silently, and it rots worst inside the code meant to catch drift.** This session hit it three times: the refresh test's seed-copy list (a literal instead of `refresh.PAYLOAD_FILES`, so `signatories.json` broke every refresh test), `tools/build_preview.py`'s `DATA_FILES` (it shipped a bundle whose Ratepayer landing rendered **zero** cards *while reporting PASS*), and `test_exactly_the_eight_signatories_flagged` (hardcoded, so it stayed green through an expansion that tripled the roster). All three passed while wrong. The tell is a literal sitting beside the thing it enumerates. Derive it — `for name in refresh.PAYLOAD_FILES`, `sorted((DOCS/"data").glob("*.json"))`, `assert flagged == on_roster` — and the check cannot go stale.
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
- **CoreWeave, Crusoe, Prologis** — added in the v2 expansion (see the Signatory registry section below); all three cleared the two-gate test as compute/colocation developers operating at hyperscaler scale.
- **SB Energy (SoftBank Group), Brookfield** — added 2026-07-30, tied to DOE's federal-land AI data center program (Portsmouth OH, Paducah KY respectively). Same two-gate test, same process. **NextEra Energy is deliberately NOT a separate slug** despite DOE/company releases naming it as the Paducah project's power-generation partner: DOE, Brookfield, and NextEra's own releases are explicit that Brookfield leases/develops/operates the data center while NextEra only builds/owns the paired generation. NextEra is independently a Ratepayer Pledge signatory (2026-07-23 expansion) and Brookfield is not — collapsing the two into one company record would let NextEra's signatory status bleed onto Brookfield's `ratepayer_pledge_signatory` flag. **The precedent for a multi-party consortium: track only the confirmed data-center developer/operator as the company; name power/utility partners in the `Project.notes`, not as additional company slugs.**
- **Amentum was considered for the same DOE federal-land program (Savannah River Site) and NOT added — a gate-2 lesson worth keeping.** It has an announced 1GW project (clears gate 1) and two first-party, named-executive quotes (Heller, Whitney) — enough material that it was added, then removed on review. Re-reading those quotes: both are about Amentum's engineering/nuclear-operations capability and national-security positioning, with zero community-impact content (no jobs figure, no ratepayer language, no environmental commitment, no engagement framing). **Having first-party quotes to attach is not the same as clearing gate 2** — the quotes have to actually be ABOUT community impact, not merely sourced from the company. Don't re-add Amentum on the strength of these two quotes alone; it needs either a standing community-impact page or a first-party statement that actually addresses jobs/tax/energy/water/grants/infrastructure/education/engagement for the host community.

The slugs (`wonder-valley`, `qts`, `crusoe`, `coreweave`, `prologis`, `sb-energy`, `brookfield`) live in `COMPANY_SLUGS` + the `CompanySlug` Literal in [schema.py](schema.py); `TestSeedCoverage.OPTIONAL_ENTITIES` in [tests/test_seed_data.py](tests/test_seed_data.py) is the test-side ledger. When adding a new non-hyperscaler entity:
1. Add the slug to all four locations above (schema Literal + COMPANY_SLUGS tuple, app.js COMPANY_SLUGS array, OPTIONAL_ENTITIES set).
2. Add a `--co-<slug>` CSS color in both light and dark `:root` blocks.
3. Add the company entry to `data/seed/companies.json` with a curated `summary`.
4. Before shipping: re-read every first-party quote you're about to attach and confirm it's actually ABOUT community impact (jobs, tax revenue, energy, water, community grants, infrastructure, education, or engagement) — not just sourced from the company. "We have quotes" and "gate 2 is cleared" are not the same claim (the Amentum lesson above).

Hyperscaler-adjacent colocation operators not yet tracked (Equinix, Digital Realty) remain **out of scope** unless they meet the same two-gate test. The QTS addition is the precedent for evaluating future operators; the SB Energy/Brookfield addition is the precedent for evaluating a DOE-adjacent or multi-party one; the Amentum non-addition is the precedent for what "clearing gate 2" actually requires.

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
- **A live source_url is not the same as a verified claim (v1.19 lesson).** `source_url` returning 200 only proves the link works — it doesn't prove the page actually contains the specific fact being cited. This bit a 2026-07-14 refresh twice: a WebSearch tool's synthesized answer aggregates facts across *all* of that search's results, not just the one URL picked as `source_url` — two figures ("largest data center campus in Texas," a "$7B+ collateral" figure) made it into records because they were in the search tool's summary, not because they were confirmed present in the specific article cited as the source. Before shipping a WebSearch-derived fact, fetch the exact `source_url` directly and confirm the claim is actually there — don't trust the search synthesis as a stand-in for the citation. `scripts/validate_moratoriums.py` already automates exactly this check for moratoriums (fetch source, search for verbatim/near-verbatim claim text); the same discipline applies manually to Claims/Projects/Tariffs, which don't have an equivalent script yet.
- **A headline's loaded word ("ban", "moratorium") is not the underlying legal action — check for the jurisdiction's own denial (2026-07-27 lesson).** Two separate Loudoun County VA records were seeded describing a permanent "ban," both wrong. Loudoun's own FAQ states outright that a blanket moratorium is "not legally permissible" under Virginia law; what actually happened both times was a zoning-ordinance change moving data centers from by-right to special-exception review — real, but not a ban. Both records were removed rather than reworded (same treatment as CLAUDE.md's other "fix/remove, don't just swap the URL" precedent). The second occurrence of the identical failure shape is the signal it's worth a standing rule, not just a one-off fix: when a headline uses a strong restrictive word for a jurisdiction, look for that jurisdiction's own clarifying statement before trusting the headline's word choice.
- **A source's own news-index/channel page, fetched directly, surfaces recency that keyword search misses (2026-07-27 lesson).** Three rounds of broad WebSearch for new data center announcements (general, company-scoped, and DCD-domain-scoped) all came back with nothing genuinely new — every lead, cross-checked against the seed, turned out already-tracked or a stale recap of months-old news (see the 2026-07-14 "generic aggregator" lesson above, recurring). WebFetch-ing DataCenterDynamics' own listing page directly (`datacenterdynamics.com/en/news/?term=construction-site-selection`) returned an actual dated headline list and surfaced 3 real new projects plus the Loudoun catch above — none of which any keyword query reconstructed. A search snippet samples a source; a listing enumerates it. When a "is there anything new?" search pass comes back stale or empty, try the source's own index/channel URL directly before concluding the pass was exhaustive.
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

### Ratepayer Protection Pledge view (v1.15, substantially revised in v2 — read the v2 section below first)

A **third top-level tab** (`view-ratepayer`) built around a real-world anchor: the White House Ratepayer Protection Pledge, signed 2026-03-04 at the White House by seven hyperscalers (Amazon, Google, Meta, Microsoft, OpenAI, Oracle, xAI); QTS became the eighth signatory via the DOE companion track on 2026-04-24 (`RATEPAYER_PLEDGE_DOE_DATE`). The view answers "who signed, and is it showing up at the data centers they've announced since?" — top-level stat tiles, a signatory roster, and a per-site scorecard. Unassessed signatory sites are split date-aware by `isPrePledgeProject()` in app.js into two sections: "Pledge-era sites awaiting assessment" (`#rp-unassessed`: announced on/after the pledge, or year-only 2026 — a bare year can't be placed either side of March 4, so it stays pledge-era rather than being mislabeled) and "Sites announced before the pledge" (`#rp-pre-pledge`). The CSV export labels the buckets `not-yet-assessed` / `pre-pledge`. Bucketing is company-agnostic (White House date) — no dated QTS site currently lands in the Mar 4 – Apr 24 DOE-track window; revisit if one does. Lazy-loads the projects/responses payload (NOT Leaflet — that stays Explorer-only) via the shared `loadProjectData()` extracted from `loadExplorerData()`. Deep-linkable at `#ratepayer`.

Two data structures back it, both in [schema.py](schema.py):
- **`Company.ratepayer_pledge_signatory`** (bool, default False) — **v2: now a MIRROR of `signatories.json`, not a hand-maintained list.** Eleven tracked companies are signatories as of 2026-07-23 (the original seven, QTS via DOE, plus CoreWeave / Crusoe / Prologis from the expansion). Still **fixed historical fact, not a curator judgment** — don't flip it for companies that publish their own commitment but didn't sign (Anthropic stays False). Flip it only when the roster says so. `test_signatory_flags_match_the_roster` asserts the two agree; `test_the_original_eight_are_still_signatories` keeps the March/DOE cohort from being dropped. The old `test_exactly_the_eight_signatories_flagged` hardcoded the set, which is exactly what let the flag sit stale through an expansion that tripled it — **don't reintroduce a hardcoded roster in a test.**
- **`Project.ratepayer`** (Optional `Ratepayer` sub-object) — a curated per-site assessment with a 3-status vocab: `affirmed` (site-specific pay-our-own-way commitment exists; `evidence_claim_id` points at the backing verbatim Claim) / `pledge_only` (signatory + post-pledge, no site-specific commitment captured) / `contested` (third party documents the site shifting costs despite the pledge). Frozen for v1.

Drift-safe rules (same spirit as the delivered block):
- **Only attach `ratepayer` to signatory projects announced on/after THEIR OPERATOR'S signing date** (v2; it was a flat 2026-03-04 before). Pre-pledge or non-signatory sites get nothing — `test_assessed_projects_belong_to_signatories` and `test_assessed_projects_announced_on_or_after_pledge` enforce the cohort boundary. Absence is honest.
- **`pledge_only` is NOT a failing grade.** It means "covered by the national signature, nothing site-specific captured." Don't write it as criticism; don't attach an `evidence_claim_id` to it (`test_pledge_only_assessments_have_no_evidence_claim`).
- **`affirmed` MUST cite a real, project-owned claim** in `evidence_claim_id`. refresh.py's cross-ref pass validates the id exists AND belongs to the same project; `test_affirmed_assessments_cite_a_real_owned_claim` mirrors it.
- **No forced one-of-each-status.** Unlike delivered, only `affirmed` + `pledge_only` are required (`test_at_least_one_affirmed_and_one_pledge_only`); the frontend legend (`renderRatepayerLegend`) only renders chips for statuses actually present in the cohort. The first `contested` examples landed 2026-06-11: the three post-pledge Amazon Mississippi sites (`amazon-clinton-ms`, `amazon-vicksburg-ms`, `aws-ridgeland-ms`), based on the May 2026 Synapse Energy Economics report (commissioned by Earthjustice / Environmental Advocates Mississippi; covered by Mississippi Today and independently by Vicksburg Daily News) estimating ~$38M in data-center-related costs already charged to Entergy Mississippi residential ratepayers — while Amazon/Entergy maintain full-cost payment and invoke the pledge. That's the canonical `contested` shape: surface both sides, don't pick one. Each contested site keeps its `evidence_claim_id` (the company's affirmation is the other half of the dispute), flips the `delivery_infra` principle to `not_met` with a dispute-aware note, and carries a paired negative `CommunityResponse` (constituency `ngo`) citing the report coverage. **Don't** mark `contested` from criticism of a rate *structure* alone (e.g. NIPSCO GenCo skepticism in Indiana) — it requires documented cost-shifting at/serving the site.
- **Status vocab mirrors to `app.js`** as `RATEPAYER_STATUSES` + `RATEPAYER_LABELS`, guarded by `test_ratepayer_statuses_match` / `test_ratepayer_labels_keys_match`. Adding a status = BACKLOG entry + the Python/JS constants + `--ratepayer-<status>` color tokens in both `:root` blocks, same drill as delivered/themes.

The roster's non-signatory flagging (Anthropic surfaces as "Own commitment") is **frontend-derived** via a keyword scan (`RATEPAYER_CLAIM_KEYWORDS` in app.js) over each company's claims — it's a discovery affordance, not a stored field, so it stays in sync as claims land. The `"100% of the grid"` keyword was added when QTS moved into the signatory group so Anthropic's "pay for 100% of the grid upgrades" keeps the non-signatory group populated (the flag surfaces the *clearest* non-signatory commitments, it isn't a census). The CSS palette reuses the delivered hues: `affirmed ↔ delivered green`, `pledge_only ↔ partial blue-grey`, `contested ↔ amber`.

### Ratepayer card source links (v1.17 fix)

Every ratepayer card (assessed, pledge-era unassessed, and pre-pledge) renders an always-visible **"Sources:" footer** via `rpCardSourcesHtml(p)` in app.js. Before v1.17, only `affirmed`/`contested` sites surfaced a link — and only after expanding two nested `<details>` — so the 18 `pledge_only` sites and all pre-pledge sites read as having *no* evidence at all. The helper dedupes by URL and links, in order: the site-specific evidence claim's `source_url` (when present) → the project's `project_page_url` → the project's `source_url` (always present, schema-required) → the pledge proclamation (`RATEPAYER_PLEDGE_URL`). Because the project's own `source_url` is always present, the footer is **robust to the claims payload not being loaded yet** (the deep-link race), unlike the evidence blockquote which needs `state.claims`. The roster also links each row (signatories → the pledge; "Own commitment" companies → their `dedicated_page_url`). `test_ratepayer_cards_have_sources_helper` guards that the helper exists and is called in both card renderers. **Don't** bury the source links back inside the collapsible evidence `<details>` — the always-visible footer is the fix.

### Non-signatory companies toggle (v1.21; roster changed in v2)

**v2 note:** CoreWeave, Crusoe and Prologis signed on 2026-07-23 and are no longer covered by this toggle. Only **Anthropic and Wonder Valley** remain genuine non-signatories. The membership is derived from the roster, so it corrects itself — but any prose naming the non-signatories will not, so check it after an expansion.

The Ratepayer view has a **"Show non-signatory companies" checkbox** (hidden `#rp-non-signatory-section`, unchecked by default) that reveals sites from companies that never signed the pledge at all — `ratepayerNonSignatoryProjects()` in app.js, the inverse filter of `ratepayerSignatories()`. These sites reuse `renderPrePledgeCard()` (same card, same source-footer helper) labeled "Not a pledge signatory" instead of getting their own render path. **Don't** attach a `ratepayer` assessment to any of these sites — the frozen rule (`_is_ratepayer_eligible` in refresh.py, `isPrePledgeProject` in app.js) is signatory + post-pledge-date only; this toggle is a comparison affordance, not a scope change to what gets assessed. See DESIGN.md's "Opt-in reveal" pattern — reuse this shape (hidden section + labeled checkbox) rather than a new tab for future adjacent-but-out-of-scope data asks.

**`refresh.py`'s audit had a signatory-blind bug (fixed 2026-07-15):** `_audit_missing_commitments` flagged "missing ratepayer" for every operational/construction project regardless of company, over-flagging ~18 non-signatory records (CoreWeave, Crusoe) that should never carry an assessment. Fixed by mirroring `isPrePledgeProject`'s signatory + date check in a new `_is_ratepayer_eligible` helper before generating `ISSUES.md`. If the medium-gap ratepayer count spikes again after adding a new company, check whether `_is_ratepayer_eligible` needs to account for it. **In v2 that helper takes a `{slug: signed_date}` map built from `signatories.json` (`_signatory_dates`) rather than a set of slugs** — see "Roster-driven eligibility" below.

### State utility tariffs view (v1.17)

A **fifth top-level tab** (`view-tariffs`, `#tariffs`) tracking state-regulated large-load / data-center electricity tariffs, scored against the design-element taxonomy from the DOE / Berkeley Lab (LBL) technical brief *"Electricity Rate Designs for Large Loads"* (Jan 2025). Modeled on the moratorium tab: stat tiles → LBL-element coverage breakdown (clickable, like the moratorium "reason breakdown") → filterable directory table → detail pop-out. Lazy-loads `data/tariffs.json` (NOT Leaflet). Data model is `Tariff` + `TariffsPayload` in [schema.py](schema.py); refresh.py mirrors seed→docs like the other payloads.

- **`TARIFF_PARAMETERS` is the frozen LBL taxonomy** — 17 design elements in 5 groups (`TARIFF_PARAMETER_GROUPS`): Eligibility & Applicability, Contract Size, Contract Duration & Exit, Energy Source, Other. Mirrored to `app.js` as `TARIFF_PARAMETERS` / `TARIFF_PARAMETER_LABELS` / `TARIFF_PARAMETER_GROUP_OF`, guarded by `test_tariff_parameters_match` (+ label/group parity). Adding an element = BACKLOG entry + the Python/JS constants + group mapping, same drill as THEMES/delivered. The store is **sparse**: a tariff only lists elements it addresses (`{status: included|partial, detail, source_url?}`); the detail pop-out iterates the full 17 and renders the gaps as "Not addressed", so "met or not" shows without storing a row for every absence.
- **Status vocab `TARIFF_STATUSES` = `approved` / `proposed` / `rejected`** (the user's "passed/proposed/rejected"). `test_all_three_statuses_present` asserts ≥1 of each so the directory reads with all three. The one `rejected` example is the **federal** FERC Talen/Amazon Susquehanna co-location ISA (Docket ER24-2172, rejected Nov 2024) — the LBL brief itself references co-location (FERC AD24-11-000), so it's on-topic even though it's not a state tariff; it's flagged as federal in its `summary`/`tariff_type`.
- **Source discipline.** Every tariff carries `source_url` + `source_title`; `additional_terms` and `legislation` each carry their own URLs. Sources were **link-checked (200) before commit** per the active-links rule; two bot-blocked URLs (mississippitoday.org homepage, a ferc.gov news page) were repointed to live equivalents. `test_prioritizes_gov_sources` asserts ≥60% of primary sources are .gov/LBL. The 11 LBL-appendix tariffs use the LBL brief PDF as a guaranteed-live `source_url` where no confirmed PUC docket URL was available — the brief is the authoritative DOE source documenting them, and `docket_number` carries the case ID regardless.
- **`legislation`** links state laws that authorize/influenced a tariff (Ohio HB 15 → AEP Ohio; Texas SB 6 → the PUCT large-load rule; Virginia SCC initiatives → the GS-5 rate class). Builder script that encodes the dataset: `.agent_outputs/build_tariffs.py` (idempotent; re-run to regenerate `data/seed/tariffs.json`, then `python refresh.py`). Coverage is curated, not all-50-state — many states have no data-center tariff yet, an honest absence the footnote calls out.
- **`jurisdiction_level`** (`state` | `federal`, default `state`) segregates the one FERC co-location case (Talen/Amazon Susquehanna) from the state-tariff stats: federal records are EXCLUDED from the "Approved/Proposed/Rejected" tiles and the "States covered" tally, surfaced instead in a separate "Federal cases" tile + a `FED` badge in the directory (`isFederalTariff()` in app.js). Keeps a federal case from reading as a state tariff. Guarded by `test_dataset_is_predominantly_state_level` / `test_federal_cases_are_clearly_federal` + the `TestTariffsView` e2e.
- **`resources` is a typed `SourceResource` list** (`{url: HttpUrl, title}`), NOT `list[dict]` — the detail renderer assumes both fields, so a missing/empty URL must fail at `refresh.py` not silently render a broken link. `additional_terms` / `legislation` are likewise typed sub-models.
- **Colors are design tokens, not hard-coded.** `--tariff-{approved,proposed,rejected,included,partial,federal}[-soft]` live in BOTH the `:root` and `[data-theme="dark"]` blocks (literal values, mirroring `--stance` / `--delivered`). **Don't** alias them via `var(--stance-*)` in `:root` only — a custom property whose value is `var(...)` does NOT propagate the dark override to descendant elements (the alias computes correctly on `:root` but children inherit the light value); use explicit literals in both blocks.
- **Directory rows are keyboard-accessible** (`role="button"`, `tabIndex=0`, Enter/Space → `showTariffDetail`), not mouse-only. `test_row_opens_detail_via_keyboard` guards it.
- **html2pdf (moratorium PDF export) is lazy-loaded** via `loadHtml2Pdf()` in app.js on first export click, NOT a blocking `<script>` in `<head>`. The blocking CDN script made every `page.goto(..., "load")` in the e2e suite wait on cdnjs (a flakiness + SRI-failure source). **Don't** move it back to `<head>`. The SRI hash lives in the `HTML2PDF_SRI` constant.

### Moratorium stat tiles — jurisdiction breakdown (v1.18)

The four stat tiles (Total / Enacted / Proposed / Failed) each show a secondary breakdown line (`<span class="rp-stat-breakdown">`) listing counts by `jurisdiction_type` in order: **city → county → state → federal**. The helper `_jurtypeBreakdown(moratoriums)` in [docs/app.js](docs/app.js) filters out zero-count types so only populated levels appear. Order is hardcoded; change the array literal in `_jurtypeBreakdown` if the order preference changes.

### Moratorium source audit script (v1.18)

`scripts/validate_moratoriums.py` — audit trail validator for `data/seed/moratoriums.json`. For each record it fetches the `source_url` and up to three resource URLs (gov/official URLs fetched first), then searches the page text for seven verifiable claims: `bill_number`, `sponsors`, `vote`, `enacted_date`, `enacted_by`, `failure_reason`, `session`. Each found claim includes a **verbatim snippet** from the source page — the audit trail linking the record field to the source document.

Usage:
```
python scripts/validate_moratoriums.py                        # all 59 records
python scripts/validate_moratoriums.py --id maine-state-2026-04  # single record
python scripts/validate_moratoriums.py --cached               # offline, use cache only
python scripts/validate_moratoriums.py --dry-run              # schema check, no fetches
python scripts/validate_moratoriums.py --fail-on-unverified   # CI gate (exit 1)
```

Outputs `moratorium_audit_report.json` (per-record JSON trail) and appends to `ISSUES.md` for records missing a `.gov` source or with unverified critical claims. Both output files are `.gitignore`d — they're run artifacts, not source. Fetched pages are cached in `.moratorium_cache/` (also `.gitignore`d); delete the directory to force a re-fetch.

**Data quality rules enforced by `tests/test_validate_moratoriums.py`** (offline, no network):
- All `failed` records must have a `failure_reason`
- All `enacted` records must have an `enacted_date`
- No duplicate IDs
- All records have the required schema fields

### Moratorium detail modal (v1.19)

The moratorium detail was converted from an inline `<aside>` (toggled with `hidden`) to a full modal overlay — same pattern as the tariff detail modal. Structure:

```html
<div id="moratorium-modal" class="moratorium-modal" hidden>
  <div class="moratorium-modal__backdrop" data-moratorium-close aria-hidden="true"></div>
  <aside id="moratorium-detail" class="moratorium-detail moratorium-modal__dialog" role="dialog" aria-modal="true" …>
    …
  </aside>
</div>
```

CSS class `.moratorium-modal` mirrors `.tariff-modal` (fixed overlay, backdrop blur, scroll lock via `body.moratorium-modal-open`). The dialog uses `.moratorium-modal__dialog.moratorium-detail` to override the inline card layout. Animation, focus trap, backdrop-click-to-close, Escape-to-close, and return-focus-on-close all follow the tariff modal pattern exactly — copy that pattern for any future detail panel that needs full-screen treatment.

The modal also surfaces three previously unused fields: `effective_date` (shown when present and distinct from `enacted_date`), `policy_type` (shown when present), and `key_stakeholders` (a grouped chip section; hidden when absent). The "Opposed" stakeholder group gets a subtle red tint via `[data-category="opposed"]` CSS.

**`badge-reason-*` CSS class drift (found + fixed 2026-07-15).** `MoratoriumReasonType` in schema.py is `energy | water | air_quality | noise | transparency | equity`, but `docs/styles.css` still had `.badge-reason-pollution` / `.badge-reason-planning` — an old taxonomy's names, from before the enum was renamed. Neither `air_quality`, `noise`, nor `transparency` had a matching CSS rule, so those badges silently fell back to the base `.badge` style with no color and, worse, no margin — three of the six "Key reasons" chips in the detail modal ran together as one unreadable word. Nothing caught it: unlike THEMES/DELIVERED_STATUSES/RATEPAYER_STATUSES, `key_reasons` has no Python↔JS parity test, and CSS class names aren't type-checked. Fixed by renaming the classes to match the live enum and adding the missing `noise` rule. If a 7th reason value is ever added, grep `docs/styles.css` for `badge-reason-` explicitly — don't assume the type-checker or an existing test will catch a mismatch here.

### Shared export helpers in app.js (v1.19)

All PDF exports across all six tabs use three shared helpers in `docs/app.js`:

- **`_exportToPDF(title, bodyHtml, filename)`** — wraps content in a styled div and calls the lazy-loaded `html2pdf` lib.
- **`_pdfTable(headers, rows)`** — builds an inline-styled HTML table string for use in `_exportToPDF`.
- **`_triggerDownload(csv, filename)`** — creates a Blob, fires `<a>.click()`, and revokes the URL. Filename accepts `"TODAY"` as a literal substring, which is NOT replaced — callers must supply the dated filename directly.

Per-tab export functions:
- `exportComparisonToPDF()` / `downloadMatrixCsv()` (Comparison)
- `downloadExplorerCSV()` / `exportExplorerToPDF()` (Explorer — respects current filters via `_filteredProjects()`)
- `downloadRatepayerCSV()` / `exportRatepayerToPDF()` (Ratepayer)
- `downloadMoratoriumsCSV()` / `exportMoratoriumsToPDF()` (Moratoriums — respects status + type filters)
- `downloadTariffCSV()` / `exportTariffsToPDF()` (Tariffs — respects status + state filters)
- `downloadAggregateCSV()` / `exportAggregateToPDF()` (Aggregate — uses `buildCompanyRollups()` + `buildStateRollups()`)

### `wireBtn` helper (v1.19)

```js
function wireBtn(id, handler) {
  const btn = document.getElementById(id);
  if (!btn || btn.dataset.wired === "1") return;
  btn.dataset.wired = "1";
  btn.addEventListener("click", handler);
}
```

One-liner for wiring a button by id with double-wiring guard. Use this for all new export or action buttons; don't inline the guard repeatedly.

### Moratorium comprehensiveness + accuracy pass (v1.20)

Big expansion + integrity pass. Moratoriums **59 → 91** (33 verified new records
across state/county/city), ratepayer scorecard **26 → 37 assessed sites**.

- **Validator v2 (`--links-only`).** `scripts/validate_moratoriums.py` now has a
  fast, deterministic link-liveness mode: a browser-UA `requests` fetcher
  (falls back to urllib) that follows redirects and classifies every URL as
  **live** (2xx) / **blocked** (403/429/SSL/timeout — real site, bot-walls us) /
  **dead** (404/410/DNS/refused). Only `dead` is actionable; this stops the
  urllib fetcher's 403/SSL false-negatives from reading as broken links.
  `--fail-on-dead-link` is the CI gate; writes `moratorium_link_report.json`
  (git-ignored). A companion **`--completeness`** mode (pure-schema, no network)
  flags records **missing a bill/ordinance #, gov link, vote, or sponsors** — the
  "still missing bill #s / links / specific language" gaps a curator fills before
  shipping (`--fail-on-incomplete` gate). Wrapped in the **`validate-moratoriums`
  skill** (`.claude/skills/validate-moratoriums/`). **The audit's job is link liveness +
  gov-source presence — deterministic and repeatable. Claim-text verification
  stays best-effort** (JS-rendered gov pages defeat any plain fetcher). Use
  WebFetch (gets through bot-walls) to actually fix links; the script can't.
- **Accuracy is a curation act, not just a link check.** The audit surfaced two
  records whose central claim was *false*, not just dead-linked: a Loudoun County
  "ban" (the county only moved data centers by-right→special-exception; no
  moratorium — **removed**) and a Connecticut "2-year >15 MW moratorium" (the real
  bills were a tax-incentive repeal + a co-location rule — **summary corrected**).
  When a source contradicts the record, fix/remove the record, don't just swap the
  URL. Also stripped **55 fabricated/dead `.gov` "resource" links** (a prior gen
  pass hallucinated plausible `.gov` paths). Net honest tradeoff: no-gov-source
  count *rose* (47) because fake gov links were removed — surfaced for future
  curation, not hidden. **Don't fabricate a `.gov` URL to satisfy the gov check.**
- **Moratorium Nation CSV** (`mjbommar.github.io/moratorium-data-2026`) is the
  richest lead source (222 rows) but carries **no per-row source URL** — mine it as
  a work-list, verify a live primary per row, never bulk-import (see BACKLOG).
- **Summary charts (`renderMoratoriumCharts`).** Pure DOM+CSS (no chart lib), so
  they re-theme on the dark swap via CSS vars — no `getComputedStyle` snapshot.
  Three charts above the table: a stacked-column **timeline** (`_morTimelineChart`,
  quarter buckets by `enacted_date||effective_date||captured_at`), and horizontal
  bar sets for **concerns** and **jurisdiction level**. New `--moratorium-{enacted,
  proposed,failed}` tokens (literal in BOTH `:root` blocks per DESIGN.md 12.12),
  reusing the tariff/stance green/amber/red language.
- **Timeline: one combined bar per quarter; jurisdiction level is a FILTER, not a
  second visual encoding.** `colour = status` is the only visual scale. Level lives in
  a segmented toggle (`.mor-toggle`, `MOR_TIMELINE_LEVELS`): **All / City-County /
  State / Federal**, each showing its record count. We tried encoding level as fill
  texture (city solid vs. hatched) and then as parallel bars — both made a small
  chart carry too much, and the parallel version doubled the axis width (see the
  clipping bug below). A toggle is the cheaper answer: one bar, one scale, level on
  demand. If a level split is ever needed *inside* a bar again, add a texture —
  **never** a second colour ramp.
- **The axis range AND y-scale derive from the FULL dataset, never the filtered
  subset.** This is what makes the toggle honest: quarters don't shift when you
  filter (it reads as filtering *in place*), and bar heights stay comparable between
  levels. Rescaling per filter would render Federal's **single** record as a
  full-height bar — as tall as a 58-record quarter. It must read as the sliver it is
  (`test_shared_yscale_keeps_federal_a_sliver`). Segment heights use `Math.max(2, …)`
  so slivers stay visible rather than rounding to nothing.
  What the toggle actually surfaces: **cities enact, states propose and fail** — the
  State view is mostly amber/red where the City/County view is green.
- **`overflow-x: auto` on a time-series chart silently eats the newest data.**
  (Learned when the levels were parallel bars: doubling the bars per quarter pushed
  the axis past the container.) The plot scrolled and **clipped the 2026 surge
  off-screen with no affordance** — it read as "the data is missing," and it shipped
  that way. The safeguards below stay in place regardless of bar count, because a
  long-enough axis will always outgrow a narrow viewport:
  (1) size so the full axis **fits** (a `max-width:560px` media query narrows the
  columns); (2) keep the **scrollbar visible**
  (`scrollbar-width: thin` + a styled `::-webkit-scrollbar`) — a hidden scrollbar is
  how data disappears quietly; (3) **park `scrollLeft` on the most RECENT** column
  after render, so whatever clips is the near-empty past, never the current surge.
  Do the park twice — once inline and once in `requestAnimationFrame` — because a
  chart rendered while its tab is still `display:none` has **zero `scrollWidth`**, so
  the inline call is a silent no-op. Guarded by
  `test_recent_quarters_never_clipped_on_narrow_viewport`.
  Measure clipping with `getBoundingClientRect` against the plot's rect —
  **not** `offsetLeft`, which is relative to the nearest *positioned* ancestor (the
  plot isn't one) and will lie to you.

### New York: an executive order and a bill are SEPARATE records (v1.20)

NY carries **two** moratorium records and they must not be conflated:
- `ny-state-eo62-2026-07` — **Executive Order No. 62**, signed 2026-07-14: the
  nation's **first statewide data center moratorium**. DEC holds pending discretionary
  permits in abeyance for data centers **≥ 50 MW**, until DPS delivers a final Generic
  Environmental Impact Statement. State environmental permitting only — **local permits
  are not covered**. Exempts manufacturing, research (incl. quantum), accredited
  education (incl. Empire AI) and medical care. Empire State Development must post a
  "Community Investment Framework" within 60 days. Primary source is the `.gov` EO text.
- `ny-state-2026-06` — the **legislature's bill**: the Responsible Data Center
  Development Act, **S10642 / A11560** (**20 MW**, 1 year), passed both chambers
  2026-06-04 and **still unsigned** as of 2026-07-26; Hochul issued the EO instead.
  Stays `proposed`.
  **Corrected 2026-07-26:** this section, and the record's own summary, previously
  cited "S7992/A7234". **S7992 is an unrelated New York labor-relations bill** —
  same failure shape as the Oregon HB4016 record (a real bill number attached to
  the wrong subject). REFRESH.md's status-re-check checklist already carried the
  fix ("NY's S7992 was superseded by S10642 after an Assembly substitution") but
  neither the data nor this file was updated to match. When a checklist records a
  renumbering, **grep the seed and the docs for the old number in the same pass** —
  a learning that only lands in the playbook doesn't correct the record.

Lesson: an executive order and a bill are different instruments with different
thresholds and different fates. When a governor "acts," check *which* instrument —
don't flip the bill record to `enacted` because an EO landed the same day.
- **PDF export redesign.** `exportMoratoriumsToPDF` builds a typographed document
  (`.mpdf-*` scoped `<style>`): serif display cover + kicker/dek, color-topped stat
  tiles, mini-bar summaries, a zebra directory table with status pills, and
  per-record detail cards each with a **sources list** (primary + resources, full
  URLs). html2canvas rasterizes, so colors are **hardcoded light-theme hex** (it
  won't resolve app CSS vars) and `scale: 1.6` + `jpeg 0.9` + `jsPDF compress`
  keeps a ~90-record export near ~9 MB instead of ~18 MB at scale 2.

### Ratepayer: individual-vs-general basis + conflict surfacing (v1.20)

Answers the two questions "was this site claimed individually or only company-wide?"
and "has any report come out that conflicts with meeting the pledge?"

- **Claim-basis badge (`rpClaimBasis`/`rpBasisBadgeHtml`).** Derived from whether a
  site-specific `evidence_claim_id` backs the record: **individual** ("Claimed
  individually") vs **company-wide** ("Company-wide pledge only"). Rendered in the
  always-visible card header. `affirmed` and `contested`-with-evidence read as
  individual; `pledge_only` reads as company-wide.
- **Conflicting reports (`rpConflictingReports`/`rpConflictsHtml`).** Surfaces
  negative `CommunityResponse`s about ratepayer cost-shift on **any** card
  (affirmed / pledge_only / contested) — a header **"⚠ Ratepayer concern"** flag +
  an expandable block listing each finding with its source. **Matching is
  id-based-first: a response whose id contains `ratepayer` is a curated conflict**
  (both the Synapse contested-site responses and the added regulator/report
  conflicts use that convention), with a keyword fallback (`RP_CONFLICT_KEYWORDS`).
  Keyword-only matching missed the Georgia PSC conflict ("shift costs onto
  residential customers" has no exact keyword) — the id tag is the reliable signal.
  Summaries note when a finding is **system/utility-wide** (Georgia Power fleet,
  Dominion cluster) rather than pinned to the one site — don't overclaim
  site-specific dispute.
- **Strict first-party bar for `affirmed`.** An `affirmed` Claim must be the
  *company's* words. A utility ESA quote (Minnesota Power's COO on the Google
  Hermantown site) is **not** first-party to the company → recorded as
  `pledge_only`, not `affirmed`. A named-company-exec quote in a trade outlet, or a
  quote attributed to the company itself, **is** first-party (Google's Wilbarger
  exec quote; Microsoft's Pecos statement) → `affirmed`.
- **New assessments:** 10 previously-unassessed pledge-era sites (7 affirmed w/
  backing Claims + 3 pledge_only) + one new post-pledge site (`microsoft-pecos-tx`,
  affirmed) + 3 conflict responses (Louisiana/Meta-Hyperion→meta-richland-la,
  Georgia-PSC→google-lagrange-ga, Dominion/JLARC→google-chesterfield-va).

### Launch / preview ritual + performance (v1.20)

The in-app **browser pane renders at a 0×0 viewport in some environments** (blank
no matter what; `navigate` often denied). Don't rely on it. To launch/preview:

- **Interactive, shareable:** `python3 tools/build_preview.py --verify` bundles the
  whole SPA into a self-contained `.preview/dashboard.html` (inlines styles.css,
  embeds every `data/*.json`, patches `fetchJson` to read the embedded data), then
  **publish that file as an Artifact**. Runs fully client-side; only the lazy Leaflet
  map (Explorer) + html2pdf export break under the artifact CSP — every other tab works.
- **Quick visual check:** headless Playwright — self-serve `docs/` with `http.server`,
  click a tab, `screenshot`, `SendUserFile`.
- **Do this on every new commit / PR.** `.githooks/post-commit` auto-rebuilds the
  bundle (needs `git config core.hooksPath .githooks` per clone; `.preview/` is
  git-ignored). The Artifact *publish* is a manual (Claude) step — a git hook can't do it.

**Performance baseline (GitHub Pages, gzipped/CDN):** first paint FCP ~340 ms · 6
requests · ~202 KB. Code-splitting works — first paint loads only index + styles +
app.js + the preloaded `companies.json`/`claims.json`; `projects`/`responses`/
`moratoriums`/`tariffs` lazy-load per tab. No images or web fonts (system stack).
**Keep it that way:** no web fonts, no un-optimized images, keep new heavy data
lazy-per-tab (never preload it). Regression signal: first paint > ~500 KB or > ~12
requests. Optimization ideas in [BACKLOG.md](BACKLOG.md).

### ISSUES.md is GENERATED — bugs do not go there

`ISSUES.md` is a **refresh.py output** (`--audit`), regenerated on every run: a
prioritized list of *data* gaps (missing `power_mw`, stale `proposed` bills).
The universal convention at the top of this file — "maintain a living issues.md
as an audit trail" — does **not** apply to this project's copy: anything
hand-written there is erased on the next refresh.

Code bugs, root causes and fixes go in the **commit message** (which is where
this project's real bug history lives) and, when they carry a reusable lesson,
in this file. Deferred work and leads go in `BACKLOG.md`. Don't hand-edit
ISSUES.md.

### Signatory registry — the breadth tier (v2)

On 2026-07-23 the pledge went from 8 organizations to 200+. `Signatory` +
`signatories.json` track them. **Two tiers, deliberately:**

- **`Company`** — depth. 13 slugs, each with curated claims, projects, a written
  summary. Adding one still requires the two-gate editorial test.
- **`Signatory`** — breadth. Every roster row, carrying only what the roster
  publishes (name, category, domain, track, date). `matched_company_slug`
  bridges the two.

**Don't** expand `companies.json` to hold the roster. It breaks the company
rule, explodes `COMPANY_SLUGS`, and implies we have researched 279
cooperatives. The thin record is the honest shape.

`scripts/build_signatories.py` builds the seed from the White House page
(`--cached` to parse the cache, `--diff` to preview adds/removals). Idempotent:
an unchanged page produces a byte-identical file, so any diff means the roster
actually moved. **It never auto-deletes** — a removal is news; `--diff` surfaces
it for a curator.

Two integrity lessons from building it:

- **The source page disagrees with itself.** On 2026-07-25 its filter chips
  advertised 281 organizations / 69 utilities while the list underneath held
  279 / 68. Both are stored — ours derived from the list, theirs verbatim in
  `roster_counts_stated` — and `drift_note` states the gap in reader-facing
  words, surfaced in the UI (`#rp-drift-note`). **Don't** silently pick one;
  reconciling a source's self-contradiction is inventing a fact.
- **Two distinct co-ops share a name.** "Southeastern Electric Cooperative"
  appears twice on different domains. The first parser deduped by slug and
  silently dropped one. It now disambiguates by domain and *raises* rather than
  dropping a row it cannot tell apart. Any dedupe over an external list needs
  the same shape: disambiguate or fail, never drop.

Governors are signatory records too (`category: "governor"`, `state` required,
sourced to the RGA release) so the state panel gets its governor row for free —
but their `notes` must record that they signed an **addendum**, not the
corporate pledge, and `test_governors_are_not_conflated_with_corporate_signatories`
enforces it.

`utility_aliases` maps tariff `utility` strings onto roster rows. **Exact
matches only, hand-curated** — AEP Ohio and AEP Texas are different companies
and no fuzzy matcher is trusted to know that. Where a holding company signed
and the tariff names its subsidiary (Berkshire → NV Energy, Exelon → ComEd,
WEC → We Energies, MDU → Montana-Dakota), the record's `notes` says so rather
than flattening the two. Coverage is 20/25 tariffs; the 5 unmatched are four
statewide frameworks and one federal FERC case — genuinely unmatchable, and
reported rather than forced.

Vocab mirrors to app.js as `SIGNATORY_CATEGORIES` / `SIGNATORY_TRACKS` (+ label
maps), parity-tested. Note the deliberate split from the source page: it files
all data-center companies under one "DATA CENTER" chip; we re-tag the seven
March-round buyers as `hyperscaler` because a company buying power and a
developer building the shell answer different questions here.

### Roster-driven eligibility (v2 — supersedes the flat pledge date)

**A site is assessable only if its operator had already signed when the site was
announced.** Before v2 this compared every project against the single White
House date, which mislabels the July cohort: a CoreWeave site announced in May
2026 predates CoreWeave's own signature by two months and cannot be measured
against a pledge that company had not yet made.

Both sides read per-company join dates from the roster:
- `refresh.py` — `_signatory_dates(signatories)` → `_is_ratepayer_eligible(p, signed_dates)`
- `app.js` — `projectPledgeDate(p)` → `isPrePledgeProject(p)`

`projectPledgeDate` falls back to the White House date while the roster payload
is still in flight, so a cold deep-link doesn't briefly render every site as
non-signatory.

The pre-pledge bucket now carries **two** reasons, and `prePledgeNote()` says
which: a 2024 Meta site predates a pledge that existed before we tracked it; a
May 2026 CoreWeave site predates *its own operator's* signature. The second is
not a gap in follow-through — it is outside the window. **Don't** collapse them
back into one label.

### Pledge-first landing + civic palette (v2; tab placement revised in v2.1)

`#overview` is the **default view** (`DEFAULT_VIEW_NAME` in app.js, hoisted
above `state` because `state` initializes from it and would otherwise hit the
temporal dead zone). Comparison gained an explicit `#comparison` hash — it had
been the bare-root view, and demoting it without one would have left it
un-linkable.

**v2.1: the landing band moved from header chrome into its own "Overview" tab.**
Originally (v2) the band sat above the tab bar, inside `<header>`, on every
view — which meant the tab bar itself was pushed below the fold on load and
needed a scroll to reach. It now lives in `#view-overview`, a normal `.view`
section in `<main>` selected by `#tab-overview`, the first tab and the new
`DEFAULT_VIEW_NAME`. `#ratepayer` (the pledge's own tab: commitments, coverage,
roster, scorecard) is no longer the default — it's one click away, same as
every other tab. The header is now just the title row + tab bar, so every tab
is reachable without scrolling regardless of which one is active.
`activateView()` triggers the same `loadRatepayerView()` loader for both
`"overview"` and `"ratepayer"`, since the Overview tab's stat tiles / coverage
bar / meters / state strip need the identical projects + signatories +
coverage payload the Ratepayer tab does — there's no separate fetch path to
keep in sync. `.topbar` is not `position: sticky` (only `.tabbar-sticky` is);
that stayed true across both layouts.

**It is not four stat tiles.** An early cut was, and four numbers said nothing
about shape. It now carries a proportional roster bar (the coalition is 63%
rural co-ops), per-commitment meters (how thin the site evidence still is), a
50-state strip (how partial coverage is), and a dated activity feed. Every
figure renders from data — `test_landing_numbers_come_from_data_not_markup`
asserts no roster count is baked into `index.html`, because the roster moves.

**Palette: cool paper / near-black ink / one deep signal blue.** The first cut
adopted the source page's cream-and-gold and read as a consumer AI product;
this is a public record. What carries the reference is the *structure* — Roman
numeral commitments, letterspaced kickers, display serif. Token names changed:
`--accent-gold` / `--accent-gold-bright` / `--band-gold` are gone, replaced by
`--accent-mark` (text-safe) / `--accent-rule` / `--band-accent`.

**Compute contrast, don't eyeball it.** The source page's ochre is 2.96:1 on its
own cream — below both the 4.5:1 small-text and 3:1 large-text floors. It was
in the spec as `--accent-gold` and would have shipped unusable. Every token in
the current palette was checked before landing.

`--font-display` is a **system serif stack**; the no-web-fonts guardrail is now
enforced by `tests/test_perf_budget.py`, not just documented.

The global `h4` rule sets `text-transform: uppercase` + sans + muted. Any new
display heading using `<h4>` must override all three (`.rp-commit-title`,
`.rp-subhead` do) or it renders as an eyebrow label.

### First-paint budget is now a test (v2)

Making Ratepayer the landing view pulled projects + responses + the roster into
first paint: **~141 KB → ~237 KB gzipped across 8 requests**, inside the 250 KB
/ 8 guardrail but with little headroom. The old ~202 KB / 6 baseline in this
file described the Comparison landing and no longer applies. (v2.1: the default
view is now Overview, not Ratepayer, but the budget is unchanged — Overview
shares Ratepayer's `loadRatepayerView()` loader and needs the identical
payload, so nothing below moved.)

`tests/test_perf_budget.py` gates it. **When it fails, make the new payload lazy
— don't raise the ceiling.** This has already been exercised once: P5 took it to
246.5 KB, and the fix was splitting `responses.json` out of `loadProjectData`
into its own `loadResponseData` (**back to 203.9 KB / 7 requests**). Responses
only decorate below-the-fold concern flags, so the Ratepayer view paints from
projects and re-renders the scorecard when they land; Explorer and Aggregate,
which render response *content*, await both. `loadRatepayerView` **awaits** the
late fetch before firing `dcb:ratepayer-ready` — several e2e tests and the
concern-first sort treat that event as "the view is complete". Sizes are measured gzipped because that is how
Pages serves them, and raw bytes flatter JSON enormously (signatories.json is
121 KB raw, 8 KB gzipped).

### `Moratorium.state_code` (v2)

Explicit field, backfilled for all 102 records. The spec expected to parse a
`", TX"` suffix off `jurisdiction`; **no record has one** — `jurisdiction` is a
bare place name ("Baltimore", "Cave City") and the id only sometimes carries a
code. 81 were derivable from the id or a state-name lookup; **20 needed hand
verification against each record's own source**, because city names are
ambiguous (Madison, Smithfield and St. Charles each exist in several states).

A payload validator rejects any non-federal record without one. That matters
because the failure mode is silent: a missing code doesn't error anywhere, the
record just stops appearing in its state's panel, which reads as "no
moratoriums here" rather than as a data gap.

### State panel (v2)

Deep-linkable at `#state/XX`, following the tariff-modal pattern exactly
(backdrop, Escape, focus trap, return-focus). Assembled entirely from records
collected for other views — no new record type backs it.

- It **lazy-loads moratoriums + tariffs on open**, because a visitor can arrive
  from the landing band without ever having opened those tabs, and a panel
  showing "no tariffs" because the payload had not loaded would be a lie.
- **Every section renders even when empty.** AK / MT / SD have a governor
  signature and nothing else; that *is* the answer and is stated, not hidden.
- **Read the state code from the hash BEFORE calling `activateView`** — it
  rewrites the hash to `#ratepayer`, so reading afterwards yields `"yer"`. This
  cost a debugging cycle.
- `"XX"` is the sentinel a few records use for virtual / multi-site
  partnerships with no physical location. It must never become a state chip
  (`NON_GEOGRAPHIC_STATE` in app.js).

### e2e: the comparison pane is hidden by default now (v2)

28 tests broke at once on `wait_for_selector("#matrix-body tr")` — the rows are
in the DOM but the pane is `hidden`, so the default `state="visible"` wait times
out. This is the same trap CLAUDE.md already documents for the Community pane.
Those tests now navigate to `/#comparison`, which is also what a real reader
does. **When you change which view is default, every test that `goto("/")` and
then waits on another view's DOM will fail — route them through the hash rather
than loosening the wait.**

### One section language, one accordion (v2.2)

Every tab had grown its own section chrome. Five heading scales
(`.summary-section > h3` — which had **no CSS rule at all** and just inherited
the global serif h3; `.agg-section-heading` at 1.05rem sans; `.hot-rail-title`
at 1rem sans; `.matrix-help` with no heading; `.rp-section > h3` at 1.1rem) and
**three unrelated `<details>` skins** (`.directory-section` a filled button bar,
`.china-context-section` an accent-left callout, `.rp-roster-details` a bare
bold summary). Six tabs that read as six products.

The Ratepayer view's shape won — display serif at **400** weight, muted 64ch
dek — and everything else is aliased onto it in the SECTION LANGUAGE block in
[styles.css](docs/styles.css). Legacy class names were aliased rather than
renamed so no JS selector or test id had to move; the ones that ended up with
**zero** remaining markup (`.summary-section`, `.view-description`,
`.agg-section`, `.agg-section-heading`) were then deleted outright.

**`.acc` is now the only collapsible-section component.** Markup contract:

```html
<details class="acc" [open]>
  <summary><h3 class="acc-title">…</h3><span class="acc-count"></span>
           <span class="acc-chevron" aria-hidden="true"></span></summary>
  <div class="acc-body">…</div>
</details>
```

Five rules that are load-bearing:

- **The heading goes INSIDE the `<summary>`.** `<details>`/`<summary>` supplies
  the expand semantics natively (no `aria-expanded` bookkeeping), and the inner
  `<h3>` keeps the section in a screen reader's heading list. Don't hoist it out.
- **Never put a button in the `<summary>`.** A click anywhere inside a summary
  toggles the panel — the old `.directory-section` shipped its CSV/PDF buttons
  there and collapsed the table out from under the reader on every export
  click. Toolbars go in `.acc-body`; `.table-controls` is styled for exactly
  that.
- **`setAccCount(id, n, singular, plural, note)`** writes the summary chip so a
  *collapsed* panel still says how much is inside. **Only a non-number clears
  it** (`Number.isFinite`); `0` renders as "0 records" — see "Zero is a result;
  missing is not" below. Pass `plural` for anything that doesn't take a bare
  `+s`; the first cut shipped "302 signatorys" and "13 companys". Pass `note`
  for a count sourced from an external list, which must carry its as-of date.
- **`openAccordionsFor(node)` before any programmatic scroll.**
  `goToPledgeTarget()` calls it, because a smooth-scroll to a collapsed section
  lands on a closed bar and reads as a broken link. It walks *all* ancestors, so
  a nested accordion opens too.
- **Collapsing a section breaks every e2e test that waits on its contents.**
  Same hidden-pane trap CLAUDE.md already documents twice (Community pane, v2
  comparison default): children of a closed `<details>` are attached but not
  painted, so `wait_for_selector` needs `state="attached"` and
  `inner_text()` returns `""` — read `text_content()`, or click the summary
  first when the test is about what the reader sees.

**The pledge band is collapsed by default** (`.acc--band`, the dark variant with
band-palette hairline and marker). The five commitments are reference material a
returning reader has already read; the live content below is what they came back
for. `test_commitments_render_as_the_pages_spine` asserts the collapsed default
*and* that expanding works, so flipping it back is a deliberate act.

`#hot-rail` deliberately did NOT become an accordion: it renders only when
contested sites exist, and a collapsible whose whole existence is conditional
reads as a bug when it vanishes.

### Sub-tabs are for alternatives; accordions are for sequences (v2.2)

`.subtabs` / `SUBTAB_GROUPS`. The rule that decides which to reach for:

> **Would a reader ever want two of these on screen at once?**
> Yes → accordion. No → sub-tab.

Sub-tabs exist in exactly **two** places, and `test_only_two_subtab_groups_exist`
guards that number — a third group has to argue against the test above:

- **Ratepayer → "Tracked sites"** — Assessed / Awaiting assessment / Before the
  pledge / Never signed. These were four sibling sections; they are four
  *bucketings of one site list*.
- **Aggregate** — By company / By signatory category / By state. Three rollups
  of the same numbers.

The Moratoriums and Tariffs tabs kept accordions on purpose: you read the charts
**and** the directory. Sub-tabs there would hide half the tab from Ctrl-F and
from the PDF exports, which walk the DOM.

Mechanics, mirroring `DETAIL_TABS`:

- **Everything iterates `SUBTAB_GROUPS`.** Adding a cohort = markup + one array
  entry. Ids are conventional: `subtab-<group>-<key>` / `subpane-<group>-<key>`.
- **`setSubtabCount()`, not `setAccCount()`.** A pill is a bare number;
  "39 sites" is right in an accordion summary and far too wide in a tab.
  The accordion summary above the strip carries the **combined** total, so
  collapsing it doesn't hide the count entirely
  (`test_accordion_summary_totals_every_cohort` pins summary == sum of pills).
- **Panels toggle via the `hidden` attribute**, and `.subtab-panel` sets
  `display: block` — safe only because the global `[hidden]` rule carries
  `!important`. See the `[hidden]` trap.
- **Arrow keys move between tabs**, per the ARIA tablist pattern.
- **Collapsing content into a sub-tab breaks every e2e test that waits on it**,
  same as accordions — four aggregate tests failed at once here. Fix by
  clicking the sub-tab (what a reader does), not by loosening the wait.

**The "Show non-signatory companies" checkbox is gone**, replaced by the
"Never signed" sub-tab. CLAUDE.md previously called that checkbox the documented
opt-in-reveal shape; a sub-tab is the same opt-in (Assessed is the default, you
have to choose the cohort) while sitting where cohorts actually compare. The
scope rule it protected is unchanged and enforced where it always was —
`_is_ratepayer_eligible` / `isPrePledgeProject` still refuse to attach a
`ratepayer` assessment to a non-signatory site.

### The Ratepayer view's own stat row is gone (v2.2)

`#rp-stats` / `renderRatepayerStats()` — "N signatories tracked in depth / sites
assessed / site-specific commitments" — was removed, along with the
"Companies tracked in depth" roster (`#rp-tracked-roster` /
`renderRatepayerRoster()`) under Coverage. Both predated the v2 roster expansion
and reported numbers the Overview landing band now reports better and
roster-wide. `companyHasRatepayerClaim()` and
`RATEPAYER_DOE_TRACK_SIGNATORIES` died with them (the roster record's own
`signed_track` is the source of truth for which track a company signed on).
`RATEPAYER_CLAIM_KEYWORDS` survives — it still backs the company-wide claim
fallback on scorecard cards.

Four e2e tests went with them. **Don't reintroduce a per-view stat row that
restates roster figures**: two places reporting the same count is how the
"11 signatories" tile sat stale through an expansion that tripled the roster.

### The pledge's five commitments are quoted, and were paraphrased (v2.2)

`PLEDGE_PRINCIPLE_DESCRIPTIONS` in app.js now holds the **verbatim** body text
from the White House pledge, re-fetched and re-verified 2026-07-28. It held
paraphrases until then, and two had drifted in the direction that flatters the
pledge:

- **`separate_rate`** claimed companies pay "for the power and infrastructure
  brought online, used or not." The source body says only that they will
  *negotiate separate rate structures*. The pay-anyway framing is that section's
  **title** — we were quoting the headline back as if it were the commitment.
  Same failure shape as the Loudoun "ban" lesson: a headline's strong word is
  not the underlying action.
- **`grid_resilience`** dropped the source's "whenever possible" hedge on backup
  generation, turning a qualified commitment into an unconditional one.

`test_commitment_text_is_verbatim_from_the_pledge` pins all five strings, so
re-tightening them into snappier lines is a deliberate edit to the test file.
If a layout needs them shorter, shorten the layout — `PLEDGE_PRINCIPLE_SHORT`
already exists for exactly that. The band's footnote now reads "titles **and
text** quoted verbatim".

Titles were already verbatim and stay so, modulo case: the source uses Title
Case, the dashboard renders sentence case throughout, and
`test_commitment_titles_are_the_pledges_headings` compares casefolded.

`PLEDGE_PRINCIPLES` / `PLEDGE_PRINCIPLE_LABELS` were mirrored Python↔JS with
**no parity test** — the only mirrored vocabulary here that lacked one. Now
guarded by `test_pledge_principles_match` / `test_pledge_principle_labels_match`.

Note the pledge's five commitments and the dashboard's eight `THEMES` are
**different axes** and are not being reconciled: THEMES is the community-benefit
taxonomy (jobs, water, education…), the commitments are ratepayer-cost
obligations. Don't map one onto the other.

### Universal lessons learned here (mirrors the canonical CLAUDE.md)

Promoted to `~/Projects/coding-best-practices/CLAUDE.md` in the same pass, and
repeated here because this is the file that actually loads in this directory.

- **A click anywhere inside `<summary>` toggles the panel**, so a button in a
  collapsible header fires *and* collapses the section. Toolbars go in the body.
  The old `.directory-section` shipped its CSV/PDF buttons in the summary.
- **Aliasing legacy class names onto a new shared rule only works if the shared
  rule wins the cascade.** `.hot-rail-title` / `.hot-rail-sub` sat later in the
  sheet and silently re-won, so the Explorer heading kept rendering a size
  smaller than every other tab while the new rule looked "not applied". Grep and
  delete the redundant declarations; a selector with zero remaining markup is
  dead code (four were, one referencing a `--text-secondary` that no `:root`
  defines).
- **A styled `<span>` standing in for a heading is invisible in review and in a
  screenshot.** The pledge band's `<h3>` became a `<span>` during the accordion
  conversion and dropped out of the document outline. Wrap in a `<div>` (a
  `<span>` can't legally contain a heading) and guard with
  `test_every_accordion_header_is_a_real_heading`.
- **Hiding content behind a disclosure or tab breaks every test that waits on
  it** — attached but not painted, so `state="visible"` times out and
  `inner_text()` returns `""`. Click the disclosure rather than loosening the
  wait. Third time this project has paid for it (Community pane → v2 comparison
  default → accordions + sub-tabs).
- **`page.goto(base + "#hash")` does not reload an SPA**, so hash routing never
  fires; successive fragment-only `goto`s are same-document navigations. The
  screenshot harness silently captured four un-rendered tabs. Use
  `/?i=<name>#hash` or `reload()`.
- **A source's heading routinely claims more than its body supports — quote the
  body.** See the commitments section above for this project's instance.
- **Never assert a layout measurement against an exact pixel floor.** A
  `min-height: 44px` sub-tab measures `43.999969...` in Playwright's
  device-scaled mobile context, so `height < 44` failed ~1 run in 5 on correct
  CSS and read as flake. `TOUCH_FLOOR_PX - 0.5` in
  `TestTouchTargets`; mutation-checked that 39px still fails.
- **`set_viewport_size` does NOT make `(pointer: coarse)` match** — only a
  context with `is_mobile`/`has_touch` does. Every other mobile test in this
  repo resizes the viewport, so all of them silently measure the *desktop*
  rule. Any test about touch behaviour needs a real touch context, and needs to
  assert the media query engages before trusting its numbers
  (`test_coarse_pointer_emulation_actually_engages`).

### A guard's SCOPE rots exactly like any other hand-written list

`tests/test_no_dead_css.py` started with an allowlist of "project-owned"
class prefixes. Codex pointed out it omitted whole families — `claims-` and
`chip-` were never in the list, so `.claims-section`, `.chip-row` and seven
others sat dead and *certified clean*. This is CLAUDE.md's own
single-source-of-truth lesson landing inside the tool written to catch drift,
for the fourth time in this project.

Now inverted: scan **every** class in styles.css, exclude a short denylist of
third-party prefixes (`leaflet`). A denylist is obvious when it needs an entry;
an allowlist is silent when it doesn't have one.

Two live classes were false-positived on the way, both from interpolations
carrying their own quotes:

```js
class="mor-toggle-btn${active ? " is-active" : ""}"
class="at-a-glance-text${isCurated ? " curator-override" : ""}"
```

A `class="(.*?)"` regex stops at the quote before ` is-active`. The fix is a
depth-tracking scanner (`_class_attr_values`) plus harvesting class names from
*inside* the interpolation's string literals — `curator-override` only ever
appears there. Leaflet's `L.DomUtil.create("div", "map-legend")` needed teaching
too.

**The pattern across all four rounds of this guard**: every time it was
tightened it produced false positives on known-good code, and every time the
loosening that fixed them had to be checked for re-opening the original hole.
Budget for that; a scanner is not a one-line test.

### Zero is a result; missing is not

Both count helpers cleared their chip on a falsy value, so `0` and "hasn't
loaded" rendered identically — blank. A directory filtered down to nothing lost
its "0 records" the moment the reader collapsed the section, which is exactly
when the chip is the only thing left saying anything. `Number.isFinite(n)` is
the check; only a non-number clears.

This is **not** in tension with the project's honest-absence rule (`renderRatepayerStats`
deliberately omitted a zero "contested" tile). The distinction: a stat tile's
*existence* asserts a finding, so a zero one manufactures one. A count chip
answers "how much is inside this section", and `0` is a true answer to that.

### Check the spec with a validator, not from memory

Codex flagged the accordion summaries as non-conforming, claiming both the
`<div>` wrapper **and** the `<h3>`-beside-spans pattern were invalid. Running
`docs/index.html` through the W3C Nu validator settled it in one call:

```
curl -sS -H "Content-Type: text/html; charset=utf-8" \
  --data-binary @docs/index.html "https://validator.w3.org/nu/?out=json"
```

The `<div>` was a real error ("Element div not allowed as child of element
summary"); the h3-with-sibling-spans pattern drew no complaint — `<summary>`
takes phrasing content *optionally intermixed with heading content*, which is a
spec change I'd have got wrong from memory in either direction. The kicker moved
inside the `<h3>` (which does take phrasing content), so no wrapper is needed.

**The same call found 22 pre-existing errors nobody had looked for**, four of
which are `aria-label` on a bare `<div>` — silently ignored by AT, so four
regions a screen-reader user hears unlabelled. Logged in BACKLOG.md, not
widened into that PR. Worth wiring into CI so the count can only go down.

`test_summaries_contain_only_conforming_children` is the offline proxy, scoped
to `details.acc > summary` so it doesn't fail on the 39 pre-existing
`.rp-card-details` summaries that have the identical defect.

### A "does this name appear anywhere?" check is not a usage check

`tests/test_no_dead_css.py` v1 asked whether a CSS class name appeared as a
substring of index.html + app.js. Codex pointed out that an **id** of the same
name answers yes: `.rp-commitments` had three orphaned rule blocks and the
guard passed on the strength of `id="rp-commitments"` sitting on an element
whose class is `rp-commit-list`. A guard that accepts an id as evidence of a
class certifies exactly what it cannot see.

v2 parses class *application* sites — `class="..."`, `className =`,
`classList.add(...)`, and this project's `el(tag, "classes")` helper. It found
two more dead selectors immediately.

**Tightening a guard needs its own false-positive pass.** The stricter version
initially reported `.mor-toggle-btn` and `.rp-state-chip` as dead, and both are
live. Cause: the interpolation contains its own quotes —

```js
class="mor-toggle-btn${active ? " is-active" : ""}"
```

— so the `class="..."` regex stops at the quote before ` is-active` and the
captured value ends mid-expression. Substituting only well-formed `${...}` left
`mor-toggle-btn${active` as a literal class name. Any residual `${` now
truncates the token to a stem. **Run a newly-strict check against known-good
code before trusting its output**; a guard that cries wolf gets disabled.

### A guard can inherit the exact blind spot of the bug it guards

`goToPledgeTarget` failed to open the signatory roster because
`openAccordionsFor()` walks **ancestors**, and the roster's `<details>` is a
**child** of the `#rp-roster-section` the target pointed at. Codex caught it.

The test written to guard the whole `PLEDGE_TARGETS` table then used
`el.closest('details.acc:not([open])')` — which also only looks *upward*.
Reverting the fix left the new test **green**. It was only caught by mutating
the fix away, which is the whole argument for doing that on every new
assertion. The guard now checks self + ancestors + descendants.

Generalizes: when you write a test for a directional bug (upward/downward,
before/after, inner/outer), the obvious API for the check usually shares the
bug's direction. Mutate the fix away and watch the test go red, or you have
written the bug twice.

Related, same review: `test_only_the_active_subtab_is_in_the_tab_order` passes
from the authored HTML alone, so deleting the `btn.tabIndex` line in
`setActiveSubtab` does **not** turn it red — `test_tab_order_follows_selection`
is what covers the JS half. Both docstrings say so. **Two tests that look like
one guard can each cover a different half and neither cover the whole.**

### The documented `<details>` display-override trap did NOT reproduce here

The base CLAUDE.md warns that an author `display:` rule on a direct child of
`<details>` outranks the UA rule hiding a closed panel. Mutation-checked in this
project's Chromium: adding `.acc-body { display: grid }` **and** deleting the
`.acc:not([open]) > :not(summary)` safeguard left the panel correctly hidden and
the test green. Current Chromium hides closed content via the slot, not a
defeatable `display: none`.

Both stay: the CSS rule as defense for engines where it does bite, and
`test_closed_accordion_does_not_paint_its_body` as the weaker assertion it can
honestly make — its docstring says so explicitly. **The transferable bit is the
method, not the result:** the test looked like a guard on that trap and would
have been believed. Mutating the code to make a new assertion go red is the only
way to know which of your guards are real (base CLAUDE.md > "a green test you
have never seen go red is a hypothesis").

### Rate cases — the proceeding layer under the tariffs (v3)

`RateCase` + `data/seed/rate_cases.json` (builder: `scripts/build_rate_cases.py`,
idempotent — edit it, re-run, then `python3 refresh.py`). A tariff is the
instrument; a rate case is the fight: the docketed PUC/PSC/FERC proceeding where
who-pays-for-data-center-load actually gets decided. Separate record type
because several cases exist in states with no tracked tariff, one tariff can
accumulate proceedings over its life, and `next_milestone` needs a home.

- **`next_milestone` is regulator-announced steps only, never a guess** — the
  schema description says so and the Home "What's next" list renders it
  verbatim. A milestone with only a season/quarter stays in the text field;
  `next_milestone_date` is for a specific announced day.
- **Statuses `pending|approved|rejected` render with the tariff palette**
  (pending shares the `proposed` amber) via `RATE_CASE_BADGE_CLASS`; the
  badge-class map is parity-tested against the status vocab so an unmapped
  status can't silently fall back to a colorless badge (the `badge-reason-*`
  failure shape).
- **Deferred-tier payload**, like `responses.json`: fetched by
  `loadRatepayerView` after first render, never preloaded — first paint stays
  at 8 requests. `tests/test_perf_budget.py`'s DEFERRED list records it.
- **Cross-refs validated at refresh time**: `related_tariff_id` must exist in
  tariffs, `related_project_ids` in projects. `coverage.json` now carries
  per-state `rate_cases` counts (federal `US` rows excluded from state cells).
- **Verify sources by fetching, and .gov order PDFs by reading them.** Two
  orders were text-extracted (zlib-decompress the PDF streams, grep the Tj/TJ
  text operators) to confirm dates/thresholds/parties before shipping: MO
  ET-2025-0184 (75 MW, issued 2025-11-24, effective 2025-12-04, Amazon/Google
  as signatory intervenors) and IN Cause 46362 (Amazon special contract dated
  2025-09-18). A state PUC **legal notice in a local paper is a dated primary
  source** — the PUCN notice for Docket 26-06023 is where 'Callisto
  Enterprises, LLC ("Google")' is the Commission's own identification.
- **Search synthesis will hand you the wrong docket.** "Georgia Power's 2025
  rate case, docket 44280" came back from search; fetching the PSC docket page
  showed 44280 is the **2022** rate case (still Open — the 2025 freeze
  stipulation extends that plan). Same v1.19 lesson, docket-shaped: fetch the
  docket page before storing a docket number.
- **.gov press URLs rot fast; dockets don't.** The MO PSC press release
  (pr-26-40) and DeKalb's agenda PDF both 404'd within months of publication.
  Cite the EFIS/docket-system URL (or the order document itself) as
  `source_url`; press releases go in `resources` if anywhere.
- **`utility_aliases` now joins three surfaces** — tariff, rate-case, and
  project `serving_utility` strings all resolve through the same hand-curated
  map (`test_utility_aliases_resolve_to_real_records` widened accordingly; the
  dead-alias guard rejected a speculative bare "NIPSCO" immediately, which is
  the guard working). The aggregate **By utility** rollup groups by resolved
  roster row, else verbatim string; display shows the roster (parent) name
  only when a group genuinely spans multiple operating utilities (Duke IN +
  Carolinas), keeps the operating name for single-string rows (SWEPCO stays
  SWEPCO), never fuzzy-matches.

### IA v3 — Home as the record's front door (2026-08-03)

Tab labels changed, **hashes did not** (deep-link compatibility): Home
(`#overview`, default) · The Pledge (`#ratepayer`) · Companies (`#comparison`)
· Moratoriums · Tariffs & Rate Cases (`#tariffs`) · Sites (`#explorer`) · By
State & Company (`#aggregate`). Home is no longer pledge-only: new
masthead/dek introducing all five record types, a **"What's next"** list
(dated docket milestones, soonest first — the user question the dashboard
exists to answer), the activity feed, and five reader paths (added: rate
watchers → `ratecases` target, planners → `moratoriums` target). The tariffs
tab gained the rate-cases section; the state panel a fifth section (e2e
updated 4 → 5); the aggregate a fourth sub-tab (CSV/PDF exports cover it —
the derived one-section-per-subtab e2e test caught the gap the same day it
was created, exactly as designed).

### Civic palette v3 — whitehouse.gov, contrast-computed (2026-08-03)

The user directed the theme to follow whitehouse.gov's colors and type. The
palette was **extracted from the live site's own CSS presets** (browser
`getComputedStyle` + stylesheet walk), not eyeballed: deep navy `#0D132D` /
`#151A30` / `#141F4D`, charcoal ink `#293340`, signal red `#B50000`, amber
`#FFBD00`, stone `#E8E6E0`, pale-gray `#D9DEE8`. Every text pairing was
contrast-computed before landing (red on white 7.08:1; amber on white 1.68:1
— so **amber is a mark color on light surfaces and a text color only on the
navy band**, where it hits 10.9:1; dark-mode muted 7.28:1). Dark mode is the
navy family, not gray. Fonts: whitehouse.gov uses Instrument Serif/Sans —
the stacks now **name those first and fall back to system faces**, which
costs zero bytes and engages when a reader has them installed; the no-web-font
budget test still enforces no `@font-face`. If the user later wants the real
faces, two self-hosted WOFF2 subsets (~60 KB, +2 requests) are the price —
that is a deliberate budget decision, not a default.

### Per-signatory deep dives — plan only, not built

[SPEC_SIGNATORY_PAGES.md](SPEC_SIGNATORY_PAGES.md) proposes `#signatory/<id>`
pages for all 302 roster rows, a stored `SignatoryCuration` work ledger, and a
REFRESH.md "Signatory sweep". **Nothing in it is implemented.** The load-bearing
constraint it works around: 291 of the 302 rows hold only what the roster
publishes, so a page titled "deep dive" over six fields is a lie told by layout
— curation state has to be stored and rendered, not implied. Read it before
starting any per-signatory work.

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
