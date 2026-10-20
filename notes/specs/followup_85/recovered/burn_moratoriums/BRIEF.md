# US burn-down brief — states, counties, municipalities (VERIFIED only)

Repo (read-only except your output file): /Users/pranava/Projects/data center community benefits.
Today 2026-10-19. Budget ~45 fetches. Accuracy and citations are the whole job.

For EACH state unit you're given, run from the repo root:
  .venv/bin/python scripts/refresh_queue.py --unit state:XX
That prints the unit's existing records (ids by type) and BACKLOG leads. Read the relevant records in
data/seed/*.json (moratoriums.json, policies.json, projects.json, rate_cases.json, tariffs.json) so you
don't duplicate them. Then find, for that state, county and municipal (and state-level) actions on data
centers from 2026-08-01 to 2026-10-19 that are NOT already recorded, and status changes to existing
records (a proposed moratorium that passed/failed, a pending rate case decided, a hearing outcome):
- moratoriums/pauses (check the legal action: a zoning change or a pause on a board's own docket is not
  a moratorium — say exactly what it is), local ordinances (zoning, noise, water, setbacks), CBAs/host
  agreements, rate-case / tariff decisions, state bills/EOs, site votes/permits/lawsuits for tracked
  companies' sites, community responses. Resolve the unit's BACKLOG leads where you can.
VERIFY mechanically: a WebFetch result is a summary, not page text. For every verbatim, run
  .venv/bin/python scripts/probe.py "<URL>" "<distinctive phrase>"
and copy the verbatim from probe's printed context; only HITs count. PDFs: curl -sL -A "Mozilla/5.0"
-o /tmp/x.pdf URL && osascript -l JavaScript /tmp/pdftext.js /tmp/x.pdf | grep -i "phrase". Prefer
.gov/municode/agenda/minutes/legislature/PUC docket pages; local news quoting officials is OK. No bare
homepages, no aggregators (datacenterbans.com, citizenportal.ai, servercountry). Event dates are event
dates (if only "Tuesday" in an article, compute and say so). Confirm bill numbers on the legislature page.

Output JSON array (write AS YOU GO): one object per finding:
{"unit":"state:XX","type":"moratorium|policy|rate_case|tariff|site_update|community_response|project",
 "action":"new|update","existing_id":"... or null","jurisdiction":"...","jurisdiction_type":"city|county|state",
 "state":"XX","title":"neutral one line","event_date":"YYYY-MM-DD","status":"...",
 "facts":{structured fields: ordinance/bill number, vote, MW threshold, duration, $ value, docket, next milestone date...},
 "summary":"1-2 neutral sentences","source_url":"...","source_title":"Outlet — headline",
 "verbatims":["exact probe-HIT sentence(s)"],"verified":true,"notes":"caveats"}
At the end reply with counts per state (verified / not) and leads you could not resolve.
