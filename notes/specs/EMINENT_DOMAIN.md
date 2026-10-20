# Eminent domain and land acquisition for data centers (research, 2026-10-19)

Owner question: where are governments (or utilities using delegated condemnation
power) taking land for data centers, or for the power built to serve them?

No record type holds this yet, so nothing below is on the site. The cases are
here with their sources so a curator can decide the shape (see "Proposed schema").

## Verified cases (quote probe-matched on the cited page)

| Case | Who takes the land | For what | Data-center link (as sourced) | Status / date | Source |
|---|---|---|---|---|---|
| Spotsylvania County, VA | County Board of Supervisors | 77,751 sq ft for the Reuse Conveyance System (reclaimed water) | County: the project "will benefit data centers" | Pulled from consent agenda 2026-04-14; 7-0 to take it up 2026-04-28; outcome not found | [Fredericksburg Free Press](https://www.fredericksburgfreepress.com/?p=167402) |
| Maryland Piedmont Reliability Project | PSEG (utility; CPCN pending, PSC Case 9773); Fourth Circuit ruling | ~67-mile 500 kV line, Frederick to Harford | PSEG project director: "part of that load growth is data centers" (FOX45, 2024); opponents call it an extension cord for Northern Virginia data centers | Fourth Circuit upheld survey access to hundreds of properties, Aug 2026; CPCN still pending | [WYPR 2026-08-20](https://www.wypr.org/wypr-news/2026-08-20/court-upholds-eminent-domain-for-mprp-in-maryland) |
| Georgia Power Ashley Park-Wansley line | Georgia Power (investor-owned; delegated condemnation) | 35-mile transmission line, Coweta/Fayette/Heard/Fulton | "70-80%" of the power to AI data centers is a CBS estimate Georgia Power did not confirm; attribute it | Land acquisition under way 2026; ~300+ parcels | [Fortune 2026-07-26](https://fortune.com/2026/07/26/georgia-power-utility-company-eminent-domain-grid-expansion-data-center/) |

## Not verified

- **Metro Nashville / DC Blox parcel by the zoo.** Council authorized negotiation or
  condemnation (~2026-08-04). The taking is *of* a data-center site for municipal
  use, not *for* a data center. Quotes missed the probe; re-fetch the council bill
  (BL2026-1489) before using. [WSMV](https://www.wsmv.com/2026/08/05/nashville-zoo-data-center-what-comes-next-after-metro-councils-vote-eminent-domain/)

## Leads

Dominion Golden-to-Mars (Loudoun, SCC route approval Apr 2026); PPL 230 kV line for
PNK Group (Gregg Twp, PA; PUC pending); AES Indiana 345 kV near Monrovia (linked by
advocates to a Google site); Andhra Pradesh APIIC allotments for the Google/Adani
Visakhapatnam cluster (allotment, not compulsory acquisition, plus a High Court
petition on non-auction allotment); MIDC data-centre parks (Maharashtra); Ohio HB 710
and Nebraska LB 1261 (eminent-domain limits, introduced only); Texas 765 kV; PA Muth bill.
No enacted state law barring eminent domain for data centers was found.

## Proposed schema (decision needed)

Option A: `SiteUpdate.kind = "eminent_domain"` on the linked project (cheap; only
works when a tracked site is served). Option B: a `Policy` with a new principle
`no_eminent_domain` for state bills limiting it, plus Option A for takings. Option C:
a new `LandTaking` record (body, condemnor type government|utility, acreage/parcels,
purpose, data-center link quote, status, docket). B covers the laws; C is the only
shape that holds utility line takings with no tracked site, which is most cases.
