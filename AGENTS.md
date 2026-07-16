# AGENTS.md — How to work in this repo as an AI agent

> Companion to [CLAUDE.md](CLAUDE.md). CLAUDE.md is the *what* (project
> intent, architecture, editorial rules); this file is the *how* (concrete
> agent workflow inside this codebase). Synced from the `coding-best-practices`
> base AGENTS.md (2026-07-14) — universal sections below are adapted to this
> repo's actual commands/paths, not pasted generically. When this file
> conflicts with the base, this file wins; it's the local source of truth.

## Read these first, in order

1. **[CLAUDE.md](CLAUDE.md)** — universal principles + project-specific
   notes. The "Project intent" and "Editorial / sourcing rules" sections
   are load-bearing for every change.
2. **[DESIGN.md](DESIGN.md)** — design system + the editorial rubric for
   `stance` tagging. Touch this before changing community-response
   handling.
3. **[BACKLOG.md](BACKLOG.md)** — what's next. Pick from here, don't
   invent.
4. **[ISSUES.md](ISSUES.md)** — what's broken. Check before reporting a
   bug as new.
5. **[REFRESH.md](REFRESH.md)** — the data-refresh playbook (companies,
   projects, claims, moratoriums, tariffs). Read before any data-curation
   session; check its "Learned patterns" log first.

## The Explore → Plan → Code → Verify loop

This repo follows the loop CLAUDE.md describes. Concretely:

- **Explore.** Use `grep`, `find`, or the Explore agent to find relevant
  code. The codebase is small enough that a single read of `schema.py` +
  `docs/app.js` covers ~80% of the surface.
- **Plan.** For anything beyond a one-line fix, present 2–3 approaches
  with pros/cons before writing code. Editorial changes (theme taxonomy,
  stance rubric, what counts as a valid source, adding a company) ALWAYS
  need a plan surface — they reshape the dataset.
- **Code.** Edit existing files first; only create new files when the
  task genuinely requires it. No new helpers for one-shot operations.
- **Verify.** Run the test suite (see "Verifying changes" below) before
  declaring done.

**Research budget.** Web searches and multi-source fetches cost 20–50K
tokens and minutes of wall-clock; most questions about this repo are
answerable from the code in seconds. Work through this ladder before
going online — see "Token economy" below for the full escalation ladder
and this project's own documented failure patterns.

**Per-item cadence in multi-item sessions.** Surface design/editorial
questions up front (e.g. "does this qualify as first-party?"), then do
**validate + test + commit per record or per fix**, not batched at the
end. Catches schema drift early and produces a clean bisect history —
this is *why* seed JSON and `docs/data/*.json` move together in the same
commit (see "What NOT to do").

## Token economy — be judicious

This project is curated (small dataset, no auto-scrapers beyond the
`connectors/` research *accelerator* — see below) so most tasks are
achieved with direct file reads and targeted searches, not large-scale
agent dispatch.

### The escalation ladder — always start at step 1

Before spawning any sub-agent or starting a WebFetch loop, ask: "Can I
answer this with a one-liner?" Escalate only when the step above
genuinely can't answer the question.

1. **Python one-liner or grep on local seed files** — free, instant.
   Check what's already in the seed *before* going to the web.
   ```bash
   python3 -c "import json; d=json.load(open('data/seed/projects.json'))['projects']; [print(p['id']) for p in d if p['company_slug']=='google']"
   ```
2. **`Read` on a known file path** — free, no network.
3. **A single targeted WebFetch/WebSearch** on a specific URL or query you
   already know is relevant. WebSearch snippets usually carry every field
   you need for "search X and add it" — reach for WebFetch only for a
   field the snippet is missing, and cap it at one fetch per entity/claim.
4. **A sub-agent for multi-step research** — only when steps 1–3 can't do
   it: many URLs to fetch in parallel, cross-repo synthesis, or the
   question genuinely requires crawling unknown pages.

**Documented failure patterns (this repo):**

- A "find new sites to add" task that immediately spawned a
  general-purpose research agent without first checking what's already in
  the seed. That agent ran 59 tool calls and consumed ~92K tokens in
  seconds — most of it confirming absences that a python one-liner on the
  existing projects would have surfaced instantly. When the work does
  require a sub-agent, hand it the already-known-IDs list so it doesn't
  re-confirm what's already there.
- Using an Explore agent to audit "what export buttons exist per tab"
  when two `grep` commands in the main context had already surfaced the
  complete answer. Rule: if you just ran a grep and have the output in
  front of you, derive the answer from it — don't spawn an agent to
  re-derive it. The tell is a prompt like "based on the grep output
  above, also check X" — that's a Read or another grep, not an agent.

### Other token-economy habits

- **Inline before subagent.** A subagent costs ~5–40K tokens of overhead;
  don't spawn one for a bounded lookup. Spawn only for genuinely
  multi-file exploration or synthesis this repo's own tools can't do
  directly.
- **Model-select per subagent** when you have the choice: simple
  gathering (grep, schema validation) → cheapest tier; multi-source
  synthesis (web research across company newsrooms, gap analysis) →
  standard tier.
- **Every spawn prompt carries a scope limiter**: "report in under N
  words," "no more than N web searches," "read only the N most relevant
  files." Default Explore breadth to `"quick"`, not `"very thorough"`
  unless the task is genuinely broad.
- **Cap fan-out width to 2–3 concurrent agents without asking.** A wide
  burst (8-10+) triggers rate-limit errors that masquerade as failures.
- **Spend down a token budget out loud.** At ~50K tokens consumed in a
  single turn, pause and offer proceed / scope-down / abort — see
  CLAUDE.md's "Token gate at 50K" and "URL fetch gate at 10." Never
  silently burn a large budget; the user deserves the choice.
- **Read the slice, not the file.** `grep -n` + `offset`/`limit` over
  whole large seed files (`claims.json` is ~200KB) when you only need one
  record.
- **Check enum/ID constraints before writing.** Look up the live
  `THEMES` / `DELIVERED_STATUSES` / `RATEPAYER_STATUSES` /
  `TARIFF_PARAMETERS` set in `schema.py` first — an invalid value forces
  a fix-and-re-commit loop. Never guess enums from memory; several of
  these are frozen vocabularies that require a BACKLOG entry to extend.
- **Confirm work isn't already done before re-running.** After a context
  reset, check `git log` / `git status` / the seed files before
  re-spawning a refresh or research pass.

## Running research & multi-agent fan-outs

Applies to `connectors/research.py` sweeps and any ad-hoc "find new
announcements" pass (see REFRESH.md § "Finding New Announcements").
Reserve fan-outs for genuinely open-ended research — most single-company
lookups are a WebSearch or two, not an agent.

- **Size to the shelf.** Ask for exactly the N leads/records you can
  realistically curate this session, ranked by recency/confidence. Never
  "find as many as possible."
- **Pre-flight against local data before spawning.** Run
  `python -m connectors.research status --list` and grep the existing
  seed *before* commissioning a search — a lead may already be tracked
  under a different id (e.g. checking `"pecos"` / `"aurora"` /
  `"terawulf"` against `data/seed/projects.json` before assuming a
  headline is a new site).
- **Batch by breadth, not by unit.** One search covering several
  companies beats one search per company when the queries are similar
  ("data center announcement <company> <month> <year>").
- **Record exhausted/dead-end sources durably** — a source that 404s or a
  county with no formal bill-numbering convention is a real finding; log
  it (BACKLOG.md or a code comment in the connector) so a future session
  doesn't re-spend a search confirming the same absence.
- **Cap sources at 2 per claim/record** at collection time; deeper
  citation chains are a separate curation pass.
- **The final report states absences, not just hits**: what you found,
  what you couldn't verify, and what you deliberately left for a future
  session. A report that lists only successes hides coverage gaps —
  reflect this honestly in ISSUES.md/BACKLOG.md.
- **`connectors/research.py` never auto-publishes.** Output lands in
  `data/candidates/` (gitignored) for a curator to hand-review. Stance,
  constituency, and verbatim-quote selection stay editorial — see
  CLAUDE.md's "Editorial / sourcing rules." Don't let a connector or
  agent infer them.

## Evaluate every agent run

When a subagent/background task returns, do a 30-second retrospective
before consuming the result:

- **Reason**: was an agent right, or would 2–3 inline `grep`/Python calls
  have done it? (See the two documented failure patterns above.)
- **Cost**: flag anything over ~40K tokens per useful result.
- **Result**: used downstream or wasted? Did it survive verification
  (spot-check the "complete" list against a grep, confirm the result
  isn't empty)?
- **One improvement**: fold the lesson into REFRESH.md's "Learned
  patterns" section or this file — not just the chat reply. If the
  correction applies to the next run, it doesn't belong only in the
  transcript.
- **Detecting a stalled (not just slow) background agent**: check its
  transcript file's mtime and line count (`stat -f "%Sm" <file>`,
  `wc -l <file>`) — never `Read`/`cat` the full JSONL, it's the raw
  transcript and will overflow context. Compare against sibling agents
  from the same dispatch that have already completed: if a sibling
  finished in 5-10 minutes and this one shows zero growth for far
  longer, it's dead, not thorough. `TaskStop` it and relaunch with a
  tighter fetch cap rather than waiting indefinitely or leaving it
  running unattended.

**Persist the retrospective, don't just perform it.** This repo's `docs/`
is the deployed site (GitHub Pages), not a notes folder — keep the running
scorecard at **[AGENT_RUNS.md](AGENT_RUNS.md)** instead. Append one row per
agent/workflow run: what it did, worked (y/n), ~tokens, and the best-ROI
alternative in hindsight. A retrospective that only lives in the chat reply
is invisible to the next session and the same mistake gets re-paid for —
see the 2026-07-14 entry (4-agent PR review fan-out, ~509K tokens for a
~940-line diff) for exactly the failure mode this guards against.

**Default fan-out for a code review is 1-2 agents, not "one per lens."**
Combine correctness + domain-accuracy + editorial checks into a single
well-scoped prompt when the diff is small-to-medium; only split into
parallel agents when a lens genuinely needs a different model, different
tool access, or the diff is large enough that one agent's context would be
overwhelmed. Point each agent at exact files/record-ids instead of "read
the whole diff + CLAUDE.md + schema.py" — most of this diff's size was
generated JSON (already schema-validated by `refresh.py --check` and
`pytest`), not code that needed a fresh code-quality pass.

A solo turn with no spawn has nothing to evaluate. Say so rather than
invent analysis.

## Verifying changes

| Change kind                                          | Run                                                            |
| ------------------------------------------------------ | ---------------------------------------------------------- |
| Schema edit                                           | `pytest tests/test_schema.py`                                 |
| Seed data edit                                        | `python refresh.py --check && pytest tests/test_seed_data.py` |
| Theme vocab change                                    | `pytest tests/test_themes_match_frontend.py`                  |
| Frontend (`docs/app.js`, `index.html`, `styles.css`)   | `pytest tests/e2e/`                                            |
| Refresh / connector change                            | `pytest tests/test_refresh.py`                                 |
| Moratorium data edit                                  | `pytest tests/test_validate_moratoriums.py` (offline checks); `python scripts/validate_moratoriums.py --cached` for the source audit trail |
| Tariff data edit                                      | `pytest tests/test_tariffs.py`                                 |
| Anything substantial                                  | `pytest` (full suite, ~15s)                                    |

**Narrowest meaningful test first, then broaden.** Run the test closest
to the change for the fast loop; escalate to the full suite before
declaring anything substantial done.

**For UI changes**, also run the dashboard locally and click through the
affected tabs — type checking and tests verify code correctness, not
feature correctness.

```bash
cd docs && python -m http.server 8000
```

**Don't assume the port is free — probe before binding.** Multiple
worktrees of this project run concurrently; a stale `http.server` from
another session can silently squat 8000 (this has happened — a second,
unrelated `uvicorn` process answering on the same port produced a
confusing 404 that had nothing to do with this repo). If `curl -s -o
/dev/null -w "%{http_code}" http://127.0.0.1:8000/` doesn't return 200,
pick a different port rather than debugging the wrong server.

**The in-app browser/preview pane can render at a 0×0 viewport** and
`navigate` calls can be silently denied even though `preview_start`
reports success. The tell: a blank screenshot, or a `navigate` that
returns "denied or failed" on a URL that curls fine. That's the *pane*
broken, not the page. Fall back to headless Playwright self-serving the
built output (`python -m http.server` on `docs/` → `page.goto` → click
the tab → `page.screenshot`) — this repo's own `tests/e2e/conftest.py`
fixtures are the reference pattern for this.

**A selector inside a `[hidden]` container needs `state="attached"`**,
not the default `state="visible"` — see the existing note above about
the Community pane. `display:none` removes the element from the box
model, so a visibility wait times out even though the element exists.

**For data changes**, diff the canonical output (`docs/data/*.json`)
structurally before committing — a plain `git diff` on a minified JSON
file shows the whole line as changed for a one-byte edit, which is
useless. Parse both sides and diff dicts instead:
```bash
python3 -c "
import json
old = json.load(open('/tmp/old.json'))  # git show HEAD:docs/data/x.json > /tmp/old.json
new = json.load(open('docs/data/x.json'))
old.pop('generated_at', None); new.pop('generated_at', None)
print('identical aside from generated_at?', old == new)
"
```
A 30-second structural diff catches unintended content drift that a
line-based `git diff` on minified output hides.

**Spot-check source URLs by status** before committing externally-sourced
records: `curl -s -o /dev/null -w "%{http_code}" -L <url>`. Only commit
links confirmed live (200) — see CLAUDE.md's "Active links only" rule.
A 403 is inconclusive (bot-blocker, not necessarily dead); a 404/DNS
failure is actionable.

**A link-liveness check is not an accuracy check.** A 200 source can
still front a record whose central claim it doesn't actually support
(this is exactly what `scripts/validate_moratoriums.py` guards against
for moratorium bill numbers/sponsors/vote counts). When the source
contradicts the record, fix or drop the *record*, not just the link.

**Run a build/codegen script twice to assert idempotency.** `python
refresh.py` run twice in a row should produce byte-identical output
(aside from `generated_at`).

## Common tasks

### Adding a claim (most common)

1. Open `data/seed/claims.json`.
2. Append one record with: stable `id`, real `source_url`, verbatim
   `statement`, today's `captured_at`, and a `theme` from the canonical
   list in `schema.py`.
3. `python refresh.py` (validates + writes `docs/data/claims.json`).
4. `pytest tests/test_seed_data.py` to confirm.

### Adding a project + community responses

1. Add the project to `data/seed/projects.json`. Required: `id`,
   `company_slug`, `lat`, `lon`, `status`, `announced_year`, `source_url`.
2. Add 1–N community responses to `data/seed/responses.json`, each
   referencing `project_id`. Per [DESIGN.md](DESIGN.md), include both
   positive and negative voices when documented — single-source negative
   should set `single_source: true`.
3. `python refresh.py && pytest`.

### Adding a theme (RARE — requires migration)

This is a schema change. **Do not do this casually.** Steps:

1. File a [BACKLOG.md](BACKLOG.md) entry first.
2. Add to `THEMES` + `THEME_LABELS` in `schema.py`.
3. Mirror in `docs/app.js` (`THEMES` + `THEME_LABELS`).
4. Add a `--theme-<slug>` CSS var in both light and dark sections of
   `docs/styles.css`.
5. Re-tag existing claims that should map to the new theme (or
   intentionally leave them).
6. Run the full test suite — `test_themes_match_frontend.py` enforces
   parity. The same drift-safe pattern applies to `DELIVERED_STATUSES`,
   `RATEPAYER_STATUSES`, and `TARIFF_PARAMETERS` — each has its own
   parity test; check `schema.py` for the current frozen vocabularies
   before assuming a new value is safe to add inline.

### Running a data refresh (per REFRESH.md)

The `connectors/` research accelerator exists now (added, see
`connectors/README.md`) — v1's "curated, not scraped" principle still
holds; the accelerator finds and stages candidates, it never
auto-publishes.

1. `python -m connectors.research status --list` — find the gap list
   (projects with no claims / no community feedback).
2. `python -m connectors.research queries --missing-feedback --limit 5`
   — generate search queries, run with WebSearch/Chrome MCP.
3. `python -m connectors.research harvest --project <slug> <url>...` —
   stage candidates into `data/candidates/` (gitignored).
4. Hand-curate candidates into `data/seed/*.json`: pick the verbatim
   quote, write the neutral summary, set editorial fields yourself.
5. `python3 refresh.py --check`, then `python3 refresh.py --audit` to
   regenerate `docs/data/*.json` + `ISSUES.md` together.
6. Commit seed + `docs/data/*.json` + `ISSUES.md` in the same commit.
   Append a dated entry to REFRESH.md's "Learned patterns" section for
   anything that surprised you.

### Reviewing your own PR

Spawn independent reviewer agents with distinct lenses (correctness,
silent-failure/error-handling, editorial/sourcing) rather than
re-reading it yourself — author bias skips the same lines twice. Give
each the exact diff scope and "report findings, don't fix." Then
critically evaluate every finding before applying it — a suggested fix
can be wrong for this project's editorial context (e.g. a reviewer
proposing to auto-classify `stance` would violate the curator-only rule
below; the right move is to decline and document why, not apply it).

### Handling PR review comments

A PR in **"COMMENTED"** state means action required, not FYI. Fetch full
review bodies (not just the summary line), extract a checklist of each
distinct issue, and verify the specific flow each names.

### Multi-agent fan-out discipline (when a sub-agent is genuinely warranted)

**This rule has been violated three times now (2026-07-14 ×2, 2026-07-15) despite
being written down each time.** The miss was never not knowing the rule — it was
not re-reading this section or [AGENT_RUNS.md](AGENT_RUNS.md)'s last entry before
sending the dispatch. **Mechanical trip-wire: if a single tool-call message is
about to contain more than 3 `Agent` invocations, stop and consolidate batches
before sending it.** "One batch per company/topic, ~15-20 records each" beats
"one batch per sub-chunk of a company" every time on backgrounded work — see the
2026-07-15 entry in AGENT_RUNS.md for a concrete case (a single 13-record
AWS/Amazon lookup split into 2 agents for no research benefit, just because it
was easier to type as two prompts).

When a task truly needs research agents (comprehensive data expansion, cross-source
synthesis), keep the run cheap and clean:

- **Cap concurrent fan-out at 2–3, never a wide burst.** A 5+-wide parallel launch
  triggers server-side hiccups that look like task failures. **Caught July 2026:** a
  5-agent burst returned one agent with **0 tool uses** (misfired), forcing a
  relaunch — ~61K tokens burned for nothing. Prefer 2–3 large **breadth-batched**
  agents (one covers all states, one all counties, one all cities) over one-agent-
  per-item. Confirm an agent is truly dead (not just slow) before relaunching, or you
  pay for the same work twice. **Also caught July 2026 (separate incident):** a
  4-agent PR-review fan-out (one per review lens) cost ~610K tokens on a diff most of
  which was already schema-validated — see [AGENT_RUNS.md](AGENT_RUNS.md) for the
  full retrospective. Default a code review to 1-2 combined-lens agents instead of
  one per lens.
- **Model-select every spawn.** Simple gathering (grep/list/schema) → cheapest tier.
  Web-research synthesis → standard tier. Reserve the inherited top-tier model for
  genuinely open-ended judgement. **Caught July 2026:** all research agents inherited
  the main-loop's top-tier model when a cheaper tier was the right fit for the task —
  same quality, far cheaper.
- **Every spawn prompt carries a scope limiter + writes to disk.** "≤2 fetches per
  record, skip a field after 2 tries"; write JSON to the scratchpad and return only
  path + count + 2–3 surprises (<120 words). Never let an agent return a giant JSON
  blob — it bloats the orchestrator and isn't auditable. Note: a soft prompt-level cap
  is advisory, not enforced — one fill agent given "≤2 fetches/record" still averaged
  ~4/record when a field was findable-but-slow. Size the batch expecting some overrun,
  and pre-flight the premise so the agent isn't chasing a field that mostly doesn't
  exist (e.g., local county/city moratoria rarely carry a formal bill number).
- **Seed the JSON contract inline first**, hand each agent an "already tracked, skip"
  partition list, and strip agent-only fields (`_evidence`) + validate against
  `schema.py` at merge.
- **Log every run in [AGENT_RUNS.md](AGENT_RUNS.md)** — one row: what it did,
  worked?, quality, ~tokens, better-in-hindsight. A retrospective kept only in the
  reply is invisible next session; that's how the same mistake gets re-paid for.
- **Spend the running total down out loud, not just at the end.** A comprehensive
  multi-agent pass that crosses ~500K tokens without a checkpoint has already made
  the user's choice for them — surface the spend and offer to scope down *while it's
  still running*, not in the post-hoc retrospective.

### Never spawn a deep-research agent for

- Adding a single new project or claim (do it directly).
- Checking if a project is already in the seed (run a python one-liner).
- Fixing a CSS/JS bug (read the file, edit it).
- Any task solvable with grep + Read + a short Bash command.

## What NOT to do

- **Don't paraphrase company claims into the `statement` field.** Quote
  verbatim. Tests catch obvious markers like "they claim that".
- **Don't add a record without a real `source_url`.** Schema rejects it,
  and reviewers will reject it harder.
- **Don't try to LLM-classify community-response stance, delivered
  status, or ratepayer assessment.** These are the most adversarial
  editorial calls in the project; a wrong tag undermines the whole
  frame. Curator-only.
- **Don't aggregate to a "trust score" or "greenwashing index."** Show
  the data; let users judge. See CLAUDE.md > "Editorial / sourcing rules".
- **Don't write UI copy in the AI register.** Headings, empty states,
  and tab labels avoid model tells (*delve / leverage / seamless /
  robust*, "it's worth noting that"). Plain, specific, human.
- **Don't introduce a new framework.** Vanilla JS + Pydantic + Playwright
  is the whole stack. Adding React / Vue / Svelte / build tooling
  contradicts the static-first principle and adds maintenance debt.
- **Don't touch `docs/data/*.json` directly.** Edit `data/seed/*.json` and
  re-run `refresh.py`.
- **Don't push `connectors/research.py` output straight into
  `data/seed/`.** It's a candidate, staged in `data/candidates/`, until a
  human picks the quote and sets the editorial fields.
- **Don't expand scope inside a fix.** A bug fix doesn't need surrounding
  cleanup; a one-shot operation doesn't need a helper.
- **Don't loosen invariants quietly.** If a rule has a test guarding it
  (frozen theme vocab, four-status `delivered`, three-status `ratepayer`,
  the eight ratepayer-pledge signatories), that test exists because
  someone got burned. Read CLAUDE.md's rationale before relaxing it.
- **Don't `--no-verify` to bypass a hook.** Fix the underlying issue.
- **Don't trust `git add` on a gitignored output dir.** `data/candidates/`
  is gitignored by design (it's scratch); don't force-add its contents
  into a commit.
- **Don't treat an empty result as a failure (or a failure as empty).**
  A legitimately empty collection (a company with no `contested`
  ratepayer sites yet) renders as an explicit "none" state in the UI;
  an extraction/parse failure is a bug to log in ISSUES.md. Conflating
  them hides coverage gaps.
- **Don't invent history for a missing file.** If a referenced doc isn't
  there, don't fabricate prior entries — create it only when the task
  calls for it.
- **Don't suggest `pip install` / `npm install` without checking the
  advisory feed first.** See CLAUDE.md > "Security & Credential Handling"
  — fetch <https://pranava0x0.github.io/vibe-coding-security/llms-ctx.txt>
  (~12 KB) and scan for the package name before recommending the install
  or editing `requirements.txt` / `package.json`. If a match is found,
  surface the warning + advisory link before proceeding. In this repo the
  trigger surfaces are `requirements.txt`, `playwright install`, and any
  future `connectors/` deps — re-check the feed whenever those touch a
  new package.
- **Don't add a `Co-Authored-By:` / machine-fingerprint line to commits
  in this repo.** `claude.coauthor` is set to `false` in this repo's git
  config — honor it. *(Flagged 2026-07-14: an earlier commit this
  session — `b14a91c` — added one anyway, before this file was synced to
  surface the config. Left as-is pending the user's call on whether to
  amend; see chat.)*

## Repo norms

- Type hints on every Python function.
- No `print()` for runtime output — use the `logging` module.
- Test alongside code, not after.
- Commit at natural checkpoints: per-feature, per-bug-fix, per-doc-update.
- Never commit `docs/data/*.json` and seed JSON in separate commits — they
  must move together so a future bisect doesn't land on a broken state.
- **Touch targets ≥ 44px on touch** — gate on `@media (pointer: coarse)`
  so desktop inline controls (tab strip, filter dropdowns) don't bloat.
- **Mobile first.** If you change UI, resize the preview to 375×812 and
  verify before declaring done — this project has a documented mobile
  `pp-row` overlap regression already (fixed in `8ad5269`); don't
  reintroduce that class of bug.
- **No API keys in code, ever.** This project currently has none (fully
  static, no backend) — if a future connector needs one, read from an
  environment variable and halt with a clear error if missing.
- **`toLocaleDateString('sv')` gives a clean local-timezone `YYYY-MM-DD`
  string** if you ever need one client-side; `new Date().toISOString().
  slice(0,10)` is always UTC, which can show tomorrow's date near
  midnight in a US timezone.
- **Delete a feature branch (local + remote) right after a successful
  merge. Don't ask.** The merge is the signal it's done. Exception:
  don't auto-delete if the merge had to be reverted.

## Escalate to a human when…

- The editorial frame would change (e.g. adding a 9th theme, changing the
  stance rubric, adding a non-named company, adding a 5th `delivered` or
  4th `ratepayer` status).
- A community response is contested and you're unsure of the stance tag.
- A company source page goes 404 / paywalls — pause and ask before
  switching to a less-canonical source. See CLAUDE.md's "News-source
  diversity" rule for negative-stance projects specifically.
- Schema fields would change in a way that cross-cuts seed + frontend +
  tests + connectors.
- A scar-tissue note in this file or CLAUDE.md seems wrong for the
  current task — the notes exist because someone hit the issue; verify
  the rationale doesn't apply before relaxing the rule.

## Cross-project hygiene

This repo lives in `.claude/worktrees/` alongside sibling worktrees of
the same project, and the user runs many other small projects in
parallel on the same machine.

- **Stay within this project's scope.** Don't open files from a sibling
  project or worktree unless explicitly asked.
- **Check `git worktree list` before assuming you're the only active
  session** — a sibling worktree may already have committed the change
  you're about to make (this happened: a `tab-order-moratorium-bills-*`
  worktree finished the tab-reorder + PDF-export fix this worktree was
  also set up to do; the fix was to fast-forward-merge, not redo it).
- **This project's tests are independent of sibling projects'.** Don't
  infer test status across repos.

## When something unexpected happens

Add a concise note to CLAUDE.md, this file, or REFRESH.md's "Learned
patterns" section (whichever is closer to the surprise). The pattern:

1. **What I expected:** one sentence.
2. **What happened:** one sentence.
3. **Why:** one sentence (root cause, not symptom).
4. **What to do next time:** one sentence (the actionable lesson).

That growth — files getting slightly more specific with each session's
surprises — is the asset. Don't rewrite from scratch; append.

### Known harness quirks

- **The security-reminder PreToolUse hook blocks an edit *once per
  rule*, then allows it.** It substring-matches danger patterns
  (`innerHTML` assignment, dynamic-code eval, shell-out calls, …)
  anywhere in the new text — including in prose/comments that merely
  *name* the pattern. On the first hit it exits 2 (edit does NOT apply)
  but the key is saved *before* it blocks, so the identical edit
  succeeds on retry. If you hit this: confirm the code is actually safe,
  then re-issue the same edit unchanged — don't contort the code to
  dodge a substring match.
