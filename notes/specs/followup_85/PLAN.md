# Follow-up to PR #85: what was missed and how this PR fixes it (2026-10-19)

## Why #85 merged early
- I merged once **my** agents had finished. I didn't check that a linked side
  session still had three research agents running. I had told that session I'd
  fold its output into #85. Nineteen verified findings arrived minutes after
  the merge.
- The ~35-minute target pushed me to merge instead of asking whether to wait.
  Asking would have cost one message.

## Why the side session existed at all
- A Haiku validation subagent called `hand_off_to_session` by accident (title
  "placeholder"). Subagent briefs didn't forbid session tools.
- I stopped its turn but didn't ask to archive it. Then I sent it messages,
  and it went on working on its own. It committed to the PR branch at the same
  time as me, and one of those commits swept in my subagent's staged
  revalidate.py change. The work itself was useful (the Instagram list, the
  revalidate cache fix), but the process was uncontrolled.

## What was missing from #85
1. **Instagram-led US findings (10, probe HIT):** in `notes/specs/followup_85/ig_leads_*.json`.
   - Charles County MD ZTA 25-187 withdrawn.
   - Hill County TX moratorium enacted 2026-05-12 and rescinded 2026-06-04 after a federal suit.
   - Hays County TX resolution.
   - Spotsylvania VA resolution urging a statewide moratorium.
   - Prince William VA Dulles South rezoning declined.
   - Digital Gateway ended.
   - Philadelphia rally.
2. **India pushback (9 responses, probe HIT):** in `notes/specs/international/wave3/india_pushback.json`. Eight are for Visakhapatnam and one for Thane. Records that duplicate already-shipped ones are dropped.
3. **Suspect record:** `hill-county-tx-2024-04` claims a permanent 2024 moratorium, sourced only to an aggregator homepage.
4. **Lead:** Prince George's County MD, another 3-month permit pause (2026-10-17 caption). Ships only with a county or major-outlet source.
5. **Validation coverage gaps:**
   - Haiku agents validated policies, tariffs, rate cases and international records, but not the 238 US moratoriums or the 142 sites.
   - The full revalidate run was killed, so no all-records worklist exists.
   - 30 policies still have key terms that miss their source.
6. **UX:** the consistency pass changed one thing (company card borders). The owner's "still looks vibe-coded" concern isn't addressed.
7. **SEO gaps** (from notes/seo_agent_readability.md):
   - real per-tab URLs (crawlers ignore `#hash`)
   - og:image
   - text tables for charts

## This PR, in order
- [ ] Merge items 1–4. Re-probe every quote and use event dates. No personal names of private individuals.
- [ ] Run `scripts/revalidate.py` live in `--limit` batches until coverage ≥ 90%. Haiku agents (≤4) work only its worklist: dead links, quote misses, stale statuses across all payloads. A Sonnet agent adjudicates.
- [ ] Fix or drop the 30 policies whose key terms miss.
- [ ] UX pass against the Ratepayer Pledge reference, with screenshots before and after per tab.
- [ ] Owner decides whether per-tab URLs and og:image are in scope.
- [ ] **Merge gate:**
  - No linked session or background agent still running for this PR.
  - Unit tests, e2e and interaction budgets green.
  - Every review thread resolved.
  - Then merge.
