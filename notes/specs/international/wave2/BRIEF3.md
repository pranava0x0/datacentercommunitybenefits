# International pass 3 (wave 2) — deeper, VERIFIED records

Read notes/specs/international/wave1/BRIEF.md (record format, owner decisions) and wave1/BRIEF2.md
(mechanical verification with probe.py / PDFKit; that overrides BRIEF.md) and follow both. Also read
existing.md in this folder: do NOT duplicate existing records; if you find a status change or a new
fact for an existing record, output it as {"type": ..., "action": "update", "existing_id": "...",
"fields": {only the changed/added fields}, ...}.

Today 2026-10-19. Budget up to ~45 fetches (WebFetch + probe). Only probe-HIT verbatims count;
set verified true only when every factual field's phrase HITs. Write your output JSON AS YOU GO.
Target: 4–8 NEW verified records per country you cover (policies, moratoriums/pauses, rate cases
(utility + regulator + docket + status + next milestone), sites with lat/lon from a probed page,
community responses, first-party company claims), plus 1–2 verified context facts and 1–3
regulators (probed URLs) per country where the country block lacks them.
Rate-case format: {"type":"rate_case","country":..,"subdivision":..,"fields":{"utility","regulator",
"docket_number","title","case_type": general_rate_case|large_load_tariff|special_contract|
rulemaking, "status": pending|approved|rejected, "filed_date","decided_date","next_milestone",
"next_milestone_date","summary"}, ...}.
Do not edit the repo except your output file.
