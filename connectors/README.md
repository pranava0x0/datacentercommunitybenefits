# Research connectors — fast community-benefit data collection

A research **accelerator** for curating the dashboard. It automates the slow,
mechanical parts of the manual loop (finding which sites are thin, generating
search queries, fetching pages politely, and — the real time-sink — pulling a
news article's **publication date** automatically). It never auto-publishes:
output is *candidate* records in `data/candidates/` for a curator to review,
because stance/constituency tagging and verbatim-quote selection stay editorial
(see [CLAUDE.md](../CLAUDE.md)).

No new dependencies — uses `requests` (already pinned) + the stdlib.

## The loop

```
status   ->  queries  ->  [WebSearch / Chrome MCP]  ->  harvest  ->  curate  ->  data/seed/
```

### 1. `status` — where are the gaps?
```bash
python -m connectors.research status --list
```
Reports projects with no claims / no community feedback, and lists the
missing-feedback sites so you can plan a batch.

### 2. `queries` — what to search
```bash
python -m connectors.research queries --missing-feedback --limit 5
python -m connectors.research queries --missing-claims --json   # machine-readable
```
Emits ready-to-run search strings per under-covered site, plus the first-party
URL pattern for that company. Run these with the agent's **WebSearch** tool or
drive them with the **Chrome browser MCP** (`navigate` + `find`/`read_page`).

### 3. `harvest` — turn URLs into candidate records
```bash
python -m connectors.research harvest --project google-mayes-county-ok \
    https://datacenters.google/locations/oklahoma/ \
    https://www.somenews.com/2025/.../article

python -m connectors.research harvest --urls-file urls.txt --out cand.json
```
For each URL it fetches once (cached under `connectors/.cache/`, ≥1.5s/host,
429-backoff) and writes a candidate:

- **first-party domain** (Meta / Google / Microsoft / AWS) → `claim_candidates`
  with **verbatim quote candidates** to pick from (never paraphrased).
- **anything else** → `response_candidate` with an **auto-extracted publication
  date** (JSON-LD / OpenGraph / `<time>`), outlet name, and a lede to rewrite.
  `stance`, `constituency`, `single_source` come out **null with a TODO** — the
  tool does not infer them.

### 4. curate
Open the candidate file, pick the verbatim quote / write the neutral summary,
set the editorial fields, then merge into `data/seed/*.json` by hand and run
`python refresh.py --check`.

## Chrome MCP bridge (JS-rendered pages)

Some first-party pages are single-page apps — `datacenters.google` is the main
one. `requests` only gets an empty shell, so `harvest` flags them as
`needs_browser` instead of emitting empty quotes. To finish the job:

1. Use the **Chrome browser MCP** to `navigate` to the URL and read the rendered
   DOM (`get_page_text` / `read_page`); save it to a file, e.g. `rendered.html`.
2. Feed that rendered DOM back through the same extractor:
   ```bash
   python -m connectors.research harvest \
       --html-file rendered.html \
       --as-url https://datacenters.google/locations/north-carolina/ \
       --project google-lenoir-nc
   ```
   You get the same `claim_candidates` (verbatim quotes) as a server-rendered
   page would have produced.

## Guardrails (why this stays "candidates")

- **No paraphrased claims** — only verbatim quote candidates are surfaced.
- **No invented dates** — if a date can't be extracted it's left null and flagged
  loudly, never guessed.
- **No machine stance** — stance/constituency are editorial; the tool refuses to
  set them.
- **Idempotent + polite** — disk cache, per-host throttle, 429 backoff.

## `scout` — "is there anything new?" without spinning up an agent

`research.py` finds gaps in records that already exist. `scout.py` finds
**leads for records that don't exist yet**, by fetching the same fixed list of
sources REFRESH.md's "Finding New Announcements" / "Moratoriums & Tariffs
Refresh" sections describe checking by hand (or via an agent), extracting
headlines, and diffing them against the seed:

```bash
python -m connectors.scout projects       # company newsrooms + DCD
python -m connectors.scout moratoriums    # trackers (datacenterbans, halcyon, ...)
python -m connectors.scout all --json
```

Output is two buckets: candidates that share no city/company/jurisdiction
words with anything in the seed ("check these first"), and candidates that
matched an existing record by a token-overlap heuristic ("probably already
tracked"). Neither bucket is authoritative — read `connectors/scout.py`'s
module docstring before trusting either one. In short, it replaces the
*fetching and first-pass triage* an agent used to do by hand; it does not
replace the judgment calls that come after (see "What a script can't do"
below).

### What a script can't do here — read before assuming this replaces an agent

Added 2026-07-30, after the first real run surfaced these directly (not
hypothetical). Six matching bugs from that first run were found and fixed in
the same pass — three from an adversarial PR review, two more from the SAME
review's follow-up pass on the fix commit, and one from just running the tool
against the live seed afterward and reading the output. Documented here as
fixed, not as open limitations, but the underlying lesson (a heuristic like
this ships with real, compounding bugs on day one, and fixing one can
introduce the next) is worth keeping:

- **Fixed: requiring 2 token hits made every single-word jurisdiction
  structurally unmatchable, not just imprecise.** The first live run flagged
  `datacenterdynamics.com`'s own headline "Brookfield to develop
  gigawatt-scale data center campus at DOE's Kentucky nuclear enrichment
  plant" as *no seed match*, even though `brookfield-paducah-ky` was already
  in the seed — the headline names the company but not the city, so token
  overlap topped out at 1 and never cleared the old flat 2-token floor.
  Checked against the live seed: **57 of 111 moratorium records** (any
  single-word city/county name once its 2-letter state code was excluded as
  "too short to count") could never match *any* headline, no matter how
  exact the wording. Fixed by letting one sufficiently distinctive token
  (length >= 4) match on its own, while still requiring two shorter tokens
  together otherwise — see `match_existing`'s docstring.
- **Fixed: the generic-word stoplist only covered company names, not utility
  names, and `relevant()`'s own word-boundary check had a hole.** An early
  run matched an unrelated "Energy Systems Integration Group (ESIG) Large
  Load Task Force" headline to `sb-energy` purely on "Energy" + "Group"; a
  parallel bug let a generic "Indiana regulators weigh new large load energy
  tariff" headline match a Duke Energy Indiana tariff record purely on
  "energy" + "indiana", because the stoplist (`_GENERIC_WORDS`, renamed from
  `_GENERIC_COMPANY_WORDS`) wasn't applied to `tariff_fingerprints()`'s
  utility-name tokens. Separately, `relevant()` had a raw-substring fallback
  clause that defeated its own padding fix and let "gw" match inside
  "Edgware" (an unrelated UK town). All three fixed in the same review pass —
  but the stoplist is inherently incomplete: a new tracked company or utility
  with a similarly generic name will need its own addition to
  `_GENERIC_WORDS`.
- **Fixed: a distinctive single token was ENOUGH to fix the false-negative
  above, and TOO MUCH for a company with many sites.** Letting one
  distinctive token match alone (the fix two bullets up) fixed Brookfield
  (one tracked project) but reopened the door for Meta, Google, and every
  other multi-site company: "Meta announces a new data center in Reno" would
  have matched some unrelated existing Meta project purely because "meta" is
  a long word, misreporting a genuinely new site as already tracked. Fixed
  with `ambiguous_tokens`: a company's name tokens only count as sufficient
  ALONE when that company has exactly one tracked project; with 2+, the name
  alone no longer clears the bar and a second token (the city) is required.
  Also fixed the same day: the keyword list only had singular phrases, so
  "Google announces new data centers in Virginia" (plural) never even
  reached the matching step — `relevant()` now checks singular/+s/+es
  variants of every keyword.
- **Fixed: administrative-unit words ("county", "township") were treated as
  distinctive place names.** Found by running the tool against the live seed
  after the review, not by the review itself: "county" alone (6 letters)
  matched `wonder-valley-box-elder-ut` (city "Box Elder County") against an
  unrelated "data center in Henderson County, Texas" headline. Same failure
  shape as the generic-company-word bug, one layer down — `_ADMIN_UNIT_WORDS`
  strips these from both project city tokens and moratorium jurisdiction
  tokens before matching. (Left alone, deliberately: two different real
  places sharing a genuinely distinctive name, like "Henderson, NV" and
  "Henderson County, TX", or the two different "Temple, TX" projects from
  different developers — that's the same "a MATCH is not proof of an actual
  duplicate" limitation the module docstring already calls out, not a new
  bug to chase.)
- **A "fetched successfully" source can still return nothing useful.**
  `datacenterbans.com` and `halcyon.io` both returned HTTP 200 but, being
  client-rendered pages, only a nav shell — `extract_links` correctly parsed
  what was there, there just wasn't a real headline list in the static HTML.
  This does NOT show up as "blocked" in the report; it silently looks like
  "checked, nothing relevant." Known JS-rendered sources should eventually
  get the same Chrome-MCP bridge `harvest --html-file` already uses.
- **No "already reviewed" memory across runs.** `CachedSession` caches by
  URL, not by "a human already looked at this candidate and decided not to
  add it." Re-running `scout` against an unchanged source re-surfaces the
  same non-matching candidates every time — fine for a single sweep, noisy
  for a recurring/scheduled one. Not built; would need a seen-candidates
  file if this gets wired into a cron-style refresh.
- Everything `research.py`'s own guardrails already exclude (verbatim-quote
  extraction, publication-date confirmation on the *specific* cited URL, the
  two-gate editorial test for a new company, any stance/constituency call)
  is equally out of scope here — `scout` only gets you to a URL worth
  reading, same as a search engine would.
