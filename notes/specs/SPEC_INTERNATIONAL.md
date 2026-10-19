# Spec: International component (v6 proposal, 2026-10-19)

> Status: **plan only, nothing built.** Inputs: `notes/specs/international/`
> (`synthesis.md`, `europe.json`, `apac.json`, `americas_mea_global.json`). Haiku agents did the
> research through a summarizing fetch. **No fact in this spec has been checked
> against a primary source.** Every candidate record in §5 is a lead until
> Phase 0 fetches it. CLAUDE.md's v1.19 rule (a live link is not a verified
> claim) applies twice over once translation is involved.

## 1. Goal, non-goals, editorial frame

### Why

CLAUDE.md has listed "Non-US data centers" as out of scope since v1. The
reason was that US sites have richer public records. That still holds. But
the owner now wants the blueprint to answer a question the US data cannot:
**what have other countries required of data centers, and what happened?**
The research found the answers abroad are mostly *solutions*: entry
conditions on new load (Ireland's renewable-matching rule, Singapore's
green-energy bid condition, Johor's reclaimed-water rule), developer-pays
connection rules (Australia's federal proposal, Hydro-Québec's dedicated
rate), and mandatory or negotiated heat reuse (Germany's EnEfG, Amsterdam,
Odense, Narvik). Those belong in the blueprint.

### Goal

A bounded, curated international layer with these properties:

1. It reuses the existing record types (`Policy`, `Moratorium`, `Tariff`,
   `RateCase`, `Project`, `CommunityResponse`, `Claim`) with a real
   jurisdiction model (ISO 3166-1 / 3166-2), so an Irish grid rule and a
   Texas tariff are the same *kind* of record.
2. It ships in its own lazy payload and its own tab. No US view, stat or test
   changes behavior.
3. Each country gets a page (the state-panel analog) showing what the country
   requires, which pauses and allocation schemes it runs, what electricity
   proceedings are open, which sites are contested, and which EU-level rules
   apply.
4. It links to the US Local Policy Frameworks principles, so a reader looking
   at "Data centers pay their own grid costs" can see how that principle is
   done abroad.

### Non-goals (wave 1)

- **No international pledge, signatory or ratepayer scorecard.** No
  multi-company signed pledge exists outside the US. Singapore DC-CFA2, UK AI
  Growth Zones and the C40 mayors' pact become `Policy` records. `Signatory`
  stays US-only and The Pledge tab is labelled as US.
- **No cross-country scores, rankings or "most progressive country"
  index.** This is the same rule as "don't aggregate to a trust score".
- **No currency conversion stored in data and no cross-currency sums.**
- **No connectors in wave 1.** Everything is curated, as US v1 was.
- **No new Company records.** The two-gate test does not change. Untracked
  operators (Goodman, NextDC, Keppel, Equinix, Nscale) appear as
  `operator_name` / `counterparties` strings, the same way the Signatory
  "thin tier" works.
- **No 9th THEME and no heat-reuse principle in wave 1.** Wave 1 has no
  heat-reuse records, so the decision moves to wave 2 (§9, OQ-7).
- **No bulk import** from any foreign list. This follows the lesson of the
  poisoned 2026-07 moratorium batch.

### Editorial frame

- **Blueprint first.** Country pages lead with the instruments: what a
  government asks of data centers. Community response comes second, as case
  evidence. Critical records (Aragon, Batam, Querétaro) are kept, not
  softened.
- **Quote as published, in the language it was published in.** A
  translation is always labelled with who made it. The original is always
  shown and is authoritative. A machine translation is never presented as a
  quote (§3.6).
- **Honest absence.** A country with one record shows one record and says
  so. A country-page section with nothing in it renders the sentence
  "Nothing recorded yet." It is never hidden. The tab dek states the country
  list and does not imply global coverage.
- **Headline is not action.** The research already contains four traps:
  - Ireland "moratorium" was really a regulator connection policy.
  - Singapore "moratorium" was an administrative freeze.
  - Johor "ban" was a tier-based approval halt.
  - Chile "revokes permit" was a court-ordered re-assessment.

  The Loudoun rule applies: find the jurisdiction's own statement before
  using the headline's word (§4).

## 2. Information architecture: options

The rule that decides it (IA v4): *before adding a tab, name the one
question only it answers.* Here: "What have other countries required of data
centers, and how did it go?" No current tab answers it. Every current tab
answers a US question.

### Option A: a country dimension on every existing tab

International records go into `policies.json`, `moratoriums.json` and the
other existing payloads. Each tab gains a country filter.

- **Pros:** an Irish rule sits right next to its US analog. There is one
  directory per record type.
- **Cons:**
  - `docs/app.js` reads `p.state` / `.state_code` in about 50 places, and
    `STATE_NAMES`, the 50-state strip, `#state/XX`, "By state" and the
    tariff "States covered" tally all assume a US state. Every one would
    need a country guard.
  - US stat tiles and Home totals would mix countries unless every counter
    is filtered. That is the "11 signatories" drift risk, multiplied.
  - Every existing lazy payload grows.
  - Tariffs and rate cases are defined around US PUC semantics.
  - The daily queue mixes units.
- **Blast radius:** most of app.js plus 30–40 e2e tests. Rejected.

### Option B: one new tab, its own payload (recommended)

`#world`, label **"International"** (short phone label "World"), placed
**last**, after Sites. Sub-tab group `intl`:

| Sub-tab | Hash | Holds |
|---|---|---|
| Countries (default) | `#world` | One card per country, with record counts in words and the curator's one-line "what's distinctive here". The card opens the country page. |
| Instruments | `#world/instruments` | Every international policy, pause, allocation round, tariff and proceeding in one directory, grouped by `POLICY_PRINCIPLES` (the blueprint axis), with filters for country, instrument and status. |
| Sites | `#world/sites` | International projects and their community responses and timelines. List only in wave 1, no map. |

The **country page** (`#country/IE`) is a panel *inside* `#view-world`.
Putting it there avoids the trap documented for the state modal ("an
invisible modal when another view is active").

- **Pros:**
  - Zero behavior change to US views.
  - One lazy fetch.
  - A clean partition: US payloads reject non-US records and the reverse.
  - The perf budget is untouched.
  - The tab answers its own question.
- **Cons:**
  - It is a 9th tab. On phones the bar already wraps with short labels, but
    interaction cost must be re-measured.
  - International instruments sit apart from their US analogs. Mitigation:
    principle cross-links in both directions (§6.4).
  - Some rendering duplication. Mitigation: reuse the existing card, badge,
    `.acc`, sub-tab and modal components; no new component styles.

### Option C: country pages only, no tab

`#country/XX` panels opened from a Home card and from principle cards.

- **Pros:** no 9th tab.
- **Cons:**
  - There is nowhere to browse "what rules exist abroad?" across countries.
  - Content behind a modal is invisible to Ctrl-F and to the DOM-walking PDF
    export.
  - The panel would need a host view, which brings back the state-modal
    trap.
  - The panel has no URL-addressable list.

### Recommendation

**Option B, with C's country page built in.** The tab-count discipline is
met because the question is distinct. Phone cost gets new UAT budgets
(§8.4). One more thing changes: The Pledge's hero dek and the masthead dek
say "US". OQ-1 asks whether the site title changes.

## 3. Data model

### 3.1 Storage and partition

- **New seed file `data/seed/international.json`**, mirrored to
  `docs/data/international.json`. Payload model:

```python
class InternationalPayload(_StrictBase):
    countries: list[Country]
    policies: list[Policy] = []
    moratoriums: list[Moratorium] = []
    tariffs: list[Tariff] = []
    rate_cases: list[RateCase] = []
    projects: list[Project] = []
    responses: list[CommunityResponse] = []
    claims: list[Claim] = []
```

  It is one file, not per type, because wave 1 is about 30 records and a
  country page needs all of them at once. Split rule: once the gzipped file
  passes 40 KB (`test_international_payload_size`), split it into
  `data/intl/<CC>.json` plus a small index. That split is a deliberate
  migration, not a default.
- **The same Pydantic models, not subclasses.** Subclasses would give each
  field two definitions that drift apart, and the JS sees the same shape
  either way. Each model gains the jurisdiction fields below, and a
  `model_validator` branches on `country`.
- **Partition validators:**
  - every US payload (`ProjectsPayload`, `PoliciesPayload`, …) gains
    `_us_only`, which requires `country == "US"`;
  - `InternationalPayload` gains `_non_us_only`, which requires
    `country != "US"`;
  - the one exception is `Policy` with `scope == "supranational"`
    (`country == "EU"`).

  The partition is what keeps every US code path's invariants safe: a null
  `state` can never reach the 50 `p.state` call sites.
- `refresh.py` `PAYLOAD_FILES` gains `"international": InternationalPayload`.
  Cross-reference checks span payloads:
  - `Claim.company_slug` and `Project.company_slug` resolve against
    `companies.json`;
  - `related_project_ids`, `project_id` and `related_tariff_id` inside the
    international payload must resolve **within** it;
  - `transposes` and `amends` (§3.8) resolve against international policies.
- **Backward compatibility:** all new fields default to US-equivalent values
  (`country="US"`, `subdivision=None`, `statement_lang="en"`), so all 134
  projects, 124 moratoriums and the rest validate unchanged with no data
  migration. Four fields go from *required* to *Optional + validator*. US
  payloads re-tighten them through `_us_only`, so the effective US contract
  is unchanged:
  - `Project.state`
  - `Project.company_slug`
  - `Tariff.state`
  - `RateCase.state_code`

### 3.2 Jurisdiction model

Two registries in `schema.py`. Both are mirrored in app.js and
parity-tested. They are dicts, not `Literal`s, because adding a country is
an editorial act and not a vocabulary migration:

```python
# ISO 3166-1 alpha-2 → English short name. "US" included so the field has one domain.
COUNTRIES: dict[str, str] = {"US": "United States", "IE": "Ireland", "CA": "Canada",
                             "SG": "Singapore", "AU": "Australia", "MY": "Malaysia"}
# ISO 3166-1 "exceptionally reserved" code; supranational policies only.
SUPRANATIONAL: dict[str, str] = {"EU": "European Union"}
EU_MEMBERS: tuple[str, ...] = (...27 ISO2 codes...)   # single source for applies_to
# ISO 3166-2 codes actually used → name. Not the full standard: only what records cite.
SUBDIVISIONS: dict[str, str] = {"CA-QC": "Québec", "AU-NSW": "New South Wales",
                                "MY-01": "Johor", "IE-D": "Dublin"}
# What a first-level subdivision is called, for labels ("Provincial", "State").
SUBDIVISION_TERMS: dict[str, str] = {"CA": "province", "AU": "state", "MY": "state"}
```

New fields:

| Field | On | Type | Rule |
|---|---|---|---|
| `country` | Policy, Moratorium, Tariff, RateCase, Claim (Project already has it) | `str = "US"` | must be in `COUNTRIES`, or in `SUPRANATIONAL` when `Policy.scope == "supranational"` |
| `subdivision` | same, plus Project | `Optional[str]` | regex `^[A-Z]{2}-[A-Z0-9]{1,3}$`, prefix must equal `country + "-"`, must be in `SUBDIVISIONS`. Must be null when `country == "US"` (US keeps `state`/`state_code`; no `US-TX` backfill, no churn) |
| `locality` | Policy, Moratorium, Project | `Optional[str]` | free text for a council or municipality ("Lane Cove Council", "Dublin City Council"). `jurisdiction` stays the display name |

Jurisdiction level, widened rather than renamed:

- `Moratorium.jurisdiction_type` gains `"national"`.
- `Policy.scope` gains `"national"` and `"supranational"`.
- `TariffJurisdictionLevel` (shared by Tariff and RateCase) gains
  `"national"`.

Validators:

- `federal` requires `country == "US"`. `federal` already means "the US
  federal government" in `isFederalTariff()`, the moratorium stats and
  `_build_coverage`. Reusing it for Canada or Australia would leak foreign
  records into those code paths, so it stays US-only.
- `national` or `supranational` requires `country != "US"`.
- Non-US `state` / `county` / `city` levels require `subdivision`, except in
  countries with no first-level subdivision in use (`SG`). A
  `NO_SUBDIVISION_COUNTRIES = ("SG",)` constant marks those.
- The existing US rules (`state_code` required for US state, county and city
  records, and `federal ⇒ "US"` for rate cases) are unchanged and now run
  only when `country == "US"`.
- `state`, `county` and `city` render with the country's term, e.g. "State
  (Johor)" or "Provincial (Québec)", through `SUBDIVISION_TERMS`. The stored
  value is not localized.

### 3.3 `Country` record (new)

```python
class RegulatorRef(_StrictBase):
    name: str; acronym: Optional[str]; role: Literal["energy_regulator", "grid_operator",
        "planning", "environment", "investment_agency"]; url: HttpUrl

class ContextFact(_StrictBase):          # a sourced number, e.g. Ireland's 23% metered share
    statement: str                        # curator English sentence
    verbatim: str                         # the source's own words (source language)
    source_lang: str = "en"
    period: Optional[str]; source_url: HttpUrl; source_title: str; captured_at: Date

class Country(_StrictBase):
    code: str                             # key of COUNTRIES (or SUPRANATIONAL for "EU")
    summary: str                          # 2–4 neutral sentences; first sentence = card line
    regulators: list[RegulatorRef] = []
    primary_languages: list[str]          # BCP-47; drives the refresh routine's translation gate
    context: list[ContextFact] = []
    last_reviewed: Date
```

`summary` is curated meta-commentary, the same as `Company.summary`. **Don't
template it from the records.** The model has no score, rating or "status"
field.

### 3.4 Currency

- New sub-model:

  ```python
  class Money(_StrictBase):
      amount: float
      currency: str
      as_stated: str
  ```

  `currency` must be in a `CURRENCIES` registry (ISO 4217: USD, EUR, CAD,
  SGD, AUD, MYR, GBP, mirrored in app.js). `as_stated` is the figure exactly
  as the source printed it ("A$7bn", "Rs 83,000 crore").
- New fields: `Project.claimed_investment: Optional[Money]` and
  `Policy.value: Optional[Money]`.
- Validator: non-US records must leave `claimed_investment_usd` /
  `value_usd` **null** and use `Money`. US records are unchanged, and
  `Money` is null for them.
- When one source gives two figures (Google Visakhapatnam: $15bn in the
  headline, about $10bn / Rs 83,000 crore for the agreement), store the one
  the instrument states, and put the conflict in `notes`. Never average or
  pick the larger.
- **FX policy:**
  - Wave 1 shows the original currency only ("CA$0.13/kWh", "A$7bn").
  - Nothing is summed across currencies. The Home and Instruments totals
    count records, not money.
  - If the owner wants a reference conversion later (OQ-4), it would come
    from a generated `fx_reference.json` of **annual-average** rates from
    one named public source (Federal Reserve H.10). It would render as
    "≈ US$X (year average, H.10)" and be **display-only**. It would never
    be stored on a record and never feed a total.

### 3.5 Units

- `power_mw` stays in megawatts.
- New `Project.import_capacity_mva: Optional[float]` for capacity a source
  states in MVA (Ireland's connection tiers: <1, 1–10 and >10 MVA). **MVA is
  never converted to MW**, because the power factor isn't published. The
  formatter shows "MVA".
- Water: `Metric.unit` is already a free string. Allow `"litres/day"` /
  `"litres/year"` and do not convert to gallons. The Companies depth grid
  keys on the presence of a metric, not its unit, so it is unaffected.

### 3.6 Language and translation

The rule: **the field that is documented as verbatim keeps the original.**
This is why `Claim.statement` keeps its meaning ("verbatim quote", now in
the source's language) instead of a new `statement_original` field. Moving
English into `statement` would quietly redefine the field for every US
record.

```python
TRANSLATION_SOURCES = ("official", "human", "machine")   # Literal + labels, parity-tested
class Translation(_StrictBase):
    text: str                     # for key_terms: see TranslatedTerms
    by: TranslationSource
    official_url: Optional[HttpUrl]   # required when by == "official"
    translator: Optional[str]         # required when by == "human"
    reviewed_at: Date
```

- `Claim`: add `statement_lang: str = "en"` (BCP-47, must be in a
  `LANGUAGES` registry: en, fr, de, nl, es, ms…) and
  `statement_translation: Optional[Translation]`. **Required when
  `statement_lang != "en"`**, forbidden when it is `"en"`.
- `Policy`: add `source_lang: str = "en"`. When it isn't `"en"`, `key_terms`
  stay in the original (they must be literally on `source_url`) and the new
  field `key_terms_translation: Optional[TranslatedTerms]`
  (`items: list[str]`, `by`, `reviewed_at`) is required, with the same
  length as `key_terms` (`_key_terms_translation_parallel`).
- `Moratorium`, `Tariff`, `RateCase`, `Project` and `CommunityResponse` get
  `source_lang` for display ("Source in French"). Their `summary` / `notes`
  fields are curator English prose and are never quotes, so they need no
  translation.
- **What each value means, and the labels:**
  - `official`: the publisher's own English version, e.g. Hydro-Québec's
    English press release. Here, prefer to *quote the English page* with
    `lang = "en"`, and keep the French original as a `resources` link.
    `official` is for the rare case where the French text is what must be
    quoted (the docket) and an official English rendering exists.
  - `human`: a named person translated it. Label: "English translation by
    <name>".
  - `machine`: **any LLM or MT output, including Claude's.** Label: "Machine
    translation (AI). The original above is authoritative." The run that
    produces a `machine` translation is still a curator act and must be
    reviewed before merge. But it is labelled as what it is. There is no
    unlabelled path.
- **UI:** the original renders first in a `<blockquote lang="fr">` (correct
  for screen-reader pronunciation and hyphenation). The labelled translation
  follows. Sorting and search see both.

### 3.7 Instrument vocabulary

The frozen-vocab migration rule applies: each addition needs a BACKLOG
entry, the Python tuple + `Literal` + labels, the JS mirror, the parity
test, and a review of existing records. Each candidate was weighed against
existing values:

| Candidate | Decision | Reason |
|---|---|---|
| **`government_framework`** (new `POLICY_INSTRUMENTS` value) | **Add.** Label "Government framework / programme" | Singapore DC-CFA / DC-CFA2, NSW Data Centre Policy Framework, UK AI Growth Zones and Singapore's Green Data Centre Roadmap are published, non-statutory government schemes. Filing them as `regulation` claims legal force they lack, and `executive_order` is wrong. US records reviewed in the migration: grep `policies.json` for "framework", "program", "strategy". Any US state strategy filed as `legislation` is re-checked. |
| Allocation round (MW per operator) | **No new type or sub-model** | `government_framework` + `counterparties` (the four awardees) + `key_terms` ("50 MW each", "more than 50 per cent … green energy") holds it, literal on source. Add a structured `allocations` list only if a second country runs rounds. |
| Grid-connection policy (CRU, Île-de-France) | **Use `regulation`** + principle `new_power` / `pay_own_way` | A regulator decision has legal force, so `regulation` is accurate. A TSO's queue practice with no decision document is not a record (see §4). |
| Designation scheme (AI Growth Zones, Aragon PIGA) | covered by `government_framework` | |
| Subsidy regime (Brazil Redata) | **Use `legislation`** + `incentive_terms` | Already how US incentive strings are filed. Forgone revenue is never `value`. |
| Court ruling (Chile, Uruguay) | **Use `SiteUpdate.kind = "lawsuit"`** on the Project | Both are site-specific. A standalone ruling type waits for a non-site ruling. |
| Reporting mandate (EED Art. 12, EnEfG PUE) | **Use `legislation` / `regulation`** + `transparency` | Fits as is. |
| **`Moratorium.formality`** (new frozen vocab `MORATORIUM_FORMALITIES = ("formal", "administrative", "de_facto")`, default `"formal"`) | **Add** | Singapore 2019–22 and Johor's tier halt are real pauses without a statute. `administrative` = an authority's announced decision (Johor). `de_facto` = no published decision, described by the authority after the fact (Singapore). The UI badge reads "Administrative pause" or "Unofficial pause". This is the Loudoun lesson expressed in the schema: the record says what kind of thing it is. **A `de_facto` record needs the authority's own statement *or* two independent sources** (`_de_facto_needs_corroboration`: `resources` ≥ 1 on top of `source_url`). All US records default to `formal`, so there is no migration. |
| **`Moratorium.lifted_date`** (Optional[Date]) | **Add** | Singapore's pause ended in 2022. It is useful in the US too (expired moratoriums), and is the curated end date CLAUDE.md said Home's "Coming up" was waiting for. Validator: requires `status == "enacted"`, and must be ≥ `enacted_date`. |
| 10th principle `heat_reuse` | **Defer to wave 2** (OQ-7) | No wave-1 record needs it. When NL/DE/DK land, compare it against `community_benefits` + theme `energy`. |

### 3.8 Supranational instruments

- An EU directive is **one** `Policy` with `scope = "supranational"`,
  `country = "EU"`, and
  `applies_to: Optional[list[str]]`. That list is validated as a subset of
  `EU_MEMBERS`, and `None` means all members. A country page shows it under
  "EU rules that apply here". There are no 27 copies.
- `transposes: Optional[str]` links a national act to the supranational
  record it implements (EnEfG to EED). The cross-ref must exist and must be
  `supranational`.
- `amends: Optional[str]` links an amendment to its parent (the June 2026
  EnEfG draft to EnEfG). It must exist and have the same `country`.
- The Instruments pane folds a lineage into one row with "1 amendment
  proposed".

### 3.9 Untracked operators

- `Project.company_slug` becomes `Optional` (US payload re-requires it).
- Add `operator_name: Optional[str]`. Validator: one of `company_slug` /
  `operator_name` is required. `operator_name` is required when
  `company_slug` is null.
- Set `company_slug` when a tracked company is a named party, either as
  operator or as anchor tenant. That matches `oracle-abilene-tx`.
  `offtaker` keeps its meaning. Example: Stargate Australia would be
  `company_slug` null, `operator_name` "NextDC", `offtaker` "OpenAI"…
  **unless** OpenAI is a named party in the source. Decide per record and
  write the reason in `notes`.
- `site_id` prefix for untracked operators: `<operator>-<city>` in
  kebab-case (`goodman-lane-cove-au`).
- The Equinix / Digital Realty "out of scope" line stays. They appear as
  `counterparties` on DC-CFA2. OQ-2.

### 3.10 Parity tests to add

New tests in `tests/test_international.py` and the existing parity files.
Every test derives from the registry; no hand-written lists:

- `test_countries_match_frontend` (`COUNTRIES` ↔ `COUNTRY_NAMES` keys and
  values)
- `test_subdivisions_match_frontend`
- `test_subdivision_terms_match_frontend`
- `test_supranational_match_frontend`
- `test_currencies_match_frontend`
- `test_languages_match_frontend`
- `test_translation_sources_match` + `_labels_match`
- `test_moratorium_formalities_match` + `_labels_match`, plus a
  `MORATORIUM_FORMALITY_BADGE_CLASS` **value** check against styles.css (the
  `RATE_CASE_BADGE_CLASS` lesson: check values, not just keys)
- `test_policy_instruments_match` (existing, in test_policies.py) picks up
  `government_framework` without edits. Add a `government_framework` badge
  value check.
- `test_jurisdiction_levels_match` for the widened `Moratorium` /
  `Policy.scope` / `TariffJurisdictionLevel` vocabularies, which app.js
  needs for labels.
- `test_eu_members_match_frontend`, if the JS renders "applies to".

## 4. Sourcing and verification rules (international)

All existing rules apply (first-party definition, verbatim quotes, fetch the
exact `source_url`, no homepage citations, event date ≠ publication date).
New rules:

1. **Primary-source ladder.** Each wave-1 record type has a named primary,
   tried first:

   | Source type | Where to look |
   |---|---|
   | Statute | Irish Statute Book; legislation.nsw.gov.au; Federal Register of Legislation (AU); Singapore Statutes Online; Gazette officielle du Québec; EUR-Lex |
   | Regulator decision | CRU decisions page; Régie de l'énergie docket (`regie-energie.qc.ca/.../dossiers/R-XXXX-YYYY`) |
   | Programme | EDB / IMDA media releases and fact-sheet PDFs; NSW Planning / DCCEEW pages |
   | Planning | NSW Planning Portal SSD application page |
   | State government | Johor state government or exco statement |

   A law-firm note or trade outlet goes in `resources`. It is the
   `source_url` only when no primary is reachable, and then the summary says
   "as reported by".
2. **Headline vs action, made concrete.** Before writing `Moratorium`, find
   the authority's own words for what it did. When the instrument is a
   condition on connection, it is a `Policy` (`regulation`), not a
   `Moratorium`. Ireland's case is the template: the CRU decision is a
   connection policy. The 2021–2025 constraint is described inside it, not
   filed as a ban.
3. **Gazette numbers are fetched, never taken from search.** Quebec "Decree
   89-2026" and Brazil "Law 15.504/2026" came from search synthesis. The
   Georgia docket 44280 lesson applies: open the gazette entry before
   storing the number.
4. **Translation discipline:**
   - verbatim and `key_terms` are in the source language;
   - translations are labelled (§3.6);
   - **a quote is never re-translated back into "the original"**;
   - when an official English version exists from the same body, cite and
     quote it.
5. **Number conflicts inside one source** (Visakhapatnam $15bn vs $10bn;
   Singapore capacity figures) are recorded as conflicts in `notes`, or the
   figure is left null.
6. **"Fetched by an agent" is not verified.** Every research quote passed
   through a summarizing fetch. Phase 0 re-fetches every `source_url`
   directly.

### `scripts/probe.py --evidence` changes

Current behavior: `norm()` folds curly quotes, dashes, NBSP and whitespace,
then `.lower()`. It sends `Accept-Language: en-US`. Clause split uses
`MIN_CLAUSE = 12`.

- **Unicode normalization:** apply `unicodedata.normalize("NFC", …)` to both
  sides. Without it, a decomposed "é" on the page won't match a composed one
  in evidence. Use `casefold()` instead of `lower()` (German ß).
- **French typography** in `NORMALIZE`: « » → `"`, U+202F (narrow NBSP
  before `; : ! ?`) → space, U+2019 is already handled. Also collapse the
  space French puts before `:;!?`, which the existing punctuation rule
  doesn't cover.
- **Per-row `lang`:** evidence rows gain an optional `"lang"`. The fetcher
  sends `Accept-Language: <lang>,<lang-base>;q=0.9`. This stops a bilingual
  site (hydroquebec.com, regie-energie.qc.ca) from content-negotiating to
  the English page while the quote is French. It also stops the reverse.
- **The translation is never probed.** The gate checks `verbatim` against
  the page in the source language. The `--evidence` check rejects a row
  whose `verbatim` equals its own `translation` when `lang != "en"`.
- **PDF text in non-ASCII encodings:** the Tj/TJ pull can return mojibake on
  French PDFs with custom font encodings. Add a status, `UNREADABLE`, for a
  page that fetched (200) but has under 5% alphabetic characters in the
  target script. It is handled like BLOCKED: a manual WebFetch read, listed
  as not machine-verified. Without it, those rows would show up as false
  MISSes.
- **CJK** (deferred to whichever wave adds JP/KR/TW): split clauses on 。、
  and set `MIN_CLAUSE` per script (≈6 for CJK). Not built in wave 1. Test
  stub `test_cjk_clause_split_xfail`.
- Tests in `tests/test_probe.py`:
  - `test_nfc_normalization_matches`
  - `test_french_guillemets_and_nnbsp`
  - `test_accept_language_follows_row_lang`
  - `test_unreadable_pdf_is_not_a_miss`
  - `test_translation_is_not_evidence`

## 5. First wave

### 5.1 Jurisdictions

**Ireland, Canada (Québec), Singapore, Australia (NSW + federal proposals),
plus the EU layer** (it applies to Ireland), with **Malaysia (Johor)** as a
two-record stretch.

The choice exercises every model change against mostly English primaries:

| Jurisdiction | Exercises |
|---|---|
| Ireland | regulator-not-PUC, MVA, EU `applies_to` |
| Québec | provincial subdivision, CAD, French docket, `RateCase` 1:1 |
| Singapore | `government_framework`, `de_facto` pause + `lifted_date`, no-subdivision country, SGD |
| NSW | AUD, a withdrawn site by an untracked operator, `proposed` national rules |
| Johor | `administrative` pause with a water trigger, Malaysian state code |

Wave 2 is NL / DE / DK / NO heat reuse, together with the `heat_reuse`
decision and real non-English quoting.

### 5.2 Candidate records

Status key:

- **S** = secondary source fetched by a research agent (summarizing fetch);
- **F** = agent fetched the primary page;
- **L** = lead (search snippet or agent-flagged gap);
- **P** = the primary to fetch in Phase 0.

**Nothing is verified.**

| # | Type | Record | Source(s) in research | Status | Primary to fetch (P) |
|---|---|---|---|---|---|
| 1 | Policy · `supranational` · `legislation` · in_effect | EU Energy Efficiency Directive (EU) 2023/1791 Art. 12 data-centre reporting + Delegated Reg. 2024/1364 (EU database) | https://energy.ec.europa.eu/topics/energy-efficiency/energy-efficiency-targets-directive-and-rules/energy-efficiency-directive/energy-performance-data-centres_en | F (Commission page) | EUR-Lex text of Delegated Reg. 2024/1364 |
| 2 | Policy · `supranational` · `regulation` · proposed | EU data-centre rating scheme (draft delegated act, >500 kW) | https://www.thegreenwebfoundation.org/wp-content/uploads/EU.datacentre.labelling.scheme-draft-delegated-regulation.Ares_.2026.3247482pdf.pdf ; https://data.consilium.europa.eu/doc/document/ST-13444-2026-INIT/en/pdf | L (dates conflict) | Commission "Have your say" / Council doc |
| 3 | Policy · `supranational` · `legislation` · proposed | Cloud and AI Development Act (proposed 2026-06-03) | https://www.wsgrdataadvisor.com/2026/06/european-commission-publishes-proposal-for-act-to-reduce-reliance-on-foreign-cloud-and-ai/ ; https://oeil.europarl.europa.eu/oeil/en/document-summary?id=1903654 | S / L | Commission COM document. Ship only community-relevant key_terms (permitting); otherwise drop as off-topic |
| 4 | Policy · IE · national · `regulation` · in_effect | CRU Large Energy User connection policy, final decision (Dec 2025): on-site/nearby generation or storage matching Maximum Import Capacity, 80% renewable match, MVA tiers | https://www.dcbyte.com/news-blogs/ireland-reopens-the-grid-for-data-centres/ ; proposed decision CRU/202504: https://www.matheson.com/insights/large-energy-users-connection-policy-update/ | S | CRU decision paper (cru.ie). The proposed decision goes in `resources` |
| 5 | Policy · IE · national · `regulation` · in_effect (superseded) | CRU 2021 direction on data-centre connections (the "effective freeze") | https://www.irishexaminer.com/business/companies/arid-41875214.html | L | CRU 2021 decision. **Not a Moratorium** unless CRU's text says pause; if it is superseded, it becomes an `amends` lineage of #4 |
| 6 | Moratorium · IE · city · Dublin City Council | Reported 12-month pause on new data-centre applications (Feb 2026) | https://www.datacentres.com/news/data-centre-moratoriums-spread-as-156b-in-projects-face-regulatory-gridlock-slot1-2026-06-25 | L | DCC minutes / development plan variation. **High Loudoun risk:** drop it if the council's own text doesn't say pause |
| 7 | Country context · IE | CSO: data centres 23% of metered electricity, 2025 | https://www.irishtimes.com/business/2026/07/07/data-centres-account-for-almost-one-quarter-of-irish-electricity-usage-in-2025/ | S | CSO statistical release (cite the CSO, not the Times) |
| 8 | Project · IE · microsoft | Microsoft Grange Castle / Dublin campus | https://baxtel.com/data-center/microsoft-dublin-db3-grange | L | Microsoft's own Ireland datacenter page; planning reference |
| 9 | Claim · IE · microsoft | Microsoft Dublin community commitment (community fund / local page) | none in research | L (gap) | Microsoft's local Ireland page. Ship only a first-party community-impact quote (gate-2 discipline, the Amentum lesson) |
| 10 | RateCase · CA · CA-QC · state level · pending | Régie de l'énergie R-4333-2026: Hydro-Québec large data-centre rate; Google an intervenor | https://www.regie-energie.qc.ca/fr/participants/dossiers/R-4333-2026/doc/R-4333-2026-C-Google-0016-Preuve-Memoire-2026_07_20.pdf | F (TOC only) | Docket index page R-4333-2026. Read the filing and the schedule for `next_milestone` |
| 11 | Tariff · CA · CA-QC · proposed | Hydro-Québec proposed large data-centre rate, ~13¢/kWh "approximately double" current large-power rate; >5 MW | https://news.hydroquebec.com/news/press-releases/all-quebec/hydro-quebec-proposing-regie-energie-new-rate-large-data-centres-adjustment-rate-cryptographic-use-applied-blockchains.html ; https://www.blg.com/en/insights/2026/07/data-centres-in-canada-current-state | F (English press release) | Same press release (English, official). `related_tariff_id` from #10. Score LBL `parameters` only from the filing text |
| 12 | Policy · CA · CA-QC · `regulation` · in_effect | Québec Decree 89-2026 (government decree on data-centre electricity) | cited inside #10 | L | Gazette officielle du Québec. Number unverified |
| 13 | Policy · CA · CA-QC · `regulation` | Ministerial (MEIE) authorization for >5 MW loads | https://www.blg.com/en/insights/2026/07/data-centres-in-canada-current-state | L | Québec statute or regulation text |
| 14 | Moratorium · SG · national · `de_facto` · enacted, `lifted_date` 2022 | 2019–2022 pause on new large data-centre approvals | https://www.reedsmith.com/articles/singapores-data-centre-expansion-jurong-island-sustainable-growth/ | S | IMDA/EDB 2022 statement describing the pause. `de_facto` needs it or two sources |
| 15 | Policy · SG · national · `government_framework` · in_effect | Pilot DC-CFA (2022; ~80 MW to four operators, 2023) | same Reed Smith URL | S | EDB/IMDA 2022–23 media release |
| 16 | Policy · SG · national · `government_framework` · in_effect | DC-CFA2: launched 2025-12-01; 200 MW provisionally allocated 2026-08-21, 50 MW each to Digital Realty, Equinix, Keppel DC, ST Telemedia GDC; >50% green-energy condition | https://w.media/?p=42718 ; https://www.edb.gov.sg/content/dam/edb-en/about-edb/media-releases/news/four-data-centre-proposals-selected-as-part-of-second-data-centre/Fact%20Sheet%20-Four%20data%20centre%20proposals%20selected%20as%20part%20of%20second%20data%20centre.pdf | S + P identified | The EDB fact sheet PDF |
| 17 | Policy · SG · national · `government_framework` · in_effect | Green Data Centre Roadmap (2024) | Reed Smith (above) | S | IMDA roadmap page |
| 18 | Project · SG · amazon | AWS Singapore investment ($9bn per BMI) | https://technode.global/2026/07/29/singapore-to-retain-top-southeast-asia-data-center-status-despite-capacity-constraints-bmi/ | S (analyst-via-press) | AWS's own Singapore announcement. **The BMI figure doesn't ship.** It may be a company-wide investment `Claim` rather than a site `Project` |
| 19 | Policy · AU · AU-NSW · state · `government_framework` · in_effect | NSW Data Centre Policy Framework and Guidelines (2026-08-17) | https://www.claytonutz.com/insights/2026/august/nsw-draws-the-line-what-the-new-data-centre-policy-framework-means-for-investors-developers-government-and-communities | S | NSW Government framework page / PDF |
| 20 | Policy · AU · AU-NSW · state · `legislation` · proposed | NSW grid-access bill (exposure draft, ≥5 MW connections; consultation closed 2026-09-14) | Clayton Utz (above) | S | NSW exposure-draft page |
| 21 | Policy · AU · national · `government_framework` · proposed | Proposed national data-centre rules: own connection costs, avoid raising power prices, minimise water, siting | https://aiunderstanding.org/news/australia-s-proposed-ai-data-centre-rules-could-spur-a-rush-for-approvals-the-guar | S (weak outlet) | DCCEEW / National Cabinet communiqué. **Don't ship on the current source.** Principle `pay_own_way` (closest cousin to the US pledge) |
| 22 | Project · AU · AU-NSW · `operator_name` Goodman · withdrawn | "Project Mars", Lane Cove, 90 MW; development application not progressed (2026-09-29) | https://ia.acs.org.au/article/2026/controversial-sydney-data-centre-plan-scrapped.html | S | NSW Planning Portal SSD page; Goodman ASX/announcement |
| 23 | CommunityResponse · #22 · `local_government` · positive-for-withdrawal | Lane Cove mayor: "a huge win for the Lane Cove community" | same ACS URL | S | Lane Cove Council's own release |
| 24 | SiteUpdate on #22 · `kind: news` / `filing` | Withdrawal; parliamentary inquiry reference | same | S | Planning Portal status change (event date) |
| 25 | Project · AU · AU-NSW · NextDC (offtaker OpenAI?) | Stargate Australia, S7 Eastern Creek, 612 MW, A$7bn, SSD | https://www.datacenterdynamics.com/en/news/openai-signs-mou-with-nextdc-for-australian-stargate-data-center-in-sydney/ | L | NextDC ASX release; OpenAI release. Decide `company_slug` per §3.9 |
| 26 | Moratorium · MY · MY-01 · state · `administrative` · enacted · reason `water` | Johor stops approving Tier 1/2 data centres; reclaimed water from Syarikat Air Johor required (Nov 2025) | https://www.nst.com.my/amp/news/nation/2025/11/1324188/johor-tightens-approvals-data-centres ; https://w.media/johor-stops-approving-tier-1-and-tier-2-data-centers-due-to-water-overuse/ | F (NST) + S | Johor state government statement. The summary must say "Tier 1 and 2 only", not "ban" |
| 27 | (check only) | Conflicting July 2026 Johor report (ban + renewables) | https://mezha.net/eng/bukvy/4e3edddf_malaysia_tightens_data/ | L | Resolve against #26 before shipping either. If it is unresolved, #26 ships with `status_detail` noting the conflict |

Expected yield after verification: **15–20 records.** Expect about a third of
the leads to fail, as the US moratorium batch did. A failed lead goes into
the research log with its reason (SPEC_POLICIES_TAB's "No record, with
reasons" pattern). It does not get a weaker source.

### 5.3 Acceptance bar (every record)

1. `source_url` fetched directly in this pass, live (2xx), and **not a
   homepage**.
2. Every `key_terms` item, quoted figure and date is literally on
   `source_url`, in the source language. `probe.py --evidence` passes, or
   the row is BLOCKED / UNREADABLE with a WebFetch read recorded as "not
   machine-verified" in the PR body.
3. Headline vs action: the authority's own description of the instrument is
   on file (§4.2). `formality` / `instrument` match it.
4. Status is as of the capture date. "Proposed" items carry the stage
   ("exposure draft", "consultation closed 2026-09-14") in
   `status_detail` / `summary`.
5. Money is stored as stated, with currency; MVA as stated. No conversion.
6. Non-English verbatim has a labelled `Translation`. None are expected in
   wave 1, except possibly #10 and #12.
7. Claims meet the first-party rule and gate 2's "actually about community
   impact" test.
8. Principles are curator-assigned: primary first, at most three, no regex.
9. Every country in the payload has a `Country` record with a curated
   `summary`, at least one `RegulatorRef`, and `last_reviewed`.

## 6. Frontend

### 6.1 View and sub-tabs

- `VIEWS` gains
  `{ name: "world", tab: "tab-world", section: "view-world", hash: "#world" }`
  as the **last** entry.
- `SUBTAB_GROUPS.intl = ["countries", "instruments", "sites"]` and
  `VIEW_SUBTAB_GROUP.world = "intl"`, so `#world/instruments` and
  `#world/sites` deep-link panes.
- `wireSubtabs()` coverage is already guarded by
  `test_every_view_subtab_responds_to_a_click`, which iterates the groups.
- Hero: h2 "International" plus a one-line dek that lists the countries from
  `COUNTRY_NAMES`, rendered from data and never hardcoded (copy rule: say
  what it holds).

### 6.2 Panes

- **Countries:**
  - one `.home-card`-style card per `Country`;
  - each card shows the name, the first sentence of `summary`, and counts in
    words ("3 rules · 1 pause · 1 open proceeding · 2 sites"), using the
    "a number without its word is a code" rule;
  - clicking a card opens the country page;
  - the EU appears as its own card ("EU-wide rules").
- **Instruments:**
  - `.acc` sections, one per `POLICY_PRINCIPLES` value that has records;
  - rows unify Policy, Moratorium, Tariff and RateCase, each with a type
    badge, a country chip and a status badge reusing the existing palettes
    (`POLICY_STATUS_BADGE_CLASS`, moratorium, tariff, rate case);
  - `.filter-bar--slim` with country, instrument/type and status selects,
    serialized to `?country=IE&type=…`;
  - rows open the existing detail modals (tariff and moratorium modal
    patterns), extended to render `Money`, `formality`, translation blocks
    and lineage;
  - Moratoriums and RateCases have no `principles` field. They go in a
    trailing "Pauses" section and a trailing "Electricity rates &
    proceedings" section instead. **No principles get inferred for them.**
- **Sites:**
  - a list of international projects, using the Sites contested logic
    (`contestedReasons`) for a "Contested" filter chip;
  - each site's detail reuses the Overview / Claims / Community tab strip
    (`DETAIL_TABS`) and `siteTimeline()`;
  - **no map in wave 1.** Leaflet stays Explorer-only. Phase 4 option:
    Explorer gets an "Include international sites" toggle that lazy-loads
    `international.json` and adds a layer. That needs the map to stop
    assuming a US bounding box.

### 6.3 Country page (`#country/XX`)

- Follows the state-panel / tariff-modal pattern: backdrop, Escape, focus
  trap, return focus.
- **It lives in `#view-world`.** `#country/XX` reads the code **before**
  `activateView("world")`, because that call rewrites the hash. This is the
  documented `#state/XX` rule. It validates against `COUNTRY_NAMES` and
  `SUPRANATIONAL`.
- **Sections, in this order. Each renders even when empty, with "Nothing
  recorded yet."**
  1. Overview: summary, regulators, context facts with sources.
  2. National and subnational rules: Policies grouped by subdivision.
  3. EU rules that apply here: supranational policies whose `applies_to`
     includes the code. **Shown only for EU members.** It is absent, not
     empty, elsewhere, because it isn't a gap for Australia.
  4. Pauses and allocation: Moratoriums plus `government_framework` records
     with counterparties.
  5. Electricity rates and proceedings: Tariffs and RateCases with
     `next_milestone`.
  6. Sites and community response.
  7. Company commitments here: Claims with `country == XX`.
- Units and money render through new formatters `formatMoney(m)` (uses
  `as_stated` verbatim, with the ISO code tooltip) and `formatMva`. Labels
  use `SUBDIVISION_TERMS`.

### 6.4 Cross-links

- **Local Policy Frameworks → International.** Each principle card gets
  "Abroad: N →" linking to `#world/instruments?principle=<key>`. N comes
  from `home.json` (`intl.by_principle`, below), so the US tab never fetches
  `international.json` to draw the link. The link is hidden when N is 0.
- **International → Local Policy Frameworks.** Each Instruments principle
  section header links to "US examples →" `#policies` with that principle
  selected.
- **Companies:** Phase 4 only. A profile line, "Also tracked abroad: N sites
  in M countries", fed from a `home.json` per-slug count.

### 6.5 Home digest (`data/home.json`)

- `_build_home` adds a small `intl` block:

  ```
  {countries, records, by_principle: {principle: n},
   latest: [..≤2..], coming_up: [..≤2..]}
  ```

  Budget: ≤ 0.4 KB gzipped. Latest and Coming-up items carry a country
  label ("Québec, Canada · Régie hearing"). They merge into the existing
  lists under the same caps, **only from stated dates** (rate-case
  milestones, `upcoming` site events).
- The **numbers band stays US**, and its label says so. **There is no sixth
  tile.** Mixing international records into "moratoriums" would make the
  tile a sum of different kinds of thing.
- Home tab cards: `test_home_cards_cover_every_other_tab` derives from
  `VIEWS`, so the 9th card is required automatically. Its count is
  `intl.records` in words.

### 6.6 Exports

- CSV and PDF for the Instruments pane and the country page, through
  `_triggerDownload` / `_exportToPDF` / `_pdfTable`.
- Columns: `country`, `subdivision`, `amount`, `currency`, `as_stated`,
  `source_lang`, `translation_by`. **There is no USD column.**
- The PDF prints the original quote and its labelled translation.
- Filenames: `international-instruments-<date>.csv`, `country-IE-<date>.pdf`.

### 6.7 Performance

- `international.json` is fetched only on:
  - `#world` activation;
  - a `#country/XX` deep link;
  - a click on an "Abroad: N" link (it navigates to `#world`).
- The loader is promise-memoized (`let _intlDataPromise = null`), per the
  PR #41 lesson. An e2e test asserts exactly one request.
- First paint stays at 5 requests and about 142 KB. Home grows by about
  0.4 KB.
- `tests/test_perf_budget.py`:
  - add `"data/international.json"` to `DEFERRED`;
  - new `test_international_payload_size` (≤ 40 KB gzipped; failing means
    split per country, **not** raise the cap);
  - assert `home.json` stays ≤ 3 KB gzipped.
- Wave-1 estimate: about 30 records × about 1.6 KB raw, about 12 KB gzipped.

## 7. Pipeline

### 7.1 `refresh.py`

- `PAYLOAD_FILES["international"] = InternationalPayload`. Seed is mirrored
  to docs like every other payload.
- **Partition check** (above) plus cross-payload cross-refs (company slugs
  into `companies.json`; everything else within the international payload).
- `_build_coverage` adds a `countries` block (per-ISO2 counts by type) next
  to `states`. International records **never** enter `states` or `totals`.
- `_build_home` adds the `intl` block. `_is_contested` is reused for
  international sites, and its existing e2e parity test is extended to
  international fixtures.
- `--audit` (ISSUES.md, generated) gains an "International" section:
  - non-English verbatim without a translation (unreachable once the
    validator exists; a safety net);
  - `proposed` records older than 180 days;
  - countries with `last_reviewed` older than 120 days;
  - `de_facto` pauses with a single source.

  `_is_ratepayer_eligible` is untouched. International projects are never
  pledge-eligible, and the partition makes that structural.

### 7.2 `refresh_queue.py` and the daily routine

- **New unit kind `country:<CC>`**, derived from `COUNTRY_NAMES` in app.js
  (mirroring how `state:` reads `STATE_NAMES`), excluding `US`. `EU` is a
  unit (`country:EU`).
  `TARGET_DAYS["country"] = 120`.
- **International sites are not `site:` units in wave 1.** They are
  reviewed inside their country unit. That keeps the US site queue's
  rhythm, and a 5-country layer adds 6 units, not 30.
- The unit-records helper (`--unit country:IE`) lists every international
  record with that `country` (and `applies_to` for EU), plus BACKLOG
  §3 `#### country:IE` leads.
- Derived follow-ups extend naturally: an international `RateCase.next_milestone_date`
  comes due like a US one.
- **Routine guardrails** (edit `.claude/skills/daily-refresh/SKILL.md`):
  - a country unit is worked unattended **only if** `Country.primary_languages`
    contains `"en"` (IE, SG, AU, MY, plus Canada through its English
    sources);
  - the routine may **not** create or change any non-English verbatim, any
    `Translation`, any `formality`, or any new country. Those become
    BACKLOG leads;
  - Québec French docket follow-ups are allowed only as `--followups-only`
    checks that bump `captured_at` when the docket page shows no change;
  - a ledger key `country:XX` that no longer names a unit fails
    `test_committed_ledger_is_valid`, which already applies.
- Rhythm change: alternate days currently rotate state ↔ company. That
  becomes state → company → country, so country units get about one slot
  every three days. At 6 units on 120 days, that is enough.

### 7.3 Connectors (feasibility, all post-wave-1)

| Source | What it gives | Feasibility | Phase |
|---|---|---|---|
| EU EED data-centre database (Art. 12 / Del. Reg. 2024/1364) | Aggregated national indicators; the Commission publishes analysis reports. Not site-level per the research | Cite-only. A context `ContextFact` per EU country from the Commission report; no scraper. Re-check site-level publication rules (OQ-8) | 4 (cite) |
| Irish CSO metered electricity (PxStat JSON-stat API) | Data-centre share of metered consumption, periodic | Small, stable, open data (licence to confirm). A connector that updates one `ContextFact` is plausible | 4 |
| Régie de l'énergie docket pages | New filings / decisions on R-4333-2026 | Structured URLs. A "new document since last check" watcher feeding follow-ups is feasible; it lists documents and never parses them into records | 4 |
| NSW Planning Portal (SSD register) | Application status for data-centre SSDs | Possible public API (lead). Status-change watcher only | 5 |
| EDB/IMDA, CRU decisions pages | New decisions | Same listing-page lesson (2026-07-27): fetch the index directly during country reviews. No connector | — |

Per CLAUDE.md, connectors use the base-class pattern (rate limit, disk
cache, UA, 429 backoff) and **emit candidates for curation, not records.**

## 8. Testing plan

### 8.1 Unit (`tests/test_international.py`)

Schema, one test per validator, each **mutation-checked** (revert the
validator and watch the test go red):

- `test_federal_level_is_us_only`
- `test_national_level_is_non_us`
- `test_subdivision_prefix_matches_country`
- `test_subdivision_in_registry`
- `test_us_records_reject_subdivision`
- `test_non_us_subnational_needs_subdivision_except_city_states`
- `test_non_us_money_not_usd_field` (`claimed_investment_usd` / `value_usd`
  must be null)
- `test_money_currency_in_registry`
- `test_translation_required_iff_non_english`
- `test_official_translation_needs_url`
- `test_human_translation_needs_translator`
- `test_key_terms_translation_parallel_length`
- `test_de_facto_needs_corroboration`
- `test_lifted_date_requires_enacted_and_order`
- `test_supranational_applies_to_subset_of_eu`
- `test_transposes_targets_supranational`
- `test_amends_same_country`
- `test_operator_or_company_required`

Partition:

- `test_us_payloads_reject_non_us` (iterates `refresh.PAYLOAD_FILES` minus
  international; **derived, not listed**)
- `test_international_rejects_us`
- `test_cross_refs_resolve_within_international`

Seed data:

- `test_every_country_record_in_registry`
- `test_every_registry_country_has_a_record`
- `test_every_international_record_has_non_homepage_source` (reuses the
  homepage detector from test_policies.py)
- `test_no_bulk_duplicates_by_source_and_title`

Backward compatibility: the existing suite runs unchanged. Add
`test_existing_us_seed_validates_without_new_fields`, which dumps each US
record and asserts that no new field appears with a non-default value.

### 8.2 Parity

§3.10, plus `test_home_intl_block_matches_payload` (counts in `home.json`
equal `len()` of the payload by principle).

### 8.3 e2e (`tests/e2e/test_international.py`)

- `test_world_tab_lazy_loads_payload_once`: no request before activation,
  exactly one after `#world`, `#world/instruments` and `#country/IE`.
- `test_country_deep_link_opens_panel` (reads the code before
  `activateView`; Escape restores focus).
- `test_country_panel_renders_every_section_even_empty`, using SG, which has
  no tariffs.
- `test_eu_section_only_for_members`: IE has it, AU doesn't.
- `test_translation_label_and_original_lang_attr`, using a fixture record
  with `lang="fr"`.
- `test_money_renders_as_stated_no_usd`
- `test_mva_not_converted`
- `test_formality_badge_text`
- `test_instruments_filters_serialize_to_url`
- `test_abroad_link_counts_from_home_json_without_fetching_intl`
- `test_us_views_unchanged_counts`: Home band, the moratorium tiles and the
  state strip equal their pre-change values on the same data. Derived from
  the US payloads, not literals.
- Hidden-pane rule: anything inside `#world/sites` or a collapsed `.acc`
  uses `state="attached"` or clicks first.

### 8.4 Interaction cost (`tools/interaction_cost.py`, `uat/interaction_budgets.json`)

New tasks, budgeted per device:

| Task | What it measures | Starting budget (mobile / tablet / desktop taps) |
|---|---|---|
| `country_page` | Home → Ireland's country page | 3 / 2 / 2 |
| `intl_principle` | find a "pay their own grid costs" rule abroad from Local Policy Frameworks | 3 / 3 / 2 |
| `intl_translation` | open a translated quote and read its original | 4 / 3 / 3 |
| `intl_contested_site` | reach Project Mars's timeline | 4 / 3 / 3 |

Re-run all 18 existing tasks with 9 tabs. **No existing budget may get
worse.** If the phone tab bar adds a row, fix the labels; don't raise the
budgets.

## 9. Rollout, risks, open questions

### 9.1 Phases

| Phase | Work | Exit criterion | Effort |
|---|---|---|---|
| **0. Decisions + verification** | Owner answers OQ-1…OQ-9. A Sonnet agent, run one at a time and checkpointing per record, fetches the "P" column of §5.2 (≈20 fetches; needs owner approval past the 10-URL gate) and writes `.agent_outputs/intl/verify.jsonl` | Each candidate marked ship / drop-with-reason | 0.5 day |
| **1. Schema + pipeline** | §3 fields, registries, validators, `InternationalPayload`, partition, refresh cross-refs, coverage/home blocks, audit, probe.py changes, BACKLOG entries for `government_framework`, `formality`, `lifted_date` | Full unit + parity suite green with an **empty** `international.json` (countries only); US payloads byte-identical after `refresh.py` | 1–1.5 days |
| **2. Wave-1 seed** | `scripts/build_international.py` (idempotent, `ensure_ascii=False`, like the other builders) writes the seed from verified rows; evidence gate | 15–20 records pass §5.3; `refresh.py` + tests green | 1–2 days |
| **3. Frontend** | `#world` tab, panes, country page, detail-modal extensions, exports, formatters, CSS tokens (none new expected; badges reuse palettes) | e2e green (`-n 4`), interaction-cost budgets met, `test_type_scale` / `test_no_dead_css` green, preview artifact published | 2 days |
| **4. Cross-links + queue** | "Abroad: N" links, Home intl items, `country:` queue units, SKILL.md guardrails, CLAUDE.md section, Explorer layer (optional), CSO/Régie watchers (optional) | One routine run works a `country:` unit end to end | 0.5–1 day (+1 for connectors) |
| **5. Wave 2** | NL / DE / DK / NO heat reuse; `heat_reuse` principle decision + migration; first real non-English quoting | Owner sign-off on translation policy in practice | 2–3 days |

Total through Phase 4: about 5–7 working days.

### 9.2 Risks and mitigations

| Risk | Mitigation |
|---|---|
| **Fabrication or synthesis errors** (wrong decree numbers, conflated dockets): the 2026-07 batch shape, worse when foreign-language | No bulk import. Primary-source ladder (§4.1). Gazette numbers fetched. Probe gate plus UNREADABLE handling. Dropped leads logged with reasons |
| **Headline-vs-action mislabels** (pause vs condition) | `formality` field. Instrument chosen from the authority's own text. `de_facto` corroboration validator |
| **Machine translation passed off as a quote** | Original stays in the verbatim field. `Translation.by` is required and rendered. `machine` is labelled. The routine can't add translations |
| **US regression** from loosening four required fields | Partition validators re-tighten. `test_us_views_unchanged_counts`. Phase-1 exit requires byte-identical US payloads |
| **Scope creep** (150+ subdivisions, every country) | `COUNTRIES` registry is the bound. Adding a country is an owner decision recorded in CLAUDE.md. `SUBDIVISIONS` holds only codes in use |
| **Tone skew** (benefit side thin, critical content heavy) | Country pages lead with instruments. The blueprint principles organize Instruments. Responses are evidence, not headline |
| **Perf drift** | Deferred list, size test with a split-not-raise rule, home.json cap |
| **Refresh load and bot walls** (DCD 403s, French sites) | Country units at 120 days, English-only unattended, follow-ups-only for Québec, BLOCKED/UNREADABLE parking (existing `--blocked` cooldown) |
| **9th tab cost on phones** | Short label "World", interaction-cost budgets, no worsening allowed |
| **Licence / IP** on EU database or foreign press | Cite-only for EED. Quote limits unchanged. CSO licence confirmed before any connector |

### 9.3 Open questions for the owner

1. **Tab and title.** Approve a 9th tab, "International" (`#world`), placed
   last? Should the masthead/title gain "and selected countries", or stay
   US-framed with the tab as the exception?
2. **Untracked operators.** May international sites carry only
   `operator_name` (Goodman, NextDC) with no Company record? Do Equinix and
   Digital Realty stay out of scope as companies (they're DC-CFA2
   awardees)?
3. **Translation policy.** For wave 1, allow `machine` translations
   (labelled AI) for French docket text, or require an official English
   source / skip the record?
4. **Currency.** Original only (recommended), or add a display-only H.10
   annual-average "≈ US$" line?
5. **Wave-1 list.** IE + QC + SG + NSW + EU layer, with Johor as stretch.
   Or swap Singapore/Johor for NL/DE so heat reuse lands in wave 1 (which
   pulls the translation work and the `heat_reuse` decision forward)?
6. **Proposed instruments.** Include not-in-force national/EU drafts
   (Australia federal rules, EU rating scheme, CADA) with as-of stage, or
   in-effect only?
7. **Heat reuse.** Agree to defer the `heat_reuse` principle to wave 2?
8. **EU database.** Cite-only (recommended), or spend a Phase-4 check on
   whether any Member State publishes site-level EED data?
9. **Refresh.** Should country units join the daily routine under the
   English-only guardrail (recommended), go to a separate weekly routine, or
   be manual only?
10. **Verification budget.** Approve the ≈20-fetch Phase-0 pass (over the
    10-URL gate) before anything is seeded?
