# UAT Baseline — Data Center Community Benefits Dashboard

_Created: 2026-06-01_
_Last run: 2026-06-01_

## Project Info
- **Stack:** Vanilla HTML/CSS/JS, static site — no build step
- **Dev server:** `python3 -m http.server 8013 --directory docs` (via `.claude/launch.json` name `docs`)
- **Entry point:** `docs/index.html`
- **Key views:** Company Comparison (tab 1), Project Explorer (tab 2), Ratepayer Protection Pledge (tab 3)
- **Data:** `docs/data/` — companies.json, claims.json, projects.json, responses.json

## Critical Flows (run every time)

1. **Page load / stats bar:** Load `http://localhost:8013` — verify stats bar shows correct counts (companies, projects, claims, responses). Counts must match seed totals from `refresh.py` output.
2. **Ratepayer tab — signatory roster:** Click tab 3; scroll to "Who's signed" — confirm 7 green-checkmark signatories and 2 non-signatory own-commitment entries (Nebius, QTS).
3. **Ratepayer tab — affirmed badge:** Scroll to site scorecard; confirm at least one "Site-specific commitment" green pill renders with a verbatim evidence quote and source link.
4. **Ratepayer tab — pledge_only badge:** Confirm at least one "National pledge only" gray pill renders with a summary and no evidence quote block.
5. **Explorer — company filter:** Switch to Project Explorer; set company filter to "amazon"; confirm project count shows 13 and all new projects (ridgeland, wilmington, caddo, bossier, vicksburg) appear in the list.
6. **Explorer — project detail:** Click any project card; confirm the detail panel opens with Overview/Claims/On the ground tabs, investment and jobs KV rows, and source link.
7. **Explorer — new Google projects:** Filter to Google; confirm 20 projects including pine-island-mn, hermantown-mn, wilbarger-tx, armstrong-tx, haskell-tx.
8. **Comparison matrix:** Switch to Company Comparison; scroll to matrix; confirm all 14 company rows render and checkmarks appear for populated cells.
9. **Dark mode:** Toggle dark mode; confirm header, cards, badges, and quote blocks all remain readable.
10. **Console clean:** After full walkthrough, check `preview_console_logs` — expect zero errors or warnings.

## Sections & Last Tested

| Section | Last Tested | Notes |
|---|---|---|
| Draft banner | 2026-06-01 | Shows stale v1.15 — UAT-001 open |
| Stats bar | 2026-06-01 | Stable — 14 co / 85 proj / 296 claims / 206 responses |
| Tab navigation | 2026-06-01 | Ratepayer tab wraps 3 lines on mobile — UAT-003 open |
| Company Comparison matrix | 2026-06-01 | Works; no horizontal scroll indicator — UAT-005 open |
| Company pop-out | 2026-06-01 | Not tested this run; test next pass |
| Project Explorer — hot rail | 2026-06-01 | Stable |
| Project Explorer — filter panel | 2026-06-01 | Sort-by truncated on mobile — UAT-002 open |
| Project Explorer — map | 2026-06-01 | Stable; Amazon filter shows 13 dots |
| Project Explorer — project list | 2026-06-01 | Stable; all 8 new projects confirmed present |
| Project detail — Overview tab | 2026-06-01 | Stable; KV grid renders correctly |
| Project detail — Claims tab | 2026-06-01 | Stable; evidence claims appear first |
| Project detail — On the ground tab | 2026-06-01 | Tab label wraps to 2 lines on mobile — UAT-004 open |
| Ratepayer tab — stat tiles | 2026-06-01 | Stable; "11 site-specific commitments" correct |
| Ratepayer tab — pledge elements accordion | 2026-06-01 | Renders; not expanded this run |
| Ratepayer tab — signatory roster | 2026-06-01 | Stable; all 7 signatories + 2 own-commitment entries |
| Ratepayer tab — site scorecard | 2026-06-01 | Stable; affirmed + pledge_only badges render correctly |
| Dark mode | 2026-06-01 | Stable; ratepayer badges correct in dark |

## Known Stable Areas
- Console: zero errors across full session
- Data counts match seed (85 projects, 296 claims, 206 responses)
- Ratepayer affirmed/pledge_only badge rendering (light + dark)
- Evidence quote blockquote rendering in ratepayer scorecard
- Project detail KV grid (investment, jobs, offtaker, source link)
- Explorer company filter count accuracy

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
