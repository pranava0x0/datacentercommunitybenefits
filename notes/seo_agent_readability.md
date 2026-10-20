# SEO, agent readability and accessibility checklist

The owner bookmarked a long X post ("Andre"/Karpathy, Oct 2026) on getting
strong SEO and agent readability for a web page. On 2026-10-19 I couldn't find
it: I scanned about 480 bookmarks back to late July in x.com/i/history →
Bookmarks, plus an X search, and none was an SEO or accessibility post by that
author. So this list is the standard practice that kind of post covers, in my
own words. It doesn't quote the post. Once someone has the link, reconcile
this list against it.

| Tip | Covered? | Where |
|---|---|---|
| One canonical URL per page | Yes | `<link rel="canonical">` in docs/index.html |
| Descriptive `<title>` and meta description | Yes | docs/index.html head |
| Open Graph / Twitter card tags for link previews | Yes | og:* and twitter:card |
| Structured data (schema.org) describing what the site is | Yes | `Dataset` JSON-LD |
| `robots.txt` that allows crawling and points to the sitemap | Yes | docs/robots.txt |
| `sitemap.xml` with lastmod, regenerated with the data | Yes | refresh.py `_write_agent_files` |
| `llms.txt`: a plain-markdown map of the site and data for AI agents, with live counts | Yes | docs/llms.txt, generated; `<link rel="alternate" type="text/markdown">` |
| Raw data reachable as stable URLs (JSON per record type) | Yes | docs/data/*.json, listed in llms.txt |
| Valid HTML (Nu validator, 0 errors) | Yes | checked 2026-10-19 |
| Automated accessibility audit (axe) per view | Yes | tests/e2e/test_accessibility.py |
| Semantic landmarks, one h1, real heading outline, skip link | Yes | existing markup and tests |
| Visible focus states, keyboard-operable tabs, rows and modals | Yes | existing CSS and e2e tests |
| Contrast computed, not eyeballed, in light and dark | Yes | palette notes in CLAUDE.md |
| Fast first paint, small payload, no web fonts | Yes | tests/test_perf_budget.py |
| Content visible without JavaScript (crawlers that don't run JS) | **No** | The SPA renders from JSON. A `<noscript>` summary, or a pre-rendered static summary per tab built by refresh.py, would cover it. |
| Per-section shareable URLs as real paths, not just `#hash` | **No** | Crawlers ignore fragments. Static per-tab pages (e.g. /moratoriums/) generated at refresh would index separately. |
| Per-record pages (one URL per moratorium, site, policy) | **No** | Biggest search win, and the largest build. See BACKLOG. |
| Markdown mirror of each page (`.md` beside `.html`) for agents | Partial | llms.txt covers the index; no per-section .md yet. |
| Social preview image (og:image) | **No** | Needs a small optimized PNG/WebP; adds one asset. |
| `lang` on non-English quotes | Yes | `quoteBlock` sets lang on international quotes |
