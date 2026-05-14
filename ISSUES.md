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

### [2026-05-14] data — OpenAI/Oracle Stargate Abilene first-party quotes unverified
**Status:** Open
**Root cause:** data
**Description:** `openai.com/index/announcing-the-stargate-project/` returns HTTP 403 to scrapers; `x.ai/blog/colossus` similar. v1 claims for these companies were captured manually; v1.1 sub-agent could not re-verify them. Quotes are still likely correct (browser-loadable), but the captured_at refresh + verbatim re-check is pending.
**Fix:** Manual browser visit + verbatim re-capture.
**Regression test:** none.

### [2026-05-14] data — Many community-response source URLs point to publication root, not specific articles
**Status:** Open
**Root cause:** data
**Description:** v1 seed includes ~10 `CommunityResponse` records where
`source_url` points to the outlet's homepage (e.g.
`https://www.oregonlive.com/`) rather than the specific article. The
schema accepts these as valid `HttpUrl`s, and `source_title` describes the
article, but a user who clicks "view source" lands on the front page
instead of the cited piece.
**Fix:** TBD — curator needs to find the specific article URL for each
record and update `data/seed/responses.json`. Tracked in
[BACKLOG.md](BACKLOG.md) under "Source URL deep-links."
**Regression test:** none yet — should add a future test
`test_response_urls_deep_link` that flags root-level publication URLs
once the data is corrected.

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

## Fixed

*(none yet — initial release)*
