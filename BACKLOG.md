# BACKLOG.md

Roadmap and ideas, prioritized. Per CLAUDE.md: when an idea comes up
during development, add it here immediately — don't lose it. Each item:
brief description + priority (low / medium / high) + (optional) acceptance
criterion.

---

## High priority

### Source URL deep-links — verify and replace publication-root URLs in responses
v1 seed has ~10 `CommunityResponse` records linking to outlet homepages
instead of specific articles (see [ISSUES.md](ISSUES.md)). For each:
locate the original article via the outlet's archive search, replace the
URL in `data/seed/responses.json`, re-run `python refresh.py`. Add a
follow-up test `test_response_urls_deep_link` that flags root-level
publication URLs.

### OpenAI / Oracle Stargate Abilene — first-party claims pending
Sub-agent research found `openai.com/index/announcing-the-stargate-project/` returns HTTP 403 to scrapers, so the v1 OpenAI / Oracle claims could not be re-verified verbatim against the canonical announcement. Current v1.1 claims for those companies still cite the original announcement URL (which loads in browsers) but the agent could only re-read the Wikipedia paraphrase. Action: visit the URL in a browser, copy verbatim quotes for each claim, refresh `captured_at`. Same for `x.ai/blog/colossus`.

### Many `project_page_url` values point to news articles, not project pages
Several projects (e.g. `google-mesa-az`) didn't have a dedicated company project page — the canonical page is a third-party press release (gpec.org, etc.) instead. Mark these in ISSUES.md and find better URLs over time. The schema accepts any HttpUrl; the field is best-effort.

### Link checker — `refresh.py --check-links`
Add a mode that HEADs every URL across all four seed payloads, reports
4xx/5xx, and exits nonzero. Hook into a weekly GitHub Actions cron so
link rot is surfaced before users hit it. Rate-limited to 2s per host.

### Per-company connector for Microsoft Datacenter Community Pledge
Microsoft's Datacenter Community Pledge page is the most stable hyperscaler
community page and has structured per-region commitments. Build the first
v2 connector (`connectors/microsoft_pledge.py`) emitting `Claim` records,
to validate the connector framework end-to-end before tackling the others.

---

## Medium priority

### Add OpenAI Stargate site list as it expands
Stargate has only one announced site (Abilene, TX) as of 2025-01. Track
new site announcements and add them as `openai-*` projects with cross-
referenced `oracle-*` capacity-tenancy projects.

### Add per-claim "delivered vs promised" callouts where evidence exists
For claims where actual outcomes have been independently reported (e.g.,
Google's water-use disclosure showing actual consumption against earlier
implied claims), add an optional `delivered_vs_promised` field to `Claim`
and surface it as an inline note in the claim card. Editorial care
required — this is the closest the dashboard would get to an evaluative
judgment.

### Project status auto-update workflow
When a project moves from `announced` → `construction` → `operational`,
there's no automated reminder to update the seed. Add a tracking column
in [ISSUES.md](ISSUES.md) for each long-lived project's expected
operational date.

### Geographic clustering for the project map
Northern Virginia "Data Center Alley" has multiple AWS sites within ~10
miles; on the map at low zoom they overlap and a click can grab the wrong
one. Consider Leaflet.markercluster, OR a custom decimation a la the
Brownfield project's hash-based decimation. Skip if v1 stays at <50
projects (current: 15).

### Theme-level filters in the Explorer view
Right now Explorer filters by company / status / stance. Add a theme
filter that surfaces only projects whose company has at least one claim
in the selected theme.

### Constituency filter in the Explorer view
Same shape as theme filter — let users narrow to projects where
regulators (or NGOs, or residents) have weighed in.

### CSV export of the comparison matrix
A "Download as CSV" button on the matrix view. Useful for journalists /
researchers who want to do their own analysis.

### URL state for filters
Currently only the `#explorer` hash is round-tripped. Add `?company=`,
`?status=`, `?stance=`, `?project=<id>`, `?company_x_theme=meta:energy`
so deep-links share a specific filtered state.

---

## Low priority / ideas

### 9th theme: noise / land use
Several recent community responses (Loudoun County hearings, Mt Pleasant
WI) center on noise from cooling fans and visual / land-use impact.
Currently those map to `engagement`, which is a stretch. Consider adding
a 9th theme `noise_land`. **REMINDER:** adding a theme requires schema
migration + frontend mirror + theme test parity update — see
[AGENTS.md](AGENTS.md). Do not do casually.

### Add Equinix, Digital Realty, QTS, CoreWeave (v2 scope)
v1 deliberately scopes to the eight named hyperscalers. As colocation
operators publish more substantive community pages — particularly around
AI workloads — revisit. Each addition needs its own slug, palette
swatch, and editorial review.

### International data centers (v2 scope)
v1 is US-only because public-records coverage is richer. Two strong v2
candidates: Ireland (Dublin DC cluster, Irish Times coverage) and
Uruguay (Google water controversy, El País coverage).

### Capture-history view
Each `Claim` already has `captured_at` and the dataset is append-only by
convention; surface a per-company "claims over time" view so a user can
see when a company adopted (or dropped) a specific commitment.

### AI-generated per-project summary (gated, with disclosure)
Similar to the adjacent Brownfield project's AI summary feature: generate
a one-paragraph natural-language summary per project, structured from the
claim + response data. **Strict editorial gates:** must be marked as
AI-generated, must read only from on-disk data (no live LLM lookups), and
must NOT make evaluative judgments — just synthesize.

### Mobile bottom-sheet for the project detail
On mobile (<640px), the project detail panel currently scrolls inline.
Adapt to a bottom-sheet pattern (drag handle, slide up from the bottom)
similar to the Brownfield project. Skip until mobile-traffic data
warrants it.

### Backups / data-source attestation
Snapshot the canonical company source pages (HTML or screenshot) at each
quarterly capture and commit to a `snapshots/` directory. Useful when a
company quietly changes wording — preserves the original text we quoted.
Storage cost is the concern; consider Wayback Machine integration
instead.

---

## Done

- **v1.1 — Project-detail tabs.** Overview / Claims / Community tab strip in the project pop-out, with count badges, in-session persistence, and reload reset.
- **v1.1 — Slim claim cards.** Tighter padding, smaller font, smaller curly quotes; compact variant inside detail panel.
- **v1.1 — Matrix checkmark glyph.** Single-claim cells render `✓`; multi-claim cells render the count.
- **v1.1 — Wonder Valley scope expansion.** First non-hyperscaler entity (O'Leary Digital, Box Elder County UT). Added wonder-valley to `COMPANY_SLUGS` + `CompanySlug` Literal + CSS palette + 3 project-tied claims + 4 community responses (Sierra Club, Utah Clean Energy, Box Elder Commission, Gov. Cox).
- **v1.1 — Data fill-in pass.** Claims grew from 25 → 93 (+68). Added project-specific claims (with `project_id` set) for all 15 hyperscaler projects + Wonder Valley, by web-scraping each project's canonical company page. Added company-level matrix-gap-fill claims for Meta jobs/infrastructure, Google jobs/engagement, Microsoft jobs/tax_revenue/infrastructure, Amazon education/engagement.
- **v1.1 — `Project.project_page_url`.** New optional schema field; renders in detail panel Overview as "Project page" link, distinct from "Record source".
