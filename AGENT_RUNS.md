# AGENT_RUNS.md — subagent/workflow retrospective log

> Append-only. One row per agent/workflow spawn (or tightly-related batch)
> where a retrospective is warranted — not every single-agent lookup, but
> every case where cost, quality, or a better alternative is worth a
> written record so the next session doesn't re-pay for the same mistake.
> See AGENTS.md § "Evaluate every agent run".

| Date | What was run | Tokens | Worked? | Best-ROI alternative in hindsight |
|------|--------------|--------|---------|-----------------------------------|
| 2026-07-14 | 4-agent parallel PR review (code-quality, silent-failure, energy/regulatory-domain, editorial/sourcing) on PR #33 (~940-line diff, mostly generated JSON already `refresh.py --check`-validated) | ~610K (122K + 157K + 188K + ~143K, one agent hit a session-limit failure partway through) | Partially — see detail below | 1-2 agents with tighter file/record scoping; see detail |

## Detail: 2026-07-14 4-agent PR review

**What happened:** asked to review "from multiple domain and coding expert
perspectives," spawned 4 concurrent full-context agents without a scope
limiter. Each re-read the diff + CLAUDE.md + schema.py from scratch. User
flagged the token spend live, before the agents even finished, as "an
insane number of tokens." One agent (silent-failure) hit a session API
limit mid-run and returned only a partial finding, which was cheap to
finish by hand (one grep + one Python one-liner) instead of resuming it.

**Was it worth it?** Genuinely mixed, not a clean "yes" or "no":
- **Real value**: the editorial and domain-expert passes caught ~12
  confirmed, actionable defects that would otherwise have shipped —
  two records citing sources that didn't support (one *contradicted*) the
  claims they'd been updated with, two fabricated-sounding statistics
  traced to WebSearch cross-result synthesis rather than the cited
  article, a mid-sentence quote truncation, a lease commitment booked as
  capex breaking the company-rollup pattern, an uncritically-amplified
  "nation's first" press-release claim the dataset's own data
  contradicted, and an inconsistent application of the ratepayer
  "met"-vs-"partial" precedent. These are the kind of errors that don't
  show up in `pytest` or `refresh.py --check` — they're domain/editorial
  judgment calls, exactly what this review type is for.
- **Real waste**: the code-quality and silent-failure passes covered
  ground that was already proven by `refresh.py --check` + the 326-test
  suite + manual `curl` liveness checks done inline during the original
  session — re-verifying "does docs/data match the seed" from scratch
  cost ~122-157K tokens for a check that `git diff` + a byte-comparison
  script does for near-zero. And 4 agents each re-loading CLAUDE.md +
  schema.py + the full diff is redundant overhead that 1-2 combined
  agents wouldn't have paid.

**Best-ROI alternative in hindsight:** one agent for code-quality +
silent-failure combined (they overlap heavily and the diff's actual code
surface — schema.py, app.js, index.html, one test file — is small), one
agent for domain+editorial combined but scoped to *only* the new/changed
record IDs (not "read CLAUDE.md in full, read schema.py in full, read
every seed file") with an explicit instruction to skip re-verifying
anything the session already confirmed inline (source-URL liveness, schema
validation, byte-identical docs/data regen). That's a ~2-agent, tightly-
scoped shape instead of 4 broad ones — probably 150-250K tokens total for
comparable finding quality, not 610K.
