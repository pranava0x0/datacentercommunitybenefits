# International wave-1 research brief (records to SHIP — accuracy and citations are everything)

Repo (read-only for you): /Users/pranava/Projects/data center community benefits. Read
notes/specs/SPEC_INTERNATIONAL.md §1, §3, §4, §5 and the research JSON in notes/specs/international/
for leads. Today 2026-10-19. The owner approved up to ~40 WebFetch calls for you. Do NOT edit the repo.
Write your output file AS YOU GO (rewrite the whole JSON each time).

Owner decisions: quotes stay in the ORIGINAL language, with a separate English translation labelled
by:"machine" (you may translate, but the original text must be copied exactly from the fetched page);
prefer an official English version of the page when one exists (then lang "en"). Proposed / draft
instruments ARE included, marked status "proposed" with the stage stated. Money is stored as stated
(amount + ISO currency + the exact printed string). Sites by companies we don't track yet may be
included; name the operator (it will be added as a company).

Target per country: 3–6 records, the most important and best-sourced, mixing:
- policy: national/regional/municipal instruments (laws, regulations, regulator decisions such as
  grid-connection rules, government frameworks/programmes like Singapore DC-CFA or UK AI Growth Zones,
  heat-reuse mandates, reporting mandates, signed community/host agreements, company plans for one
  community). instrument ∈ executive_order|legislation|regulation|local_ordinance|benefit_agreement|
  company_plan|government_framework. status ∈ in_effect|proposed|failed.
- moratorium: a pause on new data centers. formality ∈ formal (statute/ordinance) | administrative
  (an authority's announced decision) | de_facto (no published decision; described afterward — needs
  the authority's own statement or 2 independent sources). Include lifted_date if it ended.
- project: a hyperscale site (prefer Microsoft, Google, Amazon/AWS, Meta, OpenAI/Stargate, Oracle,
  xAI, Anthropic, CoreWeave, Crusoe, QTS, Brookfield sites; else the largest local operator).
- response: a community/regulator/NGO reaction to a site (stance positive|mixed|negative; constituency
  residents|local_government|ngo|academic|journalist|regulator).
- claim: a first-party company quote about community impact for that country/site (theme ∈ jobs|
  tax_revenue|energy|water|community_grants|infrastructure|education|engagement).
Also a country block: 2–4 sentence neutral summary; regulators (name, acronym, role ∈
energy_regulator|grid_operator|planning|environment|investment_agency, url); 1–3 context facts (a
sourced number, e.g. "data centres used 23% of metered electricity in 2025").

HARD RULES: every factual field must be on a page you fetched — copy a verbatim supporting sentence
(original language). Headline words ("ban", "moratorium") must match the legal action — read the
authority's own text. Bill/decree/decision numbers confirmed on the official page. Event dates are
event dates. No bare homepages as sources. Prefer .gov/official/regulator/company newsroom sources.
Mark anything you couldn't verify "verified": false (it won't ship).

Output JSON:
{"countries":[{"code":"IE","summary":"...","regulators":[...],"context":[{"statement":"English
curator sentence","verbatim":"source words","source_lang":"en","period":"2025","source_url":"...",
"source_title":"...","captured_at":"2026-10-19"}],"primary_languages":["en","ga"]}],
"records":[{"type":"policy|moratorium|project|response|claim","country":"IE","subdivision":"CA-QC or
null","locality":"council/municipality or null","fields":{...record fields: title/jurisdiction/
instrument/status/date/identifier/summary/key_terms(original language, literal on page)/principles/
benefit_themes/value{amount,currency,as_stated} for policy; jurisdiction/jurisdiction_type
(national|state|county|city)/status(enacted|proposed|failed)/formality/enacted_date/lifted_date/
duration_description/key_reasons(energy|water|air_quality|noise|transparency|equity)/summary for
moratorium; company/operator/name/city/status(announced|construction|operational|withdrawn)/
announced_year/claimed_investment{amount,currency,as_stated}/claimed_jobs/power_mw/
import_capacity_mva/acreage/lat/lon(from a fetched page e.g. Wikipedia)/notes for project; project
(name or id)/date/stance/constituency/summary for response; company/theme/statement (original
language, exact)/statement_lang/translation(English, by machine) for claim},
"source_url":"...","source_title":"Outlet — headline","source_lang":"en|fr|sv|fi|el",
"verbatim":"exact supporting sentence(s) from the page","verified":true,"notes":"caveats"}]}
Reply with a short summary of counts per country and anything unverified.
