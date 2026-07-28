# SPEC — Per-signatory deep-dive pages + work tracking

Status: **proposal, not built.** Written 2026-07-28. Companion to
[SPEC_RPP_V2.md](SPEC_RPP_V2.md), which introduced the signatory registry.

---

## 1. The ask, and the constraint it runs into

**Ask.** Every one of the 302 pledge signatories gets a deep-dive page, the
curation work per signatory is tracked, and the data-refresh playbook covers
each signatory rather than only the 13 companies we follow site by site.

**Constraint.** CLAUDE.md and `schema.Signatory` both state the two-tier design
deliberately:

> `Company` — depth. 13 slugs, each with curated claims, projects, a written
> summary. `Signatory` — breadth. Every roster row, carrying only what the
> roster publishes. […] we are not implying we have researched 279
> cooperatives because we listed them.

A "deep-dive page" for all 302 is exactly the thing that tier split exists to
prevent — **if the page implies research that has not happened.** 291 of the 302
rows currently carry nothing but name, category, domain, state, signing date,
and a source link. A page rendering those six fields under the heading
"Deep dive" is a lie told by layout.

**Resolution.** Build the page, but make *curation state a stored, first-class,
rendered fact*. A page for an unreviewed cooperative should say, above the
fold, that nobody has looked at it yet — the same honest-absence rule the
`delivered` and `ratepayer` blocks already follow. The page then becomes the
*instrument* for tracking the work (§4) rather than a claim that it is done.

### Current roster shape

| Category | Count | What we already hold beyond the roster row |
| --- | --- | --- |
| Cooperative | 176 | nothing |
| Utility | 68 | 20 of 25 tariffs join by `utility_aliases` |
| Developer | 28 | some map to tracked companies / sites |
| Governor | 23 | the whole existing state panel |
| Hyperscaler | 7 | full Company depth |
| **Total** | **302** | 11 bridge to a `Company` via `matched_company_slug` |

---

## 2. What a signatory page shows

**v1 introduces no new record type.** The page is a join over records already
collected for other views — the same discipline the state panel followed.

1. **Identity header** — name, category chip, signing track + date, domain link,
   state. All roster-published, all sourced.
2. **Curation banner** — §3. States what has and has not been checked. This is
   the first thing on the page for an unreviewed signatory.
3. **Their own commitment** — the first-party quote, when one has been captured
   (§3.2). Absent by default; absence is stated, not implied.
4. **Tariffs** — every `Tariff` whose `utility` matches this signatory's name or
   `utility_aliases`. Exact matches only; the existing hand-curated alias rule
   holds (AEP Ohio ≠ AEP Texas, and no fuzzy matcher is trusted to know that).
5. **Sites** — for a `matched_company_slug` row, that company's projects and
   their ratepayer assessments. For everyone else, empty and said so.
6. **State context** — a link into the existing `#state/XX` panel, plus, for
   governors, their state's records inline.
7. **Sources** — every URL the page rendered anything from.

Sections 4–6 render **even when empty**, following the state-panel rule: "AK /
MT / SD have a governor signature and nothing else; that *is* the answer and is
stated, not hidden."

### Routing

`#signatory/<id>` — a modal panel following the tariff / moratorium / state
pattern exactly: backdrop, Escape, focus trap, return-focus on close,
deep-linkable. Two gotchas the state panel already paid for:

- **Read the id from the hash BEFORE calling `activateView`** — it rewrites the
  hash, and reading afterwards yields a truncated string.
- **Lazy-load tariffs on open.** A visitor can deep-link here without ever
  opening the Tariffs tab, and a panel showing "no tariffs" because the payload
  had not loaded would be a lie.

Entry points: every roster row in `#rp-roster`, every utility name in the tariff
detail, the governor row in each state panel.

---

## 3. New schema

### 3.1 `Signatory.curation` — the work ledger

```python
SIGNATORY_CHECKS = (
    "domain_live",        # website_domain resolves (2xx/3xx)
    "commitment_page",    # located their own ratepayer / data-center page
    "first_party_quote",  # captured a verbatim commitment (see 3.2)
    "tariff_linked",      # joined to tariffs, OR confirmed none exist
    "sites_linked",       # joined to tracked projects, OR confirmed none
    "state_confirmed",    # HQ / service state verified against a source
)

class SignatoryCuration(_StrictBase):
    state: Literal["unreviewed", "in_progress", "reviewed"] = "unreviewed"
    checks: dict[str, bool] = {}       # keys validated against SIGNATORY_CHECKS
    last_reviewed: Optional[Date] = None
    notes: Optional[str] = None
```

Rules, mirroring the existing `delivered` / `ratepayer` blocks:

- **`unreviewed` is the default and is honest.** It means "nobody has looked",
  never "nothing to find". Do not auto-fill it.
- **A check may be `False` because we looked and there is nothing there.** That
  is a finding, not a gap — `tariff_linked: false` on a co-op with no tariff is
  *complete* work. `notes` carries the distinction; the UI reads
  `state == "reviewed"` for "we are done here", not the count of `true`s.
- **`reviewed` requires every key present**, true or false. Partial coverage is
  `in_progress`. A payload validator enforces this — otherwise `reviewed` drifts
  into meaning "somebody touched it".
- Vocabulary frozen; adding a check is a BACKLOG entry + migration + the JS
  mirror + a parity test, same drill as THEMES / DELIVERED_STATUSES.

### 3.2 `Signatory.commitment` — their own words

The blocker: a `Claim` requires a `company_slug`, and `CompanySlug` is a closed
13-value Literal. Three options:

| Option | Verdict |
| --- | --- |
| Expand `CompanySlug` to 302 | **No.** Explodes the closed vocabulary the whole comparison matrix depends on, and asserts depth we don't have. |
| Add `Claim.signatory_id`, exactly one of it or `company_slug` | Workable, but makes a required field conditional across ~340 existing claims and every consumer. |
| **`Signatory.commitment` sub-object** | **Recommended.** Additive, optional, no migration, cannot destabilize the matrix. |

```python
class SignatoryCommitment(_StrictBase):
    statement: str            # VERBATIM. The quote-don't-paraphrase rule holds.
    source_url: HttpUrl
    source_title: str
    published_at: Optional[Date] = None
    captured_at: Date
```

Same first-party bar as `Claim` (CLAUDE.md > "What counts as first-party"): the
organization's own page or filing, or a named executive quoted verbatim. A trade
article paraphrasing a co-op does not qualify. If a `Signatory` later earns
promotion to a full `Company` under the two-gate test, the commitment is the
seed of its first `Claim`.

### 3.3 Payload sizing

`signatories.json` is 121 KB raw / **8 KB gzipped** and loads at first paint.
Adding curation + commitment to all 302 rows is roughly +6–10 KB gzipped —
inside the 250 KB / 8-request budget but eating headroom that
`tests/test_perf_budget.py` exists to defend.

**Decision rule:** keep them in `signatories.json` while it stays under 15 KB
gzipped. Past that, split the detail fields into a lazy `signatory_details.json`
loaded on first panel open. Do not raise the ceiling — that is the standing
instruction when the budget test fails.

---

## 4. Tracking the work

### 4.1 Priority tiers — because 302 × manual research is not a plan

| Tier | Who | Count | Target | Why |
| --- | --- | --- | --- | --- |
| **A** | `matched_company_slug` rows | 11 | already deep | Nothing to do beyond backfilling `curation` as `reviewed`. |
| **B** | Utilities + developers | 96 | full 6-check review | They set the tariffs and build the sites — highest signal per hour. |
| **C** | Cooperatives | 176 | `domain_live` + `commitment_page` only | Individually low-signal; a full review each is months of work for little reader value. |
| **D** | Governors | 23 | `state_confirmed` + state panel | Mostly already covered by the state panel. |

Tier C's reduced target is a **stated scope decision, rendered on the page**
("cooperatives receive a lighter review — here is what that covers"), not a
silent cap. No silent truncation: if a tier is capped, the UI says so.

### 4.2 `refresh.py --audit` gains signatory gaps

`_audit_missing_commitments` currently covers projects. Extend `ISSUES.md`
generation with a signatory section, ordered by tier then by leverage:

- Tier B rows still `unreviewed` (high)
- Any signatory with a tariff join but no `commitment` captured (high — we have
  a regulated filing and no first-party words to set beside it)
- `domain_live: false` anywhere (medium — a dead domain may mean a merger,
  which is a roster event worth a curator's eyes)
- Tier C rows never checked at all (low)

The eligibility helper must be **derived, not hand-listed** — iterate the loaded
roster, exactly as `_signatory_dates` does. CLAUDE.md's single-source-of-truth
lesson was learned three times on hand-written lists that mirrored a registry;
do not add a fourth.

### 4.3 A progress meter, from data

The Ratepayer view's Coverage accordion gains a curation bar: reviewed /
in progress / unreviewed, per tier, computed from the roster. It renders the
true state, including "0% reviewed" on day one.
`test_landing_numbers_come_from_data_not_markup`
already forbids baking roster counts into `index.html`; the same rule applies here.

### 4.4 `scripts/audit_signatories.py`

Modeled on `validate_moratoriums.py`, whose split proved correct: **deterministic
link-liveness is automatable; claim verification is not.**

```
python scripts/audit_signatories.py --links-only        # domain_live for all 302
python scripts/audit_signatories.py --completeness      # schema-only, no network
python scripts/audit_signatories.py --tier B            # scope a work session
python scripts/audit_signatories.py --fail-on-dead-link # CI gate
```

`--links-only` may write `domain_live` back into the seed — it is a mechanical,
reproducible fact. **Every other check stays curator-set.** In particular, do
not let a script infer `commitment_page` from a URL pattern; that is how 55
fabricated `.gov` links got into the moratorium data.

---

## 5. Data-refresh skill coverage

Today `REFRESH.md` covers projects, moratoriums, and tariffs. The signatory
roster is refreshed wholesale by `scripts/build_signatories.py --diff`, and
nothing walks signatories individually.

**Add to REFRESH.md — "Signatory sweep":**

1. **Roster diff first.** `python scripts/build_signatories.py --cached --diff`.
   An unchanged page produces a byte-identical file, so any diff means the
   roster actually moved. The script never auto-deletes — a removal is news and
   needs a curator.
2. **Carry curation across a rebuild.** A regenerated seed must preserve
   `curation` and `commitment` by id. This is the one genuinely dangerous step
   in this spec: a naive rebuild silently discards every hour of curation work,
   and it would discard it *quietly*. Needs a merge step plus a test that
   asserts a rebuild over a curated seed preserves both blocks.
3. **Work the queue.** `--tier B`, take the top N from ISSUES.md, and for each:
   confirm domain, find their ratepayer/data-center page, capture a verbatim
   commitment if one exists, join tariffs, set the checks, stamp
   `last_reviewed`.
4. **Link sweep.** `--links-only` across all 302 each cycle; it is cheap and
   catches mergers.
5. **Never bulk-import.** Same rule the Moratorium Nation CSV earned: mine a
   list as a work-list, verify a live primary per row.

The **`data-refresh` skill** picks this up for free — it follows `REFRESH.md`
and updates it with what it learned. Two additions worth making explicit in the
skill, because they are where this work will go wrong:

- A live `source_url` is not a verified claim. Fetch the exact URL and confirm
  the commitment text is on that page. A search tool's synthesized answer
  aggregates across all results — this has already produced two bad records.
- Cap per-session scope. 302 signatories × several fetches each blows the
  10-URL-per-turn gate immediately. The tier queue exists so a session takes a
  bounded slice and says how much it left.

---

## 6. Phasing

| Phase | Scope | Rough size |
| --- | --- | --- |
| **P1** | `SignatoryCuration` + `SignatoryCommitment` schema, validators, rebuild-merge + its test, Tier A backfilled `reviewed` | 1 session |
| **P2** | `#signatory/<id>` panel, roster + tariff entry points, empty-state rendering | 1 session |
| **P3** | `audit_signatories.py`, ISSUES.md section, curation progress bar, REFRESH.md sweep | 1 session |
| **P4** | The curation itself: Tier B's 96, then Tier C's lighter pass | ongoing, many sessions |

P1–P3 are the tooling. **P4 is the actual work and does not end** — which is the
point of storing curation state rather than treating "we made pages" as done.

---

## 7. Tests

- `test_curation_vocabulary_frozen` — the 6 checks, Python ↔ `app.js` parity.
- `test_reviewed_requires_every_check_present` — blocks `reviewed` drifting into
  "somebody touched it".
- `test_rebuild_preserves_curation` — regenerate the seed over a curated fixture,
  assert `curation` and `commitment` survive by id. **The highest-value test
  here**; the failure it guards is silent and destroys manual work.
- `test_commitment_is_first_party` — every commitment carries `source_url` +
  `source_title` + `captured_at`.
- `test_signatory_panel_renders_empty_sections` — an unreviewed co-op renders
  every section with a stated absence, not a collapsed page.
- `test_unreviewed_signatory_says_so` — the curation banner is present and names
  the state; guards against a page that looks researched because it has a nice
  header.
- `tests/test_perf_budget.py` — unchanged, and it decides §3.3's split.

---

## 8. Decisions needed before P1

1. **Tier C's reduced target** — is a 2-check pass on 176 cooperatives the right
   call, or should they carry no curation record at all until something makes
   one of them interesting? (Recommendation: the light pass. `domain_live`
   catches mergers, which are real roster events.)
2. **Does a signatory page live at a URL or a modal?** This spec says modal, for
   consistency with every other detail panel here. A real per-signatory URL
   would be better for sharing and search, but it is a departure from the SPA's
   whole architecture.
3. **Promotion path** — when a signatory accumulates enough material, what
   triggers promoting it to a full `Company`? The existing two-gate test (≥1 GW
   announced + publishes its own community framing) still applies; worth stating
   that curation depth alone does not promote.
