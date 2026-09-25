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
3. **A home for per-site permits and news.** Today a permit decision is a
   `local_government` / `regulator` CommunityResponse, and a company filing
   is a dated sentence in `Project.notes`. A typed `Project.updates` list
   (date, kind: permit | approval | filing | hearing | construction | news,
   authority, docket or permit number, source) rendered as a fourth
   "Timeline" detail tab would hold what the routine finds without forcing a
   stance onto a filing. **medium**
4. **Moratorium lifecycle.** No `expired` / `lapsed` status exists, so a
   lapsed six-month pause still counts as `enacted` in the stat tiles. The
   queue now derives end dates from `duration_months`, and 4 have passed
   (Indio CA, St. Charles MO, Larimer County CO, Athens-Clarke GA). **medium**
5. **Cancelled projects.** `Project.status` has no `cancelled`. QTS Prince
   William Digital Gateway (appeal withdrawn 2026-07-02) is the precedent
   case, and Microsoft Caledonia WI (pulled Oct 2025) is another. **low**
6. **Tribal jurisdictions.** `jurisdiction_type` has no tribal value.
   Cherokee Nation (2026-08-10), Seminole Nation (March 2026) and Kickapoo
   Tribe (July 2026) have data-center bans ready to curate. KGOU, KOSU,
   Tom's Hardware and Tribal Business News covered Cherokee. **medium**
7. **Executive-order "conditions" regimes.** Massachusetts EO 658 (Healey,
   Sept 8: no state permits for >25 MW without framework compliance and a
   host-community benefits agreement; NDA ban; Ratepayer Protection Fund) is
   not a pause. Should it be filed as a Policy `executive_order` like VA EO
   22? **medium**
8. **Nebius.** It has a 1.2 GW Pennsylvania campus, which clears gate 1.
   Does it publish its own community-impact framing (gate 2)? Onboarding a
   company touches four registries. **low**
9. **Infrastructure partnerships.** Google-SpaceX GPU lease and the
   Anthropic-xAI compute rental are `Project` records with no site. Options:
   exclude them, give them their own section, or fold them into the company
   pop-out. **low**
10. **Taxes filed as tariffs.** `virginia-data-center-electricity-consumption-tax`
    is a state excise tax scored against a rate-design taxonomy and counted
    in tariff tiles. It needs an `instrument_type` field or an
    `excluded_from_stats` flag. **low**
11. **Per-signatory pages.** Three open questions in
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
_Generated by `python3 scripts/refresh_queue.py --write-backlog` on 2026-09-25. Do not edit between the markers: review dates and follow-ups live in `data/refresh_ledger.json`, and units come from the data itself._

**Coverage:** 0 of 132 sites reviewed within 90 days; 0 of 15 companies reviewed within 30 days; 0 of 52 states reviewed within 120 days.

**Due now (3)**

| Due | Unit | Check |
|---|---|---|
| 2026-08-03 | `state:CA` | moratorium `indio-ca-2026-06` (Indio) reaches its computed end date 2026-08-03: lapsed, extended, or replaced by a permanent rule? |
| 2026-08-22 | `state:MO` | moratorium `st-charles-city-2025-08` (St. Charles) reaches its computed end date 2026-08-22: lapsed, extended, or replaced by a permanent rule? |
| 2026-08-27 | `state:CO` | moratorium `larimer-county-co-2026-01` (Larimer County) reaches its computed end date 2026-08-27: lapsed, extended, or replaced by a permanent rule? |

**Next run works through**

1. `state:CA` (California): follow-up due 2026-08-03: moratorium `indio-ca-2026-06` (Indio) reaches its computed end date 2026-08-03: lapsed, extended, or replaced by a permanent rule?
2. `state:MO` (Missouri): follow-up due 2026-08-22: moratorium `st-charles-city-2025-08` (St. Charles) reaches its computed end date 2026-08-22: lapsed, extended, or replaced by a permanent rule?
3. `state:CO` (Colorado): follow-up due 2026-08-27: moratorium `larimer-county-co-2026-01` (Larimer County) reaches its computed end date 2026-08-27: lapsed, extended, or replaced by a permanent rule?
4. `site:aws-cumberland-pa` (Cumberland Valley Data Center Campus (Salem Township, PA; construction)): never reviewed; record curated 2026-05-14 (1.5x target)

**Then, sites**

| Unit | What | Why now |
|---|---|---|
| `site:aws-loudoun-va` | AWS US-East-1 (Northern Virginia) (Ashburn, VA; operational) | never reviewed; record curated 2026-05-14 (1.5x target) |
| `site:aws-new-carlisle-in` | Project Rainier (New Carlisle) (New Carlisle, IN; operational) | never reviewed; record curated 2026-05-14 (1.5x target) |
| `site:google-council-bluffs-ia` | Council Bluffs Data Center (Council Bluffs, IA; operational) | never reviewed; record curated 2026-05-14 (1.5x target) |
| `site:google-mesa-az` | Mesa Data Center (Mesa, AZ; operational) | never reviewed; record curated 2026-05-14 (1.5x target) |
| `site:google-the-dalles-or` | The Dalles Data Center (The Dalles, OR; operational) | never reviewed; record curated 2026-05-14 (1.5x target) |
| `site:google-van-buren-mi` | Google Van Buren Township Data Center (Van Buren Township, MI; announced) | never reviewed; record curated 2026-05-14 (1.5x target) |

**Then, states**

| Unit | What | Why now |
|---|---|---|
| `state:GA` | Georgia | never reviewed; 29 records |
| `state:TX` | Texas | never reviewed; 28 records |
| `state:OH` | Ohio | never reviewed; 23 records |
| `state:IN` | Indiana | never reviewed; 19 records |

**Then, companies**

| Unit | What | Why now |
|---|---|---|
| `company:coreweave` | CoreWeave (4 tracked sites) | never reviewed; record curated 2026-05-15 (4.4x target) |
| `company:crusoe` | Crusoe (6 tracked sites) | never reviewed; record curated 2026-05-15 (4.4x target) |
| `company:amazon` | Amazon (AWS) (23 tracked sites) | never reviewed; record curated 2026-05-16 (4.4x target) |
| `company:anthropic` | Anthropic (2 tracked sites) | never reviewed; record curated 2026-05-16 (4.4x target) |

**Coming up in the next 30 days (13)**

| Due | Unit | Check |
|---|---|---|
| 2026-09-29 | `state:NC` | Forsyth County: six-month moratorium was on the Sept 28 agenda — adopted? |
| 2026-10-01 | `state:NC` | rate case `nc-ncuc-duke-settlement-2026`: 2026-09-30 milestone passed; record the outcome and the next announced step |
| 2026-10-02 | `state:PA` | rate case `pa-puc-large-load-cost-allocation-2026`: 2026-10-01 milestone passed; record the outcome and the next announced step |
| 2026-10-06 | `state:NC` | Beaufort County: hearing + vote Oct 5 — outcome? |
| 2026-10-07 | `state:CA` | Mendocino County: extension hearing Oct 6 (urgency ordinance expires Oct 16) — extended or lapsed? |
| 2026-10-07 | `state:FL` | Manatee County Ordinance 26-42: second hearing Oct 6 — adopted? (WMNF's 'approved Sept 3' conflicted with the hearing schedule) |
| 2026-10-07 | `state:NC` | Raleigh: six-month draft moratorium hearing Oct 6 — adopted? |
| 2026-10-13 | `state:ME` | moratorium `bangor-city-2026-04` (Bangor) reaches its computed end date 2026-10-13: lapsed, extended, or replaced by a permanent rule? |
| 2026-10-14 | `state:CO` | Moffat County: decision Oct 13 — outcome? |
| 2026-10-14 | `state:FL` | Leon County: 18-month moratorium final hearing Oct 13 — adopted? |
| 2026-10-15 | `state:OH` | moratorium `cleveland-city-2026-04` (Cleveland) reaches its computed end date 2026-10-15: lapsed, extended, or replaced by a permanent rule? |
| 2026-10-20 | `company:anthropic` | Fluidstack TX/NY campuses: has Anthropic or Fluidstack named a town yet? (anthropic.com/news, fluidstack.io/blog) |
| 2026-10-21 | `state:VA` | Loudoun County: Board resolution Oct 20 pausing its OWN legislative approvals (NOT a moratorium; see loudoun-county-va-2026-09) — adopted? Update the record's status/summary only. |

**Reviewed in the last 14 days (0)**

None yet.
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
- Reportedly enacted and not yet verified: Harpersville (6 mo), Westover (6 mo),
  Anniston (12 mo). Fort Payne is a zoning action, not a moratorium.

#### state:AR — Arkansas
- Madison County, 3-year moratorium to Aug 31, 2029. Reportedly enacted;
  verify.

#### state:AZ — Arizona
- ACC, Aug 13 2026: "ACC Approves Measure to Ensure Electric Cooperative
  Customers Don't Pay for Large-Load Growth" (azcc.gov news item). Fetch the
  item page, then decide between a rate case and a policy.
- Pinal County project denial: a site fight, not a moratorium.

#### state:CA — California
- Escondido (45 days), reportedly enacted. El Monte (Moratorium Nation).
- SB 1168 / SB 886 / SB 887 are rate-design bills. They become
  `legislation` Policy records if passed, and the tariff comes later from
  the CPUC.
- Nvidia-leased San Jose site (300 Holger Way): permit appeal, operator
  unknown. Not addable until the operator is named.
- Imperial County project denial: a site fight, not a moratorium.

#### state:CO — Colorado
- Archuleta County, reportedly enacted. Global AI, Weld County (up to 1 GW,
  approved Sept 9) is a two-gate candidate; see §7.
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
- Failed votes to record, each with its vote count: Indiantown (4-1 against),
  Okaloosa County (3-2 against).
- EEI: FPL 20250011, Duke Energy Florida 20260064.
- Not moratoriums: Palm Beach County ("could be next"); Minneola (advanced,
  final vote unknown); Alachua and Orange counties (votes only to draft).

#### state:GA — Georgia
- **The Georgia wave (high).** 14 tracked. GPB and The Current say "about
  40" municipalities. Still open: Hall County (debating 180 days, no vote
  found), Forest Park (90 days, reportedly enacted), Lee County (WALB 5/27,
  "consider extending"), Floyd County (probably an ordinance; others cite it
  as the model), Lowndes, Effingham, Meriwether (Feb 24, extended to Nov 21,
  2026; only an AI aggregator and a 403'd paper so far, so not citable
  yet), Bulloch (existing moratorium through Dec 31, 2026 per The Georgia
  Virtue; its 4-3 rejection of an outright ban is a separate event).
  Muscogee/Columbus is an enabling overlay district, **not** a moratorium.
  The northwestgeorgianews.com roster of about 53 jurisdictions (June 2025)
  is a stale work-list.
- EEI: Georgia Power 44847.
- Microsoft "ATL50" (see company:microsoft) needs the Georgia DCA DRI record
  (apps.dca.ga.gov).

#### state:HI — Hawaii
- No state-level policy record: non-binding resolutions only.

#### state:IA — Iowa
- Salix: failed vote, 3-2 against (~Aug 22). Record it with the vote.

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
- Reportedly enacted: Rowan County (2 yr), Winchester (1 yr).
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
- Reportedly enacted: Zeeland Twp (1 yr), Garfield Twp (1 yr). Moratorium
  Nation candidates: Pontiac, Saginaw, Saline, Northville, Taylor. Wixom:
  zoning action.
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
  (ncdoj.gov, Sept 14; E-2 Sub 1406 alongside E-7 Sub 1329). Possibly its
  own RateCase.
- Moratorium Nation: Hillsborough, Durham, Apex, Boone, Canton, Wendell,
  Kings Mountain. Alamance County had a hearing Aug 17; check the outcome.

#### state:NE — Nebraska
- Gage County, 12 months, reportedly enacted.

#### state:NH — New Hampshire
- The governor has stated intentions only.

#### state:NJ — New Jersey
- NJ S731 / A796: a large-load tariff mandate for 100 MW+, passed and
  awaiting signature as of July. Watch for the utility filing that
  implements it. The NJ transparency law is a Policy candidate.

#### state:NM — New Mexico
- EEI: El Paso Electric 25-00082-UT. See also site:oracle-dona-ana-nm.

#### state:NY — New York
- Orangetown (6 mo), reportedly enacted.
- Policy: A9086 is still in committee. EO 62 and S10642/A11560 are
  moratoriums, already tracked.

#### state:OH — Ohio
- Newton Falls (12 mo), reportedly enacted. Moratorium Nation candidates
  (30+): Findlay, Avon, Massillon, Maumee, Kent, Ravenna, Tallmadge, Tiffin,
  Vermilion, Norton, Cincinnati.
- EEI: FirstEnergy 26-0697-EL-ATA, Duke Ohio 26-0755-EL-ATA, AES Ohio
  25-0958-EL-AIR.

#### state:OK — Oklahoma
- EEI: PSO PUD2025-000075, OG&E PUD2026-000046.

#### state:OR — Oregon
- Portland and Eugene NDA bans: Policy candidates (principle "no secret
  deals"). The Eugene project denial is a site fight.

#### state:PA — Pennsylvania
- Springhill Twp, reportedly enacted. West Hempfield and Clinton Twp are
  zoning actions or denials.
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
- Marysville WA, Ordinance 3381, July 13, 6 months. Port Angeles only voted
  to draft.

#### state:WI — Wisconsin
- Bellevue (12 mo), reportedly enacted.
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
  Mar–May 2026): a real site that isn't tracked.
- CoreWeave / Prime Data Centers, Elk Grove Village IL: the $850M bond is
  confirmed. The "$2.2B contracted revenue" and "15-year lease" figures
  trace only to low-tier aggregators.

#### company:crusoe
- Crusoe Warrenton MO, and a second Abilene TX campus (Microsoft-anchored,
  ~900 MW): real, first named Q2 2026, not tracked.
- Cheyenne WY "Project Jade" was reportedly paused (Bloomberg, 2026-06-09,
  paywalled). Find a readable pickup before changing
  `crusoe-cheyenne-wy`.

#### company:google
- Google Fort Wayne IN ("Project Zodiac", ~$2B, ~200 jobs, I&M territory):
  operational Dec 11 2025 per Inside Indiana Business. Never tracked.
- Google as a "possible customer" of MidAmerican's Salix IA site: no deal,
  and annexation litigation is ongoing. Too early.

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
- **Very long pages on phone.** Moratoriums runs 25 screens, Tariffs 17.5,
  The Pledge 13.4. Collapse directories by default under 600 px, or
  paginate. **medium**
- **Tiny targets on The Pledge.** 214 targets under 24 px on phone (state
  strip cells, row source links, the concern checkbox at 13 px). Tariff
  filters and moratorium level toggles are also under 24 px tall. **medium**
- **"323 organizations" on Home vs "346 signatories" on The Pledge.** The 23
  governors are the difference, and the Coverage header should say so.
  **low**
- **Two detail-view patterns.** Companies and Sites open inline panels;
  Moratoriums and Tariffs open modals. Decide deliberately, since Sites may
  want to keep the map visible. **medium**
- **Sub-tab state isn't in the URL** (`#ratepayer/pre-pledge` shape). Read
  the sub-key before `activateView`. **medium**
- **Map clustering on Sites.** Northern Virginia pins overlap. **medium**
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
