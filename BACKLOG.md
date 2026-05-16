# BACKLOG.md

Roadmap and ideas, prioritized. Per CLAUDE.md: when an idea comes up
during development, add it here immediately — don't lose it. Each item:
brief description + priority (low / medium / high) + (optional) acceptance
criterion.

---

## High priority

### Resume session: matrix gap-fill (paused 2026-05-16 after v1.8)
Eleven matrix cells still empty after three polling passes (DCD, UtilityDive,
30-day news, framework pages). Each is an honest gap — every attempt has been
made to find a verbatim first-party quote and failed. Recommended next attempts:

- **Meta — tax_revenue.** Try `about.fb.com` press releases for site-specific
  PILOT or property-tax quotes; the Beaver Dam WI announcement is the most
  likely host. Mayor / governor quotes are NOT acceptable (not first-party).
- **OpenAI — tax_revenue, water.** `openai.com/index/stargate-community/`
  returned 403 throughout the session; tax_revenue gap requires fetching it
  in a real browser (or via Wayback Machine) for verbatim copy. The water
  paragraph there almost certainly contains a shippable quote.
- **Anthropic — community_grants, education.** Needs an Anthropic statement
  *tied to a data-center community* (the Workday/LISC Solopreneurship one
  failed the site-tie test). May not exist; honest gap is acceptable.
- **Oracle — tax_revenue, engagement.** `oracle.com/news/announcement/blog/oracle-ai-infrastructure-in-2026-and-our-commitment-to-local-communities-2026-01-26/`
  is 403. We shipped community_grants + water via smallbiztrends third-party
  verification; same approach may yield engagement + tax_revenue.
- **Wonder Valley — community_grants, education.** Exhausted in May 2026
  coverage. O'Leary doesn't talk about either in any captured interview.
  Probably an honest permanent gap given Wonder Valley's framing.
- **QTS — education.** Try `q.com/resources/` STEM/scholarship pages;
  the Dane County WI $50M commitment likely has an education-tagged exec
  quote in QTS's announcement materials.
- **Crusoe — community_grants.** Sweetwater TX agreement reportedly has
  $2.2M/yr charitable funding but only paraphrased in KTXS — try Nolan County
  records for the verbatim development-agreement text.

### Resume session: next polling cycle
After ~30 days from 2026-05-16, re-run the parallel news poll. Focus on:
- DCD + UtilityDive (proven productive sources — see v1.8)
- Texas Tribune / Source NM / Wisconsin Watch / Cowboy State Daily for the
  community-pushback angle on the high-controversy sites (Wonder Valley,
  Cheyenne, Memphis, Saline Twp, Person Co NC, Kenilworth, Vineland)
- Watch for: status changes (announced → construction → operational),
  acreage/power expansions, regulator orders, NGO lawsuits, community
  benefit-agreement signings
- New sites to watch: Nebius PA campus (location TBD per May 13 disclosure);
  DTE-served Google/Oracle Michigan sites (per UtilityDive Q1)

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

- **v1.8 — DCD + UtilityDive 30-day scan.** Parallel DataCenterDynamics + UtilityDive scan for Apr 16 – May 16 2026. +5 sites (4 Google: Michigan City IN / Lima OH / Franklin Furnace OH / Linn County IA + 1 OpenAI Stargate Milam County TX "Freebird"), +7 first-party claims (Nadella on Fairwater going operational, Google's per-site community/infrastructure/education commitments, Anthropic on Colossus 1 tenancy, Oracle Saline Twp jobs, Meta LevelUp education), +5 responses (4 xAI Memphis — NAACP suit Apr 15 + injunction May 6 + DOJ statement-of-interest May 15 + MS 41-turbine permit Apr 29; 1 Meta Richland — Entergy Q1 $2B customer-benefit confirmation), +2 project field updates (Meta Richland acreage 2,250→3,650 from Phase 2 land buy; MS Mt Pleasant status construction→operational per Nadella Apr 16). DCD blocks WebFetch — agent reconstructed article-level detail from Google snippets + canonical URLs as `source_url`.
- **v1.7.1 — Community responses for new sites + OpenAI engagement gap-fill.** +41 community responses across 14 newly-added sites (21 negative, 11 mixed, 9 positive — distribution by constituency: local_government 15, residents 14, ngo 5, journalist 4, regulator 2, academic 1). Includes Wisconsin PSC "black box" critique of Meta+Alliant, Tulsa City Council moratorium pre-dating Meta Project Anthem reveal, Saline Township board 4-1 rejection → Related Digital lawsuit → $14M community-benefits settlement, Kenilworth NJ rallies (Apr 20 + May 7), Stillwater OK Park View Estates HOA suit against Google over pond sediment, Person County NC NDA controversy → Microsoft's March 2026 pledge to stop signing community-blinding NDAs, Vineland NJ rally → DataOne declines $6.2M city loan + project scaled from 2.4M to <718K sq ft. +1 OpenAI Stargate Community engagement claim verified verbatim via Sherwood News citation of openai.com/index/stargate-community/.
- **v1.7 — 30-day news poll, +19 sites + 26 claims + 7 summary refreshes + Explorer sort.** Four parallel agents polled news for Apr 16 – May 16 2026 across all 13 companies. New sites: Meta (Tulsa OK, Beaver Dam WI), Google (LaGrange GA, Stillwater OK), Microsoft (Person County NC), Amazon (Canton MS, Clinton MS), OpenAI/Oracle (Saline Township MI Stargate, $16B financing close Apr 24), Oracle (Doña Ana NM Project Jupiter with Bloom Energy fuel cells Apr 27), QTS (Eagle Mountain UT, Fayetteville GA, York County SC, East Windsor NJ), Crusoe (Sweetwater TX, Cheyenne WY Project Jade, Springfield OH), CoreWeave (Kenilworth NJ, Lancaster PA), Nebius (Vineland NJ). 26 verbatim first-party claims fill 6 of 8 matrix gaps (Google, Microsoft, Amazon, xAI, CoreWeave, Nebius now complete). Summary refreshes: factual fix to Wonder Valley (Phase 1 = ~3 GW not 1.5 GW; ~40,000 acres not 2,000); major rewrites for OpenAI (Stargate Community framework Jan 21 2026 now exists) and Oracle (per-site Q1 2026 blog framework now exists); minor updates to Meta, Microsoft, Amazon, xAI, Anthropic. Plus Explorer "Sort by" dropdown with default Composite (most benefit) score = equal-weight average of normalized investment + jobs + claim count (min-max against full catalog so ranking is stable as filters change); single-metric options for investment / jobs / claims; project name as tiebreaker.
- **v1.6.1 — Fallback gap-fill via news + executive statements.** Loosened editorial bar: news articles containing direct verbatim quotes from named executives are now acceptable as `Claim` records (paraphrases still rejected). Three parallel agents researched the 30 remaining empty matrix cells; +13 claims added (xAI 3 — Brent Mayo Memphis school upgrades / fabric of community / financial responsibility; Wonder Valley 3 — O'Leary Tucker Carlson + KUTV jobs/tax/water; Oracle 2 — Larry Ellison Stargate + Oracle Academy blog; OpenAI 1 — Lehane NABTU; Crusoe 1 — Lochmiller Wyoming workforce; CoreWeave 1 — Intrator UK closed-loop; Nebius 2 — Sutter KSHB Q&A on infrastructure cost-coverage + community grants engagement panel). Matrix coverage 71% → 83% (87/104). Kept Sam Altman's "completely untrue, totally insane" water quote OUT of the dataset — verbatim but a dismissal of critics, doesn't fit blueprint framing of solutions offered. Added "What counts as first-party" rule to CLAUDE.md.
- **v1.6 — Three new operators (Crusoe, CoreWeave, Nebius) + two major frameworks (Microsoft Jan 2026, Google Mar 2026).** Companies tracked: 10 → 13. Projects: 23 → 27 (Crusoe Abilene, CoreWeave Hammond + Polaris Forge ND, Nebius Independence MO). Claims: 149 → 180 (+31). Microsoft's Jan 2026 "Building Community-First AI Infrastructure" framework adds 8 new claims spanning all 5 commitment areas (electricity-no-pass-through, water-replenish, jobs-NABTU, tax-full-share, AI-training + volunteer-hour match). Google's Mar 2026 Affordability Pledge adds 5 new claims (pay-our-own-way, 22 GW new energy, grid resilience, 9x jobs multiplier, PUE efficiency). Honest skips for Digital Realty + Equinix (both publish corporate ESG but no per-DC community framework) and FluidStack + Verrus (B2B-positioning phase, no community framework yet). OpenAI Stargate Community page (openai.com/index/stargate-community/) still 403'd to scrapers; logged in ISSUES.md as a curator follow-up.
- **v1.5 — Editorial reframe to blueprint.** Hero copy on both views, README, CLAUDE.md project intent reframed as "blueprint of solutions / field guide" rather than "neither hit piece nor puff piece". Detail-panel "Community" tab renamed to "On the ground"; placeholder text updated. Critical responses retained — they're case-study evidence ("lessons learned") for what's working in practice. Editorial integrity rules (verbatim quotes, source attribution) unchanged.
- **v1.5 — Matrix gap-fill from main company websites.** +9 company-level claims (Anthropic water, QTS jobs/energy/engagement, xAI energy, OpenAI energy/community grants, Oracle energy). Matrix went from 50/80 (62%) cells filled to 58/80 (72%). Meta, Google, Microsoft, Amazon now have full theme coverage. Remaining empty cells concentrated in Oracle, Wonder Valley, and parts of xAI/OpenAI — all are honest "no published commitment" gaps confirmed across multiple research passes (the gap itself is editorially valuable signal).
- **v1.4 — Draft banner.** Thin top strip ("Draft · Data collection in progress · Last refresh …") signals the dataset is under active curation. Test guards content + visibility.
- **v1.4 — QTS scope expansion (10th company).** First colocation operator added under the same two-gate editorial rule as Wonder Valley. QTS Cedar Rapids IA (Ratepayer Protection Pledge canonical site, $1.75B / 612 acres / 1.05 GW), QTS Richmond VA RIC5 (first-ever FAST-41-designated data center, 622 acres), QTS Dane County WI ($50M community commitment, 750 MW), QTS Manassas VA (Prince William Digital Gateway controversy). 7 new claims, 6 new community responses spanning Alliant CEO + Cedar Rapids Mayor + Iowa skeptical advocates + Henrico residents + Federal Permitting Council + American Battlefield Trust.
- **v1.4 — Three more 2026 sites.** Google Van Buren Township MI (1 GW, 282 acres, $10M Energy Impact Fund, contested MPSC docket), Microsoft Cheyenne WY 2026 expansion (3,200 acres tripling existing footprint), OpenAI Stargate Lordstown OH (former GM/Foxconn plant, $3B SoftBank). 10 new claims, 5 new community responses including the AG Nessel mixed welcome of Google's contested-case posture.
- **v1.4 — Meta + Amazon deep dive.** Refreshed metrics: Meta Newton investment $1B → $1.5B and jobs 200 → 400 (Dec 2025 info-sheet); AWS Loudoun investment $51.9B → $91.5B and jobs 7,340 → 20,700 (2024 update); Project Rainier flipped to operational (Oct 2025); AWS Cumberland power 960 → 1,920 MW (June 2025 restructured Talen PPA). Added 22 new claims and 19 new community responses including IDEM wetland citation, residential well failures near New Carlisle, FERC follow-up dockets, Sierra Club Virginia 2025 report, Meta Newton Mansfield 33% rate hike, Richland Parish housing displacement, and Crook County school tax-break analysis.
- **v1.4 — `Claim.published_at` field.** Optional Date for the source's own publication date (press release date, article date, FERC-order date), distinct from `captured_at` (curator scrape date). Frontend renders `published_at` when present. Merge script auto-extracts from URLs containing `/YYYY/MM/DD/` path segments.
- **v1.4 — `Project.at_a_glance` per-theme summary.** Optional dict field mapping theme → 1-line phrase. Surfaced in the project Overview tab's "At a glance" section. Auto-derived from project-tied claim metrics when no curator override is provided.
- **v1.3 — Comparison view restructured around company pop-outs.** Removed the global claims list + filter chip below the matrix. Click any company row (or populated cell) to open a per-company summary pop-out with: curated 1–2 paragraph framework summary, link to the company's official community/engagement page, claim + project counts, "View this company's projects →" CTA that pre-filters the Explorer view. Added optional `Company.summary` field to the schema and curated summaries for all 9 companies — including honest "no published framework" gaps for OpenAI / Anthropic / Oracle / Wonder Valley.
- **v1.2 — Matrix simplified to checkmarks-only.** Every populated cell now renders `✓`; the digit branch from v1.1 was removed because volume belongs in the claims list, not the at-a-glance matrix. aria-label still carries the precise count.
- **v1.2 — Project physical/operational metrics.** Added `acreage`, `power_mw`, `gpu_count`, `offtaker` fields to `Project`. Filled values for all 16 projects from canonical company pages + DCD/DCF/CNBC reporting. Frontend formatters auto-convert ≥1000 MW to GW.
- **v1.2 — Wonder Valley deep dive.** +2 O'Leary interview claims (energy-mix, China-race rationale), +4 community responses: Elevate Utah policy brief, BEAR co-leads Brenna Williams and Farrah Pliley, Utah ROOTS coalition. Total Wonder Valley records now: 5 claims + 8 community responses.
- **v1.1 — Project-detail tabs.** Overview / Claims / Community tab strip in the project pop-out, with count badges, in-session persistence, and reload reset.
- **v1.1 — Slim claim cards.** Tighter padding, smaller font, smaller curly quotes; compact variant inside detail panel.
- **v1.1 — Matrix checkmark glyph.** Single-claim cells render `✓`; multi-claim cells render the count.
- **v1.1 — Wonder Valley scope expansion.** First non-hyperscaler entity (O'Leary Digital, Box Elder County UT). Added wonder-valley to `COMPANY_SLUGS` + `CompanySlug` Literal + CSS palette + 3 project-tied claims + 4 community responses (Sierra Club, Utah Clean Energy, Box Elder Commission, Gov. Cox).
- **v1.1 — Data fill-in pass.** Claims grew from 25 → 93 (+68). Added project-specific claims (with `project_id` set) for all 15 hyperscaler projects + Wonder Valley, by web-scraping each project's canonical company page. Added company-level matrix-gap-fill claims for Meta jobs/infrastructure, Google jobs/engagement, Microsoft jobs/tax_revenue/infrastructure, Amazon education/engagement.
- **v1.1 — `Project.project_page_url`.** New optional schema field; renders in detail panel Overview as "Project page" link, distinct from "Record source".
