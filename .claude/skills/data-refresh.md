# Data Refresh Skill — Data Center Community Benefits Dashboard

**Purpose:** Systematically refresh and audit the dashboard's curated data (companies, projects, claims, community responses) to keep it current with recent announcements, regulatory filings, and community feedback.

**Scope:** US data centers operated by or under lease to: Meta, Google, Microsoft, AWS/Amazon, OpenAI, Anthropic, xAI, Oracle, Wonder Valley, QTS, CoreWeave, Crusoe, and others meeting the two-gate editorial criteria.

---

## Core Workflow: Refresh Cycle

Every refresh operation follows this pipeline:

### 1. **Validate Seed Data**
```bash
python refresh.py --check
```
- Checks `data/seed/*.json` files against `schema.py`
- Validates schema constraints (required fields, field types, value ranges)
- Checks cross-references (company slugs, project IDs, claim IDs)
- Halts on any validation error (no partial commits)

### 2. **Audit Missing Commitment Details** (NEW — v1.18)
```bash
python refresh.py --audit --check
```
- Identifies projects with missing key fields based on status:
  - **Operational sites:** must have `claimed_investment_usd` and `power_mw`
  - **Construction sites:** must have `claimed_investment_usd`
  - **Announced sites:** important fields are investment, jobs, power, at_a_glance
- Generates `ISSUES.md` with prioritized gaps:
  - **Critical:** missing required fields
  - **Medium:** missing important/commitment fields
- Report format: per-project lists with missing field names
- Use to prioritize curation work and flag data gaps

### 3. **Generate Output JSON**
```bash
python refresh.py --pretty      # pretty-printed (for review)
python refresh.py               # minified (for production)
```
- Emits `docs/data/*.json` (companies, claims, projects, responses)
- Validates against schema one final time before write
- Excludes null values from JSON (clean frontend data)
- Stamps `generated_at` with today's date
- Total payload ~532 KB (includes 13 companies, 300 claims, 98 projects, 199 responses)

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
   python refresh.py --check
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
   - Run `python refresh.py --audit` to surface any now-missing fields
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
python refresh.py --check

# If clean, snapshot the current state
git log --oneline -n 1
```

### Full Refresh + Audit (Bi-weekly or after major announcements)
```bash
# Find new projects from recent commits
git log --since="2 weeks ago" --oneline -- data/seed/projects.json

# Run full validation + audit + output
python refresh.py --audit
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
- 91 projects need attention (21 critical, 70 medium)
- Common gaps by company:
  - **Google:** power_mw (many announced sites)
  - **Microsoft:** power_mw, ratepayer (Cheyenne, Person County)
  - **Amazon:** ratepayer (Loudoun, New Carlisle, Cumberland)
  - **Meta/OpenAI/Oracle:** ratepayer (post-pledge sites)
- ISSUES.md auto-generated; prioritize critical projects first

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
- [ ] Validate: `python refresh.py --check`
- [ ] Audit: `python refresh.py --audit --check` → review ISSUES.md
- [ ] Generate output: `python refresh.py --pretty`
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

This skill encodes the learnings from the v1.18 session (June 9, 2026). If gaps emerge during the next refresh cycle, update this file with the new pattern so future curators have the benefit of the discovery.
