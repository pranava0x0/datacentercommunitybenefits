# SPEC — Ratepayer Pledge v2: 200+ Signatory Tracker & Site Redesign

**Status:** Draft for review · **Author:** Claude (session 2026-07-25) · **Owner:** Pranava
**Branch:** `jam/ratepayer-pledge-redesign-191fd2`
**Decision needed:** approve/adjust decisions D1–D6, then execute phases P0–P6.

---

## 0. TL;DR (press-release framing — working backwards)

> *The Data Center Community Benefits dashboard is now the independent tracker for the
> White House Ratepayer Protection Pledge. On July 23, 2026 the pledge expanded from 8
> companies to 200+ organizations — utilities, electric cooperatives, data-center
> developers, and 23 governors. The dashboard imports the full signatory roster, scores
> real data-center sites against the pledge's five commitments, and rolls everything up
> into per-state, per-utility, and per-developer views — so a policymaker, journalist, or
> resident can answer "who signed, and is it actually showing up where I live?" in under
> ten seconds, from a landing page that speaks the pledge's own visual language.*

The site already has most of the data (117 sites, 39 pledge assessments, 25 tariffs, 97
moratoriums, per-principle rubric already in the schema). What's missing is the **roster**
(8 tracked signatories vs. 281+ on the White House page), the **rollups** (state /
utility / developer lenses), and a **landing page** built for time-to-first-insight.

---

## 1. What changed externally (verified 2026-07-25)

Facts below were verified against the cited page directly (per the v1.19 lesson: search
synthesis is not a citation). Items marked ⟲ are **rolling values** — re-verify at import
time, never hardcode.

| Fact | Value | Source |
|---|---|---|
| Expansion announced | **July 23, 2026**, event at EPA HQ | EPA newsroom release |
| Announcement-day adds | 55 utilities · 106 co-ops · 28 developers · 23 governors (≈189 orgs — the user's "188") | NOTUS / DCD via search; EPA release has no counts |
| WH roster today ⟲ | **281 orgs**: 176 cooperatives · 69 utilities · 35 developers (page's own sections drift by ±1 — it's a living list) | whitehouse.gov/ratepayer-protection-pledge/ |
| Coverage groups on WH page | 23 governors ("state regulators") · 7 hyperscalers (March round, "electricity buyers") · 250+ utilities/co-ops ("electricity sellers") · 36 developers | WH pledge page, "Coverage & Enforcement" |
| Governor instrument | Addendum to the pledge; all 23 are Republican governors; commits to "implement the principles … to the greatest extent possible in their respective positions" | RGA release, 2026-07-23 |
| The 23 states | AL, AK, AR, GA, ID, IN, IA, LA, MS, MO, MT, NE, NV, ND, OH, OK, SC, SD, TN, TX, UT, WV, WY | RGA release |
| Coverage claims | "80% of all power delivered to American homes and businesses" · "263M Americans — 75% of the population" | WH page + EPA release headline |
| Signed pledge PDF | `/wp-content/uploads/2026/07/Ratepayer-Protection-Pledge-Signed.pdf` | WH page |
| Original pledge text (.gov) | Federal Register 2026-04645 (2026-03-09) | federalregister.gov |
| Codification track | H.R. 9340 "Ratepayer Protection Act" advanced House E&C **52-0** on July 21, 2026 (would direct state PUCs to consider full-cost rules for ≥100 MW loads) | POWER Magazine (verify against congress.gov at import) |
| TVA signed | July 23, 2026 (federal utility — a `federal`-jurisdiction wrinkle like the FERC tariff case) | Chattanooga Times Free Press |
| Enforcement skepticism | Brookings: pledge "needs enforcement"; WSJ skepticism is quoted **on the WH page itself** | Brookings; WH page |

**The five commitments** (verbatim from the WH page — these map 1:1 onto the existing
`PLEDGE_PRINCIPLES` in schema.py, which is the single biggest de-risk in this spec):

| # | WH page commitment | Existing schema slug |
|---|---|---|
| I | "Build, bring, or buy new power supply." | `new_generation` |
| II | "Pay for new power delivery infrastructure." | `delivery_infra` |
| III | "Pay whether they use the power or not." | `separate_rate` |
| IV | "Invest in local jobs and workforce development." | `local_jobs` |
| V | "Contribute to grid and community resilience." | `grid_resilience` |

**WH page design language** (captured from the rendered page, tokens read via
`getComputedStyle`):

| Token | Value |
|---|---|
| Page background | cream `#F2EEE3` (`rgb(242,238,227)`) |
| Ink / text | deep navy `#151A30`; darker section navy `#0D132D` |
| Accent | gold/ochre (italic words, big numerals) |
| Display type | Instrument Serif, 400, tight tracking (−0.02em), huge sizes; italic accent words |
| Body type | Instrument Sans, 18px |
| Labels | letterspaced ALL-CAPS kickers ("THE PLEDGE", "COVERAGE") |
| Motifs | fine-line transmission-tower/power-line illustration; Roman numerals I–V; big-stat blocks with hairline top rules; "WHY" callouts under each commitment |
| Structure | one-pager with section nav: Overview → Everyday Infrastructure → The Pledge → Coverage → Signatories; filterable roster with alphabet index, category chip + domain per row |
| Hero copy | "Data centers pay *their* way. Ratepayers pay theirs." + stat quartet (200+ / 263M / 80% / 5) |

---

## 2. Current state (verified against local data, 2026-07-25)

Queried, not assumed (base-repo rule: a spec's data assumptions are guesses until you
query the data):

- **Projects:** 117 (44 announced / 46 construction / 27 operational) across **35 states**; newest `captured_at` 2026-07-15 → 10 days stale, and the user flags the site list needs a refresh.
- **Ratepayer assessments:** 39 sites (14 `affirmed` / 22 `pledge_only` / 3 `contested`). Per-principle sub-assessments already supported (`Ratepayer.principles`, statuses met/partial/not_met/unknown) and mirrored in app.js with labels + descriptions.
- **Tariffs:** 25 records, 19 states, 23 distinct utilities — names are messy ("AEP Ohio (Ohio Power Company)", "NV Energy") → roster matching needs an alias map, not string equality.
- **Moratoriums:** 97 (43 city / 28 county / 25 state / 1 federal). **No state-code field** — records carry `jurisdiction` ("…, TX") + `jurisdiction_type`; state rollups need a derived `state_code`.
- **Companies:** 10 tracked; `ratepayer_pledge_signatory` flags exactly 8 (7 White House + QTS/DOE) with tests freezing that roster.
- **Governor-state coverage:** of the 23 governor states, **20 have projects, 9 have tariffs; AK / MT / SD have no records at all** (honest-gap display needed, not fake fill).
- **Uncommitted collected data (main checkout, NOT in this worktree):** +471/−102 lines across 6 seed files, dated 2026-07-05 — a new site (`amazon-montgomery-city-mo`) with 3 claims (including an Ameren Missouri "costs … not passed on to other ratepayers" quote — pledge-relevant), a large moratorium block (+327 lines), tariffs (+81), responses (+11), and a regenerated ISSUES.md. This is the user's collected data; it predates the committed 7/15 refresh in places, so it must be **reconciled, not blindly merged** (dedupe check: e.g. `google-jackson-county-al` appears on both sides).
- **Perf baseline:** FCP ~340 ms · 6 requests · ~202 KB first paint; code-split per tab; no web fonts, no images. This is a guardrail, not trivia.
- **China research** (`china_*.json`, summary docs): committed and already wired into the moratorium payload/panel — stays as-is; no work in this spec.

---

## 3. Problem, users, jobs

**Problem (fall in love with the problem, not the solution):** The pledge grew 35× in one
day and became the organizing frame for the entire "who pays for data-center power"
debate — with a codification bill moving in Congress. Our site tracks 8 signatories
beautifully and 273+ not at all. Meanwhile the answer to the most-asked question — *"my
state/utility signed; is it real at the sites near me?"* — is scattered across five tabs
that each assume the reader already knows our information architecture.

**Users & jobs (JTBD):**

| Persona | Job-to-be-done | Today's friction |
|---|---|---|
| Policymaker / advocate | "Show me what my state signed up for, and what leverage that gives me in the next negotiation." | No state lens; governor addendum not represented at all |
| Researcher / journalist | "Which signatories have site-level evidence vs. paper-only signatures? Where is it contested?" | Scorecard exists but is buried under a comparison-matrix landing; roster absent |
| Resident / community group | "A data center was announced near me — who's on the hook for my electric bill?" | Needs 3+ tab hops (Explorer → Ratepayer → Tariffs) to assemble |
| Utility / developer staff | "What are peers committing to, and what does 'good' look like?" | Utility layer doesn't exist |

**Editorial stance (unchanged, load-bearing):** we adopt the WH page's *visual language*,
not its *voice*. The pledge is promotional; we are the independent tracker. Keep the
blueprint framing, keep the contested/critical records (Brookings, WSJ-skepticism,
Synapse/Mississippi), present the all-Republican governor roster as sourced fact without
endorsement or snark. No trust scores, no LLM-classified stances — all frozen rules stay.

---

## 4. Goals, metric, guardrails

**North-star metric — Time to First Key Insight (TTFKI):** a first-time visitor can
answer each of these from the landing view in **≤ 10 seconds / ≤ 1 click**:

1. *Who signed?* → hero stat row (orgs by category, as-of date) — 0 clicks.
2. *Is it working?* → assessed-sites tally (affirmed / pledge-only / contested) — 0 clicks.
3. *What about my state?* → state chip/finder → state panel — 1 click.

Acceptance is testable: a Playwright check asserts all three surfaces render above the
fold at 1440×900 and at 375×812, and each deep-links.

**Guardrails (fail the PR if breached):**

- First-paint payload ≤ **250 KB** / ≤ 8 requests (baseline 202 KB / 6; the redesign gets ~50 KB headroom, roster and rollups stay lazy). Add a CI size check (base-repo "budget page weight, fail CI on regression").
- **No web fonts by default** (system serif/sans stacks approximating Instrument Serif/Sans). Self-hosted subset woff2 is a later, opt-in decision (D3).
- Dark mode fully supported on every new surface (tokens in both `:root` blocks, literal values — the var-alias trap in DESIGN.md 12.12).
- Every new record type carries `source_url` + `captured_at`; roster carries `roster_as_of`. No fabricated URLs — copy verbatim from the fetch that proved them.
- All existing frozen vocabularies stay frozen (themes, delivered, ratepayer statuses, tariff params). New vocab ships with Python↔JS parity tests, same drill.

**Non-goals (v2):**

- No runtime backend, no auto-refresh from whitehouse.gov in the browser (static-first stands; import is a curator-run script).
- No per-signatory *pages* for all 281 orgs (roster rows + rollups only; rich pages remain the 10 tracked companies).
- No pledge-compliance scoring of signatories we have no site data for (absence stays honest).
- No non-US scope change, no new claim themes, no social sentiment.
- Not tracking the 106 cooperatives' individual service territories (roster + state only).

---

## 5. Decisions (options considered → recommendation)

### D1 — How to model 281+ signatories

- **(a) Expand `companies.json`** — rejected: breaks the two-gate company rule, pollutes a rich model with 281 thin records, explodes `COMPANY_SLUGS` tests.
- **(b) New lightweight `Signatory` record + `signatories.json` payload — RECOMMENDED.** Companies stay the deep-coverage tier; signatories are the breadth tier; a `matched_company_slug` bridges them.
- (c) Separate files for orgs vs. governors — rejected: one payload with a `category` field covers both; two files complicate loading for no reader benefit.

### D2 — Landing page

- (a) Keep Comparison as default, restyle only — rejected: misses the moment; the pledge is now the site's front door (title tag already says so).
- **(b) New pledge-first landing: WH-style hero band above the tab bar + Ratepayer becomes the default tab — RECOMMENDED.** Smallest change that transforms TTFKI; deep links (`#comparison` etc.) keep working; code-split untouched.
- (c) Full one-pager merging all tabs into scroll sections — rejected: kills per-tab lazy loading (perf baseline), breaks 6 tabs of deep links, weeks of rework.

### D3 — WH theme adoption scope

- **(a) Sitewide light-theme re-skin via CSS tokens (cream/ink/gold + serif display), dark mode preserved — RECOMMENDED.** All colors already flow through CSS vars; this is a token-file + type-scale change, not a rewrite. Fonts: system serif stack (`Georgia, 'Iowan Old Style', 'Times New Roman', serif`) for display, system sans for body — 0 bytes. Optional later: self-host subset Instrument Serif woff2 (~25–40 KB) behind a measured before/after.
- (b) Theme the Ratepayer view only — fallback if (a) reads as too big a visual break; produces a two-design-system app, so only on explicit request.

### D4 — Where state plans live

- (a) New 7th top-level tab "States" — rejected: tab bar is at 6 and crowds mobile.
- **(b) State panel inside the Ratepayer view + state chips in the new Coverage section — RECOMMENDED.** Reuses the tariff/moratorium modal pattern (focus trap, Esc, deep link `#state/TX`) and the existing `buildStateRollups()` from Aggregate.
- (c) Extend the Aggregate tab — cheapest but buries the pledge angle; Aggregate keeps its cross-cutting rollups and links into the state panel instead.

### D5 — Signatory-date-aware eligibility (the subtle one)

Today "pledge-era" = announced on/after 2026-03-04 AND company in the 8-flag roster.
With July signatories (utilities, developers — including **CoreWeave, currently rendered
as a non-signatory**), eligibility must become **per-signatory join date**:
a site is pledge-era if its operator (or its `matched_company_slug` signatory) had signed
by the site's announcement date; the July round's date is 2026-07-23.

- **(a) Derive from `signatories.json` (`signed_date` per record) — RECOMMENDED**; `Company.ratepayer_pledge_signatory` stays as the frozen historical fact for the original 8, tests updated to assert consistency with the roster rather than a hardcoded set of booleans.
- (b) Keep the 8-only cohort and treat July signatories as context — rejected: the user's whole ask is tracking the 200+.

**Consequences to spec now:** `_is_ratepayer_eligible` (refresh.py), `isPrePledgeProject`
(app.js), the non-signatory toggle (v1.21) and its tests all become roster-driven. The
"Not a pledge signatory" card label needs a third state: "Signed July 23, 2026 — site
announced earlier" (pre-*their*-pledge).

### D6 — Sequencing the user's collected data

- **(a) Phase 0 reconciles the uncommitted main-checkout data as its own data PR before any redesign lands — RECOMMENDED.** It touches the same seed files every later phase touches; merging it late = conflict hell. Dedupe against 7/15-committed records, re-run `refresh.py` + full tests, then rebase this branch.
- (b) Cherry-pick into this branch — rejected: leaves main's working tree dirty and orphans the user's copy.

---

## 6. Data model spec

### 6.1 New `Signatory` (schema.py) + `signatories.json`

```python
SIGNATORY_CATEGORIES = ("hyperscaler", "utility", "cooperative", "developer", "governor")
SIGNATORY_TRACKS = (
    "white-house-2026-03-04",   # original 7
    "doe-2026-04-24",           # QTS companion track
    "expansion-2026-07-23",     # July event cohort (incl. governors' addendum)
    "rolling",                  # added to the WH roster after 7/23 (e.g. TVA-style adds)
)

class Signatory(_StrictBase):
    id: str                              # slug: "aep-ohio", "gov-tx", "tva"
    name: str                            # exact roster spelling: "AEP Ohio"
    category: SignatoryCategory
    signed_track: SignatoryTrack
    signed_date: Optional[Date]          # null only for `rolling` when the add date is unknowable
    state: Optional[str]                 # REQUIRED for governor; optional HQ state otherwise
    website_domain: Optional[str]        # roster shows it: "aepohio.com"
    source_url: HttpUrl                  # WH pledge page (or RGA release for governors)
    captured_at: Date
    matched_company_slug: Optional[CompanySlug]   # bridges to the 10 tracked companies
    utility_aliases: list[str] = []      # names as they appear in tariffs.json `utility`
    notes: Optional[str]                 # e.g. "Federal utility (TVA) — signed 2026-07-23"

class SignatoriesPayload(_StrictBase):
    roster_as_of: Date                   # the WH-page snapshot date
    roster_counts: dict[str, int]        # counts AS SHOWN on the page that day (incl. drift)
    pledge_pdf_url: HttpUrl
    signatories: list[Signatory]
```

Rules, in the existing house style:

- **The roster is a snapshot, not a live mirror.** `roster_as_of` is displayed everywhere counts are ("281 organizations as of Jul 25, 2026"). The WH page's own sections disagree by ±1 (35 vs 36 developers) — store what the roster list shows, note the drift in `notes` on the payload, never "fix" it silently.
- **Governors are signatory records too** (category `governor`, `state` required, source = RGA/WH addendum) — one vocabulary, one payload, and the state panel gets its governor row for free.
- **The 7 + QTS get `matched_company_slug`** so existing company logic can derive signatory-ness from the roster (D5). CoreWeave gets matched too (it's both a tracked company and a July developer signatory). Anthropic remains unmatched/absent — still not a signatory; the "Own commitment" affordance stays.
- Validators: governor ⇒ `state` present; `matched_company_slug` ∈ COMPANY_SLUGS; ids unique; category counts ≥ (1 hyperscaler, 1 utility, 1 cooperative, 1 developer, 23 governors) so a truncated import fails loudly.
- Frontend mirror: `SIGNATORY_CATEGORIES` + labels in app.js, parity-tested (`test_signatory_categories_match`), same drill as every frozen vocab.

### 6.2 Import pipeline — `scripts/build_signatories.py`

- Fetch the WH pledge page (requests w/ browser UA, cached to `.signatory_cache/`), parse the roster list (name / category chip / domain), emit `data/seed/signatories.json`. Idempotent; re-run = clean diff of adds/renames.
- Category mapping: roster chips are COOPERATIVE / UTILITY / DATA CENTER; the 7 hyperscalers appear inside the DATA CENTER bucket on the page — the script re-tags known hyperscalers via `matched_company_slug`, everything else in that bucket is `developer`.
- Governors come from a hand-curated block (23 records, RGA source) — the WH roster list doesn't include them.
- `--diff` mode prints adds/removals vs. the committed seed before writing (curator reviews, then commits). A removal is *news*, not noise — surface it, never auto-delete.
- Liveness: reuse the validator-v2 fetcher classification (live/blocked/dead) for the handful of URLs the payload carries. No fabricated .gov links — the moratorium lesson.

### 6.3 Existing-model touches (small, deliberate)

- **`Moratorium.state_code`** (Optional, 2-letter): derived at refresh time from `jurisdiction` suffix parsing with a manual override map; refresh fails on unparseable records rather than guessing. Unblocks state rollups.
- **`Project.serving_utility`** (Optional[str]) + optional `serving_utility_signatory_id`: backfill top ~20 pledge-era sites during P6 (it's already implicit in several claims, e.g. Ameren/Entergy/NIPSCO). Null elsewhere — "Not disclosed".
- **No change** to Claim/CommunityResponse/Tariff models. H.R. 9340 and the TVA signing enter as *records* (a `resources`-style link on the payload + a landing "policy context" line), not new types.

---

## 7. UX spec

### 7.1 Landing (new, above the tab bar)

WH-page structure, our voice, both themes:

- **Hero band:** kicker `RATEPAYER PROTECTION PLEDGE — INDEPENDENT TRACKER`; display headline in serif, e.g. "Who signed — and is it showing up on the ground?" (one italic accent word, gold). Sub-line keeps the existing balanced description.
- **Stat quartet** (computed from data at render, never hardcoded): `281 orgs (as of …)` · `23 governors` · `39 sites assessed` · `5 commitments`. Each stat deep-links (roster / states / scorecard / commitments).
- **Three pathway cards** (the TTFKI surface): *For policymakers →* your state's plan · *For researchers →* the site scorecard · *For communities →* find sites near you (Explorer pre-filtered). Card pattern reuses `.rp-stat` styling lineage.
- **Draft banner stays** (it's doing expectation-setting work), restyled to the new tokens.
- Tab bar unchanged in structure; **default active tab → Ratepayer**; `#comparison` et al. still deep-link. `_lastDetailTab`-style session memory NOT added for the top-level tab (reload = pledge-first, deliberate).

### 7.2 Ratepayer view v2 (becomes the anchor view)

Section order mirrors the WH one-pager, replacing the current stat-tiles-then-roster stack:

1. **The Pledge** — five commitments as Roman-numeral cards (I–V), each with the verbatim WH title, our neutral one-line gloss, and a live count of sites `met / partial / not_met` on that principle (from `Ratepayer.principles`). This turns the existing rubric into the page's spine.
2. **Coverage** — category stat row (utilities / co-ops / developers / governors, as-of date) + **state chip grid**: 23 governor chips (filled = has data, hollow = AK/MT/SD-style empty, with an honest "no tracked records yet" state) plus chips for non-governor states that have data. Click → state panel (7.3).
3. **Signatory roster** — searchable, category-filterable list (alphabet index like the WH page; name + category chip + domain + track/date). Lazy-rendered (281 rows; render on first expand, virtualize only if measured jank). Tracked companies link to their company pop-out; `contested`-involved signatories carry the ⚠ affordance.
4. **Site scorecard** — existing cards, plus: sticky filter/search toolbar (absorbs the BACKLOG item), ⚠ concern cards sorted first, and the D5 third bucket label for sites announced before *their operator's* signing date. CSV/PDF exports gain `signed_track` + principle columns.

### 7.3 State panel (modal, deep-linkable `#state/TX`)

Tariff-modal pattern verbatim (backdrop, focus trap, Esc, return-focus). Content, all
from already-collected data:

- Header: state name + governor row (signed date + addendum quote link, or "No governor signature — data shown for context").
- **Sites** in state with ratepayer status chips → Explorer/scorecard links.
- **Tariffs** filed there (status + LBL-element count) → tariff modal links.
- **Moratoriums** (via new `state_code`) with status chips.
- **Utility signatories** operating/HQ'd there (roster subset via `state`/alias map).
- Empty sections render the standard honest placeholder, not hidden.

### 7.4 Per-utility and per-developer lenses

No new pages. The roster row *is* the lens: expanding a utility shows its tariff records
(alias-matched) and any sites where `serving_utility` matches; expanding a developer
shows its tracked projects if any (`matched_company_slug`), else roster metadata only.
Aggregate view gains a "by signatory category" rollup row-group using the same helpers.

### 7.5 Theme tokens (both `:root` blocks, literal values)

| CSS var | Light | Dark |
|---|---|---|
| `--bg` | `#F2EEE3` cream | `#0D132D` deep navy |
| `--ink` | `#151A30` | `#EDE8DA` warm off-white |
| `--accent-gold` | `#A8862C` (AA on cream at display sizes; test) | `#C9A94E` |
| `--band-navy` | `#151A30` | `#080D22` |
| `--hairline` | `rgba(21,26,48,.18)` | `rgba(237,232,218,.18)` |

Display serif stack (no webfont): `Georgia, 'Iowan Old Style', 'Times New Roman', serif`,
tight tracking on display sizes only. All existing per-company/status tokens re-checked
for contrast against the cream bg (the amber `contested` hue vs. gold accent needs a
deliberate distinction — gold = brand accent, amber = status, don't let them collide).
Existing stance/delivered/ratepayer/tariff token *names* unchanged — values retuned.

---

## 8. Phasing (Now / Next / Later — each phase = one PR, shippable end-to-end)

North-star rule from the base repo applies: smallest version that works end-to-end;
no phase merges 80%-done.

| Phase | Scope | Acceptance (falsifiable) | Est. |
|---|---|---|---|
| **P0 — Reconcile collected data** (BLOCKS ALL) | On main: review + dedupe the uncommitted 2026-07-05 seed edits vs. 7/15 HEAD; `refresh.py`; full pytest; data PR; rebase this branch | Main checkout clean; no duplicate ids; tests green; `amazon-montgomery-city-mo` + new moratorium/tariff records live | 1 session |
| **P1 — Signatory registry** | Schema §6.1 + builder §6.2 + seed import + parity tests; payload lazy-loads on Ratepayer view | 281±drift orgs + 23 governors in seed, every record sourced; `roster_as_of` rendered; count-sanity tests green | 1–2 sessions |
| **P2 — Landing + theme** | §7.1 hero/pathways, default-tab swap, §7.5 tokens sitewide, TTFKI Playwright check, CI size budget | TTFKI test passes at both viewports; first paint ≤ 250 KB / ≤ 8 req; dark mode parity screenshots | 1–2 sessions |
| **P3 — Scorecard v2 + eligibility** | §7.2 commitments spine + sticky filter; D5 roster-driven eligibility in refresh.py + app.js; non-signatory toggle rework; export columns | Principle counts match seed; CoreWeave sites re-bucketed correctly; updated cohort tests green | 1–2 sessions |
| **P4 — State panels** | `state_code` derivation + §7.3 modal + state chips + `#state/XX` deep links | Every governor state opens a panel; AK/MT/SD show honest-empty; keyboard/focus tests green | 1–2 sessions |
| **P5 — Utility layer** | Alias map (23 tariff utilities → roster ids); roster-row lenses §7.4; Aggregate category rollup | ≥ 80% of tariff records matched to a roster signatory (report unmatched, don't force) | 1 session |
| **P6 — Site-list refresh** | data-refresh skill / REFRESH.md run; roster-as-lead-list sweep (35 developers); `serving_utility` backfill top 20; ISSUES.md gaps (power_mw etc.) | New sites carry live sources; refresh + validators green; AGENT_RUNS row appended | 1–2 sessions, parallelizable after P1 |

Rollout: phases land behind nothing (static site) — the draft banner carries a one-line
"Redesign in progress" note during P2–P4 if mid-state ships.

**Agent guidance (per AGENTS.md discipline, user directive):** research-shaped phases
only — P1 roster verification and P6 site sweep get **1–2 Sonnet 5 agents max**
(`model: sonnet`), file-deliverable pattern, verbatim-URL rule in the prompt, ≤2
fetches/record scope, breadth-batched with skip-lists; append AGENT_RUNS.md
retrospectives. Code phases (P2–P5) run inline — no agents. This session spawned none
(direct fetches were cheaper: 2 searches + 4 fetches + 2 rendered snapshots ≈ well under
the 10-URL gate).

---

## 9. Risks & pre-mortem ("it's six weeks later and this failed — why?")

| Risk | Likelihood | Mitigation |
|---|---|---|
| WH page changes structure/URL; import breaks or roster silently shrinks | High (it's a campaign-style site) | Snapshot discipline (`roster_as_of`, cached HTML in repo-ignored cache); `--diff` mode makes removals a reviewed event; page PDF archived link in payload |
| Politicization reads: cream/gold + all-R governor list makes the site look aligned with the administration | Medium | Voice separation (§3); "independent tracker" kicker; keep contested/critical records prominent; both-themes neutrality pass in P2 review |
| Utility name matching produces false joins (AEP Ohio vs AEP Texas vs American Electric Power) | Medium | Curated alias map, exact-id joins only, unmatched reported in ISSUES.md — never fuzzy-auto |
| Scope creep: 281 thin records pull toward "rich pages for everyone" | Medium | Non-goal stated; two-tier model is the contract; new company additions still require the two-gate rule |
| Perf regression from roster + serif + hero | Low | Lazy roster, no webfonts, CI size budget in P2 |
| Governor "addendum" overstated as equivalent to corporate pledge | Low | Distinct category + track labels; addendum language quoted verbatim in the state panel |
| P0 reconciliation surfaces conflicting records (7/05 vs 7/15 truths) | Medium | Dedupe by id + `captured_at` recency wins; disagreements logged to ISSUES.md, not silently chosen |

**Kill/adjust criteria:** if P2's TTFKI test can't pass without pushing first paint past
250 KB, cut the hero illustration before cutting the stat row; if the roster import can't
be made deterministic, ship the July-23 announcement cohort as a static curated seed and
mark the rolling adds as a BACKLOG follow-up.

---

## 10. Open questions for Pranava

1. **D2/D3 scope confirm:** pledge-first landing + sitewide cream/ink re-theme (dark mode kept) — or theme the Ratepayer view only first?
2. **Governor records:** comfortable rendering party-uniform roster as plain fact with RGA sourcing (recommended), or add a one-line methodology note near the state chips?
3. **Webfont:** stay system-serif (0 KB, recommended) or self-host Instrument Serif subset (~25–40 KB) for closer fidelity?
4. **Comparison view demotion:** OK that the matrix is one click away instead of the landing? (Its JTBD—"does this company speak to this theme at all"—is unchanged, just no longer the front door.)
5. **P0 executor:** run the reconciliation on main directly, or want a review of the 2026-07-05 diff first?

---

## 11. Sources (fetched & verified this session)

- White House — Ratepayer Protection Pledge (roster, five commitments, coverage, design): <https://www.whitehouse.gov/ratepayer-protection-pledge/> (captured 2026-07-25; rendered snapshot + computed styles)
- Signed pledge PDF: <https://www.whitehouse.gov/wp-content/uploads/2026/07/Ratepayer-Protection-Pledge-Signed.pdf>
- EPA newsroom — expansion announcement, July 23, 2026 (five commitments verbatim; Zeldin quote; 80% headline): <https://www.epa.gov/newsreleases/president-trump-expands-historic-ratepayer-protection-pledge-protect-american>
- RGA — 23 Republican governors sign (state list; addendum language; Kemp quote): <https://www.rga.org/republican-governors-sign-president-trumps-ratepayer-protection-pledge/>
- Federal Register — original pledge text (2026-04645, 2026-03-09): <https://www.federalregister.gov/documents/2026/03/09/2026-04645/ratepayer-protection-pledge>
- DCD — "Trump expands Ratepayer Protection Pledge with 200-plus new signatories" (counts: 55 utilities / 106 co-ops / 28 developers / 23 governors) — bot-walled 403 on fetch; counts corroborated by NOTUS + search index; re-verify at import: <https://www.datacenterdynamics.com/en/news/trump-expands-ratepayer-protection-pledge-with-200-plus-new-signatories/>
- NOTUS — expansion coverage (utility names: Avangrid, Dominion, Entergy, NextEra, PG&E): <https://www.notus.org/energy/trump-expands-ratepayer-pledge-republican-governors-utilities>
- POWER Magazine — H.R. 9340 advanced 52-0 (verify against congress.gov during P1): <https://www.powermag.com/white-house-expands-data-center-ratepayer-pledge-as-congress-moves-to-codify-protections/>
- Chattanooga Times Free Press — TVA signs (2026-07-23): <https://www.timesfreepress.com/news/2026/jul/23/tva-signs-trumps-ratepayer-protection-pledge-for/>
- Brookings — enforcement critique (candidate CommunityResponse/context record): <https://www.brookings.edu/articles/the-pledge-to-protect-ratepayers-from-ai-data-center-costs-needs-enforcement/>
