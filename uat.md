# UAT Baseline — Data Center Community Benefits Dashboard

_Created: 2026-06-01_
_Last run: 2026-06-07_

## Project Info
- **Stack:** Vanilla HTML/CSS/JS, static site — no build step
- **Dev server:** `python3 -m http.server 8013 --directory docs` (via `.claude/launch.json` name `docs`)
- **Entry point:** `docs/index.html`
- **Key views:** Company Comparison (tab 1), Project Explorer (tab 2), Ratepayer Protection Pledge (tab 3), Aggregate (tab 4)
- **Data:** `docs/data/` — companies.json, claims.json, projects.json, responses.json
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
