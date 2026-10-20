# Audit: work produced but not on main (2026-10-19)

Read-only audit. Method: remote branches vs PRs; scratchpad JSON URLs diffed against `data/seed/*.json`; then checked against BACKLOG.md, REFRESH.md, the ledger and `notes/`. Recovered copies live in `recovered/`.

## 1. Branches
31 remote branches are not ancestors of `origin/main`. **29 are squash-merged** (every PR MERGED: #50-#85 incl. all `daily-refresh-*`, `jam/*`, `intl/*`, `refresh/2026-10-18`, `session/2026-10-19`, `data/validate-india-seo`). Only `data/followup-85` (current branch, notes only) has no PR.
- One tip is newer than its PR merge: `jam/festive-hopper-ggkzps` (PR #62 merged 21:00Z, tip 22:15Z, +6 commits vs main). It also carries PR #63 (merged). Diff it before deleting; not inspected beyond the date.
- Two CLOSED-unmerged PRs exist: #36 (`ui/layout-nav-above-fold-accordions`, already judged superseded in CLAUDE.md) and #29 (`claude/keen-noyce-1b8fdc`). Both branches are not on the remote list: nothing to recover.
- Seed changes from `daily-refresh-*`: each PR merged, so content is on main.

## 2. Scratchpads
`1f875a0d`, `595147a9`, `d9c0b760` are empty. `0d314164` (Instagram/India side session) and `21b868d0` (current) hold the findings below. `ig_leads_*.json` and `india_pushback.json` are already preserved in notes and named in PLAN.md items 1-2 (not repeated). The 14 `in-*` India ids from wave3/`final.jsonl` are confirmed absent from seed.

## 3. Items (verified = probe HIT / minimum fetch per the files)

| Source | Item | Verified? | On main? | Recommendation |
|---|---|---|---|---|
| burn/al_ky_ok_mn_or_mi.json | Shawnee OK moratorium through 2027, enacted 2026-08-17 (News9) | yes | no (only Shawnee County KS) | ship |
| same | Luther OK town board moratorium 2026-06-17 | yes (pre-window) | no | ship |
| same | Marshall MI one-year moratorium 2026-08-03 | yes | no | ship |
| burn/ia_wi_co_mo_sc.json | Brighton CO one-year ban, 2026-10-06 (KUNC) | yes | no | ship |
| same | Kiowa County CO emergency moratorium 2026-04-09 (county minutes) | yes | no | ship |
| same | Ralls County MO one-year moratorium (date = article date) | yes | no | ship, note date caveat |
| burn/il_ne_ks_*.json | Saline County KS three-year pause (event date unknown) | yes | no | ship after date check |
| same | Village of Nehawka NE policy 2026-08-27 | yes | no | ship as policy |
| burn/al_ky_*.json | Waite Park MN one-year moratorium 2026-05-04 | yes (pre-window) | no | ship |
| burn/ga_tx_oh_ca.json | Newton County GA extension (Apr 8 verbatim only) | partly | no (lead in BACKLOG) | hold: end date unverified |
| same | San Marcos TX policy 2026-06-16; Wilmington OH site_update 2026-09-03 | yes | no (Wilmington in BACKLOG) | ship |
| burn/leads_ne_plains_ky_tn.json | Gallatin TN 60-day pause 2026-07-29; Allen County KY 24-month | yes, but enactment body/date of Allen not confirmed | no (both in BACKLOG) | Gallatin ship; Allen hold |
| burn/ne_plains_wa_hi_ak_ky.json | Boston MA policy; Fairbanks NSB policy request | yes | no | ship as policy |
| burn/ms_nv_*.json | AZ Corporation Commission large-load tariff approved 2026-08-12; Coeur d'Alene ID policy | yes (CdA status placeholder) | no | ACC ship (tariffs tab); CdA hold |
| burn/untracked_list.json | Front Royal VA zoning ban; Bowling Green KY | yes | no | Front Royal ship as policy; Bowling Green obsolete (rejected pause) |
| burn/wy_va_in_mi_pa_mn.json | Prince William VA by-right to special review 2026-09-22; Fort Wayne council pause | yes | no (Fort Wayne in BACKLOG) | ship as policy (not moratorium) |
| burn/pa_in_mi_il_ky_leads.json | West Vincent PA hearing notice | yes | no | hold: adoption outcome unknown |
| burn/*: Edmond OK, Nelson KY, Rowan KY, Cullman AL, Camden GA, Zeeland MI, Wixom MI, Edmonson KY, Upper Burrell PA, Madison IN, White IL, Beloit WI | action found, date or primary source missing | no (verified=false) | no (most are BACKLOG leads) | hold |
| research/sites.json, announcements.json | Trenton OH petition + AWS open house, WATER Group dispute, Microsoft Woodward IA 600 acres, Riot Rockdale 191 MW lease, Project Jade to Tembo, Calvert Cliffs withdrawn | yes | no (all but Woodward are in BACKLOG as leads) | ship (Oct 18 refresh leftovers) |
| research/gov2.json | Columbus County NC hearing 2026-10-05; Charlotte extension conflict record | yes | no | hold: dated stale; re-check |
| research/power.json | Warren report on fair-share pledges; FPL PSC filing | no (verified=false) | no | hold |
| burn/eminent_domain*.json | Nashville zoo, MPRP MD, Dominion Loudoun, GA Power Ashley Park | yes | notes-only by design (EMINENT_DOMAIN.md) | obsolete as seed; keep notes |
| notes/specs/international/wave3/india_deep*.json | Airtel/Nxtra capacity, UP DC policy 2026, Tarluvada EC, 3 more responses | yes | no | ship with India pushback (PLAN item 2) |
| notes/specs/international/wave2/* | 51 verified rows, mostly secondary sources (tovima, jss.fr, atnorth, RTE, newmoney) | yes | not as these URLs | hold: deferred_needs_company + wave2 decisions; low value |

## Counts
- Branches: 31 not ancestors; 29 merged by PR, 1 current, 0 lost; 1 branch tip newer than merge (#62).
- Scratchpad: ~224 distinct URLs absent from seed; 129 appear elsewhere (notes/BACKLOG, evidence for rejected or dead links). Of the rest, ~35 verified records are real shippable gaps: **~21 moratorium/policy/tariff/site records, 14 India responses**.
- Notes: 51 verified rows absent (all international wave2/3).

## Top to ship
1. Moratorium batch missing from main: Shawnee OK, Luther OK, Marshall MI, Waite Park MN, Brighton CO, Kiowa CO, Ralls MO, Saline KS, Gallatin TN (9 records).
2. Policy-type records: San Marcos, Nehawka, Boston, Fairbanks, Front Royal, Prince William, Fort Wayne; tariff: Arizona ACC 2026-08-12.
3. Oct 18 site leftovers: Trenton OH (3), Woodward IA, Riot Rockdale, Tembo rename, Calvert Cliffs withdrawal.
4. India wave3 (14 responses plus Airtel/Nxtra, UP policy).

Caveat: "on main" was tested by source_url and by jurisdiction name in the seed; a record could exist under a different URL. Re-run `refresh.py` and the probe gate before shipping.
