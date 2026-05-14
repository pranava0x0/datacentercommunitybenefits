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
