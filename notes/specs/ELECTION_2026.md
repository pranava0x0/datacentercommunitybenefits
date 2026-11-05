# November 2026 election and data refresh

Requested November 4, 2026. The owner approved the Elections main tab, validated
data model and full research/review scope on November 4. Implemented in PR #102.

## Options

1. **Elections main tab (recommended).** A state directory with governor races,
   relevant local races, and ballot measures. Keeps policy comparisons reachable
   from Home and links to the existing legal records. Costs one navigation item;
   the phone tab bar must remain within its measured height budget.
2. **Elections under Moratoriums.** Fits the existing sub-tab pattern and adds no
   main navigation item. Broader electricity, tax and permitting policies become
   harder to discover.
3. **Separate election page.** More room for a national directory, but introduces
   another entry point and navigation to maintain.

## Proposed data contract

New `data/seed/elections.json`, validated in `schema.py` and emitted by
`refresh.py`; fetched only when the Elections view opens. No new framework.

Each contest has a stable ID, election date, state, jurisdiction, office or
ballot-measure title, capture date, and independently sourced result. Result
status distinguishes unresolved, reported/unofficial, and certified. A reported
winner is never described as certified or already serving. Store the result
source and its dated evidence separately from candidate policy sources.

Office contests record the outgoing officeholder and party, candidates and
parties, and the reported winner when verified. Each candidate’s policy statement
names the speaker, quotes a short passage verbatim, and supplies its source,
source date when known, and capture date. Use campaign pages, official statements,
and attributed debate/interview transcripts. A missing verified statement reads
“No data-center statement verified in this pass.” Do not infer a candidate’s
position from party, endorsements, the opponent’s claims, or forum discussion.

Ballot measures distinguish binding measures from advisory questions. Record
official wording and what a yes/no vote does. A successful advisory vote is not
an enacted moratorium. Passed zoning conditions are not a ban. Cross-reference
the existing moratorium or policy record only when the legal action is verified.

Party/person changes are factual comparisons of sourced names and parties. The
view makes no forecasts or assessments of a candidate’s likely conduct.
Candidate proposals remain proposals until a separate legal instrument acts.

## Research order

- Start with local seed IDs, the refresh queue and recent remote commits.
- Governor priority follows tracked site presence plus relevant moratorium and
  pledge records: Texas, Ohio, Georgia, Iowa, Pennsylvania, Wisconsin, Oregon,
  Arizona, New Mexico, Michigan, then the remaining states with governor races.
  Virginia is relevant context but has no regularly scheduled 2026 governor race;
  verify the election calendar before describing a change there.
- County/municipal races and ballot measures: begin with the Ohio charter votes,
  relevant Maryland county executive races, and places with recent pauses.
- Candidate websites and official election results first. Political forums and
  trade coverage are leads; verify the underlying named statement and legal act.
- Existing tabs retain the canonical moratorium, tariff, policy, company, site
  and pledge records. Refresh them from their own sources; election coverage
  links to them rather than copying or reclassifying records.
- Maintain a source evidence log and a jurisdiction coverage ledger. Explicitly
  report unreachable pages, unresolved results and areas not reviewed.

## Verification and shipping

- Validate, test and commit each curated record with regenerated outputs.
- Test election invariants: no winner without result evidence; certified needs
  certification evidence; winner belongs to the candidate list; unresolved races
  do not imply a winner; binding/advisory stays distinct; unique IDs; valid refs.
- Exercise source links, search, state/result filters, empty/error/retry states,
  direct URLs, back/forward, keyboard navigation and related-record navigation.
- Run the full Python and browser suites. Inspect screenshots on 375×812 and
  desktop, including dark mode, dialogs, overflow and coarse-pointer targets.
- Extend `tools/interaction_cost.py` with election-result, candidate-policy and
  ballot-to-legal-record flows. Measure taps, swipes, queries and elapsed time;
  keep existing flows within their budgets.
- Two independent review rounds with combined correctness/editorial scope;
  address findings and GitHub review comments, then recheck changed flows.
- Merge only after all promised research/review work has returned, CI passes and
  the coverage report is accurate. Verify Pages deployment and clean the branch.

## Research gate: proposed next sources

Estimate for the full requested scope: 80–140K tokens across research,
implementation, two review rounds and UAT. Roughly 100–150 distinct editorial
source pages for the 36 governor contests, relevant local measures/races and
existing-tab changes. Automated whole-dataset link checks may contact the
roughly 2,400 cited source rows but do not put all page bodies into model context.
This is a budget estimate, not a promise of exhaustive county-race coverage.

The next priority sources, after the initial ten-page check:

- https://www.texastribune.org/2026/11/04/data-center-texas-pause-gina-hinojosa-governor-policies/
- https://www.sos.state.tx.us/elections/laws/links.shtml
- https://liveresults.ohiosos.gov/
- https://actonforgovernor.com/issue/data-centers/
- https://results.sos.ga.gov/results/public/Georgia
- https://mielections.us/election/results/
- https://www.jocelynbenson.com/issues/data-centers
- https://electionresults.iowa.gov/
- https://robsand.com/issues/data-centers
- https://www.electionreturns.pa.gov/
- https://elections.wi.gov/elections/election-results
- https://results.oregonvotes.gov/
- https://results.arizona.vote/
- https://electionresults.sos.nm.gov/
- https://thecandlepublishing.com/haaland-backs-data-center-moratorium-outlines-accountability-plan-to-stand-up-for-new-mexicos-water-and-communities/
- https://www.datacenterdynamics.com/en/news/local-data-center-moratoria-limits-and-restrictions-voted-in-across-the-us/

Continue from official ballot wording/results and each remaining candidate’s
own page; discovered links are checked before publication. A blocked official
results landing page does not establish a race result.

## Baseline findings

- Started from `bfd69ec` (remote main), incorporating 12 commits newer than the
  initial local checkout. Branch: `codex/election-2026-refresh`.
- `refresh.py --check`: passed. Non-browser baseline: 545 tests passed.
- Cached source revalidation: 2,195 of 2,397 source rows classified; 202 lack a
  usable cached check; 67 quote misses; 211 blocked URLs; no cached dead links.
  These are triage findings, not proof that current sources pass or fail.
- Initial web checks confirmed explicit moratorium language on the Hinojosa and
  Benson campaign pages and candidate statements in the Georgia debate
  transcript. Election results and legal effects still need independent checks.
- Data Center Dynamics and several result/reporting URLs were inaccessible to
  the web reader. A direct DCD request returned 403; this is inconclusive, not a
  dead link. Do not use search summaries as publication evidence.
- Hayward’s own October 21 announcement confirms an immediate unanimous
  moratorium vote the previous day. It describes a statutory maximum of two
  years, not the initial ordinance term. The held backlog lead can be resolved
  by checking the ordinance’s exact duration; do not record the maximum as the
  enacted term.
- Browser baseline initially could not launch because Playwright expects
  revision 1223 and this machine has revision 1234. A local ignored symlink
  allows the baseline to use the already-installed Chromium. A browser smoke
  check passes; dependency files are unchanged.
- Home smoke check at 375×812 and 1366×900: no document overflow, no page errors;
  navigation occupies two rows on the phone and one on desktop.

## Delivered coverage and limits — November 4, 2026

- Elections: all 36 governor races, 34 reported winners, Alaska/Kansas uncalled;
  26 independently sourced outgoing governors, 42 governor policy excerpts, and
  both principal candidates represented in 17 races. Missing statements remain
  explicit. Candidate roster coverage does not claim every write-in/minor party.
- Local: Frederick County MD executive, Georgia PSC D3/D5, 17 ballot measures.
  Four municipal results carry signed certification; the others remain reported.
- Legal: added Hayward (initial 45 days), Sabattus (180 days from passage), Wells
  (180 days from June 16) and Wiscasset (six months). Eliot commencement, North
  Berwick commencement and Emporia enforceability remain held; their votes are
  visible in Elections. Other Ohio questions, Peru ME, Janesville WI, Harwood ND,
  New Jersey measures and further Maryland county races remain incomplete.
- Existing views: updated Duke Florida large-load tariff rejection; added the
  Louisiana tax-exemption protection framework; refreshed the pledge roster with
  CoreSite/SB Energy (no guessed signing dates); updated Hermantown approvals and
  pending utility review; restored Talavera's original environmental declaration
  from the official DOCM gazette. No automatic community stance, delivery or
  ratepayer assessments were changed. Discovery did not establish further
  publishable company claims; existing unresolved evidence remains below.

Both independent code-review rounds are complete. Round one fixed failed
record-link Retry navigation. Round two found an empty Wells ordinance cache;
the actual official PDF was retrieved (200, 388,330 bytes, browser User-Agent),
its sections 3/5/8 verified, and both citations changed to the working www URL.
Visual UAT corrected inherited column filters and an existing null-MW “all
sizes” assumption. Search includes candidate statements and ballot/legal text.

### Source audit

The full live pass classified 2,398 pre-integration source rows; blocked and
changed pages remain worklists, not accuracy certifications. A further live
election pass classified all 121 election source rows, with zero dead links or
quote mismatches and ten blocked URLs. Signed scanned results were read visually.
The final combined cached view is:

- dead links: 0
- quote misses: 73
- changed pages: 1513
- unchecked urls: 0
- stale statuses: 0
- blocked urls: 233
- urls checked: 2530
- rows total: 2530

Changed-page fingerprints require manual review. A quote mismatch is not proof of a false claim; no quote was rewritten from a search summary. Remaining company-claim mismatches:

- `aws-new-carlisle-in-community-fund`
- `aws-new-carlisle-in-state-gdp`
- `qts-cedar-rapids-ia-tax-revenue-ratepayer-pledge`
- `qts-richmond-va-fast-41-quote`
- `meta-prineville-or-community-grants-school-funding`
- `meta-richland-la-education-robotics-delhi`
- `xai-engagement-fabric-mayo`
- `oracle-education-academy-blog-2026`
- `meta-tulsa-engagement-demasi-proud-2026`
- `prologis-coweta-engagement-witt-codes-2025`
- `prologis-coweta-engagement-witt-execute-2025`
- `prologis-coweta-infrastructure-mason-lines-2025`
- `microsoft-leesburg-va-infrastructure-water-2026`
- `meta-los-lunas-water-2021`

Final verification: 931 tests passed (171 seconds), followed by 96 focused
seed/roster/timing checks after the final copy edit. Two consecutive refresh
builds produced byte-identical output. Source audit: all 2,530 current rows
classified, zero dead links; 233 blocked URLs and 73 excerpt mismatches remain
explicit worklists. No unresolved P1/P2 review findings.
