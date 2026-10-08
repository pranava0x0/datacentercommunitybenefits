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
_Generated by `python3 scripts/refresh_queue.py --write-backlog` on 2026-10-08. Do not edit between the markers: review dates and follow-ups live in `data/refresh_ledger.json`, and units come from the data itself._

**Coverage:** 7 of 133 sites reviewed within 90 days; 3 of 15 companies reviewed within 30 days; 0 of 52 states reviewed within 120 days.

**Due now (0)**

Nothing due.

**Next run works through**

1. `site:ms-goodyear-az` (Goodyear Datacenter Campus (Goodyear, AZ; operational)): never reviewed; record curated 2026-05-14 (1.6x target)
2. `state:GA` (Georgia): never reviewed; 31 records
3. `site:ms-quincy-wa` (Quincy Datacenter Campus (Quincy, WA; operational)): never reviewed; record curated 2026-05-14 (1.6x target)
4. `company:anthropic` (Anthropic (2 tracked sites)): never reviewed; record curated 2026-05-16 (4.8x target)

**Then, sites**

| Unit | What | Why now |
|---|---|---|
| `site:openai-abilene-tx` | Stargate Abilene Campus (Abilene, TX; construction) | never reviewed; record curated 2026-05-14 (1.6x target) |
| `site:openai-lordstown-oh` | OpenAI Stargate Lordstown (Lordstown, OH; construction) | never reviewed; record curated 2026-05-14 (1.6x target) |
| `site:qts-cedar-rapids-ia` | QTS Cedar Rapids Data Center Campus (Cedar Rapids, IA; construction) | never reviewed; record curated 2026-05-14 (1.6x target) |
| `site:qts-richmond-va` | QTS Richmond Technology Park Data Center 5 (RIC5) (Sandston, VA; construction) | never reviewed; record curated 2026-05-14 (1.6x target) |
| `site:wonder-valley-box-elder-ut` | Wonder Valley Utah Data Center Campus (Box Elder County, UT; announced) | never reviewed; record curated 2026-05-14 (1.6x target) |
| `site:xai-memphis-tn` | Colossus Supercomputer (Memphis) (Memphis, TN; operational) | never reviewed; record curated 2026-05-14 (1.6x target) |

**Then, states**

| Unit | What | Why now |
|---|---|---|
| `state:TX` | Texas | never reviewed; 28 records |
| `state:OH` | Ohio | never reviewed; 24 records |
| `state:CA` | California | never reviewed; 20 records |
| `state:IN` | Indiana | never reviewed; 19 records |

**Then, companies**

| Unit | What | Why now |
|---|---|---|
| `company:meta` | Meta (14 tracked sites) | never reviewed; record curated 2026-05-16 (4.8x target) |
| `company:openai` | OpenAI (7 tracked sites) | never reviewed; record curated 2026-05-16 (4.8x target) |
| `company:oracle` | Oracle (3 tracked sites) | never reviewed; record curated 2026-05-16 (4.8x target) |
| `company:qts` | QTS (14 tracked sites) | never reviewed; record curated 2026-05-16 (4.8x target) |

**Coming up in the next 30 days (26)**

| Due | Unit | Check |
|---|---|---|
| 2026-10-09 | `state:CA` | Oakland council Oct 6 vote on 45-day data center moratorium (oakland-ca-2026-09) |
| 2026-10-09 | `state:CA` | San Francisco Walton 45-day moratorium: Board vote outcome? |
| 2026-10-09 | `state:NC` | Beaufort County NC: Oct 5 hearing/vote outcome still unconfirmed |
| 2026-10-09 | `state:NC` | Cary NC: find the late-August enactment date to add the 18-month moratorium |
| 2026-10-09 | `state:NM` | Grant County: board formally considers a moratorium Oct 8 (only a notice of intent passed Sept 24) — adopted? |
| 2026-10-10 | `state:FL` | Manatee County Ordinance 26-42: Oct 6 second hearing outcome — adopted? |
| 2026-10-11 | `state:CA` | Escondido: staff returns Oct 10 with findings on the 45-day moratorium (escondido-ca-2026-08) — extended or lapsed? |
| 2026-10-13 | `state:ME` | moratorium `bangor-city-2026-04` (Bangor) reaches its computed end date 2026-10-13: lapsed, extended, or replaced by a permanent rule? |
| 2026-10-14 | `state:CO` | Moffat County: decision Oct 13 — outcome? |
| 2026-10-14 | `state:FL` | Leon County: 18-month moratorium final hearing Oct 13 — adopted? |
| 2026-10-15 | `site:google-van-buren-mi` | announced 2026-10-14: Final site plan vote for Google Van Buren Township data center could come Oct. 14 -- record what happened (set upcoming false or replace the event) |
| 2026-10-15 | `state:OH` | moratorium `cleveland-city-2026-04` (Cleveland) reaches its computed end date 2026-10-15: lapsed, extended, or replaced by a permanent rule? |
| 2026-10-15 | `state:OK` | OG&E large-load tariff: find the OCC cause number to add it as a proposed tariff |
| 2026-10-15 | `state:TN` | Crossville TN moratorium: find third-reading date and ordinance number to add it |
| 2026-10-15 | `state:TX` | TWDB reports to Gov. Abbott Oct 14 on penalizing data centers that skip water-use reporting (texas-state-2026-08) |
| 2026-10-16 | `state:CA` | Indio's extended moratorium (indio-ca-2026-06) expires Oct 16 2026 -- permanent ban adopted, extended again, or lapsed? |
| 2026-10-17 | `state:CA` | Indio: moratorium expired Oct 16 — permanent ban adopted, extended, or lapsed? |
| 2026-10-17 | `state:IL` | Bloomington: Planning Commission hearing Oct 16 toward a permanent data-center ordinance (bloomington-il-2026-05); second hearing Nov 16 |
| 2026-10-20 | `company:anthropic` | Fluidstack TX/NY campuses: has Anthropic or Fluidstack named a town yet? (anthropic.com/news, fluidstack.io/blog) |
| 2026-10-20 | `state:IN` | Fort Wayne: council reconsiders the 365-day pause on its own actions in mid-October (postponed 3 weeks on Sept 23) |
| 2026-10-20 | `state:TX` | TCEQ compliance report due Oct 19 on the data center permit pause (texas-state-2026-08) |
| 2026-10-21 | `state:FL` | Volusia County final hearing Oct 20 on data center ban (volusia-county-fl-ban-2026); Florida SB 484 large-load tariff filings (TECO Sept 30, FPL Oct 1) need PSC docket numbers |
| 2026-10-21 | `state:VA` | Loudoun County: Board resolution Oct 20 pausing its OWN legislative approvals (NOT a moratorium; see loudoun-county-va-2026-09) — adopted? Update the record's status/summary only. |
| 2026-10-29 | `state:CO` | Colorado PUC evidentiary hearing Oct 21–28 on Xcel's large-load tariff (xcel-colorado-large-load-tariff) |
| 2026-11-04 | `state:OH` | Nov 3 ballot: ~18 local data-center charter amendments/bans (Ohio Capital Journal Sept 14, Cloudflare-walled), incl. Trenton; and the Butler County 25 MW citizen measure tied to Amazon's $5B plan — record outcomes |
| 2026-11-06 | `state:NC` | Charlotte: the original 150-day pause expires Nov 5 — was staff's 9-month extension adopted? (charlotte-city-2026-06; the Sept 14 vote outcome was never found) |

**Reviewed or checked in the last 14 days (22)**

- 2026-10-08 `state:TX` (check): 2026-10-08 v5 refresh: Texas record gains the Sept 21 TCEQ permit pause
- 2026-10-08 `state:TN` (check): 2026-10-08 v5 refresh: Crossville TN two-year moratorium held, no enactment date on the page
- 2026-10-08 `state:OK` (check): 2026-10-08 v5 refresh: OG&E 75 MW+ large-load tariff proposal held, no OCC cause number
- 2026-10-08 `state:NC` (check): 2026-10-08 v5 refresh: added Raleigh proposed moratorium; Cary held (no enacted date on page); Duke Oct 7 tariff settlement
- 2026-10-08 `state:FL` (check): 2026-10-08 v5 refresh: added Volusia County ban ordinance (first reading)
- 2026-10-08 `state:CA` (check): 2026-10-08 v5 refresh: added Oakland (proposed) and Tulare extension moratoriums, four Sept 21 data center laws
- 2026-10-08 `state:AZ` (check): 2026-10-08 v5 refresh: added Pima County 120-day moratorium
- 2026-10-05 `site:meta-prineville-or` (check): Checked news and source link; added Apr 2026 contractor layoff note; datacenters.atmeta.com/location/prineville/ returns 404 (needs new URL, not swapped); permits not checked (partial: permits not checked, so not counted as a full review)
- 2026-10-02 `state:PA` (check): Oct 1 PUC meeting: Tentative Order on emergency load control approved; 30-day comments + 15-day replies; Nov 17 technical conference on large-load cost allocation; final order anticipated Jan 28 2027 (PUC press release).
- 2026-10-02 `site:google-van-buren-mi` (check): Wayne Co. Commission overrode Evans' veto 13-0 on Oct 1 (Fox 2); MPSC voted unanimously Oct 1 to conditionally approve DTE contracts (Planet Detroit; docket number not stated there). Added 2 responses + notes.
- 2026-10-02 `company:amazon` (review): Added Built Together (Oct 2, 2026): new $1B/5yr company_plan policy + 5 company-level claims (community_grants, education, energy x2, engagement) covering free community college, Modular Training Centers, energy-pricing/grid-cost commitment, Tier 4 backup generators, and ending government NDAs. Bumped companies.json summary + last_reviewed. No named community reaction yet (too fresh) — filed as a BACKLOG lead to re-check.
- 2026-09-30 `site:google-van-buren-mi` (review): Confirmed May 19, 2026 township tax exemption (50%/15yr + 36-mo construction, $15.4M community payment) via Belleville Area Independent; added to notes. Found but could not directly verify (paywalled/blocked): Wayne Co. Exec Evans' Sept 25 veto of that tax break + expected Oct 1 override vote, and MPSC docket U-22058's Sept 10 decision status (still pending, no order found) -- filed as backlog leads. captured_at bumped.
- 2026-09-30 `site:google-the-dalles-or` (review): Checked status/figures/news; added resp-google-dalles-mthood-water-2026 (OPB, Jan 2026): Google's Dalles water use now ~1/3 of city supply, city seeking federal legislation to expand Mount Hood reservoir without standard Forest Service review, WaterWatch/Bark objected; captured_at bumped.
- 2026-09-30 `site:google-mesa-az` (review): Checked status/figures (Phase III design-review submittal from Oct 2025/Mar 2026 predates capture; no post-2026-05 news); no community-response or news changes found; captured_at bumped.
- 2026-09-29 `site:google-council-bluffs-ia` (review): Checked status/figures, links, ratepayer eligibility (pre-pledge, none due), and news since 2026-05-14. Fixed a dead source_url (datacenters.google/locations/council-bluffs/ now 404s) to the live iowa page. Re-captured 3 claims with updated figures (investment $6.8B->$20B statewide, 2025 economic activity $2.1B->$2.7B, education orgs/Iowans updated); water grade-stabilization claim unchanged. Added a mixed CommunityResponse: the mayor's June 2026 moratorium request was unanimously declined by city council. Filed a lead for an untracked Cedar Rapids Google site.
- …and 7 more (see `data/refresh_ledger.json`).
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
- SPP High Impact Large Load (HILL): FERC approved it Jan 2026, per FERC's
  April release. The docket number is unverified. Add a federal rate case
  once it's pinned. **low**
- PJM capacity-market finding (Monitoring Analytics: data centers were 40%
  of the Dec 2025 auction). The fetchable source predates the pledge; find
  a post-March-4 edition, such as the State of the Market. **low**

#### state:AL — Alabama
- Fort Payne is a zoning action, not a moratorium.

#### state:AZ — Arizona
- ACC, Aug 13 2026: "ACC Approves Measure to Ensure Electric Cooperative
  Customers Don't Pay for Large-Load Growth" (azcc.gov news item). Fetch the
  item page, then decide between a rate case and a policy.
- Pinal County project denial: a site fight, not a moratorium.

#### state:CA — California
- El Monte (Moratorium Nation).
- SB 1168 / SB 886 / SB 887 are rate-design bills. They become
  `legislation` Policy records if passed, and the tariff comes later from
  the CPUC.
- Nvidia-leased San Jose site (300 Holger Way): permit appeal, operator
  unknown. Not addable until the operator is named.
- Imperial County project denial: a site fight, not a moratorium.

#### state:CO — Colorado
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
- Okaloosa County: Commissioner Paul Mixon's 12-month moratorium reportedly
  failed 3-2 on Sept 15, but only search headlines say so. WEAR's article
  (weartv.com) describes the board choosing to regulate through conditional
  use instead. Confirm the vote from county minutes or a fetched article
  before recording `failed`.
- `hernando-county-fl-2026-06`: unverified after five passes. Search snippets
  point to Ordinance No. 2026-23 (through June 16, 2027), but every article
  403s. Use the county's own agenda and minutes system.
- EEI: FPL 20250011, Duke Energy Florida 20260064.
- Not moratoriums: Palm Beach County ("could be next"); Minneola (advanced,
  final vote unknown); Alachua and Orange counties (votes only to draft).

#### state:GA — Georgia
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
- EEI: Georgia Power 44847.
- Microsoft "ATL50" (see company:microsoft) needs the Georgia DCA DRI record
  (apps.dca.ga.gov).

#### state:HI — Hawaii
- No state-level policy record: non-binding resolutions only.

#### state:IL — Illinois
- Prologis "Project Steel", Yorkville (see company:prologis).

#### state:IN — Indiana
- Indiana ratepayer conflict (Mirror Indy, 2026-06-25: bills up ~27%, with
  data centers cited as one driver). Needs a source that pins a cost shift
  to a specific Indiana site before it can be surfaced.
- Kokomo: zoning and regulatory actions, not a moratorium.

#### state:KS — Kansas
- Marysville KS: reportedly 12 months from Sept 14, one outlet so far.
  Distinct from Marysville WA.
- EEI: Evergy 25-EKME-315-TAR.

#### state:KY — Kentucky
- Rowan County: a two-year moratorium passed unanimously at the Fiscal
  Court's August 2026 meeting (Rowan Review on rcky.us; LEX18; WTVQ, Sept 1),
  but no source states the day. Get it from the court's minutes before adding
  the record; don't infer it from the third-Tuesday meeting schedule.
- EEI: KU/LG&E 2025-00113 / 2025-00114; Kentucky Power 2024-00305.

#### state:LA — Louisiana
- EEI: Entergy Louisiana U-36595.

#### state:MA — Massachusetts
- EO 658: see decision 7. Westfield (council "supports") and Northampton
  (study committee) are not moratoriums.

#### state:MD — Maryland
- PC72: Potomac Edison and the Exelon Maryland utilities filed large-load
  rate schedules Sept 1, 2026 (per EEI). No MD PSC case numbers located yet.

#### state:MI — Michigan
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
- Otter Tail Power docket 26-211: see decision 13. Its South Dakota twin is
  EL26-021 (75 MW threshold); don't reuse that number or threshold for MN.
- EEI: Minnesota Power 26-126. This docket is independently confirmed as
  Minnesota Power's, not Otter Tail's.
- Moratorium Nation: Inver Grove Heights.

#### state:MO — Missouri
- EEI: Evergy EO-2025-0154.
- Crusoe Warrenton (see company:crusoe).

#### state:NC — North Carolina
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
- EEI: El Paso Electric 25-00082-UT. See also site:oracle-dona-ana-nm.

#### state:NV — Nevada
- `nv-microsoft-ratepayer-protection-tariff`: the October and January hearing
  dates carried over from an earlier pass couldn't be re-confirmed (DCD
  blocked the fetch; mlq.ai is AI-generated). Confirm them from the PUCN
  docket (puc-onbase.nv.gov).

#### state:NY — New York
- Policy: A9086 is still in committee. EO 62 and S10642/A11560 are
  moratoriums, already tracked.

#### state:OH — Ohio
- Moratorium Nation candidates (30+): Findlay, Avon, Massillon, Maumee, Kent, Ravenna, Tallmadge, Tiffin,
  Vermilion, Norton, Cincinnati.
- EEI: FirstEnergy 26-0697-EL-ATA, Duke Ohio 26-0755-EL-ATA, AES Ohio
  25-0958-EL-AIR.

#### state:OK — Oklahoma
- EEI: PSO PUD2025-000075, OG&E PUD2026-000046.

#### state:OR — Oregon
- Portland and Eugene NDA bans: Policy candidates (principle "no secret
  deals"). The Eugene project denial is a site fight.

#### state:PA — Pennsylvania
- Springhill Township adopted permanent conditional-use zoning with setbacks
  on Sept 19, 2026. That is a Policy candidate (`local_ordinance`), not a
  moratorium. West Hempfield and Clinton Twp are zoning actions or denials.
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
- Gallatin: a six-month moratorium passed first reading, shortened to six
  months by a mayoral tie-break. The second-reading outcome is unconfirmed.

#### state:TX — Texas
- EEI: El Paso Electric 57568 / 56903 / 59611, SWEPCO 58796, TNMP 58964.
- Dallas (early stage), plus Lubbock and Jefferson County resolutions: not
  moratoriums.

#### state:VA — Virginia
- EEI: APCO PUR-2025-00057.
- Prince William, Christiansburg and Henry County: zoning actions.
- A statewide moratorium call (the Sturtevant and Lucas letters) is not a
  bill. Re-add only if a bill or an executive order appears.

#### state:WA — Washington
- Port Angeles only voted to draft. The Marysville record omits "Ordinance
  3381" because the number traces only to an AI aggregator. Add it if a city
  page confirms it.

#### state:WI — Wisconsin
- EEI: Xcel 4220-TE-119, MGE 3270-TE-124, WPL 6680-TE-119.

#### state:WV — West Virginia
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
- `crusoe-cheyenne-wy`: Google is now publicly confirmed as owner/operator
  ("Project Tembo," Cowboy State Daily, 2026-07-08 — quoted and dated in the
  2026-09-29 refresh). The record's company_slug is still `crusoe` for now;
  a future pass should decide whether to migrate it (and its tied claim +
  3 responses) to `company_slug: google`, or keep it under Crusoe as the
  original developer of record with a note. Needs a deliberate decision, not
  an automatic move.

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
- New Mexico regulators rejected a 17-mile gas pipeline that would have fed
  Project Jupiter (week of 2026-07-20). This is a regulator
  CommunityResponse candidate, pending a primary source.

#### site:qts-aurora-co
- The 65–80 ac / 4-building specifics in `notes` aren't on the cited
  article. Re-cite or soften them.

#### site:qts-dane-county-wi
- Jobs conflict: "450 permanent" (filing stage) vs "up to 5,000 trade jobs"
  ($12B announcement). `claimed_jobs` is left empty pending a call.

#### site:wonder-valley-box-elder-ut
- The auto-derived At-a-glance lines truncate an O'Leary marketing quote.
  Write a curator `at_a_glance` override.

---

## 4. Product and UX

From the 2026-09-25 cross-device audit (phone 390, tablet 820, laptop 1366,
desktop 1920). Performance is healthy everywhere: on Slow 4G with 4x CPU,
FCP is 0.86 s, LCP ≤ 1.4 s and TBT is ~0. The problems below are layout and
navigation.

- **Phone tab bar hides most of the site.** Only 2–4 of 7 tabs are visible
  and nothing signals that the bar scrolls. On Policy Playbook, Home and The
  Pledge are off-screen to the left. Options: a "More" menu, two rows, or
  fade edges with a chevron; shorter phone labels ("Rates", "Policy") help
  any of them. **high**
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
