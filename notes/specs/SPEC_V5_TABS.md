# v5 tab pass (2026-10-08, user-directed)

User asks: refresh all data; consider sub-tabs on every tab; Companies tab
"makes no sense, too many codes, table is all checkmarks"; Sites "feels
dated", track contested sites with local news/hearings; rename Policy
Playbook → Local Policy Frameworks; Tariffs & Rate Cases "too long to get to
the meat, filters take too much space". Max 2 agents at once. Open a PR.

## Peer trackers looked at
- **datacenterbans.com**: status buckets with counts (bans / advancing /
  discussion / none / incentives), a dated "upcoming" prose list, live news.
  No per-project timeline.
- **Erin Brockovich's map** (DCD coverage, 2026): only sites where residents
  are actively raising concerns, plus a resident report form. The lesson: the
  contested sites ARE the product for a community reader.

## Decisions
1. **Sub-tabs where panes are alternatives** (CLAUDE.md test: would a reader
   want two on screen at once? No → sub-tab). Sub-tab state goes in the URL
   as `#<view>/<subkey>` (BACKLOG §4 item), so rate cases are one link away.
   - Companies: Profiles · Commitments · Footprint
   - Sites: Map & list · Contested · By state
   - Tariffs & Rate Cases: Rate cases · Tariffs · Rate-design elements
   - Local Policy Frameworks: Principles · Latest · Directory
   - Moratoriums: left as accordions (charts + directory are read together).
   - The Pledge: keeps its one existing group.
2. **Companies.** Kill the codes (`13A 7C 3O`, `●12 ●14 ●19`) — every number
   gets its word. The checkmark matrix becomes a **commitment-depth** grid:
   each cell is Specific (≥1 claim with a figure: $, jobs, MW, gallons),
   General (written, no figure) or None, plus the claim count, with a legend.
   Clicking a cell or theme shows the companies' actual quotes for that theme.
   Profiles = one card per company: pledge status, sites by status in words,
   GW / $ / jobs, community response in words, contested sites, depth chips.
3. **Sites.** Map tiles were broken (CARTO now returns "API KEY REQUIRED";
   switched to Esri canvas). "Recently contested" rail → a full **Contested**
   sub-tab: every site with a critical community response or a contested
   ratepayer assessment, each with a dated **local timeline** (hearings,
   votes, permits, lawsuits, filings) and the next announced date.
   New typed `Project.updates` (BACKLOG decision 3, now made by the user).
4. **Rename** Policy Playbook → Local Policy Frameworks (label + heading;
   `#policies` hash unchanged for deep links).
5. **Tariffs**: rate cases first sub-tab; one-line filter bar; design-element
   chips move to their own sub-tab and become a directory filter select.

## Data refresh
- Sonnet agent: new/changed policies, moratoriums, tariffs, rate cases since
  2026-09-15 → `.agent_outputs/2026-10-08/refresh_candidates.jsonl`.
- Haiku agents: per-site local timelines for contested sites →
  `.agent_outputs/2026-10-08/site_updates.jsonl`.
- Every row gated by `scripts/probe.py --evidence` (verbatim on the page);
  BLOCKED rows re-read by a Haiku validator via WebFetch.
