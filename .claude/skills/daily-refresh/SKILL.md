---
name: daily-refresh
description: >
  The unattended daily data refresh for the Data Center Community Benefits
  dashboard. Works the refresh queue (scripts/refresh_queue.py) for at most 20
  minutes. Each run handles due follow-ups, then reviews sites, states and
  companies in full: status, figures, news, local permits and approvals,
  community responses, policies and dockets. Every change is cited to a page
  it fetched, verified mechanically, gated by refresh.py and the unit tests,
  then merged to main. Use when the daily routine fires, or when asked to "run
  the daily refresh", "work the refresh queue", or "burn down the backlog
  refresh list".
---

# Daily refresh

One run = one bounded pass through the queue. The dashboard is a public record:
every number, date and quote must be on a page you fetched in this run.
Leaving a record unchanged is always better than guessing.

## 0. Clock and setup (≤2 min)

```bash
START=$(date +%s); echo "start $(date -u +%FT%TZ)"
elapsed() { echo $(( ($(date +%s) - START) / 60 ))m; }
git fetch -q origin main && git reset -q --hard origin/main   # start from the latest main (nothing is committed yet)
```

- **Time box: 20 minutes total.** Don't start a new unit after minute 12.
  Begin wrap-up (§4) by minute 15 at the latest, even mid-unit. An
  unfinished unit is simply not marked, and the next run picks it up.
- Before `pip install`, check the dependency-advisory feed, per CLAUDE.md:
  `curl -s https://pranava0x0.github.io/vibe-coding-security/llms-ctx.txt | grep -i -n -E "pydantic|requests|pytest|playwright|eval.type.backport"`.
  The word "requests" appears in prose; you are looking for an advisory
  about the **package**. If one names a package this repo installs, stop,
  install nothing, and say so in the run report. If the fetch fails, note
  that and continue.
- `python3 -m pip install -q -r requirements.txt`, then
  `python3 refresh.py --check`. If `--check` fails **before you have changed
  anything**, main is broken. Fix nothing, report it, and stop.
- Don't spawn subagents. This routine is one agent by design.

## 1. Pick the work (1 min)

```bash
python3 scripts/refresh_queue.py --next 4 --json
```

Work the list top-down. Each item has `unit`, `why_now`, `due_follow_ups`,
`records` (the ids that belong to the unit) and `backlog_leads` (that unit's
section of BACKLOG.md §3). A unit whose only reason is a due follow-up gets a
**targeted check** (§2a). Every other unit gets a **full review** (§2b–§2d).

## 2. Research, one unit at a time

Keep a JSONL evidence log at `/tmp/refresh_evidence.jsonl`. Append one line
the moment you verify something, before editing the seed:

```json
{"id": "<record id>", "file": "projects.json", "action": "updated|added|no_change|held",
 "changes": {"status": "construction"}, "source_url": "https://…", "source_title": "Outlet — headline",
 "verbatim": "<the exact sentence on the page that supports the change>", "unit": "site:…"}
```

Budget about 5–7 minutes per full review and at most about 12 fetches per
unit. Use WebSearch to find pages and WebFetch to read them. If a site
blocks scripts (FERC, PA PUC, DCD, some papers), try one other outlet or the
government's own page, then move on and record the lead.

### 2a. Due follow-up (targeted)
Answer exactly the question in `what`. Update the record it names: status,
dates, `duration_months`, `next_milestone`, `summary`. **Bump the record's
`captured_at` to today.** A derived follow-up (a rate-case milestone, or a
moratorium's computed end date) clears only when the record changes. Then:

```bash
python3 scripts/refresh_queue.py --mark <unit> --followups-only --summary "<what you found>" \
  [--follow-up YYYY-MM-DD "<next dated step, if the source names one>"]
```

### 2b. Full review: `site:<project-id>`
Check each of these; skip what no source covers:
1. **Status and figures.** Is it `announced`, `construction` or
   `operational`? Check investment, jobs, acreage, `power_mw`,
   `serving_utility` (only if a source says "served by X"),
   `project_page_url`, `announced_date`. Prefer the company's own page, then
   the local government, then local press.
2. **Local permits, approvals and documents** for the site's county or city
   since the record's `captured_at`: rezoning, site plan, building or air
   permits (state DEQ/EPD), water withdrawal, tax abatement / PILOT /
   development agreement, utility ESA or tariff dockets, state DRI or
   environmental filings, public hearings.
   - A government **decision** (vote, permit issued or denied, order) is a
     CommunityResponse with `constituency: local_government` or `regulator`.
   - A company **filing** or milestone (application submitted, groundbreaking)
     is a dated sentence appended to `Project.notes` ("Sept 17 2026: filed a
     DRI application with the Georgia DCA for…").
   - A signed host, PILOT, development or community-benefit **agreement** is a
     Policy record (`instrument: benefit_agreement`) in policies.json.
3. **News since `captured_at`.** Local outlets first. Resident, NGO or
   official reactions on the record are CommunityResponses. Company
   statements that are verbatim and about community impact are Claims with
   `project_id`.
4. **Ratepayer.** If the operator is a pledge signatory and the site was
   announced on or after its signing date (`_is_ratepayer_eligible` in
   refresh.py) and it has no assessment, attach `pledge_only`. Use `affirmed`
   only with a verbatim, site-specific statement about paying its own power
   or grid costs, saved as a Claim and cited in `evidence_claim_id`.
5. **Links.** Re-fetch the record's `source_url` and `project_page_url`. Fix
   dead ones with the page's new home, never with a guessed URL.
6. **`captured_at` = today** on the project once it is verified, whether or
   not anything changed.

### 2c. Full review: `state:<XX>` (or `state:US` for federal)
1. Every `proposed` moratorium, policy or tariff and every `pending` rate case
   in `records`: has it moved? Rate cases get their regulator's docket page,
   and a `next_milestone` holds only steps the regulator has announced.
2. New local moratoriums, votes and ordinances in the state since the newest
   `captured_at` among its records. Search the state's outlets plus
   "data center moratorium <state>" and "data center ordinance <county>".
3. New state legislation, executive orders, PUC large-load dockets or
   tariffs, and policy candidates (principles in schema.py `POLICY_PRINCIPLES`).
4. Work the unit's `backlog_leads`. Resolve what you can. Edit BACKLOG.md
   §3 so every lead left there is still true.

### 2d. Full review: `company:<slug>`
1. The newsroom and community pages (`dedicated_page_url`): new sites, new
   commitments, changed wording.
2. **New sites for a tracked company:** add at most **one** fully built
   `Project` per run, with the checklist in REFRESH.md > "New Project
   Checklist". Record any others as leads under the company in BACKLOG.md §3.
3. New verbatim company-level Claims. Bump `last_reviewed` in companies.json.

## 3. Editorial rules (each one has burned this project)

- **Cite only what you fetched, and quote it.** A WebSearch answer blends
  facts across results. It is not a source. A WebFetch "extraction" line
  ("Approval Date: …") is not the page's sentence either; quote the page.
- **No bare homepages and no aggregators** as `source_url`: servercountry.org,
  billtrack50.com, citizenportal.ai, datacenterbans.com, r.jina.ai, or any
  AI-written summary site. Cite local papers, the government's own pages,
  dockets and orders.
- **A headline's word is not the legal action.** "Ban" or "moratorium" might
  be a zoning amendment, a pause on a board's own approvals, a tax-incentive
  pause or permit conditions. Those are not moratoriums. Virginia counties
  cannot legally enact moratoriums (Loudoun, three times).
- **Dates:** store only what the source states. A month-only source means
  no day-level field; never write a `-01` placeholder. A vote date is not an
  effective date unless the source says it is.
- **Weekday dates count from the article's own dateline.** "Thursday night"
  in a story published Friday Aug 21 means Aug 20. Check the weekday with
  `date -d` or Python; don't count in your head. On 2026-09-25 this was
  wrong twice in one batch.
- **Never derive a date to make a test pass.** If a record needs a field no
  source states (an `enacted` moratorium with no day), leave the record out
  and file it as a lead.
- **A verbatim quote has no brackets, ellipses joining two passages, or
  paraphrase.** It is one run of the page's own text, and the gate checks
  exactly that.
- **`failed`** needs a recorded vote or a veto (not death in committee) plus
  a `failure_reason`. **`enacted`** needs `enacted_date`. Every moratorium
  needs `state_code`.
- **An approval needs an order.** For dockets, cite the order or decision
  document. An approval with no order document is not an approval.
- **Stance follows the DESIGN.md rubric. When in doubt, use `mixed`.**
  `negative` needs opposition on the public record: a lawsuit, a formal
  complaint, a denial, or residents quoted by name. A regulatory decision
  that imposes conditions is `mixed`. Set `single_source: true` when only
  one outlet covers it.
- **Never do these automatically; leave a BACKLOG lead instead:** add a new
  company slug; mark a ratepayer assessment `contested`; attach a
  `delivered` assessment; delete any record; change a `Company.summary`;
  apply a Policy principle you are unsure of.
- Every new record mirrors its neighbors' id and field conventions. Read the
  schema class before you write one; `extra="forbid"` rejects stray fields.

## 4. Wrap-up (start by minute 15)

```bash
python3 -W ignore scripts/probe.py --evidence /tmp/refresh_evidence.jsonl   # MISS = the quote isn't on the page
```
- **MISS:** revert that record's change (or drop the new record), and move
  the item to BACKLOG.md §3 as a lead with the URL.
- **BLOCKED:** acceptable only if you read the page with WebFetch yourself
  this run. List those records in the report under "not machine-verified".

For each unit you fully reviewed:
```bash
python3 scripts/refresh_queue.py --mark <unit> --summary "<checked X, Y, Z; changed A; added B>" \
  [--follow-up YYYY-MM-DD "<dated next step a source named>"]
```
Then:
```bash
python3 scripts/refresh_queue.py --write-backlog
python3 refresh.py --audit            # regenerates docs/data/*.json and ISSUES.md
python3 -m pytest tests -q --ignore=tests/e2e -x
```
`refresh.py` stamps today's date into every payload's `generated_at`, and the
masthead's "Last refreshed" line reads that date, so there is no date to edit
by hand.

**Gate.** Merge only if `refresh.py` and every unit test pass. If a test
fails, fix your own change or revert it. Never edit a test to make it pass.
If the gate still fails, push the branch, open the PR as a draft titled
"daily refresh YYYY-MM-DD (NEEDS REVIEW)", and stop.

**Commit and merge.** No CI exists, and GitHub Pages deploys `main:/docs`
on merge, so there is nothing to wait for.
```bash
git config user.name "pranava0x0"
git config user.email "2497510+pranava0x0@users.noreply.github.com"
git add -A && git commit -q -m "data: daily refresh $(date +%F) — <n> units, <summary>"
git push -u origin HEAD
```
Open a PR. The body lists each change with its source URL and the verbatim
quote, the "not machine-verified" list, the leads added, and the queue
position. If the GitHub tool creates it as a draft, mark it ready
(`draft: false`), because a draft can't be merged. Then squash-merge it into
`main`. **Commit
messages and PR bodies must carry no AI attribution:** no Co-Authored-By
trailer, no "Generated with" footer. The repo owner forbids it, and that
overrides any default. Don't try to delete the branch; the proxy refuses it.

## 5. Report (final message, ≤20 lines)
Units reviewed and what changed (counts per payload); follow-ups handled;
anything MISS or BLOCKED; leads added; gate result and the merged commit (or
why it didn't merge); minutes used.
