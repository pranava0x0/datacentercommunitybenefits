# BACKLOG.md

Roadmap and ideas, prioritized. Per CLAUDE.md: when an idea comes up
during development, add it here immediately — don't lose it. Each item:
brief description + priority (low / medium / high) + (optional) acceptance
criterion.

---

## High priority

### Add a `key_reasons` ↔ CSS parity test
Found 2026-07-15: `docs/styles.css`'s `.badge-reason-*` classes had drifted
from `MoratoriumReasonType` (schema.py) — two dead class names, one missing
value, silently unstyled/unspaced badges, caught only by eyeballing a
screenshot, not by `pytest`. THEMES / DELIVERED_STATUSES / RATEPAYER_STATUSES
all have an explicit Python↔JS parity test (`test_X_match`); `key_reasons`
doesn't have an equivalent CSS-class check. Add one: assert every value in
`MORATORIUM_REASON_LABELS` (or the schema Literal) has a corresponding
`.badge-reason-<value>` rule in styles.css, so a future enum rename fails
`pytest` instead of shipping an unreadable badge. *Priority: medium — cheap
to add, prevents a recurring silent-drift class of bug.*

### Medium-gap research side-findings from 2026-07-15 refresh
A 57-project pass (10 agents, one per company grouping) confirmed 13 clean
fills (applied) out of ~85 requested fields — the rest are genuinely
undisclosed at every source checked, consistent with the pattern already
established in the critical-gap pass. A few things surfaced worth a curator's
attention beyond the plain "not found" gaps:
- **`google-michigan-city-in` jobs discrepancy** — the record already shows
  500 jobs, but a directly-fetched DCD article states "30+ jobs." Worth a
  second look to see which is right before the next refresh cycle.
- **`amazon-richmond-county-nc` has a real 1,600 MW figure**, but it's
  diesel-backup generation capacity ("21 buildings supported by 1,600
  megawatts of diesel generation" per the site's own permit application), not
  grid/IT electrical capacity like `power_mw` means elsewhere in this
  dataset. Deliberately left `power_mw` null rather than populate it with a
  category-mismatched number — flagging in case a future schema wants a
  distinct `diesel_backup_mw` field.
- **`qts-clinton-ia`, `qts-eagle-mountain-ut`, `qts-york-county-sc`** all
  have an explicit QTS non-disclosure statement on their own project pages
  ("we don't disclose specific power capacity for security and
  confidentiality reasons") — these are confirmed-never-coming gaps, not
  research misses. Don't re-research `power_mw` for these three next cycle
  without a new lead (e.g. a utility interconnection filing).
- **`aws-calvert-cliffs-md`'s widely-repeated "~1.5 GW" figure is
  unconfirmed** — traces only to a third-party tracker (dcpulse.com) that
  itself labels it an internal estimate with no source citation. Don't use it
  without a primary source.
- **`aws-wilmington-oh` has been tabled twice** by the Wilmington Planning
  Commission (Nov 2025, then Jan 7 2026) over incomplete traffic/lighting
  studies and Amazon reportedly dodging a question about PFAS in facility
  water discharge — a plausible `CommunityResponse` (negative/local_government)
  candidate not yet captured.
- **`qts-dane-county-wi` claimed_jobs left unresolved** — two conflicting
  figures exist (an early filing-stage article's "450 permanent jobs," vs.
  "up to 5,000 trade jobs" from the later formal $12B announcement); the
  jobs figure wasn't populated pending a curator call on which one is current.

### Citation-audit follow-ups from 2026-07-15 refresh (partial matches)
A 35-record spot-check (source_url fetched directly, not search-synthesis) found
5 "partial" cases: the recorded figure is plausible and likely correct, but isn't
actually stated on the record's own cited page. Not urgent (no reason to believe
the numbers are wrong), but each needs a better citation or a softened figure:
- `amazon-montgomery-city-mo` — $10B investment not on the cited aboutamazon.com
  page (only "several billion dollars, unspecified").
- `google-mayes-county-ok` — 800 jobs not stated on datacenters.google page.
- `google-henderson-nv` — $6B is Google's combined Henderson+Storey County NV
  figure per the source; misattributed solely to the Henderson site.
- `google-lenoir-nc` — 400 jobs not stated on the cited page.
- `microsoft-boydton-va` — $2B investment / 250 jobs not stated on the cited
  local.microsoft.com page (which only backs the "55 projects" claim).
- `ms-mt-pleasant-wi` — `claimed_investment_usd` ($7B) is a curator-computed
  combined total (documented transparently in `notes`), but the cited
  `source_url` only states the original $3.3B tranche. Needs a citable URL for
  the Sept-2025 $4B second-facility announcement, not a guessed one.
- `qts-aurora-co` — the 65-80 acre / 4-building specifics in `notes` aren't on
  the cited sentinelcolorado.com article; needs a primary source that actually
  states them, or the specifics should be softened.
- Two records (`google-spacex-gpu-partnership`, `microsoft-la-porte-in`) cite
  datacenterdynamics.com, which hard-blocks WebFetch/curl (403, no Wayback
  snapshot) — needs a manual browser spot-check, tooling can't verify these.

### UX inconsistency: two different detail-view interaction patterns
Found via a 2026-07-15 Playwright walkthrough of all 6 tabs. Company Comparison
and Project Explorer open detail records as an **inline pop-out panel** pushed
into the page flow (page scrolls to it, no backdrop). Moratoriums and Tariffs
open detail records as a **full-screen modal overlay** (dimmed backdrop,
centered dialog, Escape/backdrop-click to close) — the v1.19 "Moratorium detail
modal" conversion documented in CLAUDE.md was applied to those two tabs only.
Net effect: clicking a row means something different depending which tab
you're on. Worth a deliberate decision — convert Comparison/Explorer to the
modal pattern for consistency (or intentionally keep the split, e.g. "modal for
list-item drill-down, inline for a persistent map+list layout" — Explorer's
map context might genuinely want to stay on-screen). Not fixed in this session
since it's a real design call, not a bug. *Priority: medium.*

### UX quality: at_a_glance auto-derivation can surface raw promotional quotes
`wonder-valley-box-elder-ut`'s auto-derived (no manual `at_a_glance` override)
Water and Infrastructure fields truncate a first-person marketing quote
mid-sentence: "I'm the only developer of data centers on Earth that graduated
from environmental studies…". Technically working as designed (v1.4: falls
back to truncating the first claim's `statement` at ~90 chars when no curator
override exists), but the result reads oddly next to the neutral phrasing used
everywhere else. Needs a manual `at_a_glance` override for this project, and
worth checking other auto-derived fields for the same pattern. *Priority: low.*

### Leads from 2026-07-15 refresh needing a follow-up verification pass
Surfaced by scouting agents this session; not yet shippable because the key
fact came from WebSearch synthesis or a paywalled/403'd source rather than a
confirmed direct fetch (per the v1.19 "don't trust search synthesis" lesson).
- ~~Google Montgomery County MO (New Florence)~~ — **false lead, already
  tracked.** The scouting agent flagged this as a possible new project, but
  it's already fully captured as `google-new-florence-mo` (captured
  2026-05-31, $15B / 934ac / 1.2GW, ratepayer-affirmed) — same "different
  name, same site" trap the 2026-07-14 learned-pattern entry above already
  warns about (id uses the town name, not "montgomery"/"missouri"). No
  action needed; noting the near-miss so a future scout doesn't re-flag it.
- **CoreWeave / Prime Data Centers, Elk Grove Village, IL** — $850M bond
  financing confirmed live (phemex.com), but the oft-repeated "$2.2B
  contracted revenue" and "15-year lease" figures trace only to low-tier
  aggregators (timothysykes.com, stockstotrade.com) — re-verify against a
  primary filing before using.
- **Crusoe pauses Cheyenne, WY (Tallgrass/Blackstone JV, 1.8 GW)** — reported
  by Bloomberg 2026-06-09 (paywalled, not fetched). Find a non-paywalled
  pickup (Blockspace Media reportedly covered it) before adding as a status
  change.
- **QTS Prince William Digital Gateway, VA — project cancelled** — QTS
  withdrew its final VA Supreme Court appeal 2026-07-02 (confirmed via direct
  fetch, thecooldown.com) after the county's rezoning approval was voided.
  This is a strong "community pushback prevailed" case study, but the
  `Project.status` enum (`announced`/`construction`/`operational`) has no
  "abandoned/cancelled" value and this site was never added as a tracked
  project. **Needs a schema decision** before curating: add a 4th status, or
  represent it as a standalone `CommunityResponse`-style narrative instead of
  a `Project`. See DESIGN.md for precedent (delivered/ratepayer additions
  both required a frozen-vocabulary decision first).
- **`nv-energy-callisto-esa` tariff (docket 24-06014)** — likely `approved`
  per two CitizenPortal.ai regulatory-tracking articles, but both 403'd on
  direct fetch; only WebSearch's synthesized snippet is available, which is
  exactly the failure mode this project's sourcing rules warn against. Left
  `status: proposed` unchanged in the 2026-07-15 refresh. Needs a
  browser-driven (not WebFetch) pass against `puc.nv.gov`'s docket search UI.

### Drive coverage to comprehensive via the research connectors
`connectors/research.py` (added this session) automates collection: `status`
reports gaps, `queries` emits per-site search strings, `harvest` fetches URLs
and auto-extracts publication dates (the slow manual step) + verbatim quote
candidates; the Chrome-MCP bridge (`--html-file` / `--as-url`) handles
JS-rendered SPA pages like `datacenters.google`. As of this session **42/111
projects still have no community feedback and 34 have no project-tied claim**
(run `python -m connectors.research status --list`). **Priority: high.**
Work it in batches: `queries --missing-feedback --limit 10` → run searches →
`harvest` the results → curate stance/constituency (never machine-set) →
merge into `data/seed/`. Output stays in `data/candidates/` (gitignored) until
a human fills the editorial fields. Most older Meta/Google/QTS owner-operator
sites are net-positive community stories; prefer ≥2 independent outlets for any
negative stance (single-source → `single_source: true`).

### Infrastructure partnership UX exploration
v1.18 added two non-traditional "infrastructure partnership" projects: Google-SpaceX GPU lease ($920M/month, 110K GPUs) and Anthropic-xAI compute rental ($1.25B/month). These don't fit the traditional "physical data center site" model — they have no lat/lon, no community, no local jobs/tax/engagement commitments. Current schema accepts them (acreage/power_mw/gpu_count all optional, city/state can be "Virtual"/"N/A") but the UX doesn't surface them meaningfully. 

**Scope:** Determine whether these belong in the dashboard at all, and if yes, design a distinct visual treatment:
- Option A: Exclude entirely. Keep scope to owned/operated or co-located physical sites with actual community presence.
- Option B: Include but surface separately (new tab or sub-section). "Infrastructure partnerships" as a distinct lens showing how hyperscalers diversify compute sourcing (useful for researchers/policymakers understanding the hyperscaler supply-chain ecosystem).
- Option C: Fold into the company-detail pop-out as "Infrastructure partnerships" alongside the owned-site count. Surfaces at a glance without cluttering the main Explorer view.

Editorial question: does the blueprint framing include infrastructure *sourcing* decisions (Anthropic outsourcing to xAI, Google outsourcing to SpaceX)? Or is the blueprint only about *deployed* commitments at sites with actual community touchpoints?

*Priority: medium — affects v1.19 scope decision.*

### [MANUAL] Re-verify Oracle community commitment — permanent 404
`https://www.oracle.com/news/announcement/oracle-ai-infrastructure-local-communities-2026-01-26/`
is 404 with no Wayback Machine archive. Oracle's newsroom has been re-organized.
The existing oracle claims were verified via 3 third-party mirrors in v1.10; those
remain valid. Action: find whether Oracle republished the Jan 26 2026 content at a
new URL (search oracle.com/news/announcement/ for "local communities"). If no new
URL is found, mark existing oracle claims' source_url with a `dead_link: true`
annotation or update to the closest alternative oracle.com page.
*Priority: medium — claims are still supported by 3rd-party mirrors.*


### ~~Aggregate / rollup views~~ **DONE** (Jun 2026)
4th tab (`#aggregate`) ships: 4 stat tiles ($789B investment, 98K jobs,
41.2 GW, 28 states) + company rollup table + state rollup table. Each
row shows project count with A/C/O status pills, power, investment, jobs,
claims, and stance-dot response breakdown. Deep-linkable at `#aggregate`.
Lazy-loads project payload (no Leaflet).

### Time dimension / framework-evolution timeline
Every `Claim` has `published_at`. Build a timeline view showing how each
company's published framework evolved (e.g., Microsoft Datacenter
Community Pledge May 2024 → Building Community-First AI Infrastructure
Jan 2026 → NDA pledge Mar 2026; OpenAI no framework → Stargate Community
Jan 2026). Useful for tracing whether commitments emerged before vs
after community opposition. *Modest front-end work; reuses existing data
without new fields.*

### Outstanding site leads — geographic detail needed
Polling pass 2026-06-08 resolved four of six leads:
- **Nebius PA campus** (Q1 2026 earnings disclosed 1.2 GW; city TBD) — still
  open; would also require adding a new `nebius` company slug across
  schema/app.js/tests before a project record can land.
- ~~**AWS Northern IN +2.4 GW expansion** beyond New Carlisle~~ — **RESOLVED
  (no addable site).** The $15B/2.4 GW announcement names only "new sites
  across Indiana," no specific city/county. Existing `amazon-wheatfield-in`
  (near the NIPSCO Schahfer plant) likely already covers part of it. Strong
  first-party content available if we want a *company-level* AWS claim: David
  Zapolsky on "job creation, skills training… community engagement," and a
  NIPSCO-disclosed ~$1B/15yr ratepayer cost-saving — but no new project record
  until a campus is geographically named.
- ~~**Microsoft Caledonia WI**~~ — **RESOLVED: ABANDONED.** Microsoft pulled the
  244-acre Caledonia site in Oct 2025 after a 2,000-signature petition; not a
  project to add. (Mt. Pleasant / former Foxconn site is already in the seed.)
- ~~**AWS Calvert County MD**~~ — **RESOLVED: ADDED** as `aws-calvert-cliffs-md`
  (v1.18, 2026-06-08). Calvert Technology Center, Lusby MD, ~2,050 ac adjacent
  to Constellation's Calvert Cliffs nuclear plant; concept site plan filed May
  2026. Added with two verbatim AWS claims (water + energy) and a `pledge_only`
  ratepayer block.
- ~~**Stargate "Midwest" 5th site**~~ — **RESOLVED: already in seed.** Revealed
  Oct 2025 as Saline Township, MI — present as `openai-saline-twp-mi`. ⚠️ Note:
  `openai-saline-mi` appears to be a **duplicate** of the same site (same
  township, lat/lon within ~0.01°) — dedupe candidate.
- **Crusoe additional 1+ GW campus** — still open. "Project Jade" is already in
  the seed as `crusoe-cheyenne-wy`; no distinct additional Crusoe campus
  surfaced in this pass beyond Abilene/Sweetwater/Springfield/Jade (all present).

### Pattern synthesis report ("lessons-learned overlay")
Across the 194 community responses we have ~10 recurring themes:
NDA / blinding secrecy, ratepayer cost-shifting, water-draw concerns,
on-site gas turbines, brownfield reuse, construction-period housing
crisis, electrician labor shortage, racial-justice / environmental-
justice litigation, post-approval annexation maneuvers, opaque shell-
entity LLCs. A "patterns observed" overlay would crystallize the
blueprint's lessons-learned narrative without editorializing — pure
aggregation of constituency × stance × theme tags with a per-pattern
"sites where this surfaced" list. *Editorial work to define the
patterns; modest front-end to render.*

### at_a_glance fill — 8 minimal-data projects remaining
87 of 95 projects now have curator at_a_glance summaries (51 added Jun 2026).
The 8 remaining have no investment, jobs, power, or notable claims and are
best served by auto-derivation: qts-east-windsor-nj, crusoe-springfield-oh,
microsoft-heath-oh, microsoft-hebron-oh, google-wilbarger-tx, google-haskell-tx,
amazon-wheatfield-in, google-botetourt-va. Close this item when those projects
gain disclosable data worth a curator override.

### Resume session: matrix gap-fill (last refreshed 2026-05-16 after v1.11)
Six matrix cells still empty across 4 companies — all confirmed-honest gaps
after 5 polling passes. Updated targets / next-attempt notes:

- **Meta — tax_revenue.** Confirmed honest gap after the Lebanon IN, El Paso
  TX, Beaver Dam WI, Tulsa OK, and Richland LA announcement-cycle research.
  Meta executives speak about water/infrastructure/community grants; tax
  dollar figures come from state/local officials. May be a permanent
  editorial choice on Meta's part rather than a sourcing problem.
- **OpenAI — tax_revenue.** `openai.com/index/stargate-community/` returned
  403 throughout 5 passes; we shipped the water + engagement claims via
  syndicated third-party verification (Sherwood, The Register). Tax-revenue
  language requires a browser visit to openai.com — none of the third-party
  outlets quote the page verbatim on local tax.
- **Anthropic — community_grants, education.** Anthropic operates no data
  centers; the Workday/LISC Solopreneurship and Anthropic Academy programs
  exist but target nationally/globally, not data-center host communities.
  Honest permanent gap consistent with Anthropic's no-owned-DC posture.
- **Wonder Valley — community_grants, education.** Exhausted in May 2026
  coverage. Palandjian "AI-literacy courses" is reporter paraphrase. No
  named O'Leary Digital exec verbatim on either theme. Likely permanent.

### Resume session: next polling cycle
After ~30 days from 2026-05-16, re-run the parallel news poll. Focus on:
- DCD + UtilityDive (proven productive sources — see v1.8)
- Texas Tribune / Source NM / Wisconsin Watch / Cowboy State Daily / KSLA
  / Mississippi Today for the community-pushback angle on the high-
  controversy sites (Wonder Valley, Cheyenne, Memphis, Southaven MS,
  Saline Twp, Person Co NC, Kenilworth, Vineland, Caddo Parish, Port
  Washington WI, Putnam Co WV)
- Watch for: status changes (announced → construction → operational),
  acreage/power expansions, regulator orders, NGO lawsuits, community
  benefit-agreement signings
- New sites to watch: Nebius PA campus (location TBD per May 13 disclosure);
  DTE-served Google MI site beyond Van Buren Twp (Q1 disclosure flagged 1
  GW Google contract)

### Source URL deep-links — verify and replace publication-root URLs in responses
v1 seed has ~10 `CommunityResponse` records linking to outlet homepages
instead of specific articles (see [ISSUES.md](ISSUES.md)). For each:
locate the original article via the outlet's archive search, replace the
URL in `data/seed/responses.json`, re-run `python refresh.py`. Add a
follow-up test `test_response_urls_deep_link` that flags root-level
publication URLs.

### OpenAI / Oracle Stargate Abilene — first-party claims pending
Sub-agent research found `openai.com/index/announcing-the-stargate-project/` returns HTTP 403 to scrapers, so the v1 OpenAI / Oracle claims could not be re-verified verbatim against the canonical announcement. Current v1.1 claims for those companies still cite the original announcement URL (which loads in browsers) but the agent could only re-read the Wikipedia paraphrase. Action: visit the URL in a browser, copy verbatim quotes for each claim, refresh `captured_at`. Same for `x.ai/blog/colossus`.

### Many `project_page_url` values point to news articles, not project pages
Several projects (e.g. `google-mesa-az`) didn't have a dedicated company project page — the canonical page is a third-party press release (gpec.org, etc.) instead. Mark these in ISSUES.md and find better URLs over time. The schema accepts any HttpUrl; the field is best-effort.

### Link checker — `refresh.py --check-links`
Add a mode that HEADs every URL across all four seed payloads, reports
4xx/5xx, and exits nonzero. Hook into a weekly GitHub Actions cron so
link rot is surfaced before users hit it. Rate-limited to 2s per host.

### Per-company connector for Microsoft Datacenter Community Pledge
Microsoft's Datacenter Community Pledge page is the most stable hyperscaler
community page and has structured per-region commitments. Build the first
v2 connector (`connectors/microsoft_pledge.py`) emitting `Claim` records,
to validate the connector framework end-to-end before tackling the others.

---

### Bugs found and fixed in the v2 build (2026-07-25/26) — reference, no action
Recorded here because ISSUES.md is refresh-generated and cannot hold them. All
fixed; listed because each has a repeatable shape.

1. **Hardcoded list vs. registry — three separate instances, all passing while
   wrong.** The refresh test's seed-copy list, `tools/build_preview.py`'s
   `DATA_FILES`, and `test_exactly_the_eight_signatories_flagged`. The preview
   one is the worst: it shipped a bundle whose landing view rendered zero cards
   *and reported PASS*. Root cause: literal beside the thing it enumerates.
   Fixed by deriving all three. Promoted to the base CLAUDE.md.
2. **Roster labelled all 11 tracked signatories with the March 4 date** — four
   months early for the July cohort. Caught by an e2e test written for exactly
   that conflation. *Code bug.*
3. **Stat tile read "8 signatories" beside a 279-row roster.** *Code bug*, same
   root cause as #2 — company-derived where it should be roster-derived.
4. **`t.name` on tariffs is `undefined`** — the field is `tariff_name`. Hit both
   the new roster lens and the state panel. Found by reading rendered output,
   not by a test. *Code bug.*
5. **State code read from the hash after `activateView` had rewritten it**, so
   `#state/GA` yielded `"yer"` and never opened the panel. *Code bug.*
6. **`XX` (the virtual-partnership sentinel) rendered as a state chip.** *Data
   sentinel leaking into UI.*
7. **Two distinct co-ops share a name**; the first parser deduped by slug and
   silently dropped one. Now disambiguates by domain or raises. *Code bug.*
8. **`ny-state-2026-06` cited S7992** — an unrelated NY labor bill. *Data bug*,
   and REFRESH.md already knew the correct number. See the refresh log.
9. **Spec's proposed accent measured 2.96:1** on its own background, below both
   contrast floors. *Spec bug*, caught before shipping. Promoted to base
   DESIGN.md.

### First-paint headroom — reclaimed once, will need it again — **medium**
P5 pushed first paint to 246.5 KB against the 250 KB budget (3.5 KB of
headroom). Fixed by splitting `responses.json` out of `loadProjectData` into its
own `loadResponseData`: **first paint is now 203.9 KB across 7 requests.**
Responses only decorate below-the-fold concern flags, so the Ratepayer view
paints from projects and re-renders the scorecard when responses land; Explorer
and Aggregate, which render response content, await both.

Two options remain for the next time it tightens. **Do not raise the ceiling** —
the budget test says so in its failure message:
- **Ship `claims-index.json` for first paint** (counts + ids, full verbatim
  claims lazy on demand) — the pre-existing idea below, worth ~35 KB.
- **Code-split `app.js`** (~61 KB gz and the single largest asset) so the landing
  loads only the Ratepayer + shared renderers. Biggest win, most work, and it is
  vanilla JS with no bundler.

### Stale status re-checks still open after the 2026-07-27 pass — **medium**
The 2026-07-27 pass resolved 4 of the remaining 6: **henderson-nv-2026-06**
(council rejected the moratorium 2026-07-21 → `failed`), **new-albany-in-2026-06**
(enacted 2026-07-16 → `enacted`), **aps-arizona-large-load-rate-case-2025**
(docket number was simply wrong — corrected to `E-01345A-25-0105` via a direct
azcc.gov fetch), and **duke-nc-large-load-rate-case-2025** (enriched with the
2026-07-17 fast-track settlement terms; docket `E-7, Sub 1300` confirmed
distinct from the general rate case Sub 1329, no change needed). Two remain
unresolved and deliberately un-bumped:

- **hernando-county-fl-2026-06** — the final adoption vote was scheduled for
  July 7, 2026; still couldn't confirm the outcome after 4 attempts this pass
  (floridapolitics.com 402 paywall, wtsp.com timeout, tampabay28.com's cached
  copy predates the vote, wfla.com still 403s). Needs the county's own agenda/
  minutes for 2026-07-07, or a fresh news search once more coverage lands.
- **nv-energy-callisto-esa** — citizenportal.ai (both the stipulation article
  and the follow-up order article) still 403s on every direct-fetch attempt.
  WebSearch synthesis suggests the PUCN accepted a stipulation on the amended
  ESA, but the date is self-contradictory across searches (April 29, 2025 in
  one pass vs. bundled into a 2026 order alongside "NV Energy permit changes"
  and "AmeriGas margin rates" in another) — exactly the kind of unconfirmed
  synthesis this project's sourcing rules say not to ship. Still needs a
  browser-driven (not WebFetch/requests) pass against puc.nv.gov's docket
  search UI for docket 24-06014.

### Leads deferred from the 2026-07-27 refresh pass
- **NJ S731 / A796** — passed the NJ legislature, requires electric utilities to
  design a large-load tariff protecting non-data-center ratepayers for 100MW+
  customers; awaiting the Governor's signature as of this pass. Not a `Tariff`
  record yet — no NJ utility (PSE&G, JCP&L) has filed the actual rate design
  under it. Watch for the implementing filing. *Priority: medium.*
- **Michigan "Affordable and Responsible Growth Action Plan"** — Gov. Whitmer's
  policy framework (announced ~2026-07-20) aiming to make data centers pay full
  cost and protect ratepayers/water. A policy announcement, not a docketed MPSC
  rate case — same "not yet a tariff" shape as NJ S731. Watch for the MPSC
  filing that would actually implement it. *Priority: medium.*
- **Alamance County, NC** — too early to add per the Lake County FL precedent
  (CLAUDE.md / this file's 07-26 entry): commissioners have only scheduled a
  public hearing for 2026-08-17 to *consider* a moratorium, no drafted ordinance
  or vote yet. Check back after the hearing. *Priority: low, time-boxed to
  mid-August.*
- **New Colorado moratorium records lack a clean `.gov` citation.** 6 of the 7
  new CO records added this pass (all but `boulder-county-co-2026-06`, whose
  `bouldercounty.gov` source_url is a genuine .gov page) cite news outlets as
  `source_url` because `larimer.gov` 403'd every fetch attempt and no equivalent
  official page was found/confirmed for Jefferson County (jeffco.us — a real
  government domain, just not a `.gov` TLD, so the validator's regex-based GOV
  check false-negatives it), Broomfield, Woodland Park, Monument, or Longmont.
  Facts are corroborated by 3+ independently-named outlets per record (see
  REFRESH.md's 2026-07-27 entry), but a future pass should look for each city's
  own ordinance-text page as a stronger primary citation. *Priority: low —
  content is well-corroborated, this is a citation-quality upgrade.*
- **`openai-effingham-county-ga` needs a verbatim-quote follow-up.** openai.com's
  own announcement (`openai.com/index/building-ai-infrastructure-with-the-
  effingham-county-community/`) 403'd on every fetch attempt, so the project was
  added from 5+ corroborating outlets but with no `Claim` record — same shape as
  the existing "OpenAI / Oracle Stargate Abilene" item above. Action: visit the
  URL in a browser, pull verbatim community-commitment quotes (jobs, water,
  ratepayer protection — multiple outlets paraphrase a "OpenAI pays full
  infrastructure/electric-service cost, rates won't rise for residents" claim
  that reads exactly like a ratepayer-pledge-relevant statement, but no source
  put it in quotation marks, so it wasn't shipped as a claim). *Priority: medium
  — likely `ratepayer: affirmed` material once a real quote is in hand.*
- **Nvidia-leased San Jose site (300 Holger Way) — operator unclear, not added.**
  A data center at a site Nvidia leased in Dec 2024 is facing a permit appeal
  after Planning Commission approval + a CEQA exemption (20MW, interior tenant
  improvements). Distinct from the Prologis Silver Creek Valley Rd project added
  this pass. Nvidia isn't a tracked company slug and no operator/developer was
  named in coverage found so far — needs that identified before it can become a
  Project record (or a decision that Nvidia itself qualifies under the two-gate
  test, which it likely doesn't — no first-party community-impact page found).
  *Priority: low.*
- **`google-lagrange-ga` acreage discrepancy (270 vs 420 acres).** The seed's
  notes say "420-acre site"; a 2026-07-27 search citing the original Thor
  Equities/Form8tion site acquisition says 270 acres. Could be Google's build-out
  growing the footprint, or one figure being wrong — a July 2026 DCD headline
  ("Google files to expand campus in LaGrange") suggests the former but wasn't
  confirmed via direct fetch (DCD 403'd). *Priority: low.*
- **Nebius PA campus — now has concrete details, still needs a company-onboarding
  decision.** The 2026-07-27 DCD listing surfaced "Nebius details plans for 1.2GW
  data center campus in Pennsylvania" (supersedes the vaguer "city TBD" note in
  the "Outstanding site leads" item below). 1.2GW clears the ≥1GW scale gate: the
  open question is whether Nebius publishes its own first-party community-impact
  framing (gate 2) and whether it's worth the 4-location slug onboarding
  (schema.py Literal + COMPANY_SLUGS, app.js COMPANY_SLUGS, OPTIONAL_ENTITIES,
  color tokens, company summary) per CLAUDE.md's "Companies in scope" section.
  Not actioned this pass — a company-scope decision, not a routine add.
  *Priority: medium, pending an editorial call.*
- **`oracle-dona-ana-nm` gas pipeline rejection** — New Mexico regulators
  rejected a proposed 17-mile natural gas pipeline that would have supplied
  Project Jupiter's power (reported week of 2026-07-20, exact outlet not yet
  pinned down). A plausible new `CommunityResponse` (negative or mixed,
  `regulator` constituency) for an existing project — not curated this pass,
  needs a primary source fetch first. *Priority: medium.*

### Ratepayer v2 — P6 site refresh remains (P0–P5 landed)
`SPEC_RPP_V2.md` P0–P5 are done. P5's utility layer: the alias map meets the
spec's ≥80% bar (20 of 25 tariffs resolve to a roster signatory; the 5 unmatched
are four statewide frameworks and one federal FERC case — genuinely unmatchable,
reported rather than forced). Roster-row lenses and the Aggregate
by-signatory-category rollup shipped.

`Project.serving_utility` is backfilled for **18** sites — only where a source
states the serving relationship verbatim. Six candidates were rejected on
review: a *nearby* Duke plant, a *former* Duke site, an SRP donation, a business
park name, a contingent NIPSCO agreement, and a renewable procurement deal. The
remaining ~99 sites need P6 research; **don't infer a serving utility from
geography** — half the automated candidates were wrong.

- **P6 site-list refresh — not started.** The site list is stale (newest
  `captured_at` 2026-07-15) and the roster's 28 developers are an unmined lead
  list. Also wants `Project.serving_utility` backfilled for the top ~20
  pledge-era sites — it is already implicit in several claims (Ameren, Entergy,
  NIPSCO). This is a data-refresh session (REFRESH.md / the `data-refresh`
  skill), not a code session, and will blow past the 10-URL fetch gate, so it
  needs its own run with explicit approval. *Priority: medium.*

### Chesterfield County SC — enacted_date disputed between two outlets
`chesterfield-county-sc-2026-05` carries a sourcing note in its summary: the
Progressive Journal (its primary source) places the unanimous second reading in
early May 2026; a later Go Laurens roundup describes the ordinance as enacted in
early June. The May date from the primary source is used. Re-check against the
county council minutes and drop the note once resolved. *Priority: low.*

### Governor addendum text is summarized, not quoted verbatim
The 23 governor records cite the RGA release and carry a `notes` line describing
the addendum, but we never captured the addendum's own language verbatim the way
the five commitments are quoted. If the signed PDF
(`Ratepayer-Protection-Pledge-Signed.pdf`, linked in the payload) contains the
governors' text, quoting it would let the state panel show what a governor
actually committed to rather than our paraphrase. *Priority: low.*

## Medium priority

### Tariff schema needs a tax-vs-rate-design distinction
`virginia-data-center-electricity-consumption-tax` (added 2026-07-14) is a
state budget-enacted excise tax, not a utility-filed rate design — but the
`Tariff` schema has no equivalent to `jurisdiction_level: "federal"`'s
carve-out from the Approved/Proposed/Rejected and "tariffs tracked" stat
tiles (see `docs/app.js` `renderTariffStats`/`isFederalTariff`). Right now
this one record silently inflates those counts alongside genuine
PUC-approved rate designs, and it's scored against the 17-element LBL
rate-design taxonomy that structurally can't apply to a flat tax (2/17
elements, both "partial," is the ceiling for an instrument like this).
`regulator` ("Virginia Department of Taxation") and `docket_number`
("HB30, Item 3-5.24", duplicating `legislation[0].citation`) are both
values that don't cleanly fit fields documented for a PUC/PSC docket.
Needs a real migration (a new `instrument_type` field, or an `excluded_
from_stats` flag mirroring the federal carve-out) rather than a field
game — flagging here per CLAUDE.md's "don't add a status/field inline"
convention. Revisit if more tax-type (as opposed to rate-design) records
get added.

### Moratorium.resources should use the same typed model as Tariff.resources
`Moratorium.resources: Optional[list[dict]]` (schema.py) is untyped,
unlike `Tariff.resources: Optional[list[SourceResource]]`, which enforces
required `url`/`title` at validation time. `docs/app.js` (`m.resources.
forEach((res) => addResource(res.url, res.title, false))`, both call
sites) doesn't null-check `res.url`/`res.title` before using them, so a
malformed hand-entered resource (missing either key) would pass schema
validation and throw at render time. Not an active bug — the current
dataset has zero malformed entries — but worth hardening the same way
Tariff already is, given both types serve the same purpose.

### Add OpenAI Stargate site list as it expands
Stargate has only one announced site (Abilene, TX) as of 2025-01. Track
new site announcements and add them as `openai-*` projects with cross-
referenced `oracle-*` capacity-tenancy projects.

### ~~Add per-claim "delivered vs promised" callouts where evidence exists~~ **DONE (v1.13)**
Shipped as the `Delivered` sub-object on `Claim` (schema.py) with a
four-status vocabulary (`delivered`/`partial`/`contested`/`shortfall`),
rendered via `renderDeliveredPanel()` in docs/app.js. See the v1.13 entry
in the Done log below for the full writeup.

### Project status auto-update workflow
When a project moves from `announced` → `construction` → `operational`,
there's no automated reminder to update the seed. Add a tracking column
in [ISSUES.md](ISSUES.md) for each long-lived project's expected
operational date.

### Geographic clustering for the project map
Northern Virginia "Data Center Alley" has multiple AWS sites within ~10
miles; on the map at low zoom they overlap and a click can grab the wrong
one. Consider Leaflet.markercluster, OR a custom decimation a la the
Brownfield project's hash-based decimation. **Re-checked 2026-07-14: the
original "skip if v1 stays at <50 projects" condition no longer holds —
the seed now has 112 projects** — worth picking up.

### ~~Theme-level filters in the Explorer view~~ **DONE**
Shipped as a clickable theme-chip row (`renderThemeFilterChips()` /
`#theme-filter-row` in docs/app.js) rather than the originally-envisioned
dropdown — narrows to projects whose company has ≥1 claim in the selected
theme. Covered by `TestExplorerFiltersPorted` in tests/e2e/test_views.py.

### ~~Constituency filter in the Explorer view~~ **DONE**
Shipped as the `#f-constituency` dropdown, same shape as the other
Explorer filters.

### ~~CSV export of the comparison matrix~~ **DONE**
Shipped as the `#matrix-csv` button (`downloadMatrixCsv()` in docs/app.js).

### URL state for filters — mostly done, one piece remains
Company / state / status / stance / theme / constituency / open-project
already round-trip through the `#explorer` URL (`URL_FILTER_KEYS` in
docs/app.js, covered by `TestUrlState`). Still missing: a
`?company_x_theme=meta:energy`-style deep link for a specific
**Comparison-matrix cell** (not an Explorer filter) so a matrix-cell click
can be shared as a URL.

### ~~Fix broken PDF export on Explorer + Aggregate tabs~~ **DONE (2026-07-14)**
Root cause was a 3-call-site typo — `exportExplorerToPDF` and
`exportAggregateToPDF` called an undefined `formatInvestment` instead of the
existing `formatUsd`. Renamed all three call sites; re-ran the full 12-button
click-through (all 6 tabs × CSV/PDF) with zero console errors. Added
regression tests `TestExplorerView.test_pdf_export_downloads` and
`TestAggregateView.test_pdf_export_downloads` in tests/e2e/test_views.py
(121 e2e + 326 full-suite, all green) so this can't silently regress again.

### ~~Moratorium bill_number formatting consistency~~ **DONE (2026-07-14)**
14 of 59 moratorium records carry a `bill_number`; 6 had drifted from the
schema's documented no-space convention (`'SB 5982'`, `'HB 2992'`,
`'HB 4084'`, `'HF 4888 / SF 4298'`, `'SB7992/AB7234'`,
`'SB 1018-1020 / HB 5594-5596'`). Normalized to `PREFIX000` with no internal
space and a uniform `' / '` separator for companion bills. Deliberately left
two records unchanged — Vermont's `'H.149'` (period-separated is VT's own
official convention) and Henderson NV's `'Bill No. 3927'` (verified verbatim
against the source article — city ordinances cite differently than state
bills). Also left natural-language mentions of bill numbers inside
`summary`/`resources[].title` prose untouched (e.g. "HB 2992" read naturally
in a sentence) — only the structured `bill_number` field needed normalizing.
Strengthened the field's schema.py docstring so the convention doesn't drift
again. Verified in-browser: table renders cleanly, tab order intact.

---

## Low priority / ideas

### "What's new" indicator for returning visitors
`?since=YYYY-MM-DD` (or localStorage last-visit date) puts a small NEW badge
on projects/claims added after that date. Journalists and repeat users have
no way to see what changed between visits. *No schema change needed.*

### `?project=<id>` deep link (standalone)
The most common journalist sharing pattern. Part of the larger URL-state
backlog item but worth breaking out as a quick win on its own.

### ~~Aggregate / rollup table column sorting~~ **DONE (v1.17)**
Click any `<th>` in the company or state rollup tables to sort by that column.
Default sort is investment descending; click again to reverse; alpha sort for
name/state columns. Sort indicators (▲/▼) in headers; `aria-sort` for AT.

### ~~Response constituency breakdown in company pop-out~~ **DONE (v1.17)**
Compact stacked bar (positive/mixed/negative) per constituency in the
company detail pop-out. Lazy-loads the project payload if not yet loaded;
shows total response count across all the company's projects.

### ~~Tooltip preview on matrix cells~~ **DONE (v1.17)**
Hover or focus a ✓ cell → tooltip shows the first claim statement (truncated
to 160 chars) + theme label + "click to view all X claims" hint. Positioned
below the cell, clamped inside the matrix-wrap, hidden on leave/blur.

### ~~CBA / benefit agreement tracking~~ **DONE (v1.17)**
`formal_agreement: bool = False` on `Claim`. Five seed claims flagged:
Microsoft Datacenter Community Pledge, Microsoft grid-pledge, QTS Ratepayer
Protection Pledge, Microsoft Cheyenne $68M offsite pledge, OpenAI Port
Washington $175M infra commitment. Badge renders on claim cards. Two new
seed tests guard: ≥1 formal_agreement exists, all have a source_url.

### ~~Print-optimized CSS~~ **DONE (v1.17)**
`@media print` block hides chrome (nav, buttons, map, filters), shows only
the comparison view, linearizes the matrix, and appends href after links.
Replaces the minimal stub from v1.4.

### ~~Embed widget~~ **DONE (v1.17)**
`docs/embed.html?company=<slug>` renders a self-contained iframe card:
company name/HQ, 8-theme coverage grid (✓/—), claim count, formal-agreement
count, link back to full dashboard. Respects `?theme=dark|light` override
and `prefers-color-scheme`. Zero dependencies beyond companies.json + claims.json.

### ~~Wayback Machine fallback for dead links~~ **DONE (v1.17)**
`check_links.py` HEADs every source_url/dedicated_page_url/project_page_url
across all seed files (rate-limited 2 s/host), queries Wayback Machine CDX
API for each 4xx, writes `dead_links_report.json`, appends entries to
ISSUES.md. `--fix` flag writes `wayback_url` directly into seed JSON.
`wayback_url` optional field added to `Claim` and `CommunityResponse` in
schema; frontend uses it as fallback on source links and shows "(archived)"
label. Run: `python check_links.py` (read-only) or `python check_links.py --fix`.



### 9th theme: noise / land use
Several recent community responses (Loudoun County hearings, Mt Pleasant
WI) center on noise from cooling fans and visual / land-use impact.
Currently those map to `engagement`, which is a stretch. Consider adding
a 9th theme `noise_land`. **REMINDER:** adding a theme requires schema
migration + frontend mirror + theme test parity update — see
[AGENTS.md](AGENTS.md). Do not do casually.

### Add Equinix, Digital Realty, QTS, CoreWeave (v2 scope)
v1 deliberately scopes to the eight named hyperscalers. As colocation
operators publish more substantive community pages — particularly around
AI workloads — revisit. Each addition needs its own slug, palette
swatch, and editorial review.

### International data centers (v2 scope)
v1 is US-only because public-records coverage is richer. Two strong v2
candidates: Ireland (Dublin DC cluster, Irish Times coverage) and
Uruguay (Google water controversy, El País coverage).

### Capture-history view
Each `Claim` already has `captured_at` and the dataset is append-only by
convention; surface a per-company "claims over time" view so a user can
see when a company adopted (or dropped) a specific commitment.

### AI-generated per-project summary (gated, with disclosure)
Similar to the adjacent Brownfield project's AI summary feature: generate
a one-paragraph natural-language summary per project, structured from the
claim + response data. **Strict editorial gates:** must be marked as
AI-generated, must read only from on-disk data (no live LLM lookups), and
must NOT make evaluative judgments — just synthesize.

### Mobile bottom-sheet for the project detail
On mobile (<640px), the project detail panel currently scrolls inline.
Adapt to a bottom-sheet pattern (drag handle, slide up from the bottom)
similar to the Brownfield project. Skip until mobile-traffic data
warrants it.

### Backups / data-source attestation
Snapshot the canonical company source pages (HTML or screenshot) at each
quarterly capture and commit to a `snapshots/` directory. Useful when a
company quietly changes wording — preserves the original text we quoted.
Storage cost is the concern; consider Wayback Machine integration
instead.

---

## Done

- **Jun 2026 — Chrome-session source verification + Meta Huntsville + OpenAI energy gap-fill.** Browser session visited all 4 previously bot-blocked pages. Results: (1) `meta-huntsville-al` confirmed as a real, operational data center distinct from `meta-montgomery-al` — added as project 96 ($1.5B / 2018 groundbreak / 300+ ops jobs / 1,200 peak construction / Madison County / TVA 100% renewable / LEED Gold / $3.9M+ grants since 2019) with 4 project-tied claims (jobs, community_grants, energy, education) sourced from the Huntsville info sheet PDF. (2) OpenAI Stargate Community page loaded cleanly — added missing company-level energy claim (`openai-energy-pay-own-way-2026`: "we commit to paying our own way on energy, so that our operations don't increase your electricity prices") and a project-tied Wisconsin infrastructure claim (`openai-port-washington-wi-infra-175m-2026`: "$175M in local infrastructure upgrades and water restoration projects"). OpenAI tax_revenue confirmed as honest permanent gap (no specific tax language on the page). (3) xAI `x.ai/blog/colossus` now permanently redirects → `x.ai/colossus`; updated source URL on `xai-memphis-colossus` claim. (4) Oracle Jan 26 2026 page permanently 404 with no Wayback archive — moved to open backlog item for curator follow-up. Totals: 13 co / 298 claims / 96 projects / 199 responses.
- **Jun 2026 — dedicated_page_url fixes.** Three broken company links (404) replaced with verified working URLs: Meta `datacenters.atmeta.com/community/` → `datacenters.atmeta.com/`; Google `datacenters.google/community/` → `datacenters.google/`; Amazon `aws.amazon.com/about-aws/global-infrastructure/economic-impact/` → `www.aboutamazon.com/impact/economy/growth`. All three verified 200 via WebFetch before update; refresh.py clean.
- **Jun 2026 — at_a_glance fill (87/95 projects).** Mechanical pass added curator at_a_glance overrides to 51 previously-empty projects (from 36 → 87). Covers all projects with disclosable investment, jobs, MW, acreage, or notable facts; 8 minimal-data projects remain correctly served by auto-derivation.
- **v1.13 — Delivered-vs-promised assessments on Claims.** New optional `Delivered` sub-object on `Claim` with four-status vocabulary (`delivered` / `partial` / `contested` / `shortfall`). Each assessment carries: `status`, neutral 1-2 sentence `summary`, `source_url` + `source_title` for the independent-reporting evidence, and `assessed_at` curator date. Schema in [schema.py](schema.py) with `Delivered` Pydantic model + `DELIVERED_STATUSES` Literal; frontend mirror is `DELIVERED_STATUSES` + `DELIVERED_LABELS` in [docs/app.js](docs/app.js), with parity guarded by two new `test_themes_match_frontend.py` tests. Render lives in `renderDeliveredPanel()` — appended to the existing claim card only when the field is set, so cards without an assessment look identical to pre-v1.13. CSS palette mirrors stance hues (delivered↔positive, shortfall↔negative). Seeded with 12 demonstrative records covering all four statuses across 7 companies: DELIVERED (Microsoft Fairwater operational + 375 FTEs hired + Crusoe Abilene live + QTS Eagle Mountain topping out); PARTIAL (Meta + MS + Google water-replenishment commitments on track but tested by AI growth); CONTESTED (xAI Memphis water-recycling plant paused; xAI "no grid power" pledge + NAACP unpermitted-turbines suit; Microsoft "no abatements" national pledge vs site PILOTs); SHORTFALL (QTS "water-free design" vs Fayetteville 29M unmetered-gallon draw; xAI Memphis tax-revenue projection unverified). Editorial rules: absence is honest gap (no implied delivery); status is curator judgment NOT algorithmic; summary is NEUTRAL synthesis; `shortfall` requires ≥2 independent sources or a citable regulator/court finding. 17 new tests (8 schema, 4 seed-data, 2 parity, 3 e2e); CLAUDE.md + DESIGN.md + README all updated.
- **v1.12 — +11 new sites + 24 at_a_glance + 34 responses (third 4-agent pass).** Three parallel agents surfaced 11 additional 2025-2026 US data-center sites that prior polling missed: OpenAI Stargate Frontier (Shackelford TX, Vantage developer, $25B / 1.4 GW / 1,200 ac — one of the Sept 2025 five-site expansion), Microsoft long-running undertracked sites (New Albany OH, Heath OH, Hebron OH — Licking County triple; Union City GA / East US 3 anchor; West Des Moines IA 5 operational + 6th in construction, ~$6B total), Google Arkansas debut (West Memphis AR Project Pyramid $4B / 1,178 ac broke ground Oct 2025; Little Rock AR Port $1B), AWS Boardman OR Columbia River 1,300-ac land buy, QTS Project Blue Hole (Blakely GA 12M sq ft mega-campus) + DFW2 Wilmer TX expansion. 24 at_a_glance per-theme summaries added to projects from v1.0-v1.4 era that previously had only auto-derivation. 34 community responses across the 10 v1.7/v1.8 sites that previously had zero — notable patterns: QTS Fayetteville unmetered 29M-gallon water draw discovered May 11 2026; Fayetteville council banned new data centers Mar 5 2026; Google Linn County IA annexation maneuver to bypass county zoning (Supervisor Scheetz "race to the bottom"); CoreWeave Lancaster PA city council voted to draft new zoning use class; Google Lima OH + Franklin Furnace OH NDA / shell-entity (Bistrozzi LLC, Tilted Gate LLC) transparency complaints. Totals: 13 co / 276 claims / 74 projects / 194 responses.
- **v1.11 — Project-tied claims + responses for the 12 v1.9 sites.** +22 first-party verbatim claims (Meta Lebanon — Peterson energy/engagement/community, Meta El Paso — Davis infrastructure/energy + Davies jobs, Google Chesterfield — Porat engagement/infrastructure, Google Putnam Co — Allsop engagement, Oracle Port Washington — Altman energy + Hoeschele jobs, AWS Falls Twp — Zapolsky jobs, AWS Richmond Co NC — Zapolsky jobs/education, AWS Caddo — Zapolsky jobs + Wehner energy/education, AWS Bossier — Wehner infrastructure, AWS Vicksburg — Zapolsky community_grants, xAI Southaven — Musk energy + Mayo jobs/engagement). +38 community responses across the 12 sites (range from broad governor welcomes through specific resident lawsuits and NGO Clean Air Act suits). Notable: Port Washington WI voters passed an anti-data-center referendum (Apr 8 2026) requiring future TIFs over $10M to receive voter approval — first such national model. Skipped: QTS Salem Twp claims (only unnamed spokesperson available). First-paint payload budget bumped 150KB → 200KB to accommodate 276 claims.
- **v1.10 — Final gap-fill residuals + URL deep-link fixes + at_a_glance + 5 summary refreshes.** Closed Oracle engagement gap (Jan 26 2026 blog: "Oracle recognizes that when we enter a community, we have an obligation to be a good citizen" — verified via 3 third-party mirrors) and Crusoe community_grants (Cully Cavness 2021 ND newsroom — first-party Crusoe domain, predates current tracked sites but acceptable). 12 source URL deep-link fixes — key correction: resp-meta-newton-water attribution updated from Grist to NYT (July 2025 investigation). 10 curator at_a_glance per-theme summaries for highest-profile sites (Meta Tulsa/Lebanon/El Paso, MS Cheyenne, OpenAI Saline Twp, Oracle Doña Ana / Port Washington, QTS Eagle Mountain, Nebius Independence, xAI Memphis). 5 company-summary refreshes (Meta, Google, Amazon, Oracle, QTS) reflecting v1.8/v1.9 site additions.
- **v1.9 — Comprehensive 4-agent pass: +12 sites, +25 claims, +25 responses, +1 fix.** Four parallel research agents: matrix gap-fill, project-tied claims, community responses, and new-site discovery beyond the 30-day window. New sites: Meta Lebanon IN ($10B / 1 GW) + Meta El Paso TX ($10B expansion / 1 GW); Google Chesterfield VA (Project Peanut) + Google Putnam Co WV; Oracle Port Washington WI Stargate Lighthouse ($15B / 1.3 GW / 672 ac); AWS Falls Twp PA + Richmond Co NC ($10B / 800 ac) + Caddo Parish LA + Bossier Parish LA + Vicksburg MS ($3B); QTS Salem Twp PA (1,700 ac); xAI Southaven MS (Colossus 3 / MACROHARD). Project fix: aws-cumberland-pa lat/lon corrected (record had Cumberland Co PA coordinates but actual site is Salem Twp Luzerne Co adjacent to Talen Susquehanna nuclear plant). Matrix gap-fills (3): OpenAI water (Stargate Community framework via The Register), Oracle tax_revenue ($410M Pitcock Doña Ana commitment), QTS education (Dane Co WI $50M MATC + UW partnerships). 22 project-tied claims + 23 community responses across 8 previously-zero-response sites. Coverage 89% → 93%.
- **v1.8 — DCD + UtilityDive 30-day scan.** Parallel DataCenterDynamics + UtilityDive scan for Apr 16 – May 16 2026. +5 sites (4 Google: Michigan City IN / Lima OH / Franklin Furnace OH / Linn County IA + 1 OpenAI Stargate Milam County TX "Freebird"), +7 first-party claims (Nadella on Fairwater going operational, Google's per-site community/infrastructure/education commitments, Anthropic on Colossus 1 tenancy, Oracle Saline Twp jobs, Meta LevelUp education), +5 responses (4 xAI Memphis — NAACP suit Apr 15 + injunction May 6 + DOJ statement-of-interest May 15 + MS 41-turbine permit Apr 29; 1 Meta Richland — Entergy Q1 $2B customer-benefit confirmation), +2 project field updates (Meta Richland acreage 2,250→3,650 from Phase 2 land buy; MS Mt Pleasant status construction→operational per Nadella Apr 16). DCD blocks WebFetch — agent reconstructed article-level detail from Google snippets + canonical URLs as `source_url`.
- **v1.7.1 — Community responses for new sites + OpenAI engagement gap-fill.** +41 community responses across 14 newly-added sites (21 negative, 11 mixed, 9 positive — distribution by constituency: local_government 15, residents 14, ngo 5, journalist 4, regulator 2, academic 1). Includes Wisconsin PSC "black box" critique of Meta+Alliant, Tulsa City Council moratorium pre-dating Meta Project Anthem reveal, Saline Township board 4-1 rejection → Related Digital lawsuit → $14M community-benefits settlement, Kenilworth NJ rallies (Apr 20 + May 7), Stillwater OK Park View Estates HOA suit against Google over pond sediment, Person County NC NDA controversy → Microsoft's March 2026 pledge to stop signing community-blinding NDAs, Vineland NJ rally → DataOne declines $6.2M city loan + project scaled from 2.4M to <718K sq ft. +1 OpenAI Stargate Community engagement claim verified verbatim via Sherwood News citation of openai.com/index/stargate-community/.
- **v1.7 — 30-day news poll, +19 sites + 26 claims + 7 summary refreshes + Explorer sort.** Four parallel agents polled news for Apr 16 – May 16 2026 across all 13 companies. New sites: Meta (Tulsa OK, Beaver Dam WI), Google (LaGrange GA, Stillwater OK), Microsoft (Person County NC), Amazon (Canton MS, Clinton MS), OpenAI/Oracle (Saline Township MI Stargate, $16B financing close Apr 24), Oracle (Doña Ana NM Project Jupiter with Bloom Energy fuel cells Apr 27), QTS (Eagle Mountain UT, Fayetteville GA, York County SC, East Windsor NJ), Crusoe (Sweetwater TX, Cheyenne WY Project Jade, Springfield OH), CoreWeave (Kenilworth NJ, Lancaster PA), Nebius (Vineland NJ). 26 verbatim first-party claims fill 6 of 8 matrix gaps (Google, Microsoft, Amazon, xAI, CoreWeave, Nebius now complete). Summary refreshes: factual fix to Wonder Valley (Phase 1 = ~3 GW not 1.5 GW; ~40,000 acres not 2,000); major rewrites for OpenAI (Stargate Community framework Jan 21 2026 now exists) and Oracle (per-site Q1 2026 blog framework now exists); minor updates to Meta, Microsoft, Amazon, xAI, Anthropic. Plus Explorer "Sort by" dropdown with default Composite (most benefit) score = equal-weight average of normalized investment + jobs + claim count (min-max against full catalog so ranking is stable as filters change); single-metric options for investment / jobs / claims; project name as tiebreaker.
- **v1.6.1 — Fallback gap-fill via news + executive statements.** Loosened editorial bar: news articles containing direct verbatim quotes from named executives are now acceptable as `Claim` records (paraphrases still rejected). Three parallel agents researched the 30 remaining empty matrix cells; +13 claims added (xAI 3 — Brent Mayo Memphis school upgrades / fabric of community / financial responsibility; Wonder Valley 3 — O'Leary Tucker Carlson + KUTV jobs/tax/water; Oracle 2 — Larry Ellison Stargate + Oracle Academy blog; OpenAI 1 — Lehane NABTU; Crusoe 1 — Lochmiller Wyoming workforce; CoreWeave 1 — Intrator UK closed-loop; Nebius 2 — Sutter KSHB Q&A on infrastructure cost-coverage + community grants engagement panel). Matrix coverage 71% → 83% (87/104). Kept Sam Altman's "completely untrue, totally insane" water quote OUT of the dataset — verbatim but a dismissal of critics, doesn't fit blueprint framing of solutions offered. Added "What counts as first-party" rule to CLAUDE.md.
- **v1.6 — Three new operators (Crusoe, CoreWeave, Nebius) + two major frameworks (Microsoft Jan 2026, Google Mar 2026).** Companies tracked: 10 → 13. Projects: 23 → 27 (Crusoe Abilene, CoreWeave Hammond + Polaris Forge ND, Nebius Independence MO). Claims: 149 → 180 (+31). Microsoft's Jan 2026 "Building Community-First AI Infrastructure" framework adds 8 new claims spanning all 5 commitment areas (electricity-no-pass-through, water-replenish, jobs-NABTU, tax-full-share, AI-training + volunteer-hour match). Google's Mar 2026 Affordability Pledge adds 5 new claims (pay-our-own-way, 22 GW new energy, grid resilience, 9x jobs multiplier, PUE efficiency). Honest skips for Digital Realty + Equinix (both publish corporate ESG but no per-DC community framework) and FluidStack + Verrus (B2B-positioning phase, no community framework yet). OpenAI Stargate Community page (openai.com/index/stargate-community/) still 403'd to scrapers; logged in ISSUES.md as a curator follow-up.
- **v1.5 — Editorial reframe to blueprint.** Hero copy on both views, README, CLAUDE.md project intent reframed as "blueprint of solutions / field guide" rather than "neither hit piece nor puff piece". Detail-panel "Community" tab renamed to "On the ground"; placeholder text updated. Critical responses retained — they're case-study evidence ("lessons learned") for what's working in practice. Editorial integrity rules (verbatim quotes, source attribution) unchanged.
- **v1.5 — Matrix gap-fill from main company websites.** +9 company-level claims (Anthropic water, QTS jobs/energy/engagement, xAI energy, OpenAI energy/community grants, Oracle energy). Matrix went from 50/80 (62%) cells filled to 58/80 (72%). Meta, Google, Microsoft, Amazon now have full theme coverage. Remaining empty cells concentrated in Oracle, Wonder Valley, and parts of xAI/OpenAI — all are honest "no published commitment" gaps confirmed across multiple research passes (the gap itself is editorially valuable signal).
- **v1.4 — Draft banner.** Thin top strip ("Draft · Data collection in progress · Last refresh …") signals the dataset is under active curation. Test guards content + visibility.
- **v1.4 — QTS scope expansion (10th company).** First colocation operator added under the same two-gate editorial rule as Wonder Valley. QTS Cedar Rapids IA (Ratepayer Protection Pledge canonical site, $1.75B / 612 acres / 1.05 GW), QTS Richmond VA RIC5 (first-ever FAST-41-designated data center, 622 acres), QTS Dane County WI ($50M community commitment, 750 MW), QTS Manassas VA (Prince William Digital Gateway controversy). 7 new claims, 6 new community responses spanning Alliant CEO + Cedar Rapids Mayor + Iowa skeptical advocates + Henrico residents + Federal Permitting Council + American Battlefield Trust.
- **v1.4 — Three more 2026 sites.** Google Van Buren Township MI (1 GW, 282 acres, $10M Energy Impact Fund, contested MPSC docket), Microsoft Cheyenne WY 2026 expansion (3,200 acres tripling existing footprint), OpenAI Stargate Lordstown OH (former GM/Foxconn plant, $3B SoftBank). 10 new claims, 5 new community responses including the AG Nessel mixed welcome of Google's contested-case posture.
- **v1.4 — Meta + Amazon deep dive.** Refreshed metrics: Meta Newton investment $1B → $1.5B and jobs 200 → 400 (Dec 2025 info-sheet); AWS Loudoun investment $51.9B → $91.5B and jobs 7,340 → 20,700 (2024 update); Project Rainier flipped to operational (Oct 2025); AWS Cumberland power 960 → 1,920 MW (June 2025 restructured Talen PPA). Added 22 new claims and 19 new community responses including IDEM wetland citation, residential well failures near New Carlisle, FERC follow-up dockets, Sierra Club Virginia 2025 report, Meta Newton Mansfield 33% rate hike, Richland Parish housing displacement, and Crook County school tax-break analysis.
- **v1.4 — `Claim.published_at` field.** Optional Date for the source's own publication date (press release date, article date, FERC-order date), distinct from `captured_at` (curator scrape date). Frontend renders `published_at` when present. Merge script auto-extracts from URLs containing `/YYYY/MM/DD/` path segments.
- **v1.4 — `Project.at_a_glance` per-theme summary.** Optional dict field mapping theme → 1-line phrase. Surfaced in the project Overview tab's "At a glance" section. Auto-derived from project-tied claim metrics when no curator override is provided.
- **v1.3 — Comparison view restructured around company pop-outs.** Removed the global claims list + filter chip below the matrix. Click any company row (or populated cell) to open a per-company summary pop-out with: curated 1–2 paragraph framework summary, link to the company's official community/engagement page, claim + project counts, "View this company's projects →" CTA that pre-filters the Explorer view. Added optional `Company.summary` field to the schema and curated summaries for all 9 companies — including honest "no published framework" gaps for OpenAI / Anthropic / Oracle / Wonder Valley.
- **v1.2 — Matrix simplified to checkmarks-only.** Every populated cell now renders `✓`; the digit branch from v1.1 was removed because volume belongs in the claims list, not the at-a-glance matrix. aria-label still carries the precise count.
- **v1.2 — Project physical/operational metrics.** Added `acreage`, `power_mw`, `gpu_count`, `offtaker` fields to `Project`. Filled values for all 16 projects from canonical company pages + DCD/DCF/CNBC reporting. Frontend formatters auto-convert ≥1000 MW to GW.
- **v1.2 — Wonder Valley deep dive.** +2 O'Leary interview claims (energy-mix, China-race rationale), +4 community responses: Elevate Utah policy brief, BEAR co-leads Brenna Williams and Farrah Pliley, Utah ROOTS coalition. Total Wonder Valley records now: 5 claims + 8 community responses.
- **v1.1 — Project-detail tabs.** Overview / Claims / Community tab strip in the project pop-out, with count badges, in-session persistence, and reload reset.
- **v1.1 — Slim claim cards.** Tighter padding, smaller font, smaller curly quotes; compact variant inside detail panel.
- **v1.1 — Matrix checkmark glyph.** Single-claim cells render `✓`; multi-claim cells render the count.
- **v1.1 — Wonder Valley scope expansion.** First non-hyperscaler entity (O'Leary Digital, Box Elder County UT). Added wonder-valley to `COMPANY_SLUGS` + `CompanySlug` Literal + CSS palette + 3 project-tied claims + 4 community responses (Sierra Club, Utah Clean Energy, Box Elder Commission, Gov. Cox).
- **v1.1 — Data fill-in pass.** Claims grew from 25 → 93 (+68). Added project-specific claims (with `project_id` set) for all 15 hyperscaler projects + Wonder Valley, by web-scraping each project's canonical company page. Added company-level matrix-gap-fill claims for Meta jobs/infrastructure, Google jobs/engagement, Microsoft jobs/tax_revenue/infrastructure, Amazon education/engagement.
- **v1.1 — `Project.project_page_url`.** New optional schema field; renders in detail panel Overview as "Project page" link, distinct from "Record source".

---

## Deferred research leads (from the 2026-07-14 comprehensive pass)

### Mine the "Moratorium Nation" tracker for the next moratorium batch — **high**
`https://mjbommar.github.io/moratorium-data-2026/data/moratorium_inventory.csv`
is a 222-row structured inventory (lat/lon, `date_enacted_iso`, `legal_basis`,
ordinance refs) — **but it carries no per-row source URL**, so records can't ship
straight from it (active-links rule). ~110 city/township candidates remain
unverified, concentrated in **Ohio (30+: Findlay, Avon, Massillon, Maumee, Kent,
Ravenna, Tallmadge, Tiffin, Vermilion, Norton)** and **Michigan (25+: Pontiac,
Saginaw, Saline, Northville, Taylor)**. Also GA cities (AJC: 23 cities), the NC
wave (Hillsborough, Durham, Apex, Boone, Canton, Wendell, Kings Mountain), and
named singles (Inver Grove Heights MN, Cincinnati OH, El Monte CA). Workflow: use
the CSV as a work-list, find + verify a live primary source per row, then merge.

### Upgrade the 47 no-gov-source moratorium records to real `.gov` links — **medium**
`validate_moratoriums.py --links-only` lists them. Many local actions genuinely
have only news coverage; where a live council/board ordinance page exists (often
Granicus/Legistar/Municode), promote it to `source_url` or add to `resources`.

### Ratepayer conflict/site leads not yet added — **medium**
- **meta-el-paso-tx (contested)** — EPE's filing plans to move a $500M/366 MW
  plant into general retail rates after a 1–5 yr bridge (documented cost shift).
  Held back on cohort eligibility: the site was first announced ~2024 (pre-pledge);
  the $10B is a 2026-03-29 expansion. Decide whether the post-pledge expansion
  qualifies it for a `contested` assessment (source: elpasomatters.org, 2026-03-29).
- **Indiana ratepayer conflict** (Mirror Indy, 2026-06-25) — bills up to ~27% with
  data centers cited as a driver. Held back per CLAUDE.md's caution: rate-structure
  criticism with multiple drivers ≠ documented site cost-shift. Needs a source that
  pins a shift to a specific IN site (google-michigan-city / microsoft-la-porte /
  amazon-wheatfield) before surfacing.
- **PJM capacity-market finding** (Monitoring Analytics: data centers = 40% of the
  Dec 2025 capacity auction) — strong, but the best fetchable source is pre-pledge
  (2026-01-07). Source a post-3/4/2026 version (State of the Market ~Mar 2026).
- **Brookings enforcement-gap** (2026-07-09) — national context, not per-site.
  Consider a "national context" panel on the Ratepayer tab rather than attaching
  it to one project.

---

## Performance + preview + restyle notes (2026-07-14)

### Performance — baseline moved in v2; now CI-gated — **medium**
**The ~202 KB / 6-request baseline below described the Comparison landing and no
longer applies.** v2 makes Ratepayer the landing view, which pulls projects +
responses + the signatory roster into first paint: **~237 KB gzipped across 8
requests**, inside the 250 KB / 8 guardrail but with almost no headroom.
`tests/test_perf_budget.py` now fails CI on a regression and says in its failure
message that the fix is to make the new payload lazy, not to raise the ceiling.

Because headroom is thin, the two optimizations below moved from "if it grows"
to the next thing worth doing:
- **Code-split `app.js`** (~52 KB gz, monolithic — all views in one file). First
  paint only needs the Comparison logic; the moratorium/ratepayer/tariff/explorer
  renderers could load per-tab. It's vanilla JS (no bundler), so this is a manual
  module split — defer until app.js is materially bigger. **low.**
- **Ship a lightweight claims index for first paint.** `claims.json` (43 KB gz)
  preloads on the landing view, but the Comparison matrix only needs claim *counts*
  per company/theme, not full verbatim statements. A `claims-index.json` (counts +
  ids) for first paint + lazy full claims on company pop-out would cut ~35 KB off
  first paint. **medium.**
- Watch the regression signal: first paint > ~500 KB or > ~12 requests = something
  got un-split (e.g. a heavy payload accidentally preloaded, or a web font added).

### Restyle notes — the design system is solid; minor polish only — **low**
- ~~**Long Ratepayer scorecard** — sticky filter/search + concern-first ordering~~
  **DONE (v2).** `.rp-filterbar` sticks under the tab bar: search (matches site,
  company, city, state code AND spelled-out state name), status chips that only
  render for statuses actually present, and an "only sites with a ratepayer
  concern" toggle. Concern cards sort first — a documented cost-shift is the most
  consequential thing on the page and was buried alphabetically among 39 cards.
- **Moratorium timeline x-axis on mobile** — the quarter labels (`Q1'24` … `Q3'26`,
  11 columns) can get cramped under ~380 px; verify and, if tight, show every other
  label or enable horizontal scroll on the plot (`.mtl-plot` already has `overflow-x`).
- Optional **density toggle** for the long directory + scorecard lists.
- No larger restyle warranted — palette, type scale, and tokens (DESIGN.md) are
  consistent and both themes are handled.

### Moratorium `duration_description` phrasing — optional polish — **low**
The v1.20 UX fix truncates the directory cell (`shortDuration()`) and moved sponsors to
the modal, so the table is consistent + scannable and the full text stays in the modal +
tooltip. The underlying field still varies in *phrasing* ("1 year" vs "One year" vs "12
months"; "Permanent" vs "Permanent ban" vs "Permanent prohibition"). Not wrong (each quotes
the jurisdiction's own framing) but a light normalization pass to canonical labels would make
the raw data tidier. Alternatively split into `duration_label` (short, required) + keep the
detail in `summary`. Defer unless the raw field is consumed elsewhere.


---

## Deferred from the accordion / sub-tab pass (2026-07-28)

### Sub-tab state isn't in the URL — **medium**
`SUBTAB_GROUPS` state is session-only (`_activeSubtab`), so "Before the pledge"
and "By state" can't be linked to. Every other detail surface here is
deep-linkable (`#state/XX`, `#ratepayer`), which makes this the odd one out — a
reader who finds 74 pre-pledge sites can't send anyone to them. Shape: extend
the hash to `#ratepayer/pre-pledge`, reusing the state-panel router's lesson
(**read the sub-key off the hash BEFORE `activateView`** — it rewrites the hash).

### Accordion open/closed state isn't remembered — **low**
Every `.acc` resets to its authored default on reload. Deliberate for now (same
reasoning as `_lastDetailTab` not going to `localStorage`: a returning reader
should land on the structured default). Revisit only if the Ratepayer page's
length becomes a complaint again.

### `tariff-coverage-count` is a constant — **low**
The chip reads "17 elements" — the size of the LBL taxonomy, not coverage. Every
other accordion count says how much data is inside. Either make it "N of 17
addressed" or drop the chip; a count that can never change is noise.

### Per-signatory deep-dive pages — **see [SPEC_SIGNATORY_PAGES.md](SPEC_SIGNATORY_PAGES.md)** — **medium**
P1–P3 are tooling (curation ledger schema + rebuild-merge test, `#signatory/<id>`
panel, `audit_signatories.py` + REFRESH.md sweep); P4 is the curation itself and
does not end. Three decisions are open in §8 before P1 starts — the sharpest is
whether the 176 cooperatives should carry a curation record at all yet.

### Re-check the `<details>` display-override trap on a non-Chromium engine — **low**
It didn't reproduce in this project's Chromium (see CLAUDE.md). The
`.acc:not([open])` safeguard is currently defense against a threat we have not
observed here. If the e2e suite ever runs WebKit/Firefox, re-run the mutation
there; if it doesn't bite in any engine we test, the rule is dead weight.


### 22 pre-existing W3C validation errors — **medium**
Found while checking a Codex review point against the W3C Nu validator rather
than arguing from memory (`curl --data-binary @docs/index.html
"https://validator.w3.org/nu/?out=json"`). Exactly **one** of the 23 errors
belonged to the accordion work and was fixed; the other 22 predate it:

- **11×** `role` on `<th>` inside a `<table>` with no `role` — the aggregate and
  directory tables.
- **4×** `aria-label` / `aria-labelledby` on a bare `<div>` with no `role`.
  These are silently ignored by AT, so the labels do nothing today.
- **3×** `role="dialog"` + `aria-modal` on `<aside>` — the tariff, moratorium
  and state modals. Should be `<div role="dialog">`.
- **1×** `<thead>` row with no cells.

None are cosmetic: the four `aria-label`-on-`div` cases mean four regions a
screen-reader user hears unlabelled. Worth a dedicated pass, plus wiring the
validator into CI so the count can only go down.

### `.rp-card-details` summaries wrap content in a `<div>` — **low**
`<summary>` takes phrasing content optionally intermixed with heading content,
so the `<div class="rp-card-title">` inside each of the 39 ratepayer card
summaries is non-conforming — same defect as the one fixed on the pledge band,
different component. `test_summaries_contain_only_conforming_children` is
deliberately scoped to `details.acc > summary` so it stays green; widen the
selector once the card markup is fixed.
