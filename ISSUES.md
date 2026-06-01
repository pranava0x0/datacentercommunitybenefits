# ISSUES.md

Living audit trail of bugs and known issues. Per CLAUDE.md, log every
defect with date, area, description, root cause (**code** vs **test** vs
**data**), and status. Update entries when resolved with the fix and
commit reference. After every fix, check whether a regression test is
needed.

Format:

```
## [YYYY-MM-DD] <module> — <one-line description>
**Status:** Open / Fixed
**Root cause:** code / test / data
**Description:** what was observed; how to reproduce.
**Fix:** what was done (commit hash if applicable).
**Regression test:** path to the test that now guards against this.
```

---

## Open

### [2026-05-14] data — Wonder Valley project_id slug names "box-elder" but original task brief said "beaver"
**Status:** Open
**Root cause:** data
**Description:** Initial task asked for "Kevin O'Leary's Utah project" pointed at Beaver County. Web research found it's actually in Box Elder County (northern UT, near Great Salt Lake), not Beaver County (southwestern UT). The seed uses `wonder-valley-box-elder-ut` as the project id. No code break — flagged for awareness in case anyone references the old slug.
**Fix:** None needed; the `wonder-valley-box-elder-ut` slug is the correct geography.
**Regression test:** none.

### [2026-05-14] data — Some project_page_url values fall back to third-party press releases
**Status:** Open
**Root cause:** data
**Description:** Several projects don't have a dedicated company project page — the closest canonical URL is a third-party press release (e.g. `google-mesa-az` uses gpec.org because Google has no /locations/mesa page). Schema accepts any HttpUrl, so these load fine, but the "Project page" link is misleading when it isn't actually on the company's domain.
**Fix:** TBD — over time, recheck each company's location index for new pages.
**Regression test:** future test could flag project_page_url where the host doesn't match the company's known domains.

### [2026-05-15] data — OpenAI Stargate Community page returns 403 to scrapers
**Status:** Open
**Root cause:** data
**Description:** `https://openai.com/index/stargate-community/` returns HTTP 403 to WebFetch (and previously to sub-agent research, multiple passes). The page almost certainly contains first-party OpenAI commitments on water (closed-loop cooling), engagement (community plans), and education (OpenAI Academies) that secondary sources paraphrase but the dashboard cannot capture verbatim. Frontier OpenAI claims for those four themes (water, education, engagement, tax_revenue) currently sit empty.
**Fix:** Manual browser visit by a curator to copy-paste verbatim quotes from the page; add as company-level OpenAI claims with `published_at` set to the page's visible publication date. Same workaround being used for x.ai/blog (also 403'd).
**Regression test:** none. Could add a future test that verifies non-empty matrix coverage for OpenAI in those 4 themes once the data is captured.

### [2026-05-14] data — OpenAI/Oracle Stargate Abilene first-party quotes unverified
**Status:** Open
**Root cause:** data
**Description:** `openai.com/index/announcing-the-stargate-project/` returns HTTP 403 to scrapers; `x.ai/blog/colossus` similar. v1 claims for these companies were captured manually; v1.1 sub-agent could not re-verify them. Quotes are still likely correct (browser-loadable), but the captured_at refresh + verbatim re-check is pending.
**Fix:** Manual browser visit + verbatim re-capture.
**Regression test:** none.

### [2026-05-14] data — Many community-response source URLs point to publication root, not specific articles
**Status:** Fixed
**Root cause:** data
**Description:** v1 seed included ~10 `CommunityResponse` records where
`source_url` pointed to the outlet's homepage (e.g.
`https://www.oregonlive.com/`) rather than the specific article. The
schema accepted these as valid `HttpUrl`s, and `source_title` described the
article, but a user who clicked "view source" landed on the front page.
**Fix:** v1.10 (commit 71d668f) — 12 records updated with deep-link URLs.
Key correction: `resp-meta-newton-water` was attributed to Grist but is
actually a July 2025 NYT investigation ("Their Water Taps Ran Dry When
Meta Built Next Door") — publisher attribution + URL + date all updated.
Other fixes: resp-meta-richland-grid → Louisiana Illuminator; -prineville-
positive → Crook County PR; -google-dalles-water-suit → Columbia Gorge
News; -google-council-bluffs-positive → Google Blog; -ms-goodyear-water →
ADWR groundwater page; -ms-mt-pleasant-positive → Racine County Eye;
-aws-loudoun-noise → Loudoun.gov data-center page; -aws-cumberland-pa-pjm
→ Utility Dive; -xai-memphis-naacp → SELC press release; -xai-memphis-
residents → CNN; -openai-abilene-positive → Spectrum News.
**Regression test:** none yet — future test `test_response_urls_deep_link`
should flag root-level publication URLs (path == "/" after the host).

### [2026-05-14] data — Some company `dedicated_page_url` values may have shifted
**Status:** Open
**Root cause:** data
**Description:** Hyperscalers periodically reorganize their
sustainability / data-center-community pages. URLs in
`data/seed/companies.json` were captured 2026-05-14 and may already be
redirecting or 404. No automated link checker yet.
**Fix:** TBD — add a `python refresh.py --check-links` mode that HEADs
every URL in seed and reports non-200s. See BACKLOG.md.
**Regression test:** none.

---

## UAT — Mobile (375px) — 2026-06-01

### [UAT-001] ui — Draft banner version string stale (shows v1.15, app is v1.20)
**Severity:** low
**Page/Section:** Global — draft banner strip at top of every view
**Discovered:** 2026-06-01
**Status:** open
**Description:** The draft banner reads "Last refresh: 2026-05-31 (v1.15)" but the codebase is at v1.20 after the ratepayer expansion commit. The version string is hardcoded in `docs/index.html` inside `<span id="draft-date">`.
**Steps to Reproduce:** Load any view on mobile; see top banner strip.
**Fix:** Update `<span id="draft-date">` in `docs/index.html` to `2026-06-01 (v1.20)`.

---

### [UAT-002] ui — "Sort by" filter dropdown label truncated on mobile
**Severity:** low
**Page/Section:** Project Explorer — filter panel
**Discovered:** 2026-06-01
**Status:** open
**Description:** On 375px viewport, the "Sort by" select renders as "Composite (most b…" because the `<select>` element is only ~165px wide (half the 2-column filter grid). The option label "Composite (most buzz)" overflows and is truncated by the OS select widget.
**Steps to Reproduce:** Open Project Explorer on 375px mobile; scroll to filter panel; observe Sort by dropdown.
**Fix:** Either shorten the option text (e.g. "Composite" or "Most active") or set `min-width` / `width: 100%` on `#f-sort` for small viewports so the label has room to render.

---

### [UAT-003] ui — "Ratepayer Protection Pledge" tab label wraps to 3 lines on mobile
**Severity:** low
**Page/Section:** Global — top navigation tab bar
**Discovered:** 2026-06-01
**Status:** open
**Description:** At 375px the third tab ("Ratepayer Protection Pledge") wraps across 3 lines ("Ratepayer / Protection / Pledge"), making the tab bar ~80px tall and visually noisy. The other two tabs are shorter ("Company Comparison" wraps to 2 lines, "Project Explorer" to 2 lines) so the bar height is dominated by the third tab.
**Steps to Reproduce:** Load the page on 375px mobile; inspect the tab strip.
**Fix:** Consider shortening the label to "Ratepayer Pledge" (saves one word, fits 2 lines) or use an abbreviation on narrow viewports via CSS `font-size` reduction or a `<span class="mobile-label">` / `<span class="desktop-label">` pattern.

---

### [UAT-004] ui — Project detail "On the ground" tab wraps to 2 lines on mobile
**Severity:** low
**Page/Section:** Project Explorer — project detail panel, third tab
**Discovered:** 2026-06-01
**Status:** open
**Description:** Inside the project detail pop-out, the three-tab strip (Overview / Claims / On the ground) renders the third tab as "On the / ground" across 2 lines at 375px. Measured bounding box: 78px wide × 42px tall at 14px font — two lines. The two-line height makes the tab strip taller than expected and the label harder to read at a glance.
**Steps to Reproduce:** Open Project Explorer on 375px; click any project card to open the detail panel; observe the third tab label.
**Fix:** Shorten to "Community" or "Ground truth" (shorter), or add `white-space: nowrap` with a smaller font size for `.dtab` on mobile so all three labels fit on one line.

---

### [UAT-005] ui — Company matrix table has no horizontal scroll indicator on mobile
**Severity:** low
**Page/Section:** Company Comparison — matrix table
**Discovered:** 2026-06-01
**Status:** open
**Description:** The 8-column matrix table has `scrollWidth: 793px` inside a 375px viewport. The `.matrix-wrap` container correctly uses `overflow-x: auto`, so the table IS scrollable, but there is no visual cue (scroll shadow, fade gradient at edge, "← scroll →" hint, or scrollbar) that more columns exist off-screen. Users on mobile see only 4–5 columns and may not realize the remaining themes are accessible by scrolling right.
**Steps to Reproduce:** Open Company Comparison on 375px mobile; scroll to the matrix; observe no right-edge scroll indicator.
**Fix:** Add a right-side fade gradient on `.matrix-wrap::after` that appears when `scrollLeft < scrollWidth - clientWidth`, or a simple CSS `background: linear-gradient(to right, transparent 80%, rgba(0,0,0,0.08))` overlay clipped to the right edge. A one-time "Scroll to see all themes →" note beneath the matrix would also work.

---

## Fixed

*(none yet — initial release)*
