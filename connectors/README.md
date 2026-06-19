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
