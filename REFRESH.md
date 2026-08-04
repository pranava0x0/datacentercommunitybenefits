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
- Total payload ~710 KB (13 companies, 337 claims, 117 projects, 216 responses, 93 moratoriums, 25 tariffs, as of 2026-07-15)

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
- **SB Energy (SoftBank Group):** `sbenergy.com/communities/` (community framing) + `portscampus.com/` (PORTS Technology Campus project microsite) — added 2026-07-30
- **Brookfield:** `brookfield.com/views-news/newsroom` — thin so far (one joint DOE/NextEra release as of 2026-07-30)

Note: **Amentum (DOE's Savannah River Site partner) is watched but NOT tracked as a company** — see "Companies in scope" in CLAUDE.md for why (announced scale clears gate 1, but its only two first-party quotes are pure engineering/national-security capability language with no community-impact content, so gate 2 isn't actually cleared despite having quotable material). Re-check `amentum.com/news/` after lease negotiations conclude, in case a future announcement carries genuine community-impact framing.

### DOE Federal-Land AI Data Center Program (added 2026-07-30)
A fourth discovery angle, distinct from the two companies above being
DOE-adjacent: DOE itself periodically announces site selections and private
partners for AI data centers on its own land. Check `energy.gov/powering-
americas-ai-future-data-center-resource-hub` and search `"Department of
Energy" AI data center site selected` each cycle — **Oak Ridge Reservation
(TN) and Idaho National Laboratory (ID) were still in the RFP/no-partner-
selected stage as of this pass** and are not yet Project records; re-check
whether a partner has been named before adding either.

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
  (`goodjobsfirst.org`), `halcyon.io/large-load-tariff-tracker` (tariffs, found
  2026-07-30 — same "mine as a worklist, verify each row" treatment as the
  Moratorium Nation CSV).
- **Primary/gov (always the final source for a record):** state legislature bill
  trackers (`nysenate.gov`, `<state>legislature.gov`, etc.), state PUC/PSC docket
  search, city/county council agendas and minutes.
- **News for context/community reaction:** DataCenterDynamics, UtilityDive,
  regional outlets (same list as project research).

### Rate cases (v3)

`data/seed/rate_cases.json` joins the stale-pending audit: a `pending` case
older than STALE_PENDING_DAYS gets flagged in ISSUES.md like a proposed
bill/tariff. Re-check sources: the PSC/PUC docket system itself (EFIS in MO,
eDocket in AZ, starw1 in NC, PUCN in NV), PSC press pages, and **legal
notices in local papers** (dated, primary, and they carry the docket number).
Standing dated watch items as of 2026-08-03 — each is a `next_milestone` on a
record, so the Home "What's next" list is the live version of this list:
- 2026-08 (est): Oneida County WI board vote on the county moratorium
- 2026-09-30: NC large-load tariff submission (Duke/Public Staff); DeKalb GA
  moratorium expiry
- 2026-12-01: Xcel MN clean energy & capacity tariff filing
- 2027-01-01: Dominion GS-5 class effective; Duke NC new rates if approved
- Undated: ACC decision post-hearing (APS), PUCN 26-06023 schedule, LPSC
  response to the Earthjustice investigation request, FERC RM26-4 compliance

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

0. **Scout for new records first** (added 2026-07-30 — do this before `status`,
   which only covers gaps in EXISTING records):
   ```bash
   python -m connectors.scout all
   ```
   Fetches the same fixed source list as "Finding New Announcements" /
   "Moratoriums & Tariffs Refresh" above, extracts headlines, and diffs them
   against the seed. Read the "No seed match" bucket by hand (or hand it to an
   agent) before deciding a full research-agent sweep is needed — see
   `connectors/README.md`'s "What a script can't do here" for this tool's
   real, demonstrated limits (it misses matches as often as it manufactures
   false ones; treat both buckets as leads, not verdicts).

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
- 2026-07-14: a generic "New Data Center Developments" roundup blog claimed Crusoe broke
  ground on Cheyenne WY in July — false. Named-source reporting (Bloomberg, WyoFile,
  wyomingnews.com "Crusoe pulls out of Project Jade") showed Crusoe actually exited/paused
  around April 2026; Tallgrass Energy continues the power-generation half and is seeking a
  replacement data-center tenant. Lesson: weight generic aggregator/listicle roundups below
  named-source reporting, especially for anything framed as a positive status update —
  they're often stale or conflate an old announcement with the current month.
- 2026-07-14: pre-flight checking against local seed data by substring-matching company/
  state ("missouri", "aurora") missed an exact-duplicate — `google-new-florence-mo`
  already existed under a name that doesn't contain "missouri" (state field is "MO", id
  uses the town name). Caught only at `refresh.py --check` (duplicate-id validation), not
  before doing the research. Lesson: when pre-flighting a lead, also grep the specific
  place name from the headline, not just company+state — and treat schema validation as a
  backstop, not the primary duplicate-detection mechanism.
  **Recurred 2026-07-15, same record**, one week later — a scouting agent independently
  re-flagged "Google Montgomery County MO" as a possible new project; it was
  `google-new-florence-mo` all along. Prose reminders aren't sticking across sessions.
  Before curating any "new site" lead, run a mechanical check, not a remembered habit —
  e.g. `python3 -c "import json; [print(r['id'],r['city'],r['state']) for r in
  json.load(open('data/seed/projects.json'))['projects'] if r['state']=='<ST>']"` and
  eyeball every row in that state, not just a grep for the headline's place name (the
  headline said "Montgomery County," the record's `city` field says "New Florence" —
  neither substring matches the other).
- 2026-07-14: a company blog post can move (dead link) even when its content is still
  accurate — `blogs.microsoft.com/on-the-issues/2024/05/08/...` 404s but the same-day
  announcement is live at `news.microsoft.com/source/2024/05/08/...` (blogs → news
  subdomain migration). A moved-URL replacement is only safe when the new page actually
  verifies the specific claim it's sourcing — one swap was safe (project-level citation,
  not tied to one quote) and one wasn't (a claim's specific "$50M community projects"
  figure didn't appear on the replacement page); logged the latter to ISSUES.md rather
  than guessing.
- 2026-07-14: a state moratorium bill passing the legislature and a governor separately
  signing an executive order on the same general topic are NOT the same event, even when
  headlines conflate them ("Hochul enacts...moratorium" read, on a skim, like she'd finally
  signed the already-tracked SB7992/AB7234 bill). She hadn't — EO 62 is a structurally
  different mechanism (50 MW threshold vs. the bill's 20 MW) that coexists with the
  still-pending bill. Added as a separate record rather than overwriting the bill's status;
  cross-referenced both records so a reader lands on the right one either way.
- 2026-07-14 (caught by post-hoc review, not caught while curating): **WebSearch's
  synthesized "answer" text pulls from every result in that search, not just the one URL
  you pick as `source_url`.** Two facts (a "largest data center campus in Texas" claim, a
  "$7B+ collateral" figure) landed in records because they were in a WebSearch tool's
  cross-result summary — when the specific cited article was fetched directly afterward,
  neither fact was actually in it. Also happened in reverse: a "98 diesel generators"
  figure came from a headline glimpsed in search results for a URL that was never
  successfully fetched (CPR.org 403'd every attempt, curl included) — shipped as if
  confirmed. Fix going forward: after using WebSearch to find candidate facts, fetch the
  *specific* URL you're about to cite as `source_url` and confirm the fact is actually
  there before writing it into a record — don't treat the search tool's synthesis as
  equivalent to having read the source. See CLAUDE.md's "Editorial / sourcing rules" for
  the general version of this rule.
- 2026-07-14: several outlets (datacenterdynamics.com on a full GET rather than a
  status-only check, cpr.org, enr.com) return 200 to a quick `curl -o /dev/null` liveness
  probe but 403 to both WebFetch and a full-body `curl` with a browser User-Agent. A
  "confirmed live" liveness check is not the same as "confirmed fetchable" — if a fact
  needs verifying and the primary source 403s on every attempt, find a second outlet
  that covers the same fact rather than trusting the blocked source's headline/snippet.
- 2026-07-14: `njleg.state.nj.us/bill-search/<year>/<bill>` returns 200 but is a
  JS-rendered search form, not a bill-content page — fetching it gets you the site nav,
  not the bill text. Confirmed-live doesn't mean confirmed-useful-as-a-citation; for gov
  bill-tracker sites, prefer a direct bill-text/status page over a search-form URL when
  one exists, or verify the search-form URL actually resolves to content before citing it.
- 2026-07-15: full three-dimension refresh (stale bills, new scouting, gap-filling) run
  in one session. Key results: 16 stale moratorium/tariff records re-checked found 3 with
  wrong bill numbers (records were seeded from a synthesized/aggregated source that got
  the bill number wrong at creation — worth extra scrutiny on any record whose only
  resource is a generic tracker like datacenterbans.com), 1 exact duplicate (two records
  for the same Seattle ordinance under different jurisdiction labels), and one moratorium
  vs. governor's-executive-order conflation resolved cleanly by keeping both as separate
  records (same lesson as the NY EO62/bill case, generalized). 8 new enactments landed in
  a single week (2026-07-13/14) — a reminder that even a ~3-week research cadence can miss
  a fast-moving week; consider a lighter, more frequent "just check for anything this
  week" pass between full cycles.
- 2026-07-15: **gap-filling has a real, low ceiling.** Across critical (36) + medium (57)
  fields researched this session — mostly `power_mw` and `claimed_investment_usd` on
  operational/construction sites — only ~17 total came back with a clean, attributable,
  site-specific figure (roughly 18%). The other ~82% were genuine "not found," not research
  failures: hyperscalers routinely don't publish per-campus power capacity, and several
  companies (QTS on multiple sites) explicitly state on their own project pages that they
  won't disclose it "for security and confidentiality reasons." Don't re-research a
  confirmed-non-disclosed field without a new lead (a utility interconnection filing, a
  tax-abatement filing that discloses power draw for tax-calc purposes, etc.) — BACKLOG.md
  logs the specific confirmed-non-disclosed records from this pass.
- 2026-07-15: the most common failure mode in gap research is a **regional/combined figure
  masquerading as a site-specific one** — a company's own page states "$9B Texas
  investment" or "616 MW statewide" and it's tempting to attribute it to the one site in a
  record, but the same page usually also states (sometimes in the very next sentence) that
  the site-specific breakdown "has not been shared." Always check whether the number's own
  sentence scopes it to one site or to a state/region before using it — this bit multiple
  agents this session across Amazon, Google, and Microsoft records, and citing the
  regional total would have been a real (if plausible-looking) error, not just a citation
  weakness.
- 2026-07-15: a persistent per-field distinction worth remembering — a company's *renewable
  energy procurement* MW (grid supply added via a PPA/solar deal, framed as "adding N MW of
  clean energy") is a different number from the site's own *power draw/capacity*
  (`power_mw` in this schema). Meta, Google, and Microsoft info sheets consistently lead with
  the renewable-supply figure, and it's the wrong field — don't map it to `power_mw` even
  when it's the only MW figure on the page.
- 2026-07-15: **audit script bug found and fixed** — `refresh.py`'s `_audit_missing_commitments`
  flagged "missing ratepayer" for every operational/construction project regardless of
  whether the company is a pledge signatory, over-flagging ~18 CoreWeave/Crusoe records
  that should never get a ratepayer assessment per the frozen CLAUDE.md rule ("only
  signatory projects announced on/after the pledge date"). Fixed by mirroring app.js's
  `isPrePledgeProject` signatory + date-eligibility check in `_audit_missing_commitments`
  (see `_is_ratepayer_eligible`) before generating ISSUES.md. If a future refresh sees the
  medium-gap count for ratepayer spike again, check whether a new non-signatory company was
  added without this filter accounting for it.
- 2026-07-15: **agent-dispatch discipline.** Splitting one coherent research batch across
  multiple small parallel subagents (e.g. 2 agents for a single 13-record AWS/Amazon batch)
  pays the fixed per-agent overhead (observed ~80-120K tokens each) twice for no real
  benefit when the work is backgrounded, not wall-clock-sensitive. Default to fewer, larger
  agents (one per company family, roughly 15-20 records) unless the combined prompt would
  be unreasonably long. See the `feedback_agent_parallelism_discipline` memory for the full
  rule. Separately: a genuinely stalled agent (zero output growth for far longer than
  sibling agents doing comparable work — 83 min vs. 5-10 min this session) is fine to kill
  and relaunch; that's error recovery, not over-parallelization.

---

### 2026-07-26 refresh pass — learnings

- **A renumbering note in this file does not fix the data.** The status-re-check
  checklist already said "NY's S7992 was superseded by S10642 after an Assembly
  substitution", yet `ny-state-2026-06`'s summary *and* CLAUDE.md both still cited
  S7992/A7234. S7992 is an unrelated NY labor-relations bill. **When you record a
  renumbering here, grep the seed and the docs for the old number in the same
  pass** — otherwise the playbook is right and the product is wrong.
- **The `bill_number` field and the summary can disagree.** On the NY record the
  field was correct (S10642/A11560) and the prose was not. Nothing cross-checks
  the two. Worth a validator if it recurs.
- **Don't bump `captured_at` on a record whose source could not answer the
  question.** Six of ten stale records this pass were unresolvable (one source
  predated the vote it referred to; two were 403/429). They were left un-bumped so
  they stay flagged. A bumped date on an unverified record silently retires it
  from the audit for another 21 days.
- **A "first reading only" record can still be operative.** Spartanburg County
  invoked the *pending ordinance doctrine* to freeze applications immediately
  after first reading. `status` tracks the instrument (`proposed`), and the
  operative freeze belongs in the summary — don't promote it to `enacted`.
- **A unanimous vote to "pursue an ordinance" is not a moratorium.** Lake County
  FL had no drafted ordinance and no scheduled adoption vote; the record now says
  so explicitly rather than reading as a pending ban.

---

### 2026-07-27 refresh pass — learnings

Scope: closed out the 6 records left stale from 07-26, then scouted all three
dimensions (new sites, new bills/dockets, tariffs) via direct WebSearch/WebFetch
before considering any agent — none were needed this pass.

- **4 of the 6 stale records resolved cleanly; 2 stayed genuinely unresolvable.**
  Henderson NV: council *rejected* the moratorium 2026-07-21 (→ `failed`), corroborated
  by 5 independent outlets. New Albany IN: enacted 2026-07-16 (→ `enacted`), 3+ outlets.
  APS AZ tariff: the seed's docket number was simply wrong (`E-01345A-25-0134` vs. the
  real `E-01345A-25-0105`) — confirmed via a direct fetch of azcc.gov, not search
  synthesis. Duke NC tariff: enriched with the 2026-07-17 fast-track settlement (75%
  minimum-take, 10-15yr terms) without a status change. **Hernando County FL** and
  **nv-energy-callisto-esa** stayed flagged/un-bumped — 4 fetch attempts across
  floridapolitics.com (402 paywall), wtsp.com (timeout), tampabay28.com (predates the
  vote) never confirmed Hernando's July 7 final-vote outcome either way; NV Callisto's
  only lead is citizenportal.ai, still 403 on every attempt, with conflicting
  self-contradictory dates in WebSearch synthesis (April 2025 vs. a 2026 bundled order).
  Per the 07-26 rule, left both un-bumped rather than guessing.
- **The "5 new Stargate sites" news recurred as a stale-recap trap, exactly per the
  2026-07-14 lesson.** A WebSearch for "OpenAI Oracle new data center July 2026"
  surfaced `openai.com/index/five-new-stargate-sites/` and DCD coverage that read as
  fresh — but a 30-second mechanical check (`openai-shackelford-tx`,
  `oracle-dona-ana-nm` already in the seed, captured 2026-05-16, matching figures)
  showed it was the September 2025 five-site expansion being recirculated, not new
  news. Same for "Amazon $10B + Google $15B in Montgomery County" — both already
  seeded (`amazon-montgomery-city-mo`, `google-new-florence-mo`, exact dollar match).
  **Zero new data center projects or tariffs survived this pre-flight check** — every
  lead from ~8 broad searches across companies/DCD/utility-tariff angles turned out
  already-tracked. Worth noting since it means a broad "any new sites?" search after a
  ~12-day gap can legitimately come back empty; don't force a record to justify the
  search effort.
- **Moratoriums were the one dimension with a real, sizeable gap: a whole state's
  wave was missing.** Only `denver-city-2026-05` was tracked for Colorado despite a
  live wave of 7 more Front Range jurisdictions (Larimer County, Jefferson County,
  Boulder County, Broomfield, Woodland Park, Monument, Longmont) plus Surry County NC
  — all enacted between 2026-01-27 and 2026-07-21, none previously captured. Lesson:
  when a state shows just one old record and national coverage keeps mentioning
  "joining Denver/Longmont/..." in passing, treat the named peer jurisdictions as a
  worklist, not color commentary — the Broomfield article alone named 4 other CO
  jurisdictions that turned out to be real, addable gaps.
- **Longmont's ordinance is a permanent MW-threshold land-use ban, not a time-boxed
  pause** — confirmed schema already anticipates this (`duration_months` docstring:
  "Null for permanent bans or unknown durations"; the class docstring says "moratorium
  *or ban*"). Shipped with `duration_months: null`, `power_threshold_mw: 100`, and a
  `policy_type` note rather than forcing a fake duration.
- **WebFetch and the validator script's own `requests`-based fetcher don't fail on the
  same URLs.** `bizwest.com` and two `gazette.com` (Colorado Springs) articles all
  403'd on WebFetch but returned clean HTTP 200 with real content (5-12K chars) to
  `scripts/validate_moratoriums.py`'s fetcher. Where WebFetch is blocked and a
  fact is corroborated by 3+ independently-named outlets from the WebSearch pass
  (not one aggregator), that multi-outlet agreement is the fallback per the existing
  "find a second outlet" rule — don't hold a well-corroborated record hostage to one
  blocked fetcher when another one in the same toolchain already got through.
- **A bill that *mandates* a future utility tariff is not itself a tariff record.**
  NJ S731 (signed/awaiting signature as of this pass) requires NJ utilities to design
  a large-load tariff for 100MW+ data centers, but no utility has filed one yet under
  it — same for Michigan's Whitmer "Affordable and Responsible Growth" plan (a policy
  framework, not a docketed rate case). Neither got a `Tariff` record; both are worklist
  items for whenever a specific utility files under them (see BACKLOG.md).
- **A DCD "News → Construction & Site Selection" channel URL, fetched directly, beat
  every keyword WebSearch this pass.** After the initial broad searches came back with
  nothing genuinely new (see above), the user asked to specifically expand the DCD
  angle. `WebSearch` scoped to `datacenterdynamics.com` still mostly surfaced older
  recirculated stories — the breakthrough was `WebFetch`-ing
  `datacenterdynamics.com/en/news/?term=construction-site-selection` directly, which
  returned an actual dated headline list (27 Jul, 23 Jul, 22 Jul …) that no search
  query reconstructed on its own. **Lesson for next time: try fetching a source's own
  news-index/channel URL directly before concluding a search pass is exhaustive** —
  search snippets sample a source, a channel listing enumerates it.
- **That listing surfaced 3 genuinely new projects and one significant correction in
  one page-load:** OpenAI's self-developed "Project Camellia" (3.2GW, Effingham
  County GA, $20-30B, first OpenAI-owned-not-leased Stargate-family site), Meta's
  Temple TX campus going operational (first AI-optimized Meta DC in the US, with two
  clean named-executive verbatim quotes from kdhnews.com), and a new Prologis San
  Jose project (99MW, Silver Creek Valley Rd) — plus catching that
  `loudoun-county-va-2026-03` was mischaracterizing a March-**2025** (not 2026)
  by-right→special-exception zoning change as a permanent enacted ban, contradicted
  outright by the county's own FAQ ("A blanket prohibition... is not legally
  permissible"). Same failure shape as the *other* Loudoun record already removed in
  the v1.20 pass — **removed rather than reworded**, per that precedent.
- **openai.com and the DCD/Data-Centre-Magazine/mlq.ai family of sites 403'd on
  every direct-fetch attempt for the Camellia story** (6 attempts across 5 domains).
  Per the established "find a second outlet" fallback, shipped the project on the
  strength of 5+ independently-named outlets (DCD, GPB, TechRadar, Energy Digital,
  MLQ News) agreeing on the core figures, but did **not** add a Claim record without
  a verbatim quote actually read — same treatment as the existing Stargate Abilene
  backlog item. A browser-driven visit to the openai.com URL remains the way to
  close that gap.

---

### 2026-07-30 refresh pass — a new dimension (DOE federal-land program) + two waves found in passing

Scope: user explicitly asked to sweep for DOE (Department of Energy) data center
site announcements, on top of the standard three-dimension refresh. That turned
into a fourth dimension worth naming going forward, plus two moratorium waves
found while rechecking a single stale record — a reminder that "recheck two
records" and "the state next door has a wave" are unrelated in scope but often
discovered together.

- **DOE's federal-land AI data center program is a NEW company-scope
  precedent, not a one-off.** DOE announced 4 sites for private-partner AI data
  center development on federal land (Idaho National Lab, Oak Ridge, Paducah,
  Savannah River) in July 2025; by this pass, partners were selected for two
  (Amentum/Savannah River, Brookfield+NextEra/Paducah) and a related-but-earlier
  deal (SB Energy/Portsmouth) was already under construction. All three cleared
  gate 1 (≥1GW scale) trivially — **but only SB Energy and Brookfield actually
  clear gate 2**, added as full `Company` + `Project` + `Claim` records —
  `sb-energy`, `brookfield`. Amentum was added in the first cut of this PR, then
  REMOVED on code review: it has two first-party named-executive quotes, but
  both are pure engineering/national-security capability language with zero
  community-impact content — see the standalone gate-2 lesson below, and
  CLAUDE.md's "Companies in scope" for the corrected rule. **NextEra Energy was
  deliberately NOT added as a separate slug**, even though DOE/company releases
  are explicit NextEra builds/owns the Paducah generation: NextEra is a Ratepayer
  Pledge signatory (joined the 2026-07-23 expansion) and Brookfield is not, so
  collapsing them into one company record would have let NextEra's signatory
  status bleed onto Brookfield's `ratepayer_pledge_signatory` flag. When a
  multi-party consortium shows up, identify the actual data-center
  developer/operator (ask directly: "who leases and operates the DC, who just
  supplies power?") and track only that one as the `company_slug`; name the
  power/utility partners in the project's `notes`, not as second company slugs.
- **"We have first-party quotes to attach" is not the same claim as "gate 2 is
  cleared" — and this pass shipped the conflation once before a review caught
  it.** Amentum's two quotes (CEO John Heller, Energy & Environment president
  Mark Whitney) are genuinely first-party — named executives, on the record,
  in the company's own press release. They were added as `Claim` records
  without a second check on what they actually SAY: both are about Amentum's
  engineering pedigree and the deal's strategic/national-security framing, not
  about jobs, ratepayers, environment, or any other community-facing
  commitment. The two-gate test's real requirement is "the entity publishes
  ITS OWN COMMUNITY-IMPACT framing" — having *some* quotable first-party
  material satisfies the letter of "we have first-party claims to quote" while
  missing the substance entirely. Compare to QTS's or SB Energy's claims, which
  are explicitly about cost/jobs/ratepayer commitments. Going forward: before
  shipping a new non-hyperscaler company, re-read every claim being attached
  and confirm it's actually ABOUT one of the 8 community-benefit themes for
  the HOST COMMUNITY, not just about the company's capabilities or the deal's
  strategic significance.
- **A research agent's own extraction can still produce the WebSearch-synthesis
  error it's supposed to prevent.** The DOE-companies research agent initially
  read Amentum CEO John Heller's quote as two separate quotes, because
  WebFetch's markdown conversion of two different mirror pages (amentum.com and
  World Nuclear News) each truncated it to a different sentence. It caught this
  itself by pulling the original press-release PDF and confirming both fragments
  were one continuous quote — but the lesson generalizes: **a quote appearing
  twice, worded slightly differently, across two sources covering the same
  event is a truncation artifact, not two quotes** — go to the primary
  document (often a PDF press release, not the HTML mirror) before shipping
  either fragment as `Claim.statement`.
- **A company's own press release quoting a government official is not a
  first-party claim for that company.** NNSA Administrator Brandon Williams's
  quote on the Amentum/Savannah River deal, and DOE Secretary Chris Wright's
  quotes throughout, were found and explicitly excluded — they're government
  speakers, not company speakers, even when they appear on the company's own
  announcement page. Same discipline as the existing first-party rules in
  CLAUDE.md, just a new venue (a DOE press release) to apply it to.
- **Two agents' worth of research surfaced conflicting scope on the same
  company (SB Energy) with no source stating the reconciliation.** Investment
  figures ranged $30B–$500B and jobs figures were 10,000/2,000+ vs.
  35,000/2,500 depending on whether the source scoped to the initial 189-acre
  federal parcel (DOE's own March 2026 article) or the full 2,700-acre private
  campus (SB Energy's current site + June 2026 FAST-41 coverage). Resolved by
  using the larger, more current, company-published, full-scope figures
  consistently across `claimed_investment_usd`/`claimed_jobs`/`acreage`/
  `power_mw` (so the numbers stay internally consistent with each other) and
  documenting the smaller DOE-cited figure in `notes` rather than picking one
  as "correct" — neither source contradicts the other, they're just scoped
  differently, and nothing available says which scope the record should
  prefer by default.
- **A Florida moratorium wave was found entirely by accident** while
  rechecking the single stale `hernando-county-fl-2026-06` record. **Hernando
  itself stayed unresolved, and correctly so** — an initial pass inferred
  "enacted July 14" from circumstantial evidence (matching Pasco's own
  confirmed final-vote date via tandem Tampa Bay-area coverage), but a code
  review caught that the only "confirms final adoption" source was an
  advocacy op-ed, not a neutral report — reverted to `proposed` per this
  project's own don't-guess rule. Sarasota County was a clean new add
  (enacted July 9). **Pasco County's
  existing record had a real data error**: stamped `enacted_date: 2026-06-12`,
  but the June 12 WUSF article it cited only describes a **first reading**
  ("A second and final vote is scheduled for July 14") — the true enactment
  was July 14, with a 2.5 MW threshold (down from a proposed 10 MW) never
  previously captured. Two different WUSF articles, different reporters,
  different URLs, covering the same county a month apart, is exactly the shape
  that produces this error — a "final" framing in an early article's headline
  doesn't mean the vote in it was actually final.
- **A Georgia moratorium/ordinance wave is much larger and NOT actioned this
  pass** — logged to BACKLOG.md instead. One overview source cites 32 counties
  + 21 cities with moratoriums/ordinances/drafts as of mid-2025; the seed has
  2 Georgia records. This is bigger than the Colorado (07-27) or Florida
  (this pass) waves that got a dedicated in-session sweep — deliberately left
  for its own future pass rather than rushed into this one, per the
  "efficient-first, don't force scope" principle. Concrete near-term threads
  (DeKalb's repeatedly-extended moratorium, Coweta's possible second
  moratorium) are in BACKLOG.md with what's known so far.
- **`connectors/scout.py` (new)** — a mechanical "is there anything new?"
  sweep (fetch known index pages, extract headlines, diff against the seed by
  token overlap), built at the user's request after this session ran 3
  research agents. It replaces the *fetching + first-pass triage* an agent
  used to do by hand, not the judgment after it. **A same-session adversarial
  code review of the PR caught 3 real matching bugs in the first cut**
  (a flat 2-token match floor made 57 of 111 moratorium records structurally
  unmatchable regardless of headline wording; the generic-word stoplist only
  covered company names, not utility names; a raw-substring fallback in
  `relevant()` let "gw" match inside "Edgware") — all fixed in the same pass,
  with regression tests. Worth noting as its own lesson: a first-cut heuristic
  tool shipped with real, reproducible bugs on day one, not just abstract
  gaps — a review pass that actually *runs* the tool against live data (not
  just reads the diff) is what caught these. See its module docstring and
  `connectors/README.md`'s "What a script can't do here" section for the
  fixed bugs plus what's still a genuine, unfixed limit (JS-rendered tracker
  sites returning a contentless 200 that doesn't show up as "blocked", no
  memory of previously-dismissed candidates across runs). Use
  `python -m connectors.scout projects` / `moratoriums` / `all` as the FIRST
  step of a future refresh's discovery dimensions, before reaching for an
  agent — only escalate for the "no seed match" shortlist it produces, not
  for the initial fetch.
- **Agent-dispatch shape that worked well this pass**: 3 parallel background
  agents, one per research family (DOE companies deep-research; standard
  new-site scouting; moratorium/tariff scouting+verification), matching the
  existing "fewer, larger agents" rule. All three ran ~2-3x longer than a
  typical single-company gap-fill agent (the DOE one used 55 tool calls / 763s
  — by far the largest single agent this project has dispatched) because each
  was a genuinely open-ended multi-source research task, not a bounded
  per-record lookup — budget accordingly when a request spans a new,
  unexplored angle rather than a routine recheck.
