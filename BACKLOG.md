# BACKLOG.md: the one planning doc

Everything planned, pending, or waiting on a decision lives here. Everything
else is reference:

| Doc | What it is |
|---|---|
| [REFRESH.md](REFRESH.md) | How to refresh data: the playbook plus dated lessons |
| [.claude/skills/daily-refresh/SKILL.md](.claude/skills/daily-refresh/SKILL.md) | The procedure the 10:00 daily routine follows |
| [CLAUDE.md](CLAUDE.md), [AGENTS.md](AGENTS.md) | Rules for agents working in this repo |
| [DESIGN.md](DESIGN.md) | Design system and editorial rubrics (stance, constituency) |
| [ISSUES.md](ISSUES.md) | **Generated** data-gap audit (`refresh.py --audit`). Never hand-edit |
| [AGENT_RUNS.md](AGENT_RUNS.md) | Cost and quality log for every subagent run |
| [notes/specs/](notes/specs/) | Detailed specs: signatory pages (not built), Policy Playbook and Pledge v2 (built) |
| [notes/archive/](notes/archive/) | Finished or superseded plans, including this file's full text before it was consolidated on 2026-09-25 |

**Conventions.** Priority is in bold: **high**, **medium**, **low**. Delete an
item when it ships; git history is the done log. A lead about one place,
company or site goes under that unit's heading in §3
(`#### state:GA`, `#### company:meta`, `#### site:<project-id>`). The daily
routine greps those headings, so a lead filed anywhere else never gets worked.
Dated re-checks ("the Oct 6 hearing") don't go in this file. Add them to the
review ledger with `scripts/refresh_queue.py --mark … --follow-up` and they
surface in §2 on their date.

Contents: [§1 Decisions](#1-decisions-waiting-on-the-owner) ·
[§2 Refresh queue](#2-refresh-queue-generated) ·
[§3 Refresh leads](#3-refresh-leads-by-unit) ·
[§4 Product and UX](#4-product-and-ux) ·
[§5 Performance and engineering](#5-performance-and-engineering) ·
[§6 Data model](#6-data-model-and-schema) ·
[§7 Watch list](#7-watch-list-not-addable-yet)

---

## 1. Decisions waiting on the owner

Each item is blocked on a call only the owner can make. Pick one and the work
behind it unblocks.

1. **Landing page direction.** Options from the 2026-09-25 review: (A) a
   "latest changes + coming up" newsroom front page; (B) a location-first
   front door with search and the 50-state grid; (C) the Policy Playbook as
   the front page. Recommendation: A, with B's location search on top. All
   three first need the precomputed `home.json` digest in §5. **high**
2. **Daily routine merge policy.** The 10:00 routine squash-merges to `main`
   when its gates pass, like the other refresh routines. The alternative is
   to leave each run's PR open for review. Auto-merge keeps the site current
   and the review ledger moving. PR-only is safer editorially, but unmerged
   runs repeat each other's units, because the ledger lives on `main`. **high**
3. **Moratorium lifecycle.** No `expired` / `lapsed` status exists, so a
   lapsed six-month pause still counts as `enacted` in the stat tiles. The
   queue now derives end dates from `duration_months`, and 4 have passed
   (Indio CA, St. Charles MO, Larimer County CO, Athens-Clarke GA). **medium**
4. **Cancelled projects.** `Project.status` has no `cancelled`. QTS Prince
   William Digital Gateway (appeal withdrawn 2026-07-02) is the precedent
   case, and Microsoft Caledonia WI (pulled Oct 2025) is another. **low**
5. **Tribal jurisdictions.** `jurisdiction_type` has no tribal value.
   Cherokee Nation (2026-08-10), Seminole Nation (March 2026) and Kickapoo
   Tribe (July 2026) have data-center bans ready to curate. KGOU, KOSU,
   Tom's Hardware and Tribal Business News covered Cherokee. **medium**
6. **Executive-order "conditions" regimes.** Massachusetts EO 658 (Healey,
   Sept 8: no state permits for >25 MW without framework compliance and a
   host-community benefits agreement; NDA ban; Ratepayer Protection Fund) is
   not a pause. Should it be filed as a Policy `executive_order` like VA EO
   22? **medium**
7. **Nebius.** It has a 1.2 GW Pennsylvania campus, which clears gate 1.
   Does it publish its own community-impact framing (gate 2)? Onboarding a
   company touches four registries. **low**
8. **Infrastructure partnerships.** Google-SpaceX GPU lease and the
   Anthropic-xAI compute rental are `Project` records with no site. Options:
   exclude them, give them their own section, or fold them into the company
   pop-out. **low**
9. **Taxes filed as tariffs.** `virginia-data-center-electricity-consumption-tax`
    is a state excise tax scored against a rate-design taxonomy and counted
    in tariff tiles. It needs an `instrument_type` field or an
    `excluded_from_stats` flag. **low**
10. **Per-signatory pages.** Three open questions in
    [notes/specs/SPEC_SIGNATORY_PAGES.md](notes/specs/SPEC_SIGNATORY_PAGES.md) §8:
    whether cooperatives get a light curation pass, modal vs. URL, and the
    promotion path to `Company`. **medium**
12. **Repository setting: auto-delete merged branches.** Cloud routine runs
    can't delete remote branches through their git proxy. The
    vibe-coding-security repo has about 24 stale run branches for this
    reason. Turning on "Automatically delete head branches" fixes it
    server-side. **low**
13. **Trade-association compilations as docket citations.** Otter Tail Power
    MN docket 26-211 has been confirmed only in EEI's "Large Load Projects
    and Tariffs" compilation (updated 2026-09-11); mn.gov/puc is
    bot-walled. Is that citation enough for a `proposed` record? **low**
14. **Post-pledge expansions of pre-pledge sites.** `meta-el-paso-tx` was
    first announced around 2024. Its $10B expansion came 2026-03-29, and
    EPE plans to move a $500M / 366 MW plant into general rates. Does the
    expansion put the site in the ratepayer cohort, and would that make it
    `contested`? **low**

---

## 2. Refresh queue (generated)

The daily routine works this list top-down. Each review is recorded in
`data/refresh_ledger.json`, and the block below is regenerated at the end of
every run.

<!-- refresh-queue:start -->
_Generated by `python3 scripts/refresh_queue.py --write-backlog` on 2026-10-22. Do not edit between the markers: review dates and follow-ups live in `data/refresh_ledger.json`, and units come from the data itself._

**Coverage:** 10 of 142 sites reviewed within 90 days; 3 of 17 companies reviewed within 30 days; 1 of 52 states reviewed within 120 days.

**Due now (0)**

Nothing due.

**Next run works through**

1. `site:xai-memphis-tn` (Colossus Supercomputer (Memphis) (Memphis, TN; operational)): never reviewed; record curated 2026-05-14 (1.8x target)
2. `state:TX` (Texas): never reviewed; 31 records
3. `site:coreweave-hammond-in` (CoreWeave Hammond Data Center (Digital Crossroads) (Hammond, IN; announced)): never reviewed; record curated 2026-05-15 (1.8x target)
4. `company:anthropic` (Anthropic (2 tracked sites)): never reviewed; record curated 2026-05-16 (5.3x target)

**Then, sites**

| Unit | What | Why now |
|---|---|---|
| `site:amazon-boardman-or` | AWS Boardman / Columbia River Land Acquisition (Boardman, OR; announced) | never reviewed; record curated 2026-05-16 (1.8x target) |
| `site:amazon-bossier-parish-la` | AWS Bossier Parish Campus (Benton, LA; construction) | never reviewed; record curated 2026-05-16 (1.8x target) |
| `site:amazon-caddo-parish-la` | AWS Caddo Parish Campus (Blanchard, LA; construction) | never reviewed; record curated 2026-05-16 (1.8x target) |
| `site:amazon-falls-twp-pa` | AWS Falls Township Data Center Campus (Falls Township, PA; announced) | never reviewed; record curated 2026-05-16 (1.8x target) |
| `site:coreweave-kenilworth-nj` | Kenilworth NEST Campus (Kenilworth, NJ; construction) | never reviewed; record curated 2026-05-16 (1.8x target) |
| `site:coreweave-lancaster-pa` | Lancaster Data Center (Lancaster, PA; announced) | never reviewed; record curated 2026-05-16 (1.8x target) |

**Then, states**

| Unit | What | Why now |
|---|---|---|
| `state:OH` | Ohio | never reviewed; 25 records |
| `state:CA` | California | never reviewed; 23 records |
| `state:FL` | Florida | never reviewed; 21 records |
| `state:VA` | Virginia | never reviewed; 21 records |

**Then, companies**

| Unit | What | Why now |
|---|---|---|
| `company:meta` | Meta (15 tracked sites) | never reviewed; record curated 2026-05-16 (5.3x target) |
| `company:openai` | OpenAI (7 tracked sites) | never reviewed; record curated 2026-05-16 (5.3x target) |
| `company:oracle` | Oracle (3 tracked sites) | never reviewed; record curated 2026-05-16 (5.3x target) |
| `company:qts` | QTS (14 tracked sites) | never reviewed; record curated 2026-05-16 (5.3x target) |

**Coming up in the next 30 days (33)**

| Due | Unit | Check |
|---|---|---|
| 2026-10-23 | `state:CA` | Escondido extension: confirm Oct 7 vote and end date from a fetchable page (city minutes or other outlet) |
| 2026-10-23 | `state:TX` | TWDB Oct 14 enforcement report: check for coverage |
| 2026-10-24 | `state:IL` | Bloomington: find report of Oct 16 Planning Commission hearing outcome; Nov 16 second hearing |
| 2026-10-24 | `state:NC` | Beaufort County NC: Sept 14 hearing / Oct 5 outcome still unconfirmed; try Washington Daily News or county minutes |
| 2026-10-24 | `state:NM` | Grant County NM: was moratorium adopted at Oct 8 meeting? Try Silver City Daily Press / county minutes |
| 2026-10-27 | `state:CO` | Check Aurora council Oct 26 vote on indefinite moratorium |
| 2026-10-28 | `state:TN` | Confirm Memphis mayoral signature/effective date and Shelby County Commission action |
| 2026-10-28 | `state:TN` | Memphis Ordinance 18 signature/effective date; Shelby County commission vote |
| 2026-10-29 | `state:CO` | Colorado PUC evidentiary hearing Oct 21–28 on Xcel's large-load tariff (xcel-colorado-large-load-tariff) |
| 2026-10-30 | `state:OK` | OG&E large-load tariff: OCC cause number via OCC case search |
| 2026-10-30 | `state:TN` | Crossville moratorium: vote date and ordinance number from city minutes |
| 2026-11-02 | `state:CA` | Hayward October revisit; Oakland/SF 45-day pauses expire late Nov |
| 2026-11-02 | `state:OR` | Check UE 463 for an order on the stipulation |
| 2026-11-04 | `company:anthropic` | Fluidstack TX/NY campuses: has Anthropic or Fluidstack named a town yet? (anthropic.com/news, fluidstack.io/blog) |
| 2026-11-04 | `state:CO` | Moffat County: commissioners' minutes for the Oct 13 moratorium decision |
| 2026-11-04 | `state:CO` | Moffat County: re-check Craig Daily Press for the Oct 13 moratorium decision |
| 2026-11-04 | `state:FL` | Duke FL post-hearing recommendation; TECO and FPL docket numbers |
| 2026-11-04 | `state:GA` | Verify OpenAI primary quote |
| 2026-11-04 | `state:IL` | Chicago ordinance number and Rules Committee action |
| 2026-11-04 | `state:ME` | Bangor: council order/minutes for the 180-day extension (bangormaine.gov) |
| 2026-11-04 | `state:OH` | Nov 3 ballot: ~18 local data-center charter amendments/bans (Ohio Capital Journal Sept 14, Cloudflare-walled), incl. Trenton; and the Butler County 25 MW citizen measure tied to Amazon's $5B plan — record outcomes |
| 2026-11-06 | `state:NC` | Charlotte: the original 150-day pause expires Nov 5 — was staff's 9-month extension adopted? (charlotte-city-2026-06; the Sept 14 vote outcome was never found) |
| 2026-11-06 | `state:NC` | Check Charlotte extension vote |
| 2026-11-11 | `state:TX` | Fort Worth: committee report to council Nov 3, first public hearing Nov 10 (fort-worth-tx-2026-08) |
| 2026-11-14 | `state:NC` | moratorium `vance-county-nc-2026-09` (Vance County) reaches its computed end date 2026-11-14: lapsed, extended, or replaced by a permanent rule? |
| 2026-11-18 | `company:anthropic` | Fluidstack TX/NY campuses: has a town been named? (not found Oct 21) |
| 2026-11-18 | `country:GB` | Epping Forest decision; Guardian UKPN timeline |
| 2026-11-18 | `state:KY` | Prosperity One (Lewis County nuclear, 6.6 GW): any co-located data center or named offtaker? |
| 2026-11-18 | `state:PA` | rate case `pa-puc-large-load-cost-allocation-2026`: 2026-11-17 milestone passed; record the outcome and the next announced step |
| 2026-11-18 | `state:VA` | Check Loudoun Nov 17 Board outcome |
| 2026-11-21 | `state:CA` | Oakland 45-day moratorium ends ~Nov 20: extended, permanent rules, or lapsed? |
| 2026-11-21 | `state:CA` | San Francisco 45-day moratorium ends ~Nov 20; Planning hearing in November: extended or lapsed? |
| 2026-11-21 | `state:MN` | moratorium `minneapolis-city-2026-05` (Minneapolis) reaches its computed end date 2026-11-21: lapsed, extended, or replaced by a permanent rule? |

**Reviewed or checked in the last 14 days (30)**

- 2026-10-22 `state:OH` (check): Cleveland extension re-verified on Cleveland 19: paused through Jan 29 2027 or until new rules; record already correct, captured_at bumped
- 2026-10-21 `state:VA` (check): Loudoun pause resolution deferred to Nov 17; Spotsylvania Crossroads campus filed as lead
- 2026-10-21 `state:TX` (check): TCEQ Oct 19 letter added to texas-state-2026-08
- 2026-10-21 `state:TN` (check): Oct 21: Memphis Ord 18 passed (round 1) plus mayor's Oct 9 study EO added; Shelby County commission vote not found.
- 2026-10-21 `state:PA` (check): SB 1359, HB 2496 unchanged
- 2026-10-21 `state:OR` (check): Forest Grove 120-day moratorium added; Oregon DEQ pause and UE 463 docket re-verified
- 2026-10-21 `state:NC` (check): Charlotte extension hearing held Oct 12; vote pending, pause expires Nov 5
- 2026-10-21 `state:MN` (check): HF 4888 unchanged
- 2026-10-21 `state:MI` (check): SB 1018 unchanged; Schoolcraft Twp lead
- 2026-10-21 `state:ME` (check): Bangor extension order still not located
- 2026-10-21 `state:KY` (check): Prosperity One checked: nuclear campus, no data center named
- 2026-10-21 `state:IN` (check): Oct 21: Fort Wayne council rejected both Booker ordinances (3-5, 4-4); policy marked failed.
- 2026-10-21 `state:IL` (check): Oct 21: Chicago EO 2026-5 and proposed one-year moratorium ordinance added.
- 2026-10-21 `state:GA` (check): Oct 21: Effingham PSC approval (Aug) and SELC suit (Sept 21) recorded on policy and project.
- 2026-10-21 `state:FL` (check): Oct 21: Duke Energy Florida docket 20260064-EI added as rate case; no hearing outcome found.
- …and 15 more (see `data/refresh_ledger.json`).
<!-- refresh-queue:end -->

---

## 3. Refresh leads, by unit

Undated leads the routine should work when it reaches the unit. Each bullet
records what's known and why it isn't in the data yet. Cross-cutting items
come first, then locations, companies and sites.

### Cross-cutting

- **Audit the 19 homepage-sourced moratoriums.** `HOMEPAGE_SOURCED_MORATORIUMS`
  in tests/test_policies.py lists them and only lets the list shrink. For
  each one, find the ordinance or bill page, confirm the facts, then re-cite
  or remove the record. The July "enhanced" batch was 5 of 9 fabricated with
  this exact shape: a real bill number and a homepage citation. **high**
- **Mine the Moratorium Nation inventory** (`mjbommar.github.io/moratorium-data-2026`,
  222 rows, stopped updating Aug 19). Use it as a work-list only, since
  rows carry no source URL. Candidates are listed under their states below.
  **medium**
- **Upgrade the no-.gov moratorium records.** Run `validate_moratoriums.py
  --links-only` for the list, and promote any live council page
  (Granicus/Legistar/Municode) to `source_url` or `resources`. 153 of 157
  records read "incomplete" (no ordinance number, sponsors or gov link),
  mostly because local actions are covered only by local outlets. **medium**
- **Serving utility for the remaining ~99 sites.** Only where a source states
  it ("served by X"). Never infer it from geography: half the automated
  candidates were wrong. **medium**
- **Delivery evidence for 14 in-force site agreements.** The bar is a
  recipient's record of receipt, or an announcement naming recipients. Start
  with Wilmington OH and Hammond IN (see their sites). **medium**
- **EEI large-load tariff compilation** (updated 2026-09-11). Each docket is
  listed under its state; each needs its own docket-page fetch. **medium**
- **Roster: date the 44 rolling adds.** Use each organization's own press
  release (Oncor, Puget Sound Energy, Hawaiian Electric, Cleco, Digital
  Realty, Lambda, NRECA), cited in `notes`. Never guess from the snapshot
  date. The roster page lists 323 organizations but advertises 321;
  `drift_note` says so. **low**
- **Quote the governor addendum verbatim** if the signed pledge PDF carries
  its text. Today the 23 governor rows paraphrase it. **low**

### Locations

#### state:US — Federal
- (2026-10-21) Trump 'data center dividend' remarks of
  Sept 29, 2026 (Newsweek): he floated residents being paid a dividend and
  teachers a bonus. One secondary source only; no White House transcript found
  and no company response. Not recorded as a policy because no instrument
  exists. A claim that he said developers should pay for their own power is
  search-snippet only.
- (2026-10-21) Trump 'data center dividend' remarks, Sept 29, 2026: Context
  only, no record type fits. Newsweek (Sept 29, updated Oct 1): Trump told
  reporters residents of data center communities could receive a 'dividend';
  no formal program or company response reported.
- SPP High Impact Large Load (HILL): FERC approved it Jan 2026, per FERC's
  April release. The docket number is unverified. Add a federal rate case
  once it's pinned. **low**
- PJM capacity-market finding (Monitoring Analytics: data centers were 40%
  of the Dec 2025 auction). The fetchable source predates the pledge; find
  a post-March-4 edition, such as the State of the Market. **low**

#### state:AL — Alabama
- Fort Payne is a zoning action, not a moratorium.

#### state:AZ — Arizona
- (2026-10-21) APS large-load rate case: AG Mayes asked the ACC on Oct 9, 2026
  to investigate alleged cost shifting (KJZZ Oct 10; allegations, not
  findings). ALJ opinion timing from search only; azcc.gov docket
  E-01345A-25-0105 not read.
- Pima County / Beale MOA: KVOA (2026-06-11) reports the Pima Community
  College board approved a $5.9M five-year gift (record says $5M). Acceptance
  is not receipt; look for a payment record before attaching `delivered`. **low**
- Pinal County project denial: a site fight, not a moratorium.

#### state:CA — California
- (2026-10-21) Hayward: on Sept 15, 2026 the council voted 7-0 to direct
  staff to start the process for prohibiting future data center approvals
  (Local News Matters, Sept 18). A direction to staff is not yet an
  instrument, so the record was held after review. Add it once an ordinance is
  introduced or adopted; the council said it would revisit the issue in October.
- (2026-10-21) Hayward Oct revisit; Lake Elsinore; San Jose Prologis: Hayward
  council said it would revisit in October (record held; see the lead
  above). Lake
  Elsinore extension: nothing found. Prologis San Jose (99 MW, July 12 blog)
  unchanged.
- El Monte (Moratorium Nation).
- SB 1168 / SB 886 / SB 887 are rate-design bills. They become
  `legislation` Policy records if passed, and the tariff comes later from
  the CPUC.
- Nvidia-leased San Jose site (300 Holger Way): permit appeal, operator
  unknown. Not addable until the operator is named.
- Imperial County project denial: a site fight, not a moratorium.

#### state:CO — Colorado
- (2026-10-21) Moffat County: Craig Daily Press (Sept
  14) says commissioners unanimously tabled the six- or twelve-month
  moratorium to Oct 13. The Oct 13 outcome is not found (moffatcounty.net
  refused connection). Needs BOCC minutes or a Craig Daily Press story.
- (2026-10-21) Moffat County Oct 13 moratorium decision: Craig Daily Press
  front page showed nothing; commissioners' minutes not read.
- (2026-10-19) Brighton: KUNC (Oct 8) says the council "approved a one-year ban on data centers" on a Tuesday night (Oct 6 by weekday); it never names the instrument. Headline word, not a confirmed legal action: find the ordinance or minutes before recording a moratorium. Kiowa County Resolution 2026-4 is recorded (stated end Oct 9, 2026; check for extension).
- Global AI, Weld County (up to 1 GW, approved Sept 9) is a two-gate
  candidate; see §7.
- Six Colorado records cite news, not `.gov`. larimer.gov 403s, and
  jeffco.us is a real government domain that the `.gov` regex misses. Look
  for each city's own ordinance page.
- No state-level policy record: HB26-1030 died in committee.

#### state:CT — Connecticut
- No state-level policy record: PA 26-122 is administrative only. The
  governor has stated intentions but taken no action.

#### state:DE — Delaware
- EEI: Delmarva docket 25-0826.

#### state:FL — Florida
- (2026-10-21) Added rate case fl-psc-duke-large-load-
  tariff-2026 (docket 20260064-EI). The Aug 17 hearing was a standing hearing
  for four intervenors before the Prehearing Officer; the evidentiary hearing
  was noticed for Aug 25-26. No order or hearing outcome found; check the FPSC
  docket for post-hearing recommendation. Still missing: TECO docket number
  (Spectrum, Sept 30: plan filed, approval 'late this year or early next
  year') and any FPL filing; FPSC search was unreachable.
- (2026-10-21) SB 484 large-load tariff dockets: Duke Energy Florida docket
  20260064-EI (filed Apr 22, 2026; tariff suspended by Order
  PSC-2026-0218-PCO-EI June 19; motion to dismiss denied July 28) was found in
  PSC PDFs by a researcher but not re-fetched by synthesis. TECO (Spectrum,
  Sept 30) and FPL docket numbers not found. Policy fl-sb484-large-load-
  tariffs-2026 may need these.
- Okaloosa County: Commissioner Paul Mixon's 12-month moratorium proposal
  has no confirmed vote. An earlier note said it failed 3-2 on Sept 15; no
  fetched source supports that. WEAR's article (weartv.com) describes the
  board choosing to regulate through conditional use instead. Confirm any
  vote from county minutes before recording `failed`.
- `hernando-county-fl-2026-06`: unverified after five passes. Search snippets
  point to Ordinance No. 2026-23 (through June 16, 2027), but every article
  403s. Use the county's own agenda and minutes system.
- EEI: FPL 20250011, Duke Energy Florida 20260064.
- Not moratoriums: Palm Beach County ("could be next"); Minneola (advanced,
  final vote unknown); Alachua and Orange counties (votes only to draft).

#### state:GA — Georgia
- (2026-10-21) Effingham/OpenAI: the policy record's key
  term 'Electricity rates will not go up for residents because of this
  project' and its '$20 billion, four-building campus' phrasing were not found
  on any fetched page (openai.com 403s, Wayback refused); a Pulse2 reprint of
  OpenAI's post says rates will not rise, with different wording. Verify
  against openai.com or archive, then fix the quote. The IDA development
  agreement (July 21, IDA-Octans GA, LLC) appears only in a search summary.
  The suit's described tax abatement is 'nearly $900 million' per SELC.
- (2026-10-21) Effingham County OpenAI/Camellia community benefits: openai.com
  page returned 403; the M figure is from Pulse2 (fetched) and search
  summaries. Read the primary page via another route before changing the
  record. Prologis Coweta: ~900 MW and the B figure are not in the fetched
  Times-Herald/ANF articles.
- **The Georgia wave (high).** 14 tracked. GPB and The Current say "about
  40" municipalities. Still open: Hall County (debating 180 days, no vote
  found), Lee County (WALB 5/27,
  "consider extending"), Floyd County (probably an ordinance; others cite it
  as the model), Lowndes, Effingham, Meriwether (Feb 24, extended to Nov 21,
  2026; only an AI aggregator and a 403'd paper so far, so not citable
  yet).
  Muscogee/Columbus is an enabling overlay district, **not** a moratorium.
  The northwestgeorgianews.com roster of about 53 jurisdictions (June 2025)
  is a stale work-list.
- **2026-10-12 leads (untracked, not yet added).** Paulding County: Spectrum News 2026-08-03 says "Commissioners unanimously approved a temporary moratorium through Jan. 1, 2027", vote "last Tuesday" (likely Jul 28; confirm date from the county minutes). Camden County (6-month moratorium from May, ending soon; actionnewsjax), Newton County (extension, resolution R 040726b on newtoncountyga.gov). Each needs a primary source and vote date.
- EEI: Georgia Power 44847.
- Microsoft "ATL50" (see company:microsoft) needs the Georgia DCA DRI record
  (apps.dca.ga.gov).

#### state:HI — Hawaii
- No state-level policy record: non-binding resolutions only.

#### state:IL — Illinois
- (2026-10-21) Chicago: ordinance number, size
  thresholds, exemptions and committee referral for the mayor's one-year
  moratorium are not found (GovTech does not say; Ground News says Rules
  Committee, unfetched; chicago.gov and the City Clerk ELMS were unreachable).
  A '1,000 sq ft / 20% server floor space' scope appeared only in a search
  summary and was not shipped. Chicago EO text itself was not read (403);
  policy rests on the Greenberg Traurig summary.
- (2026-10-21) Chicago Executive Order 2026-5: GT alert (verified): Mayor
  Johnson signed EO 2026-5 on Aug 11, 2026 calling on Council for a temporary
  moratorium; neither the order nor introduced legislation specifies duration.
  EO itself pauses nothing. Reports of a 12-month ordinance referred to Rules
  are snippet-only. Add a record only when an ordinance number is found.
- Prologis "Project Steel", Yorkville (see company:prologis).

#### state:IN — Indiana
- (2026-10-19) Madison County: Indiana Public Radio (Aug 2026) says commissioners voted unanimously to extend the data center moratorium to a full year, but gives no vote date (2026-08-04 is the article date). Get the commissioners' minutes before adding; the original six-month June 2026 passage is also unverified.
- Jasper County / Amazon "Project Rise": Fortune (2026-07-23) reports a
  "$98 million upfront and $23 million a year for a decade" community benefit
  plan, but only in a utility executive's op-ed that doesn't name the
  developer. Find the county's own ordinance (04-06-2026B amends 02-02-2026A)
  before adding. **medium**
- St. Joseph County CEA: the delivered block was removed 2026-10-08. Its
  source ties AWS's $250K community fund to AWS's Indiana investment, not to
  the $143M agreement. Look for county records of CEA payments. **low**
- Indiana ratepayer conflict (Mirror Indy, 2026-06-25: bills up ~27%, with
  data centers cited as one driver). Needs a source that pins a cost shift
  to a specific Indiana site before it can be surfaced.
- Kokomo: zoning and regulatory actions, not a moratorium.

#### state:KS — Kansas
- (2026-10-19) Saline County KS: KSN says the commission voted 4-0 "on Tuesday" for a three-year pause on data centers, nuclear and hydrogen facilities; the article has no date (likely early 2026). Needs county minutes for an event date. Not Saline County NE (recorded).
- Marysville KS: reportedly 12 months from Sept 14, one outlet so far.
  Distinct from Marysville WA.
- EEI: Evergy 25-EKME-315-TAR.

#### state:KY — Kentucky
- (2026-10-21) Anthropic/Fluidstack TX-NY towns; The Nuclear Company: No town
  named for Fluidstack's Anthropic TX/NY sites.
- (2026-10-19) Edmonson County: Ordinance EC26-18 (one-year moratorium on data centers, AI and crypto-mining facilities) text is verified, but the adoption date is blank in the copy. Get the fiscal court minutes or the clerk's adoption date before adding.
- (2026-10-19) Allen County: WBKO (2026-06-12) quotes Judge Executive Dennis Harper that a 24-month moratorium "was put in place" but names no enacting body or date. Get the fiscal court order before adding.
- Rowan County: a two-year moratorium passed unanimously at the Fiscal
  Court's August 2026 meeting (Rowan Review on rcky.us; LEX18; WTVQ, Sept 1),
  but no source states the day. Get it from the court's minutes before adding
  the record; don't infer it from the third-Tuesday meeting schedule.
- EEI: KU/LG&E 2025-00113 / 2025-00114; Kentucky Power 2024-00305.
- (2026-10-21) Lewis County: The Nuclear Company announced "Prosperity One"
  (PR Newswire, Oct 21, 2026). It is a proposed campus of up to six AP1000
  reactors, about 6.6 GW, on the Ohio River, with construction targeted for
  2028. The release names no data center, offtaker or large-load customer;
  probe.py confirms "data center" is absent. Not a site record. Watch for a
  co-located data center or a named offtaker, and for the county's
  nuclear-ready designation filing with the Kentucky Nuclear Energy
  Development Authority.

#### state:LA — Louisiana
- EEI: Entergy Louisiana U-36595.

#### state:MA — Massachusetts
- EO 658: see decision 7. Westfield (council "supports") and Northampton
  (study committee) are not moratoriums.

#### state:MD — Maryland

- **Prince George's County: second 3-month data-center permit pause (lead, 2026-10-19).** Instagram caption dated 2026-10-17 only; county Council newsroom (Oct items) and WTOP index showed nothing, search engines blocked. Needs a pgccouncil.us or major-outlet source before appending to `prince-georges-county-md-2026-07`. **medium**
- PC72: Potomac Edison and the Exelon Maryland utilities filed large-load
  rate schedules Sept 1, 2026 (per EEI). No MD PSC case numbers located yet.

#### state:ME — Maine
- (2026-10-21) Bangor: BDN's Oct 7 article says the pause
  was 'recently extended for another 180 days' with no vote date or tally.
  bangormaine.gov AgendaCenter 403s and the Oct 14 agenda PDF has no
  extractable text. Needs council minutes before recording an extension date.

#### state:MI — Michigan
- (2026-10-21) Schoolcraft Township (Kalamazoo County) Ordinance 295: WOOD TV:
  township board set to review Ordinance 295, a one-year moratorium on data
  center permits/licenses/approvals (or until zoning is amended), at a Tuesday
  evening meeting; article undated, outcome unknown. Check township board
  minutes, then add a moratorium record.
- (2026-10-19) Marshall: WWMT (Aug 10) reports a 365-day moratorium; the only date is the resolution PDF label "8-3-2026", not a stated vote date. Confirm Aug 3 from council minutes, then record (enacted, 12 months).
- Zeeland Township: a new year-long moratorium passed unanimously at a
  Tuesday meeting in early September 2026 (FOX17, which has no dateline).
  It needs the meeting date from township minutes before it can be added.
- Moratorium Nation candidates: Pontiac, Saginaw, Saline, Northville,
  Taylor. Wixom: zoning action.
- Policy: HB6137 / SB1050 (would require CBAs) were introduced, not passed.
  Gov. Whitmer's "Affordable and Responsible Growth Action Plan"
  (~2026-07-20) is a framework; watch for the MPSC filing that implements it.
- EEI: Consumers U-21859, I&M U-21986, DTE U-22061.

#### state:MN — Minnesota
- (2026-10-19) Waite Park: KNSI (May 5) says the council "unanimously passed" a one-year moratorium; no meeting date in the article (May 4 is unverified). Needs the council agenda or minutes.
- Otter Tail Power docket 26-211: see decision 13. Its South Dakota twin is
  EL26-021 (75 MW threshold); don't reuse that number or threshold for MN.
- EEI: Minnesota Power 26-126. This docket is independently confirmed as
  Minnesota Power's, not Otter Tail's.
- Moratorium Nation: Inver Grove Heights.

#### state:MO — Missouri
- (2026-10-19) Ralls County: Muddy River News (Aug 25) reports a one-year moratorium to Sept 1, 2027; the vote date is not stated. Needs commission minutes.
- EEI: Evergy EO-2025-0154.
- Crusoe Warrenton (see company:crusoe).

#### state:NC — North Carolina
- (2026-10-21) Charlotte extension vote, Fayetteville, Cumberland, Pitt:
  Charlotte pause expires Nov 5; extension vote date (Oct 26?) is snippet-
  only. Fayetteville council approved a 120-day delay on considering a
  moratorium Apr 27 (CityView, not a pause). Cumberland County six-month
  moratorium (June 15) and Pitt County Nov 16 hearing: snippet-only.
- (2026-10-18) Charlotte extension: Oct 12 public hearing held per GovTech's
  schedule; outcome and final vote not found. WSOC says up to 9 months,
  GovTech 11 months (to Oct 11, 2027). Update `charlotte-city-2026-06` when
  the council votes. Davidson County: Oct 26 agenda item
  (`davidson-county-nc-2026-09`). Columbus County: Oct 5 hearing on a 120-day
  pause, outcome unfound; add a record once minutes or coverage report it.
- (2026-10-18) Duke large-load settlement (filed ~Oct 6, E-7 Sub 1329 /
  E-2 Sub 1380): thresholds (50 MW@80% LF or 150 MW, 75% minimum billing,
  Jan 1 2027) are in the SELC-hosted PDF but probe couldn't extract text.
  Fetch the NCUC filing and add them to `nc-ncuc-duke-settlement-2026`.
- AG Jeff Jackson's proposed ≥100 MW rate class, filed in Duke's dockets
  (ncdoj.gov, Sept 14; E-2 Sub 1406 alongside E-7 Sub 1329). Confirmed live
  2026-09-29 via ncnewsline.com / ncdoj.gov coverage — still worth its own
  RateCase once the docket page itself is fetched to pin the exact docket
  numbers and filing date.
- Moratorium Nation: Hillsborough, Durham, Apex, Boone, Canton, Wendell,
  Kings Mountain — not yet checked.
- Forsyth County: the Sept 28 item was a commissioners' briefing (work
  session), not a formal vote — co.forsyth.nc.us lists it as "Briefing,"
  and a Sept 14 WS Chronicle piece said staff would return with tax-revenue
  estimates, legal language and milestones before any formal moratorium
  vote. No post-briefing outcome coverage found as of 2026-09-29; re-check
  after the Oct 5 regular meeting.

#### state:NH — New Hampshire
- The governor has stated intentions only.

#### state:NJ — New Jersey
- NJ S731 / A796: a large-load tariff mandate for 100 MW+, passed and
  awaiting signature as of July. Watch for the utility filing that
  implements it. The NJ transparency law is a Policy candidate.

#### state:NM — New Mexico
- Doña Ana PILOT record: probe.py found neither the "$50M water fund" nor
  the "$360M" on the record's own source_url. Both may be real (Oracle blog,
  El Paso Matters), but the executed CBA (now its own record) doesn't contain
  the water fund. Re-source or trim the PILOT record. **high**
- EEI: El Paso Electric 25-00082-UT. See also site:oracle-dona-ana-nm.

#### state:NV — Nevada
- (2026-10-21) Haiku could not reach the PUCN portal for
  docket 26-06023; the seed's Procedural Order No. 1 text was previously read
  from the portal API, so no change was made.
- (2026-10-21) Callisto/Google ESA docket 26-06023: PUCN portal search (puc-
  onbase.nv.gov) needed; homepage listed no 26-06023 documents.
- `nv-microsoft-ratepayer-protection-tariff`: the October and January hearing
  dates carried over from an earlier pass couldn't be re-confirmed (DCD
  blocked the fetch; mlq.ai is AI-generated). Confirm them from the PUCN
  docket (puc-onbase.nv.gov).

#### state:NY — New York
- Policy: A9086 is still in committee. EO 62 and S10642/A11560 are
  moratoriums, already tracked.

#### state:OH — Ohio
- (2026-10-18) Trenton: city charter amendment banning data centers >25 MW;
  FOX19 calls it Issue 17 on the Nov 3 ballot, but the Butler County BOE
  page wasn't reachable and an Ohio Supreme Court ruling said November
  placement wasn't required. AWS held an Oct 15 open house. No project
  record until AWS's site, size and utility are public.
- Wilmington / AWS compensation agreement: local coverage (search only,
  Journal-News 429) says the 30-year abatement's final council vote had not
  happened by Sept 2026 and the offer changed to $10M. The record says
  in_effect with $1.5M. Check council minutes; correct status/terms. **high**
- Ashville / EdgeConneX (proposed): search results say the Ohio Supreme Court
  ordered a referendum petition forwarded on Aug 7, 2026. Confirm and update
  status. **medium**
- Moratorium Nation candidates (30+): Findlay, Avon, Massillon, Maumee, Kent, Ravenna, Tallmadge, Tiffin,
  Vermilion, Norton, Cincinnati.
- EEI: FirstEnergy 26-0697-EL-ATA, Duke Ohio 26-0755-EL-ATA, AES Ohio
  25-0958-EL-AIR.

#### state:OK — Oklahoma
- (2026-10-19) Shawnee: News 9 (Aug 19) says the commission approved a moratorium through the end of 2027, effective immediately, without a meeting date or vote. Aug 17 is unconfirmed. Needs city minutes. Luther is recorded.
- EEI: PSO PUD2025-000075, OG&E PUD2026-000046.

#### state:OR — Oregon
- Portland and Eugene NDA bans: Policy candidates (principle "no secret
  deals"). The Eugene project denial is a site fight.

#### state:PA — Pennsylvania

- **Philadelphia 'No Data Centers in Philly' campaign** calls for a council moratorium (WHYY, article ~2026-09-13; rally the Monday after). No tracked Philadelphia project to attach a response to and no council bill found; held as a lead. Source: https://whyy.org/articles/data-center-protest-philadelphia/ **low**
- (2026-10-19) Upper Burrell Township: Resolution 6-2026 (curative amendment on data centers, 3-0, supervisors' May 6, 2026 minutes). Not a moratorium; a Valley News Dispatch report of a 180-day moratorium has no adopting vote found. Check for a later ordinance before adding a policy record.
- Springhill Township: the board approved a resolution on Sept 3, 2026
  barring data-center and power-plant applications until its next meeting
  (recorded as `springhill-township-pa-2026-09`) and tabled two ordinances
  to a Sept 17 vote. The Sept 17 outcome is not found; an earlier note that
  permanent zoning was adopted Sept 19 is unsupported. Check township
  minutes, then add a Policy (`local_ordinance`) if adopted.
  West Hempfield and Clinton Twp are zoning actions or denials.
- King of Prussia (Upper Merion) denied MLP Ventures' five buildings. That
  is a single project's permit fate, so watch for an actual ordinance. The
  Allentown "Bill 20" setbacks are a zoning ordinance, not a moratorium.

#### state:RI — Rhode Island
- No state-level policy record: incentive bills died in committee.

#### state:SC — South Carolina
- Jasper County, first reading. `chesterfield-county-sc-2026-05` has a
  disputed enacted date: its primary source says early May and a later Go
  Laurens roundup says June. Check the council minutes and drop the note.
- EEI: Duke 2025-172-E / 2025-154-E; generic docket 2026-138-E.

#### state:TN — Tennessee
- (2026-10-21) Shelby County (TN) commission: a Govly
  meeting summary (app.govly.com/public/meetings/99828) says the committee
  sent a proposed unincorporated-county data center moratorium forward without
  a recommendation (title Oct 7, metadata Oct 6). No full-commission vote
  found; needs commission minutes. Millington TN: two searches found no
  moratorium. Memphis: the mayor's signature and effective date for Ordinance
  18, and its ordinance number, are not in WREG's report; check City Clerk
  records. Added memphis-tn-mayor-eo-data-center-review-2026-10 (a study, not
  a pause).
- (2026-10-21) Shelby County Commission: WREG: Commission 'expected to
  continue discussions' on a possible moratorium; headline mentions a 12-month
  pause. No reading or vote found. Millington TN: nothing found.
- (2026-10-19) Gallatin: WSMV (Jul 29) says commissioners approved a 60-day pause on new data center applications, "not the full moratorium" proposed earlier; no vote date. Needs minutes before recording.
- (2026-10-18) Memphis council vote on `memphis-city-2026-10` set for Oct 20;
  WREG reportedly said it wasn't taken up. Record the outcome.
- (2026-10-19) Gallatin city: WSMV (2026-07-29) says commissioners "have approved a 60-day pause on new data center applications" but gives no vote date, and other outlets report a 12-month proposal advancing; reconcile from city minutes before adding a record.
- Gallatin: a six-month moratorium passed first reading, shortened to six
  months by a mayoral tie-break. The second-reading outcome is unconfirmed.

#### state:TX — Texas
- (2026-10-21) Fluidstack/TeraWulf: TeraWulf's July 6,
  2026 release says a Fluidstack-led group bought TeraWulf's 50.1% JV stake in
  a 168 MW campus in Abernathy, Texas, and will lead it; the release does not
  link it to Anthropic. TeraWulf also has a 20-year Anthropic lease at
  Hawesville, Kentucky. Anthropic/Fluidstack's Nov 12, 2025 post says only
  'New York and Texas'. No NY site confirmed. Do not attribute Abernathy to
  Anthropic without a source.
- (2026-10-21) TCEQ permitting after the Sept 21 directive: Seed now carries
  the Oct 19 TCEQ letter (Inside Climate News, WebFetch-read, probe-blocked).
  Still to fetch: Public Citizen/FracTracker analysis and TCEQ's own response;
  ERCOT audit expected mid-December 2026 (Bracewell, secondary).

- **Hill County TX / Project Aquila:** moratorium (3-2, 2026-05-12) and rescission (2026-06-04) shipped as `hill-county-tx-2026-05`. The old `hill-county-tx-2024-04` ("permanent", datacenterbans.com homepage) was removed: neither KWTX article mentions any 2024 moratorium. Project Aquila (RCM Hill, 1,235 MW, 800+ acres) has no project record: needs a developer or county source, KWTX only so far. **medium**
- El Paso / Meta CBA: council directed staff (2026-06-23) to draft one in 45
  days. No draft or signed agreement found as of 2026-10-08. Add when terms
  exist. **low**
- EEI: El Paso Electric 57568 / 56903 / 59611, SWEPCO 58796, TNMP 58964.
- Dallas (early stage), plus Lubbock and Jefferson County resolutions: not
  moratoriums.

#### state:VA — Virginia
- (2026-10-21) qts-manassas-va: QTS moved its site to q.com and the PWDG page
  (old source_url) is gone; the record now cites the Manassas campus page,
  which doesn't mention the Prince William Digital Gateway. Source the PWDG
  rezoning/litigation sentences in the notes to court or county pages.
- (2026-10-21) Spotsylvania 'Crossroads Technology
  Campus': WJLA (Sept 21, updated Sept 28) says the planning commission voted
  4-2 to recommend approval and the Board of Supervisors hearing is next;
  attorney claims $8B and $30M+/yr tax revenue; applicant RCK Digital
  Crossroads LLC (Kettler) per county filings; AWS named as applicant by the
  reporter only. No tracked project record exists. Not added: Amazon's role
  has no named or first-party statement, no MW, acreage conflict (555 vs 633
  acres), and the vote date is unstated. Re-check for the Board vote, then add
  as a project.
- (2026-10-21) Spotsylvania County: Crossroads Technology Campus (Kettler):
  Not added as a site. WJLA (published Sept 21, updated Sept 28, 2026):
  Planning Commission voted 4-2 to recommend a special-use permit and 4-2 that
  it is in accordance with the comprehensive plan; the article says the permit
  is for Amazon Web Services and the developer's attorney (Charles Payne,
  Kettler) says the project 'includes a cloud operator, Amazon'. County
  filings reviewed by the researcher name RCK Digital Crossroads LLC as
  applicant and no tenant; no first-party Amazon statement found. Campus ~555
  acres (633 in earlier filings), est. B and M+ annual county tax per the
  developer's attorney (stated, unverified), three substations, power early
  2030s. Next: Board of Supervisors hearing and vote, date unannounced. Add as
  an Amazon site only once Amazon or the county names AWS.

- **Spotsylvania Board of Supervisors 4-2 resolution (2026-08-11)** supporting a statewide moratorium (WJLA, https://wjla.com/news/local/spotsylvania-county-backs-call-for-statewide-moratorium-on-data-centers-abigail-spanberger-ai-energy-use-zoning-decisions). Advocacy resolution to the governor, no schema fit (not a moratorium, no tracked project). **low**
- **Prince William Dulles South Innovation Center rezoning declined (~2026-07-07; E&E News, vote count not reported).** No project record exists; event date is inferred from "Late Tuesday" in a 07-08 article, confirm on the dateline before adding. The Digital Gateway ending is already on `qts-manassas-va` (2026-07-02). **medium**
- (2026-10-18) Loudoun: Board resolution scheduled Oct 20 to pause its own
  legislative action on data center and substation applications for up to a
  year (county news flash, Sept 17/24). A pause on the Board's own docket, not
  a moratorium. Update `loudoun-county-va-2026-09` after the vote.
- EEI: APCO PUR-2025-00057.
- Prince William, Christiansburg and Henry County: zoning actions.
- A statewide moratorium call (the Sturtevant and Lucas letters) is not a
  bill. Re-add only if a bill or an executive order appears.

#### state:WA — Washington
- (2026-10-18) Pierce County: emergency ordinance (6-1, Aug 25) pausing
  data centers >10 MW; Oct 20 hearing. County pages 403'd and snippets
  disagree on the number (2026-577 vs O2026-557). Add once a county page
  confirms.
- Port Angeles only voted to draft. The Marysville record omits "Ordinance
  3381" because the number traces only to an AI aggregator. Add it if a city
  page confirms it.

#### state:WI — Wisconsin
- (2026-10-21) Port Washington TID referendum court ruling; Florence County:
  Port Washington: oral ruling reportedly set Oct 19 on the ballot initiative,
  outcome not found; not a moratorium. Florence County zoning agenda item
  'Moratorium for Data Centers' (Aug 5): outcome not found.
- (2026-10-18) Mount Pleasant Village Board vote on Microsoft's amended
  seven-building site plan expected "later this month" (WPR); no date.
- EEI: Xcel 4220-TE-119, MGE 3270-TE-124, WPL 6680-TE-119.

#### state:WV — West Virginia
- (2026-10-21) Nscale lost Microsoft deal (DCK Oct 19): Possible impact on the
  tracked Nscale Monarch (Mason County WV) site; article body unreadable.
  Follow up.
- Appalachian Power / Google large-load settlement (WVPB, Jan 2025: 100 MW
  minimum, 12-yr term, 80% take). Find the PSC case number and outcome.
  Pairs with `google-putnam-county-wv`. Also EEI docket 24-0611-E-T-PW.

### Companies

#### company:amazon
- Butler County / Trenton OH ($5B, 18 buildings): the annexation petition
  was withdrawn, and the 25 MW citizen measure is on the Nov 3 ballot
  (ledger follow-up on state:OH). No Amazon confirmation yet.
- Built Together (announced 2026-10-02, $1B/5yr company-wide community plan):
  too fresh for named-critic or local-government reaction coverage at capture
  time. Re-check in a week or two for NGO/resident/elected-official reactions
  (positive, mixed, or skeptical) to add as CommunityResponses; also watch
  for the first site-specific grant or training-center announcement under
  the program, which could become a project-tied Claim or a `delivered`
  assessment once independent reporting exists.

#### company:anthropic
- Anthropic + Fluidstack ($50B, TX and NY): neither primary source names a
  town. Once one does, the site and Dario Amodei's quote on the Fluidstack
  blog ("meaningful economic impact in the communities where we operate")
  become addable together. Don't guess from third-party candidates
  (TeraWulf Abernathy, Cipher, Lake Mariner).
- Riot Platforms Rockdale TX ($9.1B lease): every source still says
  "reportedly", and Riot's 10-Q names only "a leading frontier AI lab".
- Honest permanent gaps: community_grants, education.

#### company:coreweave
- CoreWeave Cedar Creek / Bastrop County TX (EdgeConneX AUS02, first named
  Mar–May 2026): a real site that isn't tracked. 2026-09-27: DCD's own
  article on it (datacenterdynamics.com) 403'd this run; still not
  citable, still not tracked.
- CoreWeave / Prime Data Centers, Elk Grove Village IL: the $850M bond,
  15-year CoreWeave lease and ~$2.2B contracted-revenue figures are
  confirmed by a Bloomberg-sourced GuruFocus wire story (2026-06-01, mirrored
  on tradingview.com; Bloomberg's own page 403'd) — still not a first-party
  CoreWeave/Prime source, so not yet promoted to a tracked Project. Needs a
  primary source (SEC filing, company statement) before adding.

#### company:crusoe
- `crusoe-warrenton-mo` added 2026-09-29 (announced, tax-abatement source
  only). Crusoe's own community page (crusoe.ai/about/communities/warrenton)
  404s — find its live equivalent and add a first-party Claim; also confirm
  site acreage and a total investment figure (only a per-phase $8.3B
  equipment-cost figure was found).
- A second Abilene TX campus (Microsoft-anchored, ~900 MW), first named Q2
  2026: still not tracked.
- `crusoe-cheyenne-wy`: decided 2026-10-19. The Crusoe record is `withdrawn`
  (Crusoe left Project Jade, per its own Wyoming Tribune Eagle source), and
  Google's campus is a separate record, `google-cheyenne-tembo-wy`. The tied
  claim and responses stay on the Crusoe record as history.

#### company:google
- Google Fort Wayne IN ("Project Zodiac", ~$2B, ~200 jobs, I&M territory):
  operational Dec 11 2025 per Inside Indiana Business. Never tracked.
- Google as a "possible customer" of MidAmerican's Salix IA site: no deal,
  and annexation litigation is ongoing. Too early.
- Google Cedar Rapids IA: a new data center campus named alongside the
  Council Bluffs expansion in Google's $7B Iowa investment (blog.google,
  2025-05-30, "development of both a new data center in Cedar Rapids and
  expansion of our existing facility in Council Bluffs"). Never tracked as
  its own Project (found 2026-09-29 during the site:google-council-bluffs-ia
  review).

#### company:meta
- Meta New Albany OH ("Prometheus", slated to open in 2026): never tracked.
  Create `meta-new-albany-oh`, then attach Chris Rinkus's Aug 18 2026 quote
  ("…paying the full cost of the energy our data centers use — so others
  are not negatively impacted…", datacenters.atmeta.com) as the `affirmed`
  evidence claim. Don't ship the quote as an orphan company-wide claim.
- "Future Is for Everyone Fund" ($1B): company-wide, no site to attach.
- Honest gap: tax_revenue. Meta executives don't quote tax figures.

#### company:microsoft
- "ATL50", 5235 Stonewall Tell Rd, Union City GA: a GA DCA DRI application
  filed Sept 17 2026 (88 ac, two 3-story buildings, launch 2032). It sits
  next to the tracked `microsoft-union-city-ga` (4810 Stonewall Tell Rd) and
  is probably a second campus. Confirm it from the DRI record.
- IREN / Microsoft Childress TX "Horizon 1" ($9.7B contract, Nov 2025):
  not tracked.
- The "Responsible datacenter development in the state of Texas" letter to
  Gov. Abbott (local.microsoft.com PDF, Aug 2026) is an image-only scan.
  It needs OCR before it can be quoted; possibly relevant to
  `microsoft-pecos-tx` and `microsoft-castroville-tx`.
- The Northern Virginia community page's five region-wide commitments are a
  candidate company claim.

#### company:openai
- openai.com 403s to scripts. The Stargate Community tax language, the
  Abilene announcement and the Effingham County GA post all need a
  browser read for verbatim quotes. Effingham is likely `affirmed` material.
- Honest gap: tax_revenue.

#### company:oracle
- `oracle.com/news/announcement/oracle-ai-infrastructure-local-communities-2026-01-26/`
  is a permanent 404 with no archive. Find where it was republished. If it
  wasn't, the claims keep their three third-party mirrors.

#### company:prologis
- "Project Steel", Yorkville IL (540 ac, 24 buildings, $40M development
  agreement approved Mar 24 2026, first phase summer 2027): never tracked.
- "Responsible Data Center Development Commitments" (Aug 10 2026):
  company-wide. Not fetched yet.

#### company:qts
- The $250M Texas water pledge (Aug 31) and $1B Global Water Stewardship
  Pledge (Sept 9) are company- or state-wide, with no site to attach.
- Prince William Digital Gateway cancellation: see decision 5.

#### company:wonder-valley
- Honest gaps: community_grants, education.

### Sites

#### International records held for an operator company (2026-10-19)
- Verified but unshipped, because `Project.company_slug` needs a registered
  operator: Mayo Data Hub Killala (IE), Campus IA Fouju (FR; MGX / Bpifrance
  / Mistral / NVIDIA), Inzai Chiba (JP; Colt DCS Japan), and, with no
  operator named at all, Abbots Langley (GB) and Muan Oryong (KR). Each
  comes with its responses. Add the operator (owner rule: international
  operators become companies), then ship. Research is in
  `notes/specs/international/wave2/`. **medium**

#### Claims and responses held after the 2026-10-19 link check
- Resolved 2026-10-19 (reval pass): QTS Dane County claims and
  `aws-water-positive-2030` repointed and re-quoted; `resp-google-lima-epa-hearing-negative`
  re-sourced to WDTN. Still open on Lima: WDTN calls the applicant "an unnamed
  company" (Project BOSC; reported as Bistrozzi LLC), so the Google attribution
  on project `google-lima-oh` is unconfirmed. PFAS/VOC and "health" wording
  were cut because no fetched page has them. **medium**
- Removed 2026-10-19 (reval pass), no supporting page found after a targeted
  search: `resp-meta-prineville-positive` (Crook County press-release URL
  redirects to the county homepage; nothing equivalent found), moratorium
  `boise-id-2026-05` (homepage-only citation; two searches found no Boise
  action). The AWS Pennsylvania and xAI/Tom's Hardware links were replaced,
  not removed. Re-add Boise only with the city's ordinance.
- Figures on `google-mesa-az`, `ms-quincy-wa`, `ms-goodyear-az` that no
  fetched source states (Mesa 187 ac / 400 MW / 2019 year; Quincy 270 ac and
  the "flagship" framing; Goodyear 300 ac / 480 MW) were left in place but
  are unverified; Mesa investment was corrected to the $600M groundbreaking
  figure and Quincy/Goodyear investment and jobs were nulled. Find Mesa's
  2019 council agenda (DCD reports $1bn, 187 ac) and Microsoft's own Quincy/
  Goodyear figures. **medium**
- Meta info-sheet claims (Prineville, Newton, Richland, Huntsville) now cite
  Wayback copies of the 2024-25 sheets; the current sheets differ ($2B+
  Georgia, $5.6M+ Newton schools, $5.7M+ Prineville, $4.5M+ Huntsville, 220 MW
  Oregon). Re-capture current figures as new dated claims, don't overwrite.
  **medium**
- `aws-infrastructure-pa-2024`: the announcement was June 9, 2025 (PA Governor
  release), not 2024; the id keeps "2024". The quote is now David Zapolsky's.
- Georgia PSC rule decision date corrected to 2025-01-23 (the PSC release
  says "Thursday", dated January 23); the dead fact-sheet link was dropped.
- `new-hampshire-state-2026-04`: the "moved" gc.nh.gov billText URL in the
  first reval list pointed at SB520; the record now cites the HB1265 bill
  status page (id=1685).
- Cleveland extended through 2027-01-29, Athens-Clarke lifted 2026-04-07
  (earlier text said April 8), Kiowa extended to 18 months per the
  2026-09-24 minutes; find Kiowa's written extension resolution and
  Cleveland's ordinance number. **medium**
- Removed 2026-10-19 because no page, live or archived, contains their
  words: google-economic-impact-reports, google-grants-for-good,
  meta-stem-education, meta-engagement-dialogue, ms-pledge-2024,
  ms-community-investment-wi (the $50M was Microsoft's land price, not a
  community investment), sb-energy-community-grants-cba (the $40M fund is
  described only in NVIDIA's release, not SB Energy's words). Re-add only
  with a fetched first-party quote.


#### site:amazon-shreveport-la
- Held at `pledge_only`. Keith Klein's "Amazon pays its own way" (KTBS, Aug
  18 2026) is investment-wide, with no electricity-cost content. Upgrade to
  `affirmed` if Amazon publishes a site-specific power-cost statement (its
  Wharton and Pecos County posts are the model).

#### site:amazon-montgomery-city-mo
- Preserve Montgomery County, LLC sued Montgomery County and the Missouri
  Department of Economic Development on Feb 17, 2026, alleging 10 Sunshine Law
  violations tied to a data center approval (ABC17:
  https://abc17news.com/news/top-stories/2026/02/17/lawsuit-filed-to-stop-montgomery-county-data-center/).
  The article names no company. Find a source that ties the suit to this site,
  or to `google-new-florence-mo`, before recording it. A record sat on the
  Google site citing an article that never mentions the suit; it was removed
  2026-10-08. **medium**
- The $10B figure isn't on the cited aboutamazon.com page, which says only
  "several billion". Re-cite or soften it.

#### site:amazon-richmond-county-nc
- (2026-10-19 validation) source_url (DCD) blocked; WSOC Oct 30 2025 says Amazon 'officially
  breaking ground'; WUNC Sep 2026 says under construction. Acreage 800/500
  jobs unverified. → Optionally repoint to WSOC.
- The 1,600 MW figure is diesel backup generation from the permit, not grid
  capacity, so `power_mw` is left null on purpose.

#### site:aws-calvert-cliffs-md
- The "~1.5 GW" figure traces only to dcpulse.com's unsourced estimate.
  Don't use it without a primary source.

#### site:aws-wilmington-oh
- The Planning Commission tabled it twice (Nov 2025, Jan 7 2026) over
  traffic and lighting studies and an unanswered PFAS question. This is a
  CommunityResponse candidate. Separately, reporting suggests no
  benefit-agreement payment amid litigation; the wnewsj.com source 403'd.

#### site:google-henderson-nv
- $6B is Google's combined Henderson + Storey County figure, not
  Henderson's alone.

#### site:google-lagrange-ga
- Acreage conflict: 420 ac (notes) vs 270 ac (the original Thor
  Equities/Form8tion purchase). A July DCD headline suggests an expansion.

#### site:google-lenoir-nc
- The 400 jobs figure isn't on the cited page.

#### site:google-mayes-county-ok
- (2026-10-19 validation) $15B and $12M are Oklahoma-wide per Google page. → Scope the figures.
- The 800 jobs figure isn't on the cited datacenters.google page.

#### site:google-michigan-city-in
- Jobs: the record says 500; a directly fetched DCD article says "30+".

#### site:google-van-buren-mi
- Wayne Co. Executive Warren Evans vetoed the township's May 19, 2026 tax
  exemption (and a related community-benefits agreement) on 2026-09-25,
  calling the approval process "rushed"; commissioners were expected to
  vote to override the veto at their Oct. 1, 2026 meeting. Detroit News and
  Crain's Detroit Business both cover it but 402/403'd on direct fetch this
  run; try again or find an unpaywalled mirror before adding as a
  CommunityResponse (constituency: local_government) + updating
  Project.notes with the outcome.
- The May 19, 2026 township tax exemption (50%/15yr + 36-mo construction
  exemption, $15.4M to the township for capital projects — confirmed via
  bellevilleareaindependent.com) is a candidate for a `benefit_agreement`
  Policy record; not added this run for lack of time to pick the right
  principles.
- MPSC docket U-22058 (contested case, AG pushing 90% min billing demand
  vs. DTE's 80%) had a Sept. 10, 2026 decision target; no order confirming
  a decision was found this run. Check ADMS
  (adms.apps.lara.state.mi.us) or mi-psc.my.site.com for the order once
  issued.
- Van Buren Township's Planning Commission final site-plan vote (delayed
  from Aug. 26) was expected Sept. 23 or Oct. 14, 2026; not confirmed this
  run.

#### site:meta-prineville-or

- **Dead `source_url` (2026-10-05).** `https://datacenters.atmeta.com/location/prineville/` returns 404. Needs Meta's current Prineville page; no guessed URL. Permits/ratepayer/Crook County school-tax items not checked.

#### site:meta-newton-ga
- (2026-10-19 validation) source_url 404; project page is a 2021 post with none of the record's
  figures (1120 MW, 416 ac, $1.5B, 400 jobs, operational). No fetched
  replacement. → Find a primary source for the figures or label them.
- **Dead `source_url` (2026-10-04).** `https://datacenters.atmeta.com/location/newton/`
  returns 404 (also in a browser-UA fetch). The `project_page_url`
  (`/2021/03/hello-georgia/`) is live but is the 2021 announcement, which does not
  state the $1.5B / 400-job / 1,120 MW figures. Needs Meta's current Newton page
  (or a fetchable local-press source) before the URL is swapped; no guessed URL.
  Unit not marked reviewed: figures, permits and news were not completed.
  2026-10-05 follow-up: Meta's April 3 2026 page
  (`https://datacenters.atmeta.com/2026/04/operating-responsibly-at-the-stanton-springs-data-center/`)
  is live but carries no investment/jobs/MW/acreage figures either. It does say
  "Meta partners with Newton County Water and Sewerage Authority to secure 100% of the water
  used at our Stanton Springs Data Center. We do not utilize groundwater in our operations."
  - a candidate water Claim (project_id meta-newton-ga) that conflicts with the
  groundwater-concern response already on record. Not added this run (not verified against a
  second source). `/stanton-springs-data-center/` returns 404.

#### site:microsoft-boydton-va
- $2B and 250 jobs aren't on the cited local.microsoft.com page.

#### site:microsoft-fayetteville-ga
- No first-party community quote yet. Only architecture quotes exist
  (Russinovich, Speirs). One outlet places the site in South Fulton near
  Palmetto; AJC and three trackers say Fayette County.

#### site:ms-mt-pleasant-wi
- `claimed_investment_usd` ($7B) is a curator-computed total. It needs a
  citable URL for the Sept 2025 $4B second-facility announcement.

#### site:oracle-dona-ana-nm
- (2026-10-19 validation) Abq Journal (Sep 2026): 26% complete, 'current energy plan would still be
  fueled by natural gas' vs notes 'Bloom fuel-cell-powered'. Crypto
  Briefing (single trade outlet) reports project 'reportedly being
  mothballed'; unconfirmed. Force-majeure notice seen only in search
  summary. → Human review: energy wording; verify mothballing/force
  majeure on primary sources before adding updates.
- New Mexico regulators rejected a 17-mile gas pipeline that would have fed
  Project Jupiter (week of 2026-07-20). This is a regulator
  CommunityResponse candidate, pending a primary source.

#### site:qts-aurora-co
- (2026-10-19 validation) Campus 160 MW; QTS plans up to 200 MW across Colorado. → Scope note.
- The 65–80 ac / 4-building specifics in `notes` aren't on the cited
  article. Re-cite or soften them.

#### site:qts-dane-county-wi
- Jobs conflict: "450 permanent" (filing stage) vs "up to 5,000 trade jobs"
  ($12B announcement). `claimed_jobs` is left empty pending a call.

#### site:wonder-valley-box-elder-ut
- (2026-10-19 validation) power_mw 3000 (phase 1, from county approval per notes) vs own source
  (PRN) '7.5 gigawatts per campus'. → Notes attribute 3 GW to the May 4
  county approval; leave, but consider stating both.
- The auto-derived At-a-glance lines truncate an O'Leary marketing quote.
  Write a curator `at_a_glance` override.

---

#### site:amazon-caddo-parish-la
- (2026-10-19 validation) Shares one combined $12B figure with amazon-bossier-parish-la
  (KSLA/Opportunity Louisiana cite $12B across both parish campuses); the
  two records double-count it. Neither source gives a per-site split. →
  Keep the combined figure on one record and null it on the other, or note
  it as combined; needs a curator decision.

#### site:amazon-bossier-parish-la
- (2026-10-19 validation) Double-counts the combined $12B with amazon-caddo-parish-la;
  'construction' status unconfirmed (KSLA Feb 2026 says construction
  'expected to begin imminently'). → Dedupe the $12B; re-check status
  against a later source.

#### site:coreweave-ellendale-nd
- (2026-10-19 validation) power_mw 150 is the added lease; own source says 400 MW across three
  leases. → Decide whether power_mw should be the site total (400).

#### site:ms-goodyear-az
- (2026-10-19 validation) source_url 404; project page covers Goodyear+El Mirage jointly; record's
  250 jobs/$1B/300 ac/480 MW unsupported by fetched pages. → Find
  Goodyear-specific source.

#### site:ms-quincy-wa
- (2026-10-19 validation) source_url 404; none of 600 jobs/270 ac/$4B supported by fetched project
  page. → Find Quincy-specific source.

#### site:google-haskell-tx
- (2026-10-19 validation) source_url 404; replacement KTXS (Nov 2025) says Google 'prepares to
  build', so 'construction underway' is unverified by any fetched page. →
  Verify construction via TDLR/abatement filing before keeping status.

#### site:aws-new-carlisle-in
- (2026-10-19 validation) source_url 404; live Amazon page describes $15B/2.4 GW/1,100+ jobs for
  Northern Indiana vs record's $11B/2,200 MW/1,000 jobs. → Re-scope record
  to the $15B plan or keep 2024 figures with a different source.

#### site:google-mesa-az
- (2026-10-19 validation) source_url 404; GPEC project page says $600M (2023 groundbreaking) vs
  record $1.2B. → Check whether $1.2B is multi-phase; find supporting
  source.

#### site:google-the-dalles-or
- (2026-10-19 validation) source_url 404; Oregon page says 2006 vs announced_year 2005; $7B is
  Oregon-wide. → Fix announced_year if confirmed; find site page.

#### site:amazon-clinton-ms
- (2026-10-19 validation) Record's source (aboutamazon release) does not state the $1B Clinton
  figure or 100 jobs; OurTupelo/Mississippi Today (Jun 9 2026) does for
  jobs. Status 'announced' despite ribbon-cutting and 1,500 peak
  construction workers. → Consider repointing source_url to OurTupelo and
  re-checking status.

#### site:microsoft-cheyenne-wy
- (2026-10-19 validation) Existing 2026-07-14 annexation update: yourwyominglink says 'late Monday
  night' (July 13) while publishing July 14. → Re-date existing update to
  2026-07-13 if confirmed.

#### site:crusoe-sweetwater-tx
- (2026-10-19 validation) No independent corroboration of Crusoe at the Sweetwater site found; KTXS
  names Crusoe Energy Systems. → Verify company attribution.

#### site:crusoe-abilene-tx
- (2026-10-19 validation) Mid-2026 completion date has passed; status 'construction' needs current
  source. claimed_jobs uses 5,600 daily construction workers, not a jobs
  total. → Re-check status; label jobs.

#### site:google-armstrong-tx
- (2026-10-19 validation) Source replaced with Crusoe release, which names Crusoe as developer and
  does not state 1,300 acres; notes say 'Crusoe assisting with site
  preparation'. → Find an acreage source; reword developer note.

#### site:google-west-memphis-ar
- (2026-10-19 validation) acreage 1178 (Project Pyramid filing per notes) vs KAIT8 1,100 acres;
  Google blog source does not state acreage/jobs. → Curator to reconcile.

#### site:qts-manassas-va
- (2026-10-19 validation) Notes say rezoning approved Nov 2022 and ~2,139 acres; WTOP says Dec 2023
  and 2,000 acres. → Verify with county records.

#### site:qts-clinton-ia
- (2026-10-19 validation) Own source: 3,500 acres, M3 zoning, $1.5B taxable revenue (not investment)
  vs record ~3,400 ac, M5, $1.5B investment. → Verify and correct.

#### site:meta-montgomery-al
- (2026-10-19 validation) Own source says $800M/100 jobs; record $1.5B/1,100 jobs rely on notes'
  Sept 2025 expansion (other source). → Add a source for the expansion.

#### site:meta-kuna-id
- (2026-10-19 validation) Own (2022) source says $800M+ and ~100 jobs; record figures from Sept 2026
  Meta statement per notes. → Cite the 2026 statement.

#### site:sb-energy-piketon-oh
- (2026-10-19 validation) DOE page: 189-acre initial phase, 10,000 construction + 2,000+ permanent
  jobs vs record 2,700 ac, 37,500 jobs. → Reconcile scopes (SB Energy
  full-campus vs DOE phase 1).

#### site:aws-cumberland-pa
- (2026-10-19 validation) $20B is Pennsylvania-wide per Amazon, presented as this campus. → Scope
  the figure.

#### site:microsoft-new-albany-oh
- (2026-10-19 validation) $1B is shared across New Albany, Heath, Hebron per own source. → Scope the
  figure.

#### site:meta-eagle-mountain-ut
- (2026-10-19 validation) $3B is Meta's total Utah investment per Utah Business. → Scope the figure.

#### site:amazon-vicksburg-ms
- (2026-10-19 validation) claimed_jobs 200 not stated for Warren County; page gives 2,000 statewide.
  → Find site-specific source.

#### site:oracle-abilene-tx
- (2026-10-19 validation) gpu_count 450,000 vs Network World ~400,000 GB200. → Reconcile.

#### site:qts-eagle-mountain-ut
- (2026-10-19 validation) Notes say three buildings; QTS page says five buildings in phase one. →
  Verify.

#### site:qts-blakely-ga
- (2026-10-19 validation) QTS page: 'concept stage', no start date, 1,400 MW vs notes' July 2026
  construction timeline. → Verify timeline; check status.

#### site:meta-el-paso-tx
- (2026-10-19 validation) ICN describes the 366 MW gas facility as powering the data center, not
  'backup via 813 generators'. → Reword notes after verification.

#### site:crusoe-goodnight-tx
- (2026-10-19 validation) Building 4 due March 2027 vs notes' Feb 2027 go-live window. → Update
  notes.

#### site:aws-boling-tx
- (2026-10-19 validation) TDLR start date 9/1/2026 vs notes' Aug 1 2026. → Update notes.

#### site:google-gray-county-tx
- (2026-10-19 validation) Page: 'air cooling to limit water consumption' vs notes 'zero water
  consumed'. → Soften wording.

#### site:aws-ridgeland-ms
- (2026-10-19 validation) Amazon page: 'pay 100% of the costs associated with our new data center
  campuses' vs notes 'all grid infrastructure and upgrade costs'. → Align
  wording.

#### site:microsoft-heath-oh
- (2026-10-19 validation) Own page: vertical-construction timeline 'has not yet been determined' vs
  notes 'completion early 2028'. → Verify.

#### site:google-lea-county-nm
- (2026-10-19 validation) Quote wording in notes differs from Google page ('While discussions are
  ongoing'). → Fix quote.

#### site:microsoft-douglasville-ga
- (2026-10-19 validation) announced_year 2023 vs Azure region blog Feb 2021. → Verify site-specific
  year.

#### site:google-sand-springs-ok
- (2026-10-19 validation) Rezoning is in Osage County per Public Radio Tulsa; notes say Tulsa/Creek
  border. → Fix location text.

#### site:qts-york-county-sc
- (2026-10-19 validation) Venue of May 12 meeting: Oakridge Elementary per Post and Courier vs
  notes' Middle School. → Fix notes.

#### site:crusoe-springfield-oh
- (2026-10-19 validation) Source: 'did not return a request for comment' vs notes 'declined
  comment'. → Fix notes.

#### site:microsoft-castroville-tx
- (2026-10-19 validation) TDLR completion date 7/24/2028 vs notes June 2028; TDLR est. cost $400M. →
  Update notes.

#### site:coreweave-hammond-in
- (2026-10-19 validation) 'Up to $4M' community impact payment not stated on the city page. → Source
  it.

#### site:qts-cedar-rapids-ia
- (2026-10-19 validation) 2,000 jobs vs 30 high-tech jobs in source; 1,050 MW/$1.75B unverified. →
  Label job categories.

#### site:coreweave-lancaster-pa
- (2026-10-19 validation) Page says 600+ construction and 75+ operational jobs; record 775. → Fine
  as sum; confirm.

#### site:google-franklin-furnace-oh
- (2026-10-19 validation) Later coverage (search only) says 792 acres/1.7M sq ft vs record 500,000
  sq ft. → Verify.

#### site:google-pine-island-mn
- (2026-10-19 validation) Validator could not find the existing 2026-10-11 MPR 'on pause' item; TRO
  (May 22) added as update. No 'paused' status exists. → Confirm TRO still
  in force.


#### country:GB — United Kingdom
- (2026-10-21) Nscale Loughton: Microsoft
  termination added from Data Center Knowledge (Oct 19). The UK Power Networks
  'early to mid-2030s' timeline is DCK's citation of The Guardian; fetch the
  Guardian piece to confirm and check whether Epping Forest District Council
  has decided. Nscale's US Monarch (WV) record is not mentioned in the DCK
  piece.

## 4. Product and UX

- **Querétaro evidence follow-up (2026-10-14).** The planning guide attributes
  the 2023 assessment's estimated generator emissions and a registry image (concession
  855979, 25,000 m³/year, aquifer 2203). Authenticate the live registry entry,
  matching municipal denominator/year, generator permit and runtime records
  before publishing facility-use figures or a violation finding. Confirm any
  Microsoft–Ascenty tenancy independently; proximity is insufficient. **medium**

From the 2026-09-25 cross-device audit (phone 390, tablet 820, laptop 1366,
desktop 1920). Performance is healthy everywhere: on Slow 4G with 4x CPU,
FCP is 0.86 s, LCP ≤ 1.4 s and TBT is ~0. The problems below are layout and
navigation.

- ~~**Phone tab bar hides most of the site.**~~ Done 2026-10-08: the bar
  wraps to two rows of short labels at ≤960px (interaction-cost UAT).
- **Moratorium end dates on Home "Coming up".** Removed 2026-10-08 (Codex
  on #63): `duration_months` is often a rounded "45 days" or "through Oct
  16", so start + N months invented deadlines. Add an explicit, curated
  `ends_on` date to Moratorium, backfill it from each record's own source,
  then list end dates again. The refresh queue's derived end-date follow-ups
  have the same rounding problem. **medium**
- **Moratoriums directory has no search.** On a phone, an older record is
  many swipes down the table. Add a jurisdiction/bill search like Sites'
  `#f-q`, then add a task for an older record to `tools/interaction_cost.py`.
  **medium**
- **The Pledge scorecard is 4 swipes in on a phone.** Consider a jump link
  or putting the scorecard before Coverage. Measure before and after.
  **low**
- **Benefit Agreements: tag the rest.** 28 records carry feature tags.
  Re-check each untagged agreement's source for the nine terms, and add the
  Michigan HB 6137-style "permit or hookup gated on a CBA" as a 10th feature
  only with a BACKLOG migration. **medium**
- **Landing redesign** once decision 1 is made. **high**
- **Stat tiles stack raggedly on phone.** Content-sized tiles (`flex: 0 1
  auto`) wrap into rows of 1, 1, 1, 2, 1, taking about 1.3 screens before
  any content. Use a two-column grid under ~600 px. **medium**
- **The Home "Recent changes" feed is unsorted and roster-only.** It lists
  items in code order, not by date, and never shows new moratoriums,
  policies, tariffs, rate-case decisions or sites, which is most of what
  changes. It should be derived from all record types (see `home.json` in
  §5). **medium**
- **"Upcoming docket dates" can show past dates.** Between a milestone
  passing and the routine re-checking it (due the next day), Home lists a
  date that is already over. Filter out past dates, or label them "awaiting
  outcome". **low**
- **Very long pages on phone.** Moratoriums runs 25 screens, Tariffs 17.5,
  The Pledge 13.4. Collapse directories by default under 600 px, or
  paginate. **medium**
- **Tiny targets on The Pledge.** 214 targets under 24 px on phone (state
  strip cells, row source links, the concern checkbox at 13 px). Tariff
  filters and moratorium level toggles are also under 24 px tall. **medium**
- **"323 organizations" on Home vs "346 signatories" on The Pledge.** The 23
  governors are the difference, and the Coverage header should say so.
  **low**
- **Contested-site timelines: thin sites.** v5 researched all 59 contested sites;
  14 still have no typed events (nothing verifiable found), only their
  community responses on the timeline. Same method: Haiku per site, probe
  gate, per-event date check. **medium**
- **Announced upcoming dates are thin.** No verified future hearing/vote
  dates turned up for any contested site. Agendas (county/city .gov) are
  where they live; a per-site agenda check would make "Next date first"
  sorting useful. **medium**
- **Companies › Commitments: a "first-party figure" check.** Depth counts a
  claim as Specific when it has a `metric`; a curator pass should confirm
  each metric's number is in the quote itself. **low**
- **Map clustering on Sites** is still open (Northern Virginia). **medium**
- **State totals table:** add a policy-count column (`coverage.json` already
  has it). **low**
- **Per-principle "what's missing" view:** which of the 9 principles each
  state has no record for. **low**
- **Per-utility panel** (`#utility/<slug>`: tariffs, rate cases, served sites,
  roster row). **low**
- **Framework-evolution timeline** per company, using `Claim.published_at`.
  **low**
- **Pattern synthesis overlay:** about 10 recurring lessons (NDAs, cost
  shifts, water draw, turbines, housing, annexation…) with the sites where
  each surfaced. **low**
- **National-context panel on The Pledge** for findings that aren't about
  one site (Brookings enforcement gap, PJM capacity share). **low**
- **Desktop CLS 0.07–0.10** on Home and Sites as numbers and cards fill in.
  Reserve their space. **low**
- **Phone header is 145 px** because the title wraps to two lines. **low**
- Matrix-cell deep link; "what's new since your last visit" badge;
  capture-history view; phone bottom sheet for project detail; density
  toggle for long lists; accordion memory; `tariff-coverage-count` shows the
  constant 17. **low**
- PDF exports still use the pre-2026-08-24 look (display serif, red chrome).
  **low**

---

## 5. Performance and engineering

- **First paint is at 246.5 of 250 KB gzipped.** Home fetches `claims.json`
  (49 KB) and `projects.json` (60 KB) to show six numbers and a short list.
  Emit a small `home.json` digest from refresh.py (numbers, dated changes
  across all payloads, upcoming dates). That drops Home to about 140 KB,
  and every landing option needs it. **high**
- **First-paint test should observe real requests.** `test_perf_budget.py`
  sums a hand-written `FIRST_PAINT` list, so pulling a payload back into boot
  fails nothing. Record requests in Playwright up to the first render and
  fail on any payload not in the allowed set (PR #62 review). **medium**
- **e2e: one context fixture.** ~8 tests build their own `browser.new_context`
  and miss the autouse fast-fail timeouts and tile stub; move both into a
  shared context fixture and import `E2E_WAIT` from conftest. **low**
- **Code-split `app.js`.** It is 85 KB gzipped and loads whole on every
  view. **medium**
- **Home builds the Pledge view's DOM** (7.5K nodes at load) because both
  share `loadRatepayerView()`. Render only what's visible. **low**
- **22 W3C validation errors.** 11× `role` on `<th>`, 4× `aria-label` on a
  bare `<div>` (silently ignored by screen readers), 3× `role=dialog` on
  `<aside>`, and 1× empty `<thead>` row. Wire the validator into a test so
  the count only goes down. **medium**
- **`key_reasons` ↔ CSS parity test.** Assert that every reason value has a
  `.badge-reason-<value>` rule. This bug shape has shipped three times.
  **medium**
- **`.rp-card-details` summaries wrap a `<div>`,** which is non-conforming.
  Fix the markup, then widen `test_summaries_contain_only_conforming_children`.
  **low**
- **Link checking on a schedule.** `check_links.py` exists but has no CI;
  the daily routine checks only the records it touches. **low**
- **Re-check the `<details>` display trap on WebKit/Firefox** if e2e ever
  runs there. **low**
- **The Microsoft Datacenter Community Pledge connector** would be the first
  real v2 connector. **low**
- **Source snapshots:** Wayback captures of quoted company pages at each
  capture. **low**

---

## 6. Data model and schema

- **`Moratorium.resources` is an untyped `list[dict]`.** Type it as
  `SourceResource`, like tariffs, policies and rate cases. The renderer
  assumes `url` and `title` exist. **medium**
- **No `rejected` rate case exists,** so that badge never renders against
  real data. Find a genuine one; don't fabricate one. **low**
- **A 9th theme, noise / land use.** This needs a migration plus frontend
  parity (see CLAUDE.md > Theme taxonomy). **low**
- **`duration_description` phrasing varies** ("1 year" / "One year" / "12
  months"). Normalize it, or split out a short `duration_label`. **low**
- **`diesel_backup_mw`,** if backup generation should be tracked apart from
  `power_mw` (see site:amazon-richmond-county-nc). **low**
- **v6 vocabulary migrations (2026-10-19, owner-approved, done):** policy
  instrument `government_framework`, principle `heat_reuse` (labelled as
  mainly international), scopes `national` / `supranational`, moratorium
  `jurisdiction_type: national` and `formality` (formal / administrative /
  de_facto). US records were reviewed: none needed re-tagging, and every
  existing default is the US value. Re-check whether any US state "strategy"
  filed as `legislation` is really a `government_framework`. **low**
- **No `withdrawn`/`cancelled` project status.** `aws-calvert-cliffs-md`
  (withdrawn Aug 4, 2026) still reads "announced" with a note. Add a status
  plus frontend handling; decide whether withdrawn sites stay in the
  ratepayer cohort. **medium**
- **8 minimal-data projects** are served by at-a-glance auto-derivation. Add
  overrides when they gain disclosable facts. **low**

---

## 7. Watch list (not addable yet)

Each item has the trigger that would make it addable.

- **Amentum, Savannah River Site SC (1 GW, DOE selection 2026-07-20).** Gate
  2 fails: its quotes cover capability, not the community. Re-check after
  the lease is signed.
- **Aligned Data Centers "Project Phoenix", Shippingport PA** (2 GW,
  groundbreaking Sept 17). Does Aligned publish community-impact framing?
- **Global AI, Weld County CO** (up to 1 GW, approved Sept 9): borderline on
  gate 1.
- **Equinix, Digital Realty:** corporate ESG only, with no per-site community
  framework.
- **DOE Oak Ridge and INL:** energy.gov still names only the Portsmouth /
  SoftBank partnership.
- **GIC/Macquarie "Theseus Infrastructure" (Anthropic):** no site disclosed.
- **Halcyon large-load tariff tracker:** 218 tariffs behind a contact form.
  It's a work-list, not a source.
- **International sites** (Dublin; Uruguay water): out of scope until v2.

### Held international records (2026-10-19, verified but not shipped)

Wave 4 round 3 (`notes/specs/international/wave4/gb_r3.json`, `se_fi_gr_r3.json`), no tracked operator, so held:
- **GB planning appeals with no named operator:** Abbots Langley, Bedmond Road (SoS grant 12 May 2025, ref APP/P1940/W/24/3346061; developer Greystoke Land, 96 MW per the Council's case); Woodlands Park landfill, Iver (Council refusal 25 Jun 2024, SoS grant 9 Jul 2025, APP/N0410/W/24/3347353; Greystoke/Altrad); Court Lane, Iver (SoS grant 6 Dec 2024, APP/N0410/W/24/3337981; Affinius Capital, 140 MW reserved, no operator named); DC01 UK, Elstree (Hertsmere outline approval, The Register 24 Jan 2025, secondary only; Equinix sale unverified). The earlier "AWS Iver" judicial-review label is not supported by the Court Lane letter and was not shipped. Sources are in the round-3 file.
- **FI Lahti Kujala** (ecogrid.energy / Peab, city news 25 Aug 2026, permit application filed): untracked operator.
- **SE atNorth SWE02 Stockholm** (30 MW, go-live Q4 2027, atNorth release 29 Jan 2026): atNorth HQ unverified. **SE Vertical Data, Sollefteå** (release 11 Sep 2026): untracked operator, the 500 MW grid figure is the company's characterisation.
- **GR ADMIE Agios Stefanos 130 MW:** stored only as a Greece context fact (the regulator freeze); ADMIE is a grid operator, not a developer.

Leads from `deep_ie_gb_eu_nordics_gr_ar_sg.json` (2026-10-19), none shipped:
- **IE Meta Community Action Grants, Meath 2027 round** (open 14 Sep to 19 Oct 2026; over EUR 4.8m to 186 projects since 2019): reported by Meath PPN quoting Meta. Needs Meta's own grants page before a Claim.
- **IE Microsoft / Fortum Espoo-Kirkkonummi heat pumps** (waste-heat deliveries "next year", Aug 2026 press): needs a Fortum or Microsoft primary.
- **IE AWS Tallaght build date**: DCD reports a groundbreaking that conflicts with the 2023 opening. Resolve from SDCC or Codema before adding a timeline.
- **IE AWS grid connection**: trade press (2025) says EirGrid called AWS ineligible. Check EirGrid's DCCOPP v3 constrained-area list first.
- **GB Culham AI Growth Zone** (UKAEA, Oxfordshire; 100 MW rising to 500 MW; Find a Tender 005218-2025): operator not tracked; needs a decision on whether a government project record is allowed.
- **GB Google Waltham Cross heat re-routing offer**: not in The Register article; find Google's own statement before a Claim.
- **SE Microsoft Gavle/Sandviken**: no 2026 district-heating item found. **GR** Microsoft Attica and Dromeus/APTO Spata: nothing new. **AR** Stargate Argentina, **SG** green data centre roadmap, **EU** EED: nothing new this pass.

Researched and probe-verified in `notes/specs/international/wave2/deep_au_ca_sg_cl_ar_se_fi_gr.json`,
held because the operator is not a tracked company (add the company first;
international-only operators are allowed per the v6 owner decision, but HQ and
slug need confirming):
- **atNorth** (SE SWE02 Kista 30 MW project, Stockholm mayor welcome response,
  heat-reuse claim; FI Espoo Kesko heat-reuse and Caruna infrastructure claims).
  atNorth's HQ was not verified in wave 2.
- **Dromeus Capital-APTO, Spata GR** (80 MW project plus the municipal-council
  and Council of State residents responses, newmoney.gr, 2025-11-24).
- **Synapse Real Estate Corp., Olds AB** (1,400 MW gas plant denied by the AUC,
  Decision 30732-D01-2026, 2026-08-18; AUC news release PDF). The AUC says it is
  not a view on data centres as such.
- **Régie R-4333-2026 intervenor response** (AQCIE/CIFQ information request,
  2026-05-22, 5 MW threshold could be split into 4.9 MW subsidiaries). Not
  shipped: a `CommunityResponse` needs a `project_id` and the case has no site.
  Candidate home if the schema ever allows a rate-case-attached response.

Held from `notes/specs/international/wave2/deep_jp_kr_in_gb_fr_ie.json` (leads, not shipped):
- **JP METI/ANRE data-centre notice** (data_center2026.html): data-centre items in
  periodic reports from FY2026 submissions, PUE 1.3 or lower for new data centres
  from FY2029. HTTP 403 to WebFetch, so the quote could not be probed. National
  policy candidate once a fetchable copy exists.
- **JP Akita City AI data centre** (up to 500 MW, Shulman Advisory, Aug 2026) and
  **NTT Data Inzai/Shiroi, Chiba** (about 250 MW, secondary). Developers not tracked.
- **JP Utsunomiya solicitation schedule**: application and preferred-bidder dates
  come from secondary reports only; read section V.2 of the solicitation PDF
  before adding a timeline entry.
- **KR dedicated AI data-centre electricity rate** (Ministry of Climate, Energy and
  Environment, 2026-06-29, via asiae). Ministry release not found.
- **KR Google / LG Uplus domestic data centre** (March 2026, secondary only) and
  **Microsoft third Busan AI data centre** (local news, status unconfirmed).
- **GB Section 35 directions**: Dartford New Barn Road (CSE52 Ltd, up to 300 MW,
  2026-07-02) and Wapseys Wood (Buckinghamshire). Developers not tracked.
- **GB UK NSIP commencement date** (8 Jan 2026 per secondary sources): not verified
  on legislation.gov.uk, so left out. The NSIP-route sentence is on
  `gb-ai-growth-zones-2025`.
- **IE Naas appeals** to An Coimisiún Pleanála on a permitted 38.69 ha data centre
  (Aug 2025). Developer not confirmed as tracked.
- **FR Orange / Morrison JV** (EUR 3bn, 400 MW, exclusivity 2026-07-27). Neither tracked.
- **FR Ozans-Châteauroux**: add a CommunityResponse once the CNDP pre-consultation
  reports.

- India leads (2026-10-19, notes/specs/international/wave3/india_deep3.json): Bhogapuram/Vizianagaram farmers' protest (7 Oct 2026, Deccan Chronicle) — no tracked site; Telangana DEF investigation on land assignment for Microsoft/Amazon sites (Scroll/Rest of World) — spans two untracked sites; Mahul/Mumbai water concerns on the state green data-centre parks (Land Conflict Watch). Each needs a tracked project before it can ship as a response. State policy PDFs (TN, MH, TG, AP) unreachable.

### Follow-up 85 claim-quote pass: removed claims, leads (2026-10-19)

Removed because no first-party quote is on the cited page (re-source from a primary page if one exists):
- xAI Memphis (Chamber URL no longer contains them; x.ai/memphis/our-commitment returns 403 to scripted fetches, so unverified): jobs 500, tax $100M, $80M wastewater facility, substations $35M + $20M, "no grid power in emergencies". Re-read x.ai's page in a browser.
- Google Franklin Furnace (WSAZ): reporter paraphrase of Chadwick, no quotation marks. Ratepayer assessment moved to pledge_only. Lead: the May 2026 information-fair Q&A or a Google blog post with a direct quote.
- Reporter paraphrases: Amazon Clinton water/jobs (SuperTalk), Loudoun $150k grants, New Carlisle $7M roads, Wonder Valley O'Leary jobs. Meta Lebanon energy sentence is unattributed announcement text (Peterson not credited).
- Google: 24/7 CFE 2030 goal, 120% water replenishment target (not on current sustainability pages; check snapshots), Oklahoma Porat quotes (no direct quotes on page). Amazon "100% renewable in 2023" (page now reports 2025). CoreWeave Polaris Forge renewable, Hammond "$4M" impact payment, Lordstown "$3B". Oracle "100,000 jobs" was Trump's remark, not Ellison's. Crusoe Abilene jobs (literal quote has no jobs content).
Re-attributed: Oracle Port Washington energy quote is Peter Hoeschele (OpenAI), not Altman.
Wayback-pinned (live pages have drifted; add new dated claims): Google Oregon/Iowa/Virginia, Meta Richland construction/operational jobs.

- Re-source from Wayback (snapshot near 2026-05-14): google-247-cfe-2030 (sustainability.google/operating-sustainably) and google-water-replenish-120 (sustainability.google/commitments/water). Both targets are absent from Google's live pages as of 2026-10-19, so the claims were removed; restore them as dated captures if a snapshot carries the sentence.
