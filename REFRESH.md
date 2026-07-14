# REFRESH.md — Data Center Community Benefits data refresh playbook

> Project refresh playbook, read by the generic `data-refresh` skill (~/.claude/skills/data-refresh). Keep current: every refresh run appends learned patterns; structural pipeline changes get edited into the body.


**Purpose:** Systematically refresh and audit the dashboard's curated data (companies, projects, claims, community responses, moratoriums, tariffs) to keep it current with recent announcements, regulatory filings, and community feedback.

**Scope:** US data centers operated by or under lease to: Meta, Google, Microsoft, AWS/Amazon, OpenAI, Anthropic, xAI, Oracle, Wonder Valley, QTS, CoreWeave, Crusoe, and others meeting the two-gate editorial criteria.

## Three refresh dimensions

Every refresh session should consider all three — they have independent cadences and independent tooling:

1. **New sites/projects** — new data center announcements from the 8 hyperscalers + tracked non-hyperscaler entities. See "Finding New Announcements" below.
2. **New bills/dockets** — new or updated moratorium bills (city/county/state/federal) and utility large-load tariffs. See "Moratoriums & Tariffs Refresh" below.
3. **Gap-filling existing records** — missing fields on records already in the seed (power_mw, ratepayer assessments, claims/feedback coverage). See "Filling Gaps" below.

Don't treat this as one undifferentiated "go find stuff" pass — each dimension has a different staleness signal and a different verification bar (a new moratorium bill needs a live gov source; a gap-fill on an existing project just needs one more first-party field).

---

## Core Workflow: Refresh Cycle

Every refresh operation follows this pipeline:

### 1. **Validate Seed Data**
```bash
python3 refresh.py --check
```
- Checks `data/seed/*.json` files against `schema.py`
- Validates schema constraints (required fields, field types, value ranges)
- Checks cross-references (company slugs, project IDs, claim IDs)
- Halts on any validation error (no partial commits)

### 2. **Audit Missing Commitment Details + Stale Pending Bills**
```bash
python3 refresh.py --audit --check
```
- Identifies projects with missing key fields based on status:
  - **Operational sites:** must have `claimed_investment_usd` and `power_mw`
  - **Construction sites:** must have `claimed_investment_usd`
  - **Announced sites:** important fields are investment, jobs, power, at_a_glance
- **Flags stale `proposed` moratoriums/tariffs** (v1.20): any `proposed` record whose
  `captured_at` is `STALE_PENDING_DAYS` (21) or older gets listed — a pending bill
  or docket is a moving target and needs a re-check, unlike `enacted`/`approved`/
  `failed`/`rejected` records, which are stable once captured and are never flagged.
- Generates `ISSUES.md` with prioritized gaps:
  - **Critical:** missing required fields
  - **Medium:** missing important/commitment fields
  - **Stale Pending Bills / Tariffs:** `proposed` records due for a status re-check
- Report format: per-project / per-bill lists with missing fields or staleness age
- Use to prioritize curation work and flag data gaps across all three refresh dimensions
- **Note:** `--audit --check` writes ISSUES.md but does NOT write `docs/data/*.json`. Run without `--check` to regenerate outputs AND ISSUES.md together.

### 3. **Generate Output JSON**
```bash
python3 refresh.py --pretty      # pretty-printed (for review)
python3 refresh.py               # minified (for production)
python3 refresh.py --audit       # minified + generates ISSUES.md
```
- Emits `docs/data/*.json` (companies, claims, projects, responses, moratoriums, tariffs)
- Validates against schema one final time before write
- Excludes null values from JSON (clean frontend data)
- Stamps `generated_at` with today's date
- Total payload ~700 KB (13 companies, 334 claims, 113 projects, 216 responses, 91 moratoriums, as of 2026-07-14)

---

## Finding New Announcements (Last 3 Weeks)

Target the most productive news sources per CLAUDE.md backlog + v1.8 experience:

### Company Newsrooms (First-Party Source)
- **Meta:** `datacenters.atmeta.com/`
- **Google:** `blog.google/innovation-and-ai/infrastructure-and-cloud/` (Meitner Energy Center, project announcements)
- **Microsoft:** `news.microsoft.com/source/topics/datacenters/` + `local.microsoft.com/blog/`
- **Amazon:** `aboutamazon.com/news/aws/` (search for data center + infrastructure keywords)
- **OpenAI:** `openai.com/index/` (Stargate updates)
- **Oracle:** `oracle.com/news/announcement/` (Stargate, Project Jupiter updates)
- **xAI:** `x.ai/blog/`
- **QTS:** `q.com/news/`
- **CoreWeave:** `coreweave.com/blog/`
- **Crusoe:** `crusoe.ai/resources/blog/`

### High-Signal Third-Party Sources
- **DataCenterDynamics** (`datacenterdynamics.com/en/news/`) — 90%+ hit rate on new sites
- **UtilityDive** (`utilitydive.com`) — grid/energy angle
- **Regional outlets** (Texas Tribune, Wisconsin Watch, Mississippi Today, etc.) — community response angle

### Search Strategy
- Company name + "data center" + date range (last 3 weeks)
- "Stargate" + site name (for OpenAI/Oracle/SoftBank)
- Regional keywords: "data center" + city/county name + state
- Regulatory filings: state PSC dockets, FERC orders, local planning dept records

---

## Moratoriums & Tariffs Refresh

Run `python3 refresh.py --audit --check` first — the "Stale Pending Bills / Tariffs"
section of `ISSUES.md` tells you exactly which `proposed` records need a status
re-check before you go looking for anything new.

### Sources
- **Trackers (aggregators, verify before trusting):** `datacenterbans.com`,
  `interconnectedcapital.com/research/data-center-moratoriums`, MultiState's
  `multistate.us/insider` state-legislation roundups, Good Jobs First
  (`goodjobsfirst.org`).
- **Primary/gov (always the final source for a record):** state legislature bill
  trackers (`nysenate.gov`, `<state>legislature.gov`, etc.), state PUC/PSC docket
  search, city/county council agendas and minutes.
- **News for context/community reaction:** DataCenterDynamics, UtilityDive,
  regional outlets (same list as project research).

### Status re-check checklist (for anything flagged stale)
1. Search `<jurisdiction> data center moratorium <bill number or name>` for the
   most recent coverage.
2. If status changed (e.g. `proposed` → `enacted`/`failed`), update `status`,
   `enacted_date`/`failure_reason` as applicable, and bump `captured_at`.
3. If status is unchanged, just bump `captured_at` to today so it doesn't
   re-flag until the next `STALE_PENDING_DAYS` window — but only if you
   actually re-verified it; don't bump the date on a record you didn't check.
4. Watch for **bill renumbering** — a bill can be substituted/renumbered
   between chambers mid-session (e.g. NY's S7992 was superseded by S10642 after
   an Assembly substitution). Cross-check the bill number against the current
   legislature site, not just the original announcement.
5. New moratorium/tariff candidates found along the way: verify against a
   primary/gov source before adding (per "Data quality rules" in CLAUDE.md);
   run `python scripts/validate_moratoriums.py --id <new-id>` after adding a
   moratorium to confirm the audit trail resolves.

---

## Filling Gaps in Existing Records

The `--audit` critical/medium sections of `ISSUES.md`, plus
`python -m connectors.research status`, are the two entry points for this
dimension — no new site to discover, just missing fields on records already
in the seed.

```bash
python -m connectors.research status                       # coverage gaps: N projects w/o claims, M w/o feedback
python -m connectors.research queries --missing-feedback --limit 10   # emit search queries for a batch
python -m connectors.research queries --missing-claims --limit 10
```
- `queries` prints ready-to-run search strings per project; run them (WebSearch
  or the Chrome MCP bridge for JS-rendered pages).
- `harvest` fetches the resulting URLs, auto-extracts publication dates and
  verbatim quote candidates, and writes to `data/candidates/` (gitignored) —
  it never auto-merges into `data/seed/` and never infers stance/constituency.
- A human still curates: pick the right quote, set stance/constituency, and
  merge the reviewed candidate into `data/seed/`.
- See `BACKLOG.md` → "Drive coverage to comprehensive via the research
  connectors" for the current gap count and priority order.

---

## Creating / Updating Project Records

### New Project Checklist

1. **Verify first-party source** (company press release, blog, investor filing)
   - No paraphrasing — quote verbatim from the company or named executive
   - If using news article with a direct quote, cite both speaker + venue (e.g., "Bloomberg — Smith on Microsoft's Cheyenne pledge")

2. **Populate required fields**
   ```json
   {
     "id": "company-city-state-short",
     "company_slug": "meta|google|...",
     "name": "Formal project name",
     "city": "City",
     "state": "ST",
     "country": "US",
     "lat": null,        // null for virtual partnerships
     "lon": null,        // null for virtual partnerships
     "status": "announced|construction|operational",
     "announced_year": 2026,
     "claimed_investment_usd": null,  // when available
     "claimed_jobs": null,            // when available
     "source_url": "https://...",     // MUST be live/200 status
     "source_title": "Source title",
     "captured_at": "2026-06-09"
   }
   ```

3. **Fill in optional commitment fields** (per status expectations):
   - `power_mw`: announced total capacity (from company disclosure or credible reporting)
   - `acreage`: land footprint (cumulative for multi-phase sites)
   - `gpu_count`: AI accelerator count (only when publicly disclosed)
   - `offtaker`: workload owner (e.g., "OpenAI" for Stargate, "Anthropic" for Project Rainier)
   - `at_a_glance`: curator-written 1-line per-theme summaries (optional; auto-derived if absent)
   - `ratepayer`: assessment of ratepayer-protection pledge compliance (optional; important for post-Mar 4 2026 sites)

4. **Link to project-tied claims**
   - Create `Claim` records with `project_id` pointing to the new project
   - Each claim is a first-party verbatim statement tied to a theme
   - Claims are the evidence base for the project's community benefits

5. **Run validation**
   ```bash
   python3 refresh.py --check
   ```

### Common Data Gaps (Use ISSUES.md to Prioritize)

**High-priority fill-ins (operational/construction sites):**
- `claimed_investment_usd` — press release or S-1 filing
- `power_mw` — utility interconnection application, company spec sheet, or DCD/DCF reporting
- `ratepayer` assessment — check if company signed the White House pledge (Mar 4, 2026) + whether site-specific commitment exists

**Medium-priority:**
- `claimed_jobs` — construction + operational; company press release
- `at_a_glance` — curator summary; auto-derived if absent
- `gpu_count` — rare; only disclosed by some companies (Google, OpenAI, Crusoe sometimes)

**Low-priority for announced sites:**
- Investment/jobs/power often unavailable pre-announcement; leave null and revisit at construction milestone

---

## Handling Updates to Existing Projects

### Status Changes (announced → construction → operational)

1. **Update the project record**
   ```json
   "status": "operational",
   "captured_at": "2026-06-09"
   ```

2. **Add a project-tied claim** for the operational milestone
   - Sourced from company announcement or press coverage
   - Theme: `infrastructure` (typical) or `engagement` (if there's a formal ceremony/community event)

3. **Add community responses** if available
   - Operational feedback from residents, local government, NGOs
   - Set `stance` to positive / mixed / negative
   - Include `constituency` (residents, local_government, ngo, regulator, journalist, academic)

### Investment/Capacity Increases

Example: Meta Richland Parish Phase 2 (May 2026)

1. **Update numeric fields**
   ```json
   "claimed_investment_usd": 10000000000,  // original 2024 announcement
   "notes": "May 9 2026: Meta acquired additional ~1,400 acres for Phase 2 expansion; cumulative footprint now ~3,650 acres. Total investment guidance updated in LPSC disclosure to $15B+."
   "acreage": 3650
   ```

2. **Add a claim** documenting the expansion
   - Sourced from regulatory filing (LPSC order, Entergy Q1 earnings, company update)
   - Theme: `infrastructure` or `energy` (if grid cost-share updates)

3. **Audit + ratepayer update**
   - Run `python3 refresh.py --audit` to surface any now-missing fields
   - If the company is a pledge signatory + the expansion is post-pledge, add `ratepayer` assessment

### Regulatory Approvals / Permitting Milestones

Example: AWS Calvert Cliffs site plan filing (May 4, 2026)

1. **Update the notes field with the date and detail**
   ```json
   "notes": "... filed a concept site plan application on May 4, 2026 …"
   ```

2. **Update `captured_at`** to reflect the refresh date

3. **Add a claim** if the approval comes with new first-party details
   - Theme: typically `engagement` (for community input) or `infrastructure` (for grid/water approvals)

---

## Periodic Refresh from Recent Commits

To keep the dashboard current without full audits every week:

### Quick Refresh (Weekly)
```bash
# Check for git changes in data/seed/ since last refresh
git diff <last-refresh-commit>..HEAD data/seed/

# Validate only (no write, no audit)
python3 refresh.py --check

# If clean, snapshot the current state
git log --oneline -n 1
```

### Full Refresh + Audit (Bi-weekly or after major announcements)
```bash
# Find new projects from recent commits
git log --since="2 weeks ago" --oneline -- data/seed/projects.json

# Run full validation + audit + output
python3 refresh.py --audit
git status  # shows updated docs/data/*.json + ISSUES.md
git add -A
git commit -m "data: refresh $(date +%Y-%m-%d) — audit + new projects"
```

### Commit Message Convention
```
data: refresh 2026-06-09 — audit + new projects

- Added Google-SpaceX GPU partnership (110K GPUs, $920M/mo)
- Added Anthropic-xAI infrastructure partnership ($1.25B/mo)
- Audit: 21 critical + 70 medium gaps in commitment details
- Updated 8 projects with recent status changes (ratepayer, power, acreage)

See ISSUES.md for full audit report.
```

---

## Learnings from v1.18 Refresh Session

### 1. Infrastructure Partnerships (NEW RECORD TYPE)
- Google-SpaceX GPU lease + Anthropic-xAI compute partnership don't fit the "physical data center with community presence" model
- Schema updated: `lat` and `lon` now Optional to support virtual infrastructure partnerships
- UX decision pending: include in dashboard? If yes, how to surface?
- See BACKLOG.md "Infrastructure partnership UX exploration" for design question

### 2. Ratepayer Pledge Assessments (PRIORITIZE)
- White House Ratepayer Protection Pledge signed Mar 4, 2026 by seven hyperscalers
- Post-pledge projects should have `ratepayer` assessment:
  - `affirmed`: site-specific pay-our-way commitment captured
  - `pledge_only`: covered by national signature, no site-specific commitment yet
  - `contested`: third-party documents cost-shift despite pledge
- 40+ projects missing ratepayer assessment — high priority for next refresh

### 3. Missing Commitment Details (AUTOMATED AUDITING)
- As of 2026-06-30 audit: **34 critical + 71 medium gaps** across 105 projects
- Common gaps by company:
  - **Google:** power_mw (most operational sites — not publicly disclosed per project)
  - **Meta:** power_mw (older operational campuses), ratepayer (post-pledge construction sites)
  - **Microsoft:** power_mw (most operational + construction), ratepayer (several post-pledge sites)
  - **Amazon/AWS:** claimed_investment_usd (site-level figures rolled into state commitments), ratepayer
  - **OpenAI/Oracle/xAI/CoreWeave:** claimed_investment_usd (Stargate/partner sites), ratepayer
  - **QTS:** claimed_investment_usd + power_mw (both Manassas VA and Richmond VA)
- Most `power_mw` gaps require web research (sites don't publish per-campus capacity)
- Most `claimed_investment_usd` gaps are site-level slices of larger state-level commitments (can't safely attribute without a first-party site-level figure)
- ISSUES.md auto-generated; prioritize critical projects first
- Run `python3 refresh.py --audit` (not `--audit --check`) to regenerate docs/data/ AND ISSUES.md together

### 4. Recent Announcements Pipeline
- 25 projects captured May 19–June 8 shows the refresh cadence is working
- Most recent: Stargate Michigan (June 1 groundbreaking), AWS Calvert (May 4 site plan)
- 3-week research window is sustainable; stick to company newsrooms + DCD + regional outlets

### 5. Schema Flexibility
- Optional lat/lon allows infrastructure partnerships without physical coordinates
- Optional fields throughout (power_mw, acreage, gpu_count, claimed_jobs, etc.) match editorial reality
- Schema validation at refresh time catches drift early

---

## Checklist: Running a Full Refresh

- [ ] Identify announcement window (e.g., last 3 weeks)
- [ ] Search company newsrooms + DCD + regional outlets
- [ ] Extract first-party claims (verbatim quotes only)
- [ ] Create/update project records in `data/seed/projects.json`
- [ ] Create project-tied claims in `data/seed/claims.json`
- [ ] Create community response records (if applicable)
- [ ] Validate: `python3 refresh.py --check`
- [ ] Audit: `python3 refresh.py --audit --check` → review ISSUES.md
- [ ] Generate output: `python3 refresh.py --pretty`
- [ ] Review `docs/data/*.json` diffs for correctness
- [ ] Commit with descriptive message (include ISSUES.md changes)
- [ ] Push to remote if ready for frontend deployment

---

## Links & References

- **Schema:** `schema.py` — single source of truth for all record types
- **Refresh driver:** `refresh.py` — validation, audit, output generation
- **Project intent & design:** `CLAUDE.md` ("Project-specific notes" section) + `DESIGN.md`
- **Backlog:** `BACKLOG.md` — infrastructure partnership UX, next polling cycle, etc.
- **Issues:** `ISSUES.md` — auto-generated audit report (commit after refresh)
- **Data directory:** `data/seed/` (source of truth) → `docs/data/` (frontend feeds)

---

## Contact / Questions

This playbook encodes the learnings from the v1.18 session (June 9, 2026). If gaps emerge during the next refresh cycle, update this file with the new pattern so future curators have the benefit of the discovery.

---

## Research connectors accelerator (`connectors/`)

The manual search strategy above has a CLI accelerator — use it to find gaps and turn URLs
into candidate records (it never auto-publishes; curation stays editorial):

1. **Load state.** Read `ISSUES.md`, `BACKLOG.md`, and run:
   ```bash
   python -m connectors.research status --list
   ```
   This reports projects with no claims / no community feedback — the gap list. The
   recurring ask is **new data centers and new utility tariffs**; prioritize those unless
   told otherwise.

2. **Search.** Generate queries and run them with WebSearch (or Chrome MCP for JS-rendered
   first-party pages like `datacenters.google`):
   ```bash
   python -m connectors.research queries --missing-feedback --limit 5
   python -m connectors.research queries --missing-claims --json
   ```

3. **Harvest** promising URLs into candidate records (cached, ≥1.5s/host, 429-backoff):
   ```bash
   python -m connectors.research harvest --project <slug> <url> [<url>...]
   ```
   First-party domains → `claim_candidates` with **verbatim quote candidates**; everything
   else → `response_candidate` with auto-extracted publication date. `stance` /
   `constituency` / `single_source` come out null with a TODO — fill them editorially,
   never let the tool infer them.

4. **Curate** candidates from `data/candidates/` into `data/seed/*.json` by hand: pick the
   verbatim quote, write the neutral summary, set editorial fields, carry source URL +
   capture date. Contested items get both sides, per CLAUDE.md.

Full detail: `connectors/README.md`.

## Learned patterns (append-only, dated)

- 2026-07-07: consolidated the flat `.claude/skills/data-refresh.md` skill into this
  playbook per the one-generic-skill convention (base CLAUDE.md); added the connectors
  accelerator section. Flat skill files in `.claude/skills/` never registered with Claude
  Code anyway (directory + SKILL.md format required).
