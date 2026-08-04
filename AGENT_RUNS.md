# AGENT_RUNS.md — subagent/workflow retrospective log

> Append-only. One row per agent/workflow spawn (or tightly-related batch)
> where a retrospective is warranted — not every single-agent lookup, but
> every case where cost, quality, or a better alternative is worth a
> written record so the next session doesn't re-pay for the same mistake.
> See AGENTS.md § "Evaluate every agent run".

| Date | What was run | Tokens | Worked? | Best-ROI alternative in hindsight |
|------|--------------|--------|---------|-----------------------------------|
| 2026-07-14 | 4-agent parallel PR review (code-quality, silent-failure, energy/regulatory-domain, editorial/sourcing) on PR #33 (~940-line diff, mostly generated JSON already `refresh.py --check`-validated) | ~610K (122K + 157K + 188K + ~143K, one agent hit a session-limit failure partway through) | Partially — see detail below | 1-2 agents with tighter file/record scoping; see detail |
| 2026-07-14 | (Independent parallel session, merged in via reconciling PR #33 with main) 7-agent moratorium + ratepayer comprehensive pass — see "Detail: 2026-07-14 moratorium + ratepayer comprehensive pass" below | ~996K across 7 runs (~61K pure waste on one misfired relaunch) | Mostly yes | Cap fan-out at 2-3 not 5; model-select (Sonnet not Opus) for research agents; surface the running spend around ~500K instead of only at the end |
| 2026-07-15 | Full three-dimension data refresh: 6-agent wave (stale-bill re-checks + scouting), 6-agent wave (critical-gap fill, incl. 1 stalled-agent relaunch), 3-agent wave (citation audit + 2 verification checks), 10-agent wave (medium-gap fill) — see "Detail: 2026-07-15 refresh fan-out" below | ~2.3-2.5M (approximate — each of ~24 completed agents fell in the 83K-121K range; the AWS/Amazon medium-gap batch alone was split into 2 agents for 13 records) | Mostly yes, at a bad price | See detail — this is the **third** recorded instance of the 2-3-agent cap being violated in this file |
| 2026-07-25/26 | **Ratepayer Pledge v2 implementation (SPEC_RPP_V2 P0–P5) — zero agents spawned** | ~0 agent tokens (all inline) | Yes | Nothing; the no-agent call was right. See detail below |
| 2026-07-28 | **None — solo, deliberately.** IA restyle (accordions + sub-tabs), copy verification against a primary source, spec authoring | ~0 agent tokens; whole session in the main loop | Yes | Nothing. This is the shape that should stay solo — see detail below |

## Detail: 2026-07-15 refresh fan-out

**What happened:** a data-refresh request expanded into all four REFRESH.md
dimensions (stale bills, new scouting, critical gaps, medium gaps) plus a
citation audit and a UX pass, dispatched as four separate waves of parallel
agents rather than being scoped as 2-3 large batches per wave. The medium-gap
wave alone was 10 concurrent agents for 57 records — e.g. a single 13-record
AWS/Amazon batch got split into 2 agents ("AMZN-A" 7 records, "AMZN-B" 6
records) for no reason beyond "one email full of tasks, split it in half."
The user flagged this live, twice: once after a legitimate stalled-agent
relaunch got read as part of the same pattern, and again after the 10-agent
medium-gap wave landed — "why did you do it again? ... You have 2 agents for
AWS, huge waste." This despite AGENTS.md § "Multi-agent fan-out discipline"
already stating the 2-3 cap in bold, with two prior dated incidents in this
exact file.

**Was it worth it?** The research itself was genuine and largely well-done —
agents correctly declined to misattribute regional/statewide figures to
single sites, caught real citation errors (a project sourced to an unrelated
company's SEC filing, a superseded investment figure), and honestly reported
"not found" rather than guessing on the ~80% of fields that are genuinely
undisclosed. The *quality* of individual agent runs wasn't the problem — the
*count* was. Splitting AMZN-A/AMZN-B, or the 3-way Google medium-gap split,
paid the ~80-120K fixed per-agent overhead (system prompt, tool schemas,
framing) a second and third time for zero added research capability, on
fully-backgrounded work where the user wasn't waiting on wall-clock time.

**One improvement, concretely:** before dispatching a wave of >3 agents,
re-read this file's last entry and AGENTS.md § "Multi-agent fan-out
discipline" first — the rule already existed in writing twice; the miss was
not consulting it, not not knowing it. A mechanical trip-wire beats a prose
reminder: **if a single Agent tool_call block is about to contain more than
3 invocations, stop and consolidate batches before sending it**, the same
way `TaskStop`+relaunch is now the default response to a stalled (not just
slow) agent — checked via `stat`/`wc -l` on the transcript file's mtime/size
without reading its content, compared against sibling agents' actual
completion times, not a fixed timeout.

**What went right (keep doing):** legitimate stalled-agent recovery — the
original Meta critical-gap agent had zero transcript growth for 83 minutes
while 4 sibling agents in the same wave finished in 5-10 minutes each;
`TaskStop` + a tighter-capped relaunch was the correct call, not more
waste. Every agent this session also correctly flagged its own "not found"
results instead of fabricating a plausible-looking figure — the honesty
held up even under the volume problem.

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

## Detail: 2026-07-14 moratorium + ratepayer comprehensive pass

> From an independent parallel session (main PR #32), preserved here rather
> than in `docs/agent-runs.md` (that path was removed as part of reconciling
> PR #33 with main — `docs/` is the deployed GitHub Pages site, not a notes
> folder, so a retrospective log doesn't belong there; consolidated to this
> root-level file alongside the other project meta-docs).

| Run | What it did | Worked | Quality | ~tokens | Better in hindsight |
|-----|-------------|:------:|---------|--------:|---------------------|
| M1 state-moratoriums | Found 6 verified state records | y | good, honest gaps | 155K | `model: sonnet` (multi-source synthesis, not Opus) |
| M2 county-moratoriums | 13 county/township records | y | good; flagged `_evidence` strip + gov-source ratio | 153K | sonnet |
| M3 city-moratoriums | 14 city records + surfaced the Moratorium Nation CSV (222-row lead list) | y | high value (the CSV is the best lead source) | 170K | sonnet |
| R1 ratepayer-assess | Assessed 10 unassessed sites, flagged 2 for strict-bar review | y | high, self-caveated | 131K | sonnet |
| R2 conflicts+sites (attempt 1) | — | **n** | **0 tool uses, misfired** | 61K wasted | see note ↓ |
| R2 conflicts+sites (relaunch) | 5 conflict reports + 2 new sites | y | good | 161K | sonnet |
| Fill gaps (13 records) | bill#/gov-link/vote/language for the new records → 8 enriched (2 ordinance #s, 7 gov links, 2 sponsors) | y | high integrity: verified-only, dropped WebSearch-only details, honest dead-ends | 165K · 52 tool calls · 9.7 min | model:sonnet was right; but `≤2 fetches/record` scope limit NOT honored (52 calls ≈ 4/record) — a soft prompt cap doesn't bind |

**Session total: ~996K subagent tokens across 7 runs** (of which ~61K pure waste on the
R2 misfire). This is the "spend down a token budget out loud" lesson: the user
authorized "be comprehensive," but I never surfaced the running spend — should have
noted it crossing ~500K and offered a scope checkpoint.

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

### Fill-agent retrospective (the 4 questions, per AGENTS.md)

- **Reason** — agent justified? **Yes.** 13 records each needing a fetch + extraction
  from frequently-bot-walled county sites, with a verbatim-vs-paraphrase judgment call,
  is genuine multi-step research well past the 10-URL inline gate. Not a grep/one-liner.
- **Cost** — 165K tokens → 8 records enriched (~20K each) / 12 touched (~14K each).
  Under the ~40K-per-useful-result flag, so acceptable. But **52 tool calls for 13
  records is ~4/record — 2× the `≤2 fetches/record` scope limit I set.** A prompt-level
  cap is advisory, not enforced; the agent grinds when a field is findable-but-slow.
- **Result** — used downstream (8 records integrated), survived verification (I
  independently curl-checked all 7 gov links = 200), and the agent's honesty was the
  best part: it **dropped** unverified WebSearch-only attributions rather than ship them.
- **One improvement** — a cheap pre-flight would have right-sized the "fill bill #" goal:
  a 1-minute check that **local county/city moratoria rarely carry a formal bill number**
  (only 2 of 13 did) would have reframed the task as "gov link + vote + language, bill#
  where it exists" and set honest expectations up front. Folded into BACKLOG/ISSUES.

### What went right (keep doing)

- Every agent wrote JSON to disk and returned a short summary (no giant blobs in the
  orchestrator).
- Breadth-batched by tier (state / county / city), each with a "already tracked, skip"
  partition list → zero cross-agent duplicate records.
- Seeded the JSON contract with inline `python -c` inspection before spawning → no
  schema-retry loops on integration (only a `sponsors` string→list coercion + a
  Project `captured_at` field, both caught at validate time).
- Stripped agent-only `_evidence` fields and validated against `schema.py` at merge.


### Detail: 2026-07-25/26 Ratepayer Pledge v2 (P0–P5) — a deliberate no-agent session

**Nothing was delegated.** Six phases of a 381-line spec — schema work, a roster
importer, a sitewide re-theme, a new modal, an eligibility rewrite, ~90 new
tests — ran inline. The spec itself budgeted "1–2 Sonnet agents max" for the
research-shaped phases (P1 roster verification, P6 site sweep) and explicitly
said code phases run inline. That held.

**Why no agent was the right call for the research parts too.** P1's roster
looked like the classic fan-out task: 281 organizations to verify. It was one
`urllib` fetch of the White House page plus a 20-line regex — the roster is
clean server-rendered HTML with `data-cat` / `data-domain` attributes on every
row. **An agent would have re-derived by reading what a `re.findall` returns in
one call**, and would probably have paraphrased the names instead of copying
them. Cost: ~4 fetches + local parsing for the whole 302-record registry.

The same shape held in P0: the spec described "~471 lines of uncommitted seed
edits" needing reconciliation and implied a substantial merge. A single
`python3 -c` structural diff (id-set comparison across five payloads) collapsed
it to *six genuinely new records* in one call, because main was far behind the
branch. **A research agent pointed at "reconcile this diff" would have burned
six figures of tokens rediscovering that.**

**Where the tokens actually went:** reading existing code before editing it
(app.js is 5.3K lines and every change had to fit its conventions), and the
Playwright verification loop — screenshot, read, fix, re-shoot. That loop caught
things no test would have been written for: an em-dash accent rendering as a
gold rule, meter labels ellipsising to "New power su…", an `undefined` tariff
name, a bogus `XX` state chip. **Cheap and irreplaceable; keep it.**

**The rule this reinforces:** exhaust `curl` + `re` + `python3 -c` before
reaching for an agent. Three of this session's most expensive-looking subtasks
(reconcile the diff, import 281 signatories, backfill serving utilities) each
reduced to one local command plus a judgement call that a human-in-the-loop
reviewer — not an agent — had to make. The judgement was the *only* part that
couldn't be automated: 6 of 24 automated `serving_utility` candidates were
false positives, and no agent prompt would have reliably caught "a *former*
Duke Energy site" as not-a-serving-utility.


## Detail: 2026-07-28 accordion / sub-tab IA pass — zero agents, and that was right

**What the session did:** converted six tabs' ad-hoc section chrome onto one
heading language + one accordion component, removed two stale UI blocks, added
sub-tabs where sections were alternatives, verified the pledge copy against
whitehouse.gov, and wrote a per-signatory implementation spec.

**Agents/workflows spawned: none.** Worth logging *because* it's a null result —
this log's standing lesson is "exhaust `grep` + `python3 -c` before reaching for
an agent," and this session is the clean case for it. Every discovery step was a
targeted local command:

- `grep -n "accordion\|<details"` across three files found all three legacy
  disclosure skins in one call.
- `grep -rn "<constant>" docs/ tests/` before every deletion told me exactly
  which tests and call sites would break — this is what made removing two
  renderers safe.
- An 8-line `HTMLParser` well-formedness check caught unbalanced tags after each
  structural edit, instantly and for free. Much faster than a browser round-trip
  and it never gave a false pass.
- One `WebFetch` of the primary source settled the copy question that no amount
  of code-reading could.

**The one place a subagent would have paid:** nothing here. A parallel reviewer
over the final diff might have found the `<span>`-for-`<h3>` regression — but the
base CLAUDE.md's own "`<details>`-collapse trap" entry found it first, during the
learnings pass, at zero marginal cost. **Reading your own accumulated notes is
the cheapest reviewer you have**, and it beat the agent that wasn't spawned.

**Cost shape:** the expensive part of this session was not search, it was the
four full e2e suite runs (~110s each) after each structural change. That's the
right thing to spend on and shouldn't be optimized away — two of the four caught
real breakage (4 aggregate tests on the sub-tab conversion, and the pluralization
bug surfaced by a screenshot, not a test).

## 2026-08-03 — Data refresh + rate-case layer + IA v3 + civic palette

**Agents/workflows spawned: none.** The heavy lifting was research, and the
cheap tools carried it: WebFetch/WebSearch for discovery, the in-app browser
pane for bot-walled pages (DCD, ferc.gov article pages, nevadaappeal legal
notices — the pane loads what curl cannot), and an 18-line zlib/regex PDF text
extractor to verify two .gov orders (MO ET-2025-0184, IN Cause 46362) that the
fetch tool could only save as binary. One live-site `getComputedStyle` walk
settled the whitehouse.gov palette question that no amount of recall could.
Cost shape matched the 2026-07-28 entry: the expensive part was the two full
e2e runs (~102 s each), both of which caught real breakage (state-panel
section count, aggregate export coverage).
