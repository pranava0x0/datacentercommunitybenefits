# Agent-run scorecard

One row per subagent / workflow run. Purpose (per coding-best-practices
`AGENTS.md` → "Evaluate every agent run"): a retrospective kept only in a chat
reply is invisible to the next session, so the same mistake gets re-paid for.
Append here instead. Columns: run · what it did · worked? · quality · ~output
tokens · best-ROI alternative in hindsight.

## 2026-07-14 — moratorium + ratepayer comprehensive pass

| Run | What it did | Worked | Quality | ~tokens | Better in hindsight |
|-----|-------------|:------:|---------|--------:|---------------------|
| M1 state-moratoriums | Found 6 verified state records | y | good, honest gaps | 155K | `model: sonnet` (multi-source synthesis, not Opus) |
| M2 county-moratoriums | 13 county/township records | y | good; flagged `_evidence` strip + gov-source ratio | 153K | sonnet |
| M3 city-moratoriums | 14 city records + surfaced the Moratorium Nation CSV (222-row lead list) | y | high value (the CSV is the best lead source) | 170K | sonnet |
| R1 ratepayer-assess | Assessed 10 unassessed sites, flagged 2 for strict-bar review | y | high, self-caveated | 131K | sonnet |
| R2 conflicts+sites (attempt 1) | — | **n** | **0 tool uses, misfired** | 61K wasted | see note ↓ |
| R2 conflicts+sites (relaunch) | 5 conflict reports + 2 new sites | y | good | 161K | sonnet |
| Fill gaps (13 records) | bill#/gov-link/vote/language for the new records | y | Sonnet, scope-limited ≤2 fetches/rec | — | this is the model to copy |

### Lessons folded into AGENTS.md this session

1. **Cap concurrent fan-out at 2–3, not 5.** I launched 5 research agents at once;
   R2 came back with **0 tool uses** (a server-side hiccup that looks like a task
   failure) and had to be relaunched — the exact "wide burst → rate-limit → wasteful
   retry" tax `coding-best-practices/AGENTS.md` warns about. ~61K tokens burned for
   nothing. Two large breadth-batched agents would have been safer and as thorough.
2. **Model-select per agent.** All research agents inherited the main (Opus) model.
   Web-research synthesis is a **Sonnet** job (~cheaper, same quality here). Only the
   fill agent used `model: sonnet` — copy that.
3. **Keep this scorecard from turn 1, not at the end.** Started it only when the user
   pointed out I'd skipped the AGENTS.md discipline. The retrospective is required;
   persisting it here is what makes it useful next session.

### What went right (keep doing)

- Every agent wrote JSON to disk and returned a short summary (no giant blobs in the
  orchestrator).
- Breadth-batched by tier (state / county / city), each with a "already tracked, skip"
  partition list → zero cross-agent duplicate records.
- Seeded the JSON contract with inline `python -c` inspection before spawning → no
  schema-retry loops on integration (only a `sponsors` string→list coercion + a
  Project `captured_at` field, both caught at validate time).
- Stripped agent-only `_evidence` fields and validated against `schema.py` at merge.
