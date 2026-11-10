# Proposal: one "Policy" tab for moratoriums and frameworks

Status: proposal only, nothing is built. Owner decision needed.

## Why

- Readers don't sort government actions by our record types. A county that
  pauses data centers and then adopts zoning standards appears on two tabs.
  Today that county's pause and its rules are 4+ taps apart, and each tab has
  to link to the other ("Pauses and bans are in Moratoriums", "Development
  rules and agreements are in Frameworks").
- Ten top-level tabs wrap into two rows on tablet and phone (88 px of chrome).
  Nine would also wrap. Eight fits one row on a tablet.
- Both tabs already share a state filter, a directory, a map and a "latest"
  list. Merging them removes duplicated controls.

## Shape

**Tab: Policy** (`#policy`; `#moratoriums` and `#policies` redirect to it).

| Sub-tab | Contents | Comes from |
|---|---|---|
| Latest *(default)* | Newest actions of every kind, dated: pauses, laws, orders, ordinances | Frameworks "Latest" + moratorium dates |
| Pauses | The moratorium directory: place, date, status, length, reasons | Moratoriums → Directory |
| Rules | The frameworks directory, with a type filter (order / law / regulation / ordinance) | Frameworks → Directory |
| By principle | The nine principle cards | Frameworks → Principles |
| Map | One map with two layers, pauses and rules | Moratoriums → Map + jurisdiction map |
| Trends | Timeline and concerns charts | Moratoriums → Trends |

- **One stat row for the whole tab:** pauses enacted, rules in effect, states
  acting, newest action date. The Home card then leads with one number.
- **Draft plans and Evidence** (planning tools) move to Benefit Agreements,
  where the Home "Draft a benefit plan" and "Check impact claims" buttons
  already send readers.
- **Benefit Agreements stays its own tab.** It answers a different question:
  what did communities win, not what did governments require.
- **Data stays separate.** `moratoriums.json` and `policies.json` keep their
  schemas and the "pure pauses go in Moratoriums" rule. Only the view merges.

## Result

Tabs: Home · The Pledge · Policy · Benefit Agreements · Elections ·
Power Costs · Companies · Sites · International. That is nine, or eight if
Companies joins Sites as a sub-tab.

## Costs and risks

- About 40 e2e tests address `#moratoriums` or `#policies` panes. Redirects
  keep deep links working, but selectors move.
- Interaction budgets for moratorium and policy tasks need re-measuring.
- PDF and CSV exports become one per sub-tab rather than one per tab.
- Effort: one focused PR, roughly the size of the v5 sub-tab pass.

## Decision needed

1. Merge the views as above? (Recommended.)
2. Fold Companies into Sites as well, to reach eight tabs?
