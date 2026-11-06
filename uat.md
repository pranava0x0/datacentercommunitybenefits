# UAT Baseline — Data Center Community Benefits Dashboard

_Created: 2026-06-01_
_Last run: 2026-11-06_

## 2026-11-06 summary, geography and preview checks

Checked 360×812, 375×812 and 1366×900, light/dark themes, source links,
canonical legal dialogs, map state/status/topic/layer filters, empty search,
pointer pan/zoom, keyboard clusters, selection focus and Back/deep links. No
horizontal document overflow. Phone navigation is two 44px rows; all Moratoriums
sub-tabs fit. Numbered eyebrows, generic view introductions and explanatory
footer copy are removed. Sources remain attached to the records.

Original `docs/index.html` opens offline, including Elections and Map. A native
preview test blocks JSON and ESM requests and verifies classic-script adapters.
Hosted Home and Elections make no map-data or preview-adapter requests. Map has
no external tiles. Repeated refresh/bundle generation is byte-identical.

All 26 tasks across three devices and two disclosure contexts complete: 156
paths in `uat/interaction_costs.json`. Existing budgets are unchanged. New map
budgets equal measured counts, with one swipe allowance only on paths that
already need vertical swipes.

| Flow from Home | Phone interactions / seconds | Tablet | Desktop |
| --- | --- | --- | --- |
| Map overview | 2 / 2.2 | 2 / 2.2 | 2 / 2.2 |
| Savannah River announcement | 7 / 3.4 | 5 / 3.4 | 7 / 3.3 |
| Texas outline to SB6 record | 6 / 3.9 | 6 / 4.0 | 6 / 4.0 |
| Hernando outline to moratorium | 8 / 3.9 | 6 / 3.9 | 8 / 3.9 |

Times include fixed automation settling waits, not reading time. The Texas
flow initially cost 15 phone interactions; compact record links and direct
outline selection reduce it to six. Full summaries remain in legal dialogs.
DOE announcements sort newest first; coordinate detail remains available.

Three fresh contexts per view/device, without throttling, measured local
first-content medians of 56–58ms for Home/Elections and 81–82ms for Map. Baseline
Home/Elections was 56–58ms, so no material cold-local latency change is claimed.
Home’s Latest list moves up 194px on phone and 305px on desktop. Exact samples,
request names and positions are in `uat/map_summary_performance.json`; production
network latency is not estimated by these figures.

Two independent review rounds checked implementation and primary-source
accuracy. Fixed Augusta’s statistical CCD match, project-search associations,
keyboard focus, public research-process copy, type-scale drift and phone
sub-tab overflow. Public DOE references are not private project parcels; the
Springhill ambiguity and named asset-coordinate gaps stay explicit.

## 2026-11-05 winner and prior policy comparisons

Tested 360×812, 375×812 and 1366×900 with actual data, light/dark themes,
source popups, filters, search, empty matches, canonical legal dialogs, Escape,
direct links and all ten tabs. No document overflow or page errors. The offline
bundle opens without data fetches; no unrelated project/response/claim payloads
load on Home or Elections. Lead winner/prior statements no longer need a
disclosure click. Sources retain publication or access dates.

| Flow from Home | Phone interactions / seconds | Tablet | Desktop |
| --- | --- | --- | --- |
| Incoming Texas governor | 1 / 1.6 | 1 / 1.6 | 1 / 1.7 |
| Texas winner and actual prior policies | 3 / 1.9 | 1 / 1.9 | 1 / 1.9 |
| Sabattus vote to legal moratorium | 6 / 2.8 | 4 / 2.7 | 4 / 2.8 |

These automation times include navigation and fixed settling delays, not reading.
All 22 tasks on three devices in default/expanded contexts are recorded in
`uat/interaction_costs.json`; budgets are unchanged. The comparison previously
cost four phone interactions and two on tablet/desktop.

Cold local HTTP rendering used three fresh browser contexts per view/device,
without CPU/network throttling. Median first-content readiness was 57ms on
phone and desktop for Elections, and 56ms for Home. Baseline Elections was
58ms; this small difference is within run noise. The larger policy dataset
retains the same request count. Offscreen card layout is deferred. These local
figures do not estimate production network latency. Samples and request names
are in `uat/election_policy_performance.json`.

Both independent reviews are clear after fixes to citations, source dates,
party aliases, actual prior identity/party and California commencement wording.
Full-suite verification also removed two obsolete CSS selectors. Screenshot
and browser traces remain in `.preview/policy-comparisons/`.

## 2026-11-04 election refresh — PR #102

Tested all ten tabs with actual published data at 360×812, 375×812 and
1366×900, plus interaction measurements at 390×844 and 820×1180. No document
or legal-dialog overflow or page errors. Phone navigation stays within two
rows. Checked light/dark themes, party-change filtering, candidate statements,
search, canonical moratorium/policy dialogs, Escape, keyboard source focus,
direct record links, Back and failed-load Retry. Four Maine certifications
were read from signed returns; proposals and advisory questions stay distinct.

132 device/context paths completed without errors; the 18 election paths were
repeated after correcting inherited column filters and targeting both candidate
quotes. Existing 19 task budgets are unchanged. New mobile comparison/legal
budgets allow one additional swipe for layout sensitivity.

| Flow from Home | Mobile interactions / seconds | Tablet | Desktop |
| --- | --- | --- | --- |
| Reported election result | 1 / 1.75 | 1 / 1.63 | 1 / 1.62 |
| Both Texas candidates' statements | 6 / 2.52 | 2 / 2.43 | 2 / 2.44 |
| Sabattus vote to canonical moratorium | 6 / 2.80 | 4 / 2.72 | 4 / 2.73 |

Interactions include taps, vertical/horizontal swipes and typed queries.
Times include cold Home navigation, loading and automated settling waits;
they exclude human reading time and are observations, not latency budgets.
Every measured flow/context has its own elapsed time in
`uat/interaction_costs.json`. Local screenshots and actual-data checks are in
`.preview/election-research/uat/` (ignored, not shipped).

Visual review caught two errors the no-overflow checks missed: tall empty
filter rows inherited from the generic column filter bar, and “all sizes”
wording when an area threshold existed without a stored MW threshold. The
filter geometry now has a browser regression check; the legal detail uses
“See scope below.” Both independent review rounds have no unresolved P1/P2.

## Interaction cost (tracked from 2026-10-08)

How many taps, swipes and typed queries a reader needs, starting cold on
Home, to reach a specific piece of information. Measured by
`python3 tools/interaction_cost.py` on mobile (390×844, touch) first, then
tablet (820×1180) and desktop (1366×900). Each device has its own budget in
`uat/interaction_budgets.json`, enforced by `tests/e2e/test_interaction_cost.py`.
Full paths are in `uat/interaction_costs.json`; one dated summary line per run
goes to `uat/interaction_costs_history.jsonl`.

A swipe is 0.75 of the visible area. "Default" is the page as shipped, so a
collapsed section costs a tap to open. "Expanded" forces every section
accordion open first.

| Task | Mobile before | Mobile now | Tablet | Desktop | What changed |
|---|---|---|---|---|---|
| Latest change (Home) | 2 | 2 | 0 | 1 | |
| Next hearing or deadline (Home) | 4 | 3 | 3 | 1 | Phones show 5 Latest items, then "Show N more" |
| Last section card (Home) | 0 | 2 | 0 | 0 | Seven compact rows (was six tall cards); every card now in reach |
| Open the newest record | 3 | 3 | 1 | 2 | |
| Did Entergy sign the pledge? | 7 | 6 | 4 | 4 | Roster moved to the top of The Pledge (still collapsed) |
| A site's pledge scorecard | 5 | 5 | 3 | 3 | |
| What's happening in Virginia | 4 | 5 | 2 | 3 | +1: the roster now sits above the state grid |
| A signed benefit agreement (Frameworks) | 7 | 5 | 3 | 3 | Tab bar wraps; no side-swipes |
| A signed agreement's terms (new tab) | n/a | 4 | 1 | 1 | Benefit Agreements tab |
| Raleigh moratorium detail | 5 | 4 | 2 | 2 | Tab bar wraps |
| Next step in a rate case | 4 | 3 | 1 | 1 | Tab bar wraps |
| Google's water quotes | 7 | 5 | 3 | 3 | Tab bar wraps |
| A contested site's timeline | 4 | 3 | 2 | 2 | Tab bar wraps |
| What residents said about one site | 22 | 5 | 5 | 5 | Site search box; list above the map on phones |

Expanded vs default: the expanded context costs more wherever a long
reference list sits above the target. On a phone, opening every Pledge
section pushes the scorecard from 5 to 69 swipes and the state grid from 5 to
66, because the 300-row roster opens above them. That is the case for keeping
the roster collapsed. Elsewhere the two contexts match, because their targets
sit outside accordions.

Still worth improving (logged in BACKLOG.md):
- Moratoriums has no search; Raleigh is reachable only because it is recent.
  An older record would need many swipes on a phone.
- On a phone, the scorecard sits 4 swipes into The Pledge.

## 2026-09-23 PR #48 run

Local published `docs/` output tested at 1440×900, 390×844, and 375×812.
All seven tabs opened. The Policy Playbook loaded its 98-record directory;
the principle shortcut opened a filtered directory, a record opened its
source-backed detail panel, and Escape closed it. A state cell opened six
sections. Dark mode worked. No page errors or document-level horizontal
overflow occurred at any width. Mobile latest actions retained their state
labels. Screenshots: `.preview/uat-screenshots/2026-09-23-*` (local, ignored).
Screenshot review found repeated outcome words in two Latest actions; the
timeline wording was fixed, then the walkthrough passed again.

Current critical flow additions: open `#policies`, use an **All N** principle
shortcut after setting other filters, open a policy and its related site,
then open a state cell from `#ratepayer`. Check status and source in each
detail panel. Verify phone widths at 375–390px.

## 2026-09-22 PR #47 run

Tested local PR at 375×812, 768×1024, and 1280×900. All seven current views
(Home, The Pledge, Companies, Moratoriums, Tariffs, Sites, Aggregate) rendered.
Roster showed 346 rows; search for `entergy` narrowed to one. Moratoriums
showed 157 rows and proposed filter narrowed to 12. Tariffs showed 29 rows and
approved filter narrowed to 22. Aggregate showed 15 company rows and investment
sort changed to ascending. A site card opened its detail panel. Dark mode worked.
No page errors or document-level horizontal overflow at any tested width.
Screenshots: `/tmp/uat-2026-09-22-{mobile,tablet,desktop}.png` (temporary).

The older critical-flow counts below are historical. Use the current seed
counts when repeating those flows.

## Project Info
- **Stack:** Vanilla HTML/CSS/JS, static site — no build step
- **Dev server:** `python3 -m http.server 8013 --directory docs` (via `.claude/launch.json` name `docs`)
- **Entry point:** `docs/index.html`
- **Key views:** Home, The Pledge, Companies, Moratoriums, Tariffs & Rate Cases, Policy Playbook, Sites
- **Data:** `docs/data/` — validated JSON payloads emitted by `refresh.py`, including policies and coverage
- **Embed widget:** `docs/embed.html?company=<slug>`

## Critical Flows (run every time)

1. **Page load / stats bar:** Load `http://localhost:8013` — verify stats bar shows correct counts (companies, projects, claims, responses). Counts must match seed totals from `refresh.py` output.
2. **Ratepayer tab — signatory roster:** Click tab 3; scroll to "Who's signed" — confirm 7 green-checkmark signatories and 2 non-signatory own-commitment entries (Nebius, QTS).
3. **Ratepayer tab — affirmed badge:** Scroll to site scorecard; confirm at least one "Site-specific commitment" green pill renders with a verbatim evidence quote and source link.
4. **Ratepayer tab — pledge_only badge:** Confirm at least one "National pledge only" gray pill renders with a summary and no evidence quote block.
5. **Explorer — company filter:** Switch to Project Explorer; set company filter to "amazon"; confirm project count shows 13 and all new projects (ridgeland, wilmington, caddo, bossier, vicksburg) appear in the list.
6. **Explorer — project detail:** Click any project card; confirm the detail panel opens with Overview/Claims/On the ground tabs, investment and jobs KV rows, and source link.
7. **Explorer — new Google projects:** Filter to Google; confirm 20 projects including pine-island-mn, hermantown-mn, wilbarger-tx, armstrong-tx, haskell-tx.
8. **Comparison matrix:** Switch to Company Comparison; scroll to matrix; confirm all 14 company rows render and checkmarks appear for populated cells.
9. **Matrix tooltip:** Hover a non-empty matrix cell — confirm tooltip appears with theme label, quote snippet, and hint text; move mouse away and confirm tooltip hides.
10. **CBA badge:** Open microsoft-cheyenne-wy in Explorer → Claims tab; confirm at least one "Formal agreement" badge renders.
11. **Aggregate tab:** Click tab 4; confirm stat tiles (4), company table (≥8 rows), state table, and sort arrows work on Investment header click.
12. **Constituency breakdown:** Open Microsoft company pop-out; confirm constituency breakdown stacked-bar renders with at least 1 row after project data loads.
13. **Embed widget:** Navigate to `/embed.html?company=meta`; confirm company name, theme grid, claim count render. Test `/embed.html?company=fakecompany` shows "Unknown" error. Test `/embed.html` (no param) shows "No company" hint.
14. **Dark mode:** Toggle dark mode; confirm header, cards, badges, and quote blocks all remain readable.
15. **Console clean:** After full walkthrough, check `preview_console_logs` — expect zero errors or warnings.

## Sections & Last Tested

| Section | Last Tested | Notes |
|---|---|---|
| Stats bar | 2026-06-07 | Stable — counts match seed |
| Tab navigation | 2026-06-07 | 4 tabs; mobile wrapping cosmetic |
| Company Comparison matrix | 2026-06-07 | Works; checkmarks only (v1.2) |
| Matrix tooltip | 2026-06-07 | v1.17 — renders on hover, hides on leave; getBoundingClientRect fix applied |
| Company pop-out | 2026-06-07 | v1.17 — constituency breakdown renders after project data loads |
| Project Explorer — hot rail | 2026-06-07 | Stable |
| Project Explorer — filter panel | 2026-06-07 | Stable |
| Project Explorer — map | 2026-06-07 | Stable |
| Project Explorer — project list | 2026-06-07 | Stable |
| Project detail — Overview tab | 2026-06-07 | Stable; KV grid renders correctly |
| Project detail — Claims tab | 2026-06-07 | v1.17 — CBA badge renders on formal_agreement=true claims |
| Project detail — On the ground tab | 2026-06-07 | Stable |
| Ratepayer tab — stat tiles | 2026-06-07 | Stable; 3 tiles |
| Ratepayer tab — pledge elements accordion | 2026-06-07 | Renders; collapsed by default |
| Ratepayer tab — signatory roster | 2026-06-07 | Stable; all 7 signatories + own-commitment entries |
| Ratepayer tab — site scorecard | 2026-06-07 | Stable; affirmed + pledge_only badges render |
| Aggregate tab | 2026-06-07 | v1.17 — 4 stat tiles, company + state tables, sort indicators |
| Embed widget | 2026-06-07 | v1.17 — loads company theme grid; CSP meta tag added; error states work |
| Dark mode | 2026-06-07 | Stable |
| Policy Playbook | 2026-09-23 | Stats, principles, directory, detail, and source links passed at three widths |
| State panel | 2026-09-23 | Six sections loaded from a state cell at three widths |
| Tab navigation and dark mode | 2026-09-23 | Seven tabs and theme toggle passed at three widths |

## Known Stable Areas
- Console: zero errors across full session
- Ratepayer affirmed/pledge_only badge rendering (light + dark)
- Evidence quote blockquote rendering in ratepayer scorecard
- Project detail KV grid (investment, jobs, offtaker, source link)
- Explorer company filter count accuracy
- Aggregate rollup build (cached: built once per renderAggregateView call)

## Known Flaky / Unstable Areas
- **Ratepayer tab label** (UAT-003): wraps to 3 lines at 375px — cosmetic, stable to reproduce
- **"On the ground" detail tab** (UAT-004): wraps to 2 lines — cosmetic, stable to reproduce
- **Matrix scroll discoverability** (UAT-005): no visual indicator — easy to miss columns

## Exploration Notes
- The company select filter requires `dispatchEvent(new Event('change', {bubbles:true}))` when set programmatically — native `fill` fails on `<select>` elements here.
- Project cards must be clicked via `.querySelector('#project-list li')` + `.click()` — the `preview_click` CSS selector approach fails for dynamically rendered list items.
- The `.dtab` class is the selector for project detail panel tabs.
- Matrix `overflow-x: auto` is on `.matrix-wrap`; the `<table>` itself has `overflow: visible`.
- All 8 new v1.20 projects confirmed present and opening correctly in detail view.
- No ratepayer block shown for pre-pledge projects (Wilmington OH — announced 2025 ✓).
- Matrix tooltip uses `getBoundingClientRect()` post-show for correct clamping (v1.17 fix).
- Aggregate sort click calls `renderAggregateView()` to ensure `_aggSort` state picked up correctly; rollup data is rebuilt (O(n), n≤100) on each sort.
- Constituency breakdown lazy-loads via `loadProjectData()` if project data isn't already present; never visible with 0 rows.

## 2026-10-14 — plans, evidence and agreement terms

Fresh baseline at `b2872a7`, same device settings and tasks as the candidate.
`uat/interaction_comparison.json` preserves before/after paths and counts;
new tasks have no prior equivalent. All 14 existing default paths stayed
unchanged or improved. Measure first-line reachability, not reading the
entire plan or agreement; scrolling through full documents costs more.

| Task | Mobile before → after | Tablet before → after | Desktop before → after |
|---|---|---|---|
| Signed agreement terms | 4 → 1 | 1 → 1 | 1 → 1 |
| County draft decision | absent → 1 | absent → 1 | absent → 1 |
| State draft decision | absent → 3 | absent → 3 | absent → 3 |
| Querétaro water evidence | absent → 4 | absent → 2 | absent → 2 |

One selection costs two taps: open picker, choose option. The county path is
one tap with zero swipes; the state path adds that selection. Phone water
evidence takes two taps and two swipes. Full/expanded paths are also recorded.
Benefits now puts sourced terms before background and feature chips; provision
counts remain in Terms. Delivery panels remain visible on full cards.
Frameworks uses two sub-tab rows on phones so its five panes remain visible
without horizontal swipes. Home links open drafts or evidence directly.

Checked 375px, 390px and 1366px layouts, downloads for both plans, URL reload,
keyboard arrows, lazy loading and failed-import retry. Screenshots inspected
locally. Offline preview embeds the same guide source and passes its smoke test.
Draft numbers are illustrative; registry authenticity, the municipal percentage,
current generator authorization, actual emissions and tenancy remain unverified.

PR #71 review fix: the water task now reaches an explicit verdict, evidence
status and limitation, rather than stopping at the story claim. Re-measured
on all three devices: totals remain 4/2/2; the stored paths reflect the corrected
question. Maryland stays out of the CBA-required filter; its community-benefits
principle and official source remain. One review round; both inline findings fixed.

## 2026-10-18 refresh pass

New task `moratorium_older` (find Hernando County, FL): 4 on every device via
the new Moratoriums search box. Before it, an older record meant scrolling a
185-row table whose phone rows were ~115px tall (Key Reasons badges wrapped
into a column); that column is now hidden under 600px and reasons stay in the
detail panel. Budgets tightened to the measured totals (+1 only where vertical
swipes make a count layout-sensitive); 45 budgets went down, none up. #72
fixes measured in the same run: Back after a tab click, shareable policy
records, search typed during Sites loading survives render.

## 2026-10-19 session

Budgets: `tablet.latest_item_record` 1 → 3. The task opens the newest
*moratorium* in Home's date-sorted Latest feed. The site timeline refresh added
five newer site votes above it, so it now sits two swipes down on a tablet,
the same as on a phone. That is a data change, not a layout one.
`tablet.home_coming_up` 4 → 3 (measured 2). Phone paging (#79) cut page
heights at 390px: Pledge 11.4k → 4.5k px, Moratoriums 15.6k → 4.2k px. Every
other task is unchanged.

Final verification: 931 tests passed (171 seconds), followed by 96 focused
seed/roster/timing checks after the final copy edit. Two consecutive refresh
builds produced byte-identical output. Source audit: all 2,530 current rows
classified, zero dead links; 233 blocked URLs and 73 excerpt mismatches remain
explicit worklists. No unresolved P1/P2 review findings.

### Published verification and signing-date follow-up

PR #102's Pages build succeeded at commit `7fc84ad`. Published-site checks at
375×812 and 1366×900 loaded all 56 election records, selected the six documented
party changes, and opened Sabattus's canonical legal record with no page errors
or overflow. Screenshots: `.preview/election-research/uat/published-*.png`.

A subsequent GitHub review found that SB Energy's unpublished signing date was
being replaced by March 4 in frontend cohort wording. The follow-up keeps it
under Not assessed with “Signing date unpublished — pledge timing unknown”;
the CSV keeps the date blank and makes no pledge-era claim. Both new browser
regressions passed, and actual cards were inspected at 375/1366px. Independent
follow-up review found no further issue.

Follow-up release gate: 933 tests passed in 160 seconds, including all
interaction budgets. No source data or assessment statuses changed.

## 2026-11-05 local preview and load speed

Reproduced the screenshot by opening `docs/index.html` as a file: JSON fetches
were blocked and the Elections module import failed. The rebuilt standalone
`.preview/dashboard.html` works without networking at 375×812 and 1366×812:
Home, Elections and the Sabattus legal-record link load with zero external
requests or page errors. The raw-file error now links to the published view.

Removed boot-time prefetch of projects, responses and claims; each owning view
still requests its data. In the same local HTTP test (uncompressed server,
150 ms latency, 200 KB/s down, 4× CPU), Elections usable content improved from
5.94 s to 4.44 s and resource transfer dropped from 1,390,945 to 705,502 bytes
(excluding the HTML document). Home was unchanged at about 3.84 s. These are
single controlled observations, not a production latency promise. The offline
preview populated the first record in 52–54 ms; waiting for the view fade
to finish took 250 ms total on this machine. Before/after JSON and screenshots
are in `.preview/load-speed/` (ignored).

The new browser checks force idle callbacks to run, proving unrelated payloads
are absent after startup and Companies still loads claims when opened. An
independent bounded review found no actionable bug.

Release checks: all ten tabs rendered offline at 375/1366px with no document
overflow. 937 tests passed in 161 seconds, including all interaction budgets.
The preview build verification passed with 56 election records and its legal link.

November 5 final suite: 942 tests passed. The 132 interaction paths, offline
preview and two byte-identical refresh runs passed; no budgets were increased.

## 2026-11-06 policy coverage and compact layouts

Frameworks now has 141 records, including four additions checked against the
New York governor's order, Texas governor's directive, Fayetteville city FAQ
and Loudoun county release. Related moratorium records link to the same
instrument; Loudoun's existing special-exception requirement remains distinct
from its proposed pause. Eleven further coverage leads remain unverified in
BACKLOG.md. The Fayetteville FAQ's printed ordinance number needs confirmation
against the instrument before becoming a formal identifier.

Elections leads with nine winners' sourced pause proposals. All 54 records
remain; statements and additional policies open inline. On a 375×812 phone,
the first policy row begins at 381px instead of 655px, and its closed height
fell from 868px to 320px. At 1366×900 it begins at 318px instead of 414px,
with height 107px instead of 291px. The directory no longer begins with
result-count cards. Shared summary strips stay visible across subtabs;
headings render at full opacity immediately after navigation.

Two independent review rounds covered source accuracy, winner/prior-holder
attribution, copy, layout and touch targets. The second checked all ten tabs
and 92 subtab/device/theme combinations at 375px touch and 1366px desktop in
light and dark themes. No page errors or document overflow remained. Phone
Trends toggles wrap, and active map search results precede the map.

Release gate: 965 tests passed in 310 seconds. All 156 interaction paths
(26 tasks × three devices × two disclosure contexts) passed without raising
budgets. Elections policy takes one navigation action on each device; measured
script time was 2.17–2.26s. DOE announcement lookup takes 6 actions on phone
and 5 on tablet/desktop; moratorium lookup takes 7 and 6 respectively. These
script times include the harness's deliberate waits and typing. Detailed
per-flow times are in uat/interaction_costs.json.

Three fresh local-browser samples per view/device measured Home and Elections
ready at roughly 63ms and the map at 80–81ms. The previous version measured
55–58ms for Home/Elections; this change does not establish a load-speed gain.
These unthrottled loopback observations are not production latency estimates.
Home and Elections still avoid map, DOE and preview-adapter requests.
Before/after measurements: uat/policy_layout_performance.json.

## 2026-11-06 framework fields and individual map sites

Refreshed ten existing records (five frameworks and five moratoriums) and added
Raleigh's existing zoning rules, separate from its application pause. Frameworks
has 142 records; Moratoriums has 250. Missing dates stay unknown rather than
using announcement/capture dates as approval dates. Remaining date and reason
work is recorded in BACKLOG.md. The source audit and scope are in
notes/specs/FRAMEWORK_MAP_REFRESH_2026_11_06.md.

The map renders 33 individual DOE stars without numbered clusters. Hover/focus
previews, canonical record/source links, closeable selection details and a
literal color/status legend were checked on phone and desktop. Off-canvas
regions leave the keyboard sequence; Escape-dismissed previews stay dismissed
until the trigger is left. Two independent review rounds found these two
accessibility issues, then verified their fixes with no remaining findings.

Search and State stay visible; the remaining map filters and layers share one
disclosure. Directory filters have visible labels; the benefits checkbox stays
primary. Phone counts and filters use compact rows; tablet navigation uses five
equal columns. All ten tabs passed 138 subtab/device/theme checks at 375, 820
and 1366px in light and dark themes, without page errors or document overflow.

The first full run exposed excessive scrolling in map selection and the phone
agreement filter. The next exposed one added desktop Evidence scroll from the
new scope caption. Compact record lists, responsive filter rows and tighter
paragraph spacing fixed the measured regressions. Existing budgets were kept.

Release gate: 970 tests passed in 190 seconds. All 156 interaction paths
(26 tasks × three devices × two disclosure contexts) passed within unchanged
budgets. The map opens in two actions, DOE announcement lookup takes five,
and linked framework/moratorium lookup takes six on all three devices.
Filtering agreements takes three actions. Script times are about 2.2s, 3.2s,
3.8–4.0s and 2.7–2.8s respectively, including deliberate harness waits.
Full per-flow times are in uat/interaction_costs.json.

On a 375px phone the map begins at 612px rather than 797px. The first framework
row remains at 724px versus 722px, while its filters now have visible labels.
At 1366px that row moves from 448px to 428px. Fresh unthrottled loopback samples
are in uat/framework_map_performance.json; they are not production latency
estimates. Frameworks does not request map/DOE data or preview adapters.

The offline preview passed, and two refresh/preview builds were byte-identical.
Source HTTP blocks remain distinguished from unavailable or contradictory
evidence. The incomplete cached moratorium audit ran with --no-issues; it is
not counted as an accuracy pass. New facts were checked against primary text.
