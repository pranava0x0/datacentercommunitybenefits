# Answer-engine readability (AEO) checklist

Source: Rob Hoffman, "11 optimizations" for getting recommended by AI answer
engines such as Meta Muse, X, 2026-10-19.
https://x.com/RobHoffman_/status/2112212215583658420

This is my interpretation for this project, not his wording. His frame is a
product page trying to be recommended. Ours is a public record that should be
the source an agent cites when someone asks "which counties have paused data
centers?" or "did my utility sign the ratepayer pledge?". Only the parts that
fit a reference site are kept.

| # | His point, as it applies here | Status here | What to do |
|---|---|---|---|
| 1 | Agents read the accessibility tree. Every icon-only control needs a name, every form field a label, every image alt text, and nothing important should live only in an image. | Mostly covered: the theme toggle has `aria-label`, filters have `.sr-only` labels, no content images, and the axe test runs per view. | Keep the axe test as the gate. Check that map markers and the moratorium timeline bars expose a text equivalent. A chart with no table is image-only content. |
| 2 | Key facts must be in the raw HTML, not injected by script. Content that only appears after JS runs is invisible to most crawlers. | **Not covered, and the biggest gap.** The whole SPA renders from JSON at runtime, so the served HTML has headings and "—" placeholders, no facts. llms.txt and the JSON files partly offset this for agents that follow links. | Have refresh.py write the Home digest into index.html at build time: totals, latest actions, coming-up dates. Plus a `<noscript>` or pre-rendered summary per tab, and ideally static per-tab pages (/moratoriums/, /pledge/) generated from the same data. |
| 3 | Put the reader's main question, in plain words, as the first H2 under the title. | Not covered: view headings are labels ("Moratoriums"), not questions. | Give each tab's dek or first H2 its reader question: "Which places have paused data-center development?", "Who signed the Ratepayer Protection Pledge, and is it showing up at their sites?", "What have operators promised host communities?" Tab labels stay short. |
| 4 | Answer that question in under ~100 words, with an "it depends" that names cases instead of one blanket claim. | Partly: deks are one line, with no direct answer. | Under each question, two or three sentences generated from the data: "As of {date}, {n} jurisdictions have enacted pauses, mostly cities and counties; states mostly propose and fail." Derived, so it can't go stale. |
| 5 | Replace slogans with a definition: what it is, who it's for, what it does. | Partly: the Home dek describes the record but not who it's for. | One definitional sentence at the top of Home and in llms.txt: "A sourced public record of… for policymakers, advocates, researchers and journalists, showing…" |
| 6 | Testimonials and proof as selectable text, not images. | Covered: quotes are verbatim text with source links. | — |
| 7 | State key facts with an "as of" date. | Covered at record level: every record has `captured_at`, and claims show "as of". Not at page level. | Put "as of {refresh date}" on headline totals (Home tiles, tab counts). The draft banner already carries the refresh date. |
| 8 | Let AI crawlers in explicitly in robots.txt. | Covered: `User-agent: * / Allow: /` admits every crawler, including Meta's. | Optional: name the crawlers (meta-webindexer, GPTBot, ClaudeBot, PerplexityBot, Google-Extended) explicitly, so intent is unambiguous to a reader of the file. |
| 9 | Fix broken links: they stop crawlers exploring and lower trust. | Covered by tooling: `scripts/revalidate.py` classifies every source URL, and the daily routine acts on dead ones. | Run it over the full set and clear the dead-link list. Source links matter more here than on a product page, because they carry the citation. |
| 10 | Semantic HTML: nav, header, main, button, not divs with click handlers. | Covered: landmarks, buttons, tablists and `<details>`, with Nu at 0 errors. | Spot-check generated rows: directory rows are `role="button"` divs, and a native `<button>` or link would read better. |
| 11 | Freshness: update every 30–90 days and show published and updated dates near the top. | Covered in practice by the daily routine; the refresh date is in the banner and llms.txt. | Expose "Updated {date}" in the HTML near the title, not only in the banner and after JS, plus `dateModified` in the JSON-LD written by refresh.py. |

## Highest-value next changes, in order

1. Build-time facts in the HTML (#2): Home totals plus each tab's question and answer, written into index.html (or static per-tab pages) by refresh.py.
2. Reader questions with derived short answers per tab (#3–4).
3. "As of / Updated {date}" in the served HTML, plus `dateModified` in the JSON-LD (#7, #11).
4. A text table behind each chart (#1).
