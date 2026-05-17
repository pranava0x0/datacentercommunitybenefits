# DESIGN.md — Design system & editorial rubric

> The visual language and the editorial rules that the dashboard's
> credibility rests on. Touch this before changing how claims, projects,
> or community responses are categorized or displayed.

---

## 1. Visual design system

### Type

- **Display / headlines** — system serif stack: `Charter`,
  `Source Serif 4`, `Iowan Old Style`, `Apple Garamond`, `Baskerville`,
  `Times New Roman`. Used for `<h1>`–`<h3>`, the hero block, and verbatim
  claim quotes (so claims read as quoted material, not editorialized).
- **Body / UI** — system sans stack (`-apple-system`, `Segoe UI`, `Roboto`).
- **Numerals** — `font-variant-numeric: tabular-nums` on any element
  showing counts in a column, so digits line up.

**Don't add a Google Fonts link.** The system stack is intentional for
performance and offline-friendliness — same call as adjacent projects in
this org.

### Color tokens

All colors live as CSS custom properties on `:root` (light) and
`[data-theme="dark"]`. JS reads them via `getComputedStyle()` — never
hard-code a hex value in `app.js`.

Three palettes:

| Group           | Vars                                                         | Used for                                                          |
| --------------- | ------------------------------------------------------------ | ----------------------------------------------------------------- |
| Surface / text  | `--bg`, `--surface`, `--surface-2`, `--text`, `--text-muted`, `--border` | App chrome, cards, dividers                                       |
| Per-stance      | `--stance-{positive,mixed,negative}` + `*-soft` variants     | Community-response cards: left-border + soft background per stance |
| Per-company     | `--co-{meta,google,microsoft,amazon,openai,anthropic,xai,oracle}` | Subtle 3px left border on claim/project cards, matrix row dot     |
| Per-theme       | `--theme-{jobs,tax_revenue,energy,water,community_grants,infrastructure,education,engagement}` | Matrix column header underline, theme chip dot                    |

### Per-company colors are NOT brand colors

This is deliberate. Using a company's actual brand color (Meta blue,
Google primary blue, Microsoft red/green/yellow grid) would imply
endorsement / official affiliation. The palette in this dashboard is
**brand-adjacent but neutral** — desaturated tones that distinguish
companies without claiming to represent them.

If a company's legal team asks the dashboard to remove "their color,"
the answer is: it isn't theirs. Update the value if it's genuinely close
to a registered mark; otherwise no action.

### Stance colors and what they mean visually

| Stance     | Light       | Dark        | Meaning                                                  |
| ---------- | ----------- | ----------- | -------------------------------------------------------- |
| `positive` | `#2f7a4d`   | `#6cc18a`   | Green — approval, support, positive coverage             |
| `mixed`    | `#b07024`   | `#d6a44c`   | Amber — caveats, partial support, complex reception      |
| `negative` | `#a3372f`   | `#e07a72`   | Red — opposition, complaint, regulatory or legal action  |

The stance color is the **only** color in the dashboard that carries
editorial weight (good vs bad signaling). Everything else is neutral.

### Layout

- **Mobile-first.** Comparison matrix degrades to compressed cell padding
  + smaller font; explorer layout collapses from two-column to single
  column at 960px.
- **Sticky topbar** with the tab strip — users can switch views from any
  scroll position.
- **Project detail panel** uses the `[hidden]` attribute paired with
  `[hidden] { display: none !important }` in CSS (CLAUDE.md > "[hidden]
  trap").

---

## 2. Editorial rubric

The dashboard's value depends on this rubric being applied consistently.
Curators (and any future AI assist) MUST follow it.

### What counts as a "claim"

A claim is a public, attributable statement by a hyperscaler about a
community benefit from their data centers. Concretely:

- ✅ A sentence on the company's published sustainability or
  community-impact page, quoted verbatim.
- ✅ A specific commitment in a press release tied to a project
  announcement.
- ✅ A pledge in a public regulatory filing (FERC, PUC, SEC).
- ❌ A quote from an executive in a paywalled trade-press interview
  (low replicability; users can't verify).
- ❌ A social-media post (ephemeral, can be deleted).
- ❌ A figure from an analyst report or third-party think tank — those
  belong in community responses, not claims.

The `statement` field is **verbatim**. If the original wording is awkward
or runs long, quote a self-contained sentence rather than rewording.

### Theme assignment

Each claim maps to **one** theme. When a claim spans multiple themes
(common with combined energy + water pledges), pick the most specific —
e.g. "120% water replenishment by 2030" is `water`, even if framed in a
broader sustainability context.

The eight themes are:

| Theme              | Includes                                                          |
| ------------------ | ----------------------------------------------------------------- |
| `jobs`             | Construction, operational, indirect/induced employment claims     |
| `tax_revenue`      | Property/sales tax contributions, abatement framing               |
| `energy`           | Renewable PPAs, efficiency, grid investment, carbon commitments   |
| `water`            | Usage, recycling, watershed restoration, water-positive pledges   |
| `community_grants` | Direct philanthropy, community funds, donation programs           |
| `infrastructure`   | Roads, fiber, utilities investment beyond the site fence          |
| `education`        | STEM programs, scholarships, workforce training, partnerships     |
| `engagement`       | Community input during siting, transparency, advisory boards      |

If a claim genuinely doesn't fit any theme, the right move is to file a
[BACKLOG.md](BACKLOG.md) entry to discuss adding a 9th theme — not to
shoehorn it.

### Community-response stance rubric

This is the **most adversarial** editorial call in the project. The
rubric:

- **`positive`** — the constituency unambiguously supports the project,
  cites a specific benefit, and the response is on the public record
  (city statement, press release, public testimony, on-the-record
  interview).
- **`mixed`** — the constituency expresses both support and concern; or
  supports the project conditionally; or the response is a regulatory
  decision that imposes conditions without rejecting outright.
- **`negative`** — the constituency opposes the project, cites a
  specific harm, and the opposition is on the public record (lawsuit
  filing, NOI, NAACP letter, formal complaint, on-the-record
  interview, contemporaneous news report quoting affected residents).

**When in doubt, pick `mixed`.** A wrongly-tagged `negative` is worse than
a `mixed` that should have been `negative` — the former is editorially
indefensible.

### Constituency assignment

Each response carries a `constituency` from a fixed list. Use the
**primary speaker** in the source, not the author of the article:

- `residents` — affected neighbors, individuals
- `local_government` — city council, county board, state agency,
  elected official
- `ngo` — non-profit, advocacy group, community organization,
  environmental org
- `academic` — university researcher, think tank publishing peer-
  reviewed work
- `journalist` — newsroom investigation, editorial board, where the
  story is itself the response (e.g., the disclosure-lawsuit angle)
- `regulator` — PUC, FERC, EPA, state DEQ, etc., acting in regulatory
  capacity

### Source diversity

For `negative` stance responses, prefer at least **two independent
sources from different outlets** before flagging. Single-source negative
responses MUST set `single_source: true` — the frontend renders a "single
source" badge so users can weight accordingly.

### Capture dates and staleness

- Claims and projects always carry `captured_at`. Re-capture quarterly.
  Old captures stay in the dataset (append-only); the field surfaces as
  "as of YYYY-MM-DD" so historical drift is visible.
- Companies' `last_reviewed` field tracks when a curator last spot-checked
  that company's published page. If a company hasn't been reviewed in
  >180 days, [BACKLOG.md](BACKLOG.md) should carry an entry.

### Delivered-vs-promised assessments (v1.13)

Each `Claim` can optionally carry a curator `Delivered` assessment with
one of four statuses, scored against independent reporting:

- **`delivered`** — independent reporting confirms the commitment was
  met. Requires either a first-party company milestone announcement
  corroborated by a third party, or a regulator/court finding.
- **`partial`** — meaningful progress but short of the stated scope. Use
  when the company is demonstrably tracking toward the goal but the
  goal hasn't been hit and the pace makes the original target
  uncertain.
- **`contested`** — the company maintains it's delivering; another
  party (resident group, regulator, lawsuit, investigative
  reporting) documents a shortfall. Surface both — don't pick a side.
- **`shortfall`** — independent reporting documents the commitment was
  not delivered. Use only with strong corroboration (≥2 independent
  sources or a citable regulator/court finding). A wrongly-tagged
  `shortfall` is worse than a `contested` that should have been
  `shortfall`.

**Absence is editorially valuable.** A claim WITHOUT an assessment means
"the curator hasn't done the work yet," NOT "implied delivery." The
dashboard surfaces no badge in this case. **Don't** invent a fifth
"unknown" status to fill rows.

The `summary` field on `Delivered` is a NEUTRAL synthesis — not a quote,
not adversarial framing. The `source_url` cites the underlying evidence
(distinct from `claim.source_url`, which cites the original commitment).

A seed-data test (`test_at_least_one_of_each_delivered_status`) requires
that the shipped dataset has at least one example of each of the four
statuses so the legend reads with real records behind every color.

### Things the dashboard explicitly does NOT do

- Aggregate claims into a numeric "credibility score."
- LLM-classify stance.
- LLM-classify delivered-vs-promised (this is exactly as adversarial as
  stance — a wrong call is editorially indefensible).
- Track social-media sentiment.
- Predict outcomes ("will this project deliver on its promises?"). The
  `Delivered` field is **retrospective only** — it scores what already
  happened, not what's expected.

These are all editorially indefensible at the dashboard's scale and
operationally fragile.

---

## 3. Cross-cutting UX rules

- **Every card surfaces its source.** Claim cards have a `Source: <link>`
  line; response cards have one too. No exceptions.
- **Null fields render as explicit placeholders.** "Not disclosed",
  "—", "N/A" — never an empty cell.
- **Filters are reversible.** Every filter chip has a clear button; the
  Reset button restores the default state.
- **Tab state survives URL.** `#explorer` deep-links to the project view.
- **Theme persists.** Light/dark choice is stored in `localStorage`.
- **Focus indicators visible.** Every interactive element has a focus
  ring; never `outline: none` without a visible replacement.

---

## 4. When to revisit this document

- A new theme is added (rare; requires backlog discussion).
- The stance rubric drifts in practice (track in ISSUES.md if you find
  yourself stretching the definition).
- A new constituency type is needed.
- The visual identity shifts (e.g., adopting a real font, adding map
  basemap).
