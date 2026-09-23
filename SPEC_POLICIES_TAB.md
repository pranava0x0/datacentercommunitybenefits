# Spec — Policies & Agreements tab (v3.1)

## Why

The dashboard tracks moratoriums (pauses), tariffs and rate cases (who pays
for power), and company claims. It has no home for the instruments in
between: a governor's executive order that sets conditions rather than a
pause, a state law that attaches community-benefit or water strings to a tax
incentive, a county's host-community agreement, a company's published
community plan. Several of these were being filed as moratoriums with a
`policy_type` apologizing for it ("Conditional permitting framework (not a
pause on development)"). They are the core of the blueprint framing: what a
community can actually ask for, and what others have already won.

## Record type: `Policy` (`data/seed/policies.json`)

One record type, with an `instrument` field, rather than two. A state
framework that *requires* a community benefit agreement and the agreement a
county then signs share every field that matters (jurisdiction, date,
status, themes, concrete terms, source), and one directory with an
instrument filter answers "what has been required, and what has been
signed?" side by side.

| field | type | notes |
|---|---|---|
| `id` | str | `<jurisdiction-or-company>-<short>-<yyyy>` |
| `title` | str | short human title, e.g. "Executive Order 2026-05 — data center siting" |
| `instrument` | `executive_order` / `legislation` / `regulation` / `local_ordinance` / `benefit_agreement` / `company_plan` | frozen vocab |
| `status` | `in_effect` / `proposed` / `failed` | agreement signed = `in_effect` |
| `scope` | `federal` / `state` / `county` / `city` / `company` | who sets it |
| `jurisdiction` | str | "Pennsylvania", "Hammond, IN", "Microsoft (company-wide)" |
| `state_code` | str? | required unless scope is `federal` or `company` |
| `identifier` | str? | bill / EO / ordinance / resolution number |
| `date` | date? | signed / enacted / announced; null only for undated proposals |
| `company_slugs` | list[CompanySlug]? | tracked companies party to it |
| `counterparties` | list[str]? | other named parties (untracked developers, utilities, school districts) |
| `benefit_themes` | list[Theme] (≥1) | reuses the frozen 8-theme taxonomy |
| `community_benefits_framework` | bool | true when it requires, creates or *is* a community benefit agreement / fund / host payment |
| `key_terms` | list[str] (≥1) | concrete, source-verifiable commitments ("$10M community fund", "air-cooled; no municipal water") |
| `value_usd` | float? | stated dollar value of committed community benefits, only when the source states one |
| `summary` | str | 2–4 neutral sentences |
| `source_url` / `source_title` | | live, primary preferred (.gov for public instruments; company newsroom for plans) |
| `resources` | list[SourceResource]? | secondary coverage |
| `related_project_ids` | list[str]? | cross-ref validated by refresh.py |
| `related_moratorium_id` | str? | cross-ref validated — for records the moratorium tab also carries |
| `captured_at` | date | |

Frozen-vocab drill (same as THEMES / tariffs): Python tuple + Literal +
labels in schema.py, mirrored in app.js, parity-tested.

## Tab: "Policies & Agreements" (`#policies`)

Placed after Tariffs & Rate Cases. Same skeleton as Moratoriums / Tariffs,
reusing their components:

1. `.hero` title + one-line dek.
2. Stat tiles (`.rp-stat` shape): policies in effect · states with a policy ·
   benefit agreements · company plans · records with a community-benefits
   framework.
3. Instrument breakdown (clickable bars → filter), like the moratorium
   concern chart.
4. Directory (`.acc`): filters for instrument, scope, state, theme,
   "community benefits framework only"; table rows open a detail modal
   (the tariff/moratorium modal pattern: backdrop, Escape, focus trap).
5. CSV + PDF export via the shared `_triggerDownload` / `_exportToPDF`.

Lazy-loads `data/policies.json` on tab activation — never on first paint
(perf budget). State panel (`#state/XX`) gets a sixth section; Home gets a
tile/card via `coverage.json` totals; aggregate unchanged in v1.

## Research plan

Efficient-first: existing records already name ~15 sites with CBAs, PILOTs,
development agreements and community funds (grep of projects / claims /
responses). Those are the agreement work-list; the state-policy pass starts
from scratch.

Two Sonnet agents, run in parallel (user cap: two at a time), each writing
one JSON object per line to a scratchpad JSONL the moment a record is
verified, plus a progress log of every state / company / locality checked —
including the ones with nothing to report, which are honest absences.

- **Agent A — state policies & EOs.** Every state + DC. Executive orders,
  statutes, regulations that set conditions on data centers (siting,
  incentive strings, water, ratepayer/grid, disclosure, community benefits).
  Skip pure moratoriums (Moratoriums tab) and utility tariffs (Tariffs tab).
- **Agent B — agreements & company plans.** The 15 companies' published
  community plans; then site-level CBAs / host / development / PILOT
  agreements with community payments, starting from the work-list, then a
  per-company sweep of tracked localities.

Verification bar (both): fetch the exact `source_url`, confirm each
`key_terms` item is actually on that page (the v1.19 search-synthesis
lesson), live links only, no fabricated .gov paths, headline words ("ban",
"agreement") checked against the instrument itself.

## Research log (2026-09-23 pass)

Shipped 68 records across 38 states plus 10 company-wide plans: 29
legislation, 6 executive orders, 21 benefit agreements, 12 company plans
(2 of them site pledges).

**States with no state-level policy that cleared verification** (several
have local agreements). These are open leads, not "no policy exists": MD, CT, MS, WI, MO, ND, ID, NM, ME, VT, NH,
RI, DE, AK, HI, DC, WY, IA, AR. Oklahoma's ratepayer act is HB 2992, which is
already a moratorium record. Bills that never passed a chamber (GA SB421, NY
A9086, MI HB6137/SB1050) were left out.

**Companies with no company-wide community plan found:** Oracle, xAI (it has
a Memphis site pledge instead), SB Energy, Wonder Valley, Brookfield (it has
a Paducah site pledge instead).

## Out of scope for v1

- Moving misfiled non-moratorium records (PA EO 2026-05, OK HB2992, WA
  SB5982) out of `moratoriums.json`. They stay on the Moratoriums tab for
  now and are not duplicated here. `related_moratorium_id` exists for the
  migration (and for any future record that genuinely overlaps). The move
  itself is a BACKLOG item.
- Delivered-vs-promised on agreements (the `Delivered` pattern) — later.
