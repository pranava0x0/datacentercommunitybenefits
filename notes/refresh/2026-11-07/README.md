# November 7, 2026 refresh

The published additions are 97 US moratorium records, 45 projects (38 US,
seven international), 52 verbatim company statements and 11 US policy
frameworks or agreements. The US directory now contains 347 moratorium
records, 180 projects and 153 policies; the international directory contains
69 projects. These totals include historical actions and proposals, not
only currently operative restrictions.

## Coverage

- [State coverage](state-coverage.json): searches executed against the actual
  governor and energy-office domains for all 50 states, plus 42 local-gap
  queries. Search outcomes and returned sources are retained. A search with
  no result does not establish that no relevant action exists.
- [Lead dispositions](lead-dispositions.json): all 623 rows from three
  public inventories were reconciled with local IDs and primary-source
  evidence. The inventories were lead lists, not publication evidence.
  The original 226 strict-name Calyx gaps resolve to 88 verified-new
  candidates, five aliases, 30 blocked and 103 insufficient-evidence leads.
  Other discoveries came from the additional inventories and official searches.
- [Company coverage](company-coverage.json): all 33 tracked company
  landing pages and follow-up sources were reviewed. [Roster dispositions](roster-dispositions.json)
  account for all 61 initial gaps and preserve the larger QTS, NEXTDC, Colt
  and CloudHQ inventories. A listed location without an established original
  announcement year or project phase remains a lead.
- [Held state records](held-state-records.json): 15 candidates withheld
  because of unresolved dates, elapsed terms, source access or legal scope.
  Hazle, Clearfield and Cincinnati study/review actions were independently
  curated as frameworks rather than blanket application moratoria.

The initial full source audit classified 1,724 URLs across 2,929 source rows.
It recorded 230 blocked URLs and two redirects requiring review. Its 87
exact-text misses were reviewed individually in [the disposition log](existing-source-triage.json).
Policy terms can be supported paraphrases; an exact-text miss is not proof
of a factual error. Conversely, a live URL is not proof that every field
on its record is accurate.

## Material corrections

The refresh restores exact wording for company quotations, uses Microsoft's
primary Pecos statement, corrects Indiana's tax-exemption payment base and
eligibility dates, preserves Wisconsin's alternative water-compliance path,
and distinguishes Virginia's requested PJM advocacy from an enacted cost
allocation. PORTS-Pike's community fund is $80 million: $40 million from
SB Energy and an additional $40 million from OpenAI.

Independent review corrected Fort Wayne's January 19, 2024 announcement
versus April 26 groundbreaking; removed Madison's 40 MW IT load from the
total-electrical-capacity field; clarified Lamar's 180-day extension, Ralls'
conjunctive acreage/value definition and Marengo's extension-only waiver;
and corrected Maine's sponsor and veto-sustain date and Cave City's adoption
date. Wrightstown ends its pause on adoption of comprehensive zoning,
not on the later effective date.

The map adds 101 Census boundaries and associates all eligible new legal
records with their jurisdictions. Town/city and county/city identities
were checked separately, including Oneonta town, Highland town in Sullivan
County, Beetown town and Spokane County. The existing 33 DOE points remain
individual stars; six site-linked announcements remain highlighted.

## Limits and follow-up

No new ratepayer assessment, delivery status or community-response stance
was assigned. New company-wide promises remain distinct from site-specific
evidence. Eighteen of the 19 existing ratepayer-evidence chains were
rechecked; Van Buren's blocked source remains unverified. Three Prologis
quotations behind an obfuscated/paywalled source remain unverified rather
than silently rewritten. Historical records are not described as freshly
confirmed merely because their citations still exist.

Meta Singapore's current opening remains unconfirmed. Prince William
County and Microsoft Silver Springs lack verified original announcement
years. Individual Google Loudoun and Singapore campuses remain grouped
where phase-to-address matching is unresolved. Malaysia, Norway and Denmark
leads remain outside the existing fixed country registry. Regional investment
plans, financing facilities and proposed credits are not assigned as parcel
construction budgets or delivered benefits. Approximate company registry
points for Cedar Rapids and Columbia County were withheld from the site map
because they identify localities rather than verified campus parcels.

The Elections summary and direct state comparisons shipped in
[PR #112](https://github.com/pranava0x0/datacentercommunitybenefits/pull/112).
This data pass retains that layout and the searchable directory.
