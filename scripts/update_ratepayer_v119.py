"""One-shot script: add ratepayer assessments to 11 existing projects,
upgrade amazon-clinton-ms, add evidence claims, and add new projects.
Run once from the repo root: python scripts/update_ratepayer_v119.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
PROJECTS_PATH = ROOT / "data/seed/projects.json"
CLAIMS_PATH = ROOT / "data/seed/claims.json"

# ---------------------------------------------------------------------------
# New claims to add (evidence for AFFIRMED assessments + key ratepayer quotes
# for pre-pledge new projects that have explicit public commitments)
# ---------------------------------------------------------------------------

NEW_CLAIMS = [
    # --- google-van-buren-mi ---
    {
        "id": "google-van-buren-mi-energy-pay-costs-2026",
        "company_slug": "google",
        "theme": "energy",
        "statement": (
            "We've agreed to finance the entire 2.7 gigawatts of new power supply "
            "through an agreement with DTE to help ensure any costs associated with "
            "our data center project come to us (Google)."
        ),
        "source_url": "https://michiganadvance.com/2026/03/17/google-and-dte-announce-van-buren-township-data-center-agreement-commit-to-contested-case-hearing/",
        "source_title": "Michigan Advance — Google and DTE: Van Buren Township data center agreement and contested case hearing",
        "captured_at": "2026-06-01",
        "published_at": "2026-03-17",
        "project_id": "google-van-buren-mi",
    },
    # --- google-franklin-furnace-oh ---
    {
        "id": "google-franklin-furnace-energy-pay-100pct-2026",
        "company_slug": "google",
        "theme": "energy",
        "statement": (
            "Google in Ohio will pay 100% of the electric required to run the campus "
            "along with paying AEP to provide infrastructure locally."
        ),
        "source_url": "https://www.wsaz.com/2026/05/15/google-hosts-data-center-information-fair/",
        "source_title": "WSAZ — Google hosts Scioto County data center information fair (May 2026)",
        "captured_at": "2026-06-01",
        "published_at": "2026-05-15",
        "project_id": "google-franklin-furnace-oh",
    },
    # --- meta-lebanon-in ---
    {
        "id": "meta-lebanon-energy-pay-full-costs-2026",
        "company_slug": "meta",
        "theme": "energy",
        "statement": (
            "We pay the full costs for energy used by our data centers and work closely "
            "with utilities to plan for our energy needs years in advance to ensure "
            "residents aren't negatively impacted."
        ),
        "source_url": "https://datacenters.atmeta.com/2026/02/hello-lebanon/",
        "source_title": "Meta Data Centers — Hello, Lebanon! (Feb 2026)",
        "captured_at": "2026-06-01",
        "published_at": "2026-02-11",
        "project_id": "meta-lebanon-in",
    },
    # --- amazon-caddo-parish-la ---
    {
        "id": "amazon-caddo-energy-pay-100pct-2026",
        "company_slug": "amazon",
        "theme": "energy",
        "statement": (
            "Amazon has worked with the local utility, Southwestern Electric Power Company "
            "(SWEPCO), to ensure we pay 100% of the costs associated with our new data "
            "center campus in Louisiana. This includes covering all expenses for new energy "
            "infrastructure and upgrades required to serve the data centers."
        ),
        "source_url": "https://www.aboutamazon.com/news/company-news/amazon-data-center-louisiana-new-jobs",
        "source_title": "Amazon — Caddo and Bossier parishes Louisiana data center announcement (Feb 2026)",
        "captured_at": "2026-06-01",
        "published_at": "2026-02-23",
        "project_id": "amazon-caddo-parish-la",
    },
    # --- amazon-bossier-parish-la (same joint announcement) ---
    {
        "id": "amazon-bossier-energy-pay-100pct-2026",
        "company_slug": "amazon",
        "theme": "energy",
        "statement": (
            "Amazon has worked with the local utility, Southwestern Electric Power Company "
            "(SWEPCO), to ensure we pay 100% of the costs associated with our new data "
            "center campus in Louisiana. This includes covering all expenses for new energy "
            "infrastructure and upgrades required to serve the data centers."
        ),
        "source_url": "https://www.aboutamazon.com/news/company-news/amazon-data-center-louisiana-new-jobs",
        "source_title": "Amazon — Caddo and Bossier parishes Louisiana data center announcement (Feb 2026)",
        "captured_at": "2026-06-01",
        "published_at": "2026-02-23",
        "project_id": "amazon-bossier-parish-la",
    },
    # --- amazon-vicksburg-ms ---
    {
        "id": "amazon-vicksburg-energy-pay-100pct-2026",
        "company_slug": "amazon",
        "theme": "energy",
        "statement": (
            "Amazon has worked with Entergy Mississippi to ensure we pay 100% of the "
            "costs associated with our new data center campuses, covering all expenses "
            "for new energy infrastructure and upgrades."
        ),
        "source_url": "https://www.aboutamazon.com/news/company-news/amazon-25-billion-mississippi-data-centers",
        "source_title": "Amazon — $25 billion Mississippi data centers announcement (Apr 2026)",
        "captured_at": "2026-06-01",
        "published_at": "2026-04-09",
        "project_id": "amazon-vicksburg-ms",
    },
    # --- amazon-clinton-ms (upgrade from pledge_only; same Mississippi announcement) ---
    {
        "id": "amazon-clinton-ms-energy-pay-100pct-2026",
        "company_slug": "amazon",
        "theme": "energy",
        "statement": (
            "Amazon has worked with Entergy Mississippi to ensure we pay 100% of the "
            "costs associated with our new data center campuses, covering all expenses "
            "for new energy infrastructure and upgrades."
        ),
        "source_url": "https://www.aboutamazon.com/news/company-news/amazon-25-billion-mississippi-data-centers",
        "source_title": "Amazon — $25 billion Mississippi data centers announcement (Apr 2026)",
        "captured_at": "2026-06-01",
        "published_at": "2026-04-09",
        "project_id": "amazon-clinton-ms",
    },
    # --- aws-ridgeland-ms (new project, same Mississippi announcement) ---
    {
        "id": "amazon-ridgeland-energy-pay-100pct-2026",
        "company_slug": "amazon",
        "theme": "energy",
        "statement": (
            "Amazon has worked with Entergy Mississippi to ensure we pay 100% of the "
            "costs associated with our new data center campuses, covering all expenses "
            "for new energy infrastructure and upgrades."
        ),
        "source_url": "https://www.aboutamazon.com/news/company-news/amazon-25-billion-mississippi-data-centers",
        "source_title": "Amazon — $25 billion Mississippi data centers announcement (Apr 2026)",
        "captured_at": "2026-06-01",
        "published_at": "2026-04-09",
        "project_id": "aws-ridgeland-ms",
    },
    # --- google-pine-island-mn (pre-pledge, no ratepayer block, but notable energy claim) ---
    {
        "id": "google-pine-island-energy-pay-grid-costs-2026",
        "company_slug": "google",
        "theme": "energy",
        "statement": (
            "Google will cover 100% of the costs for new grid infrastructure required "
            "to serve the facility. That protects Minnesota ratepayers."
        ),
        "source_url": "https://blog.google/innovation-and-ai/infrastructure-and-cloud/global-network/data-center-pine-island/",
        "source_title": "Google Blog — Pine Island, Minnesota data center announcement",
        "captured_at": "2026-06-01",
        "published_at": "2026-02-24",
        "project_id": "google-pine-island-mn",
    },
    # --- google-hermantown-mn (pre-pledge, energy claim) ---
    {
        "id": "google-hermantown-energy-grid-partnership-2026",
        "company_slug": "google",
        "theme": "energy",
        "statement": (
            "Google and Minnesota Power are partnering to bring 700 megawatts of new "
            "clean energy — including 300 megawatts of wind and 400 megawatts of "
            "battery storage — to the Arrowhead region, with no cost increases to "
            "existing Minnesota Power customers."
        ),
        "source_url": "https://www.datacenterdynamics.com/en/news/google-confirms-it-is-behind-403-acre-data-center-campus-in-hermantown-minnesota/",
        "source_title": "Data Center Dynamics — Google confirms 403-acre Hermantown, Minnesota campus",
        "captured_at": "2026-06-01",
        "project_id": "google-hermantown-mn",
    },
]

# ---------------------------------------------------------------------------
# Ratepayer assessment updates for EXISTING projects
# ---------------------------------------------------------------------------

RATEPAYER_UPDATES = {
    "google-van-buren-mi": {
        "status": "affirmed",
        "summary": (
            "Google and DTE filed contracts with the Michigan Public Service Commission "
            "confirming Google finances all 2.7 GW of new power supply needed, ensuring "
            "no costs associated with the Van Buren Township campus shift to existing ratepayers."
        ),
        "evidence_claim_id": "google-van-buren-mi-energy-pay-costs-2026",
        "assessed_at": "2026-06-01",
    },
    "openai-lordstown-oh": {
        "status": "pledge_only",
        "summary": (
            "Covered by OpenAI's Stargate Community pledge ('pay our own way on energy'); "
            "no Lordstown-specific utility agreement or named-executive commitment for this site has been published."
        ),
        "assessed_at": "2026-06-01",
    },
    "microsoft-person-county-nc": {
        "status": "pledge_only",
        "summary": (
            "Covered by Microsoft's national 'pay our own way' commitment and Duke Energy's "
            "standard data center contract language; no Person County-specific ratepayer "
            "filing or named executive quote tied to this site has been captured."
        ),
        "assessed_at": "2026-06-01",
    },
    "google-franklin-furnace-oh": {
        "status": "affirmed",
        "summary": (
            "Google Area Operations Manager Timothy Chadwick stated publicly at a May 2026 "
            "community information fair that Google will pay 100% of its electricity costs "
            "and all AEP infrastructure for the Scioto County campus."
        ),
        "evidence_claim_id": "google-franklin-furnace-energy-pay-100pct-2026",
        "assessed_at": "2026-06-01",
    },
    "meta-lebanon-in": {
        "status": "affirmed",
        "summary": (
            "Meta's own newsroom and the City of Lebanon both confirmed Meta pays the full "
            "costs for energy at the Lebanon campus, with Boone REMC and Wabash Valley Power "
            "Alliance covering service at no added cost to existing customers."
        ),
        "evidence_claim_id": "meta-lebanon-energy-pay-full-costs-2026",
        "assessed_at": "2026-06-01",
    },
    "google-chesterfield-va": {
        "status": "pledge_only",
        "summary": (
            "Virginia's SCC-approved GS-5 rate class requires Dominion Energy data center "
            "customers to cover their own grid upgrade costs; no Project Peanut-specific "
            "Google commitment letter or site-level filing has been published."
        ),
        "assessed_at": "2026-06-01",
    },
    "amazon-caddo-parish-la": {
        "status": "affirmed",
        "summary": (
            "Amazon and SWEPCO President Brett Mattison jointly confirmed at the February "
            "2026 announcement that Amazon pays 100% of all project-specific infrastructure "
            "costs, with zero pass-through to residential or business customers."
        ),
        "evidence_claim_id": "amazon-caddo-energy-pay-100pct-2026",
        "assessed_at": "2026-06-01",
    },
    "amazon-bossier-parish-la": {
        "status": "affirmed",
        "summary": (
            "Part of the same joint Caddo/Bossier announcement: Amazon and SWEPCO confirmed "
            "Amazon pays 100% of all new energy infrastructure costs for both Louisiana campuses, "
            "with no costs passed through to residential or business customers."
        ),
        "evidence_claim_id": "amazon-bossier-energy-pay-100pct-2026",
        "assessed_at": "2026-06-01",
    },
    "amazon-vicksburg-ms": {
        "status": "affirmed",
        "summary": (
            "Amazon's April 2026 Mississippi announcement explicitly states it pays 100% of "
            "all grid infrastructure and upgrade costs for its Mississippi campuses, including "
            "Warren County/Vicksburg, under its Entergy Mississippi agreement."
        ),
        "evidence_claim_id": "amazon-vicksburg-energy-pay-100pct-2026",
        "assessed_at": "2026-06-01",
    },
    "google-little-rock-ar": {
        "status": "pledge_only",
        "summary": (
            "Entergy Arkansas VP Ventrell Thompson told the Little Rock City Board that Google "
            "is required to pay its full infrastructure costs; however, as of June 2026 no "
            "final rate agreement for the Port of Little Rock site has been signed or published."
        ),
        "assessed_at": "2026-06-01",
    },
    "amazon-boardman-or": {
        "status": "pledge_only",
        "summary": (
            "Oregon's POWER Act (HB 3546, 2025) statutorily requires new large energy users "
            "to pay 100% of distribution infrastructure costs; Amazon's 1,300-acre Morrow "
            "County site is pre-development with no site-specific commitment yet filed."
        ),
        "assessed_at": "2026-06-01",
    },
    # Upgrade from pledge_only to affirmed
    "amazon-clinton-ms": {
        "status": "affirmed",
        "summary": (
            "Amazon's April 2026 Mississippi-wide announcement covers the Clinton/Hinds County "
            "campus: Amazon pays 100% of all new energy infrastructure costs under its "
            "Entergy Mississippi agreement, with no costs passed through to existing ratepayers."
        ),
        "evidence_claim_id": "amazon-clinton-ms-energy-pay-100pct-2026",
        "assessed_at": "2026-06-01",
    },
}

# ---------------------------------------------------------------------------
# New projects to add
# ---------------------------------------------------------------------------

NEW_PROJECTS = [
    # AWS Madison County / Ridgeland, MS expansion (Apr 9, 2026 — post-pledge)
    {
        "id": "aws-ridgeland-ms",
        "company_slug": "amazon",
        "name": "AWS Madison County Campus (Ridgeland Expansion)",
        "city": "Ridgeland",
        "state": "MS",
        "country": "US",
        "lat": 32.4282,
        "lon": -90.1329,
        "status": "construction",
        "announced_year": 2026,
        "claimed_investment_usd": 11000000000,
        "claimed_jobs": 700,
        "notes": (
            "Part of Amazon's $25B Mississippi commitment announced April 9, 2026. "
            "Expansion of Amazon's existing Madison County operations cluster in Ridgeland, "
            "served by Entergy Mississippi. Amazon pays 100% of all grid infrastructure "
            "and upgrade costs under the same Entergy Mississippi agreement covering all "
            "Amazon's Mississippi campuses."
        ),
        "source_url": "https://www.aboutamazon.com/news/company-news/amazon-25-billion-mississippi-data-centers",
        "source_title": "Amazon — $25 billion Mississippi data centers announcement (Apr 2026)",
        "captured_at": "2026-06-01",
        "published_at": "2026-04-09",
        "offtaker": "Amazon",
        "ratepayer": {
            "status": "affirmed",
            "summary": (
                "Amazon's April 2026 Mississippi announcement explicitly covers all new "
                "campuses including Ridgeland/Madison County: pays 100% of grid infrastructure "
                "costs via its Entergy Mississippi agreement."
            ),
            "evidence_claim_id": "amazon-ridgeland-energy-pay-100pct-2026",
            "assessed_at": "2026-06-01",
        },
    },
    # AWS Wilmington / Clinton County, OH ($4B, land acquired Aug 2025 — pre-pledge)
    {
        "id": "aws-wilmington-oh",
        "company_slug": "amazon",
        "name": "AWS Clinton County Campus (Wilmington)",
        "city": "Wilmington",
        "state": "OH",
        "country": "US",
        "lat": 39.4454,
        "lon": -83.8330,
        "status": "announced",
        "announced_year": 2025,
        "claimed_investment_usd": 4000000000,
        "claimed_jobs": None,
        "notes": (
            "AWS acquired ~590 acres in Jefferson Township, Clinton County in August 2025. "
            "Proposed $4B campus on 471 acres off US-68. As of May 2026, twice tabled by "
            "Clinton County planning commission due to community opposition and unresolved "
            "approval questions. Legal action filed by neighbors. Port authority negotiating "
            "with Wilmington City Schools on a community benefit deal."
        ),
        "source_url": "https://www.datacenterdynamics.com/en/news/aws-data-center-project-tabled-in-wilmington-ohio/",
        "source_title": "Data Center Dynamics — AWS Wilmington Ohio project tabled (2026)",
        "captured_at": "2026-06-01",
        "acreage": 590.0,
        "offtaker": "Amazon",
    },
    # Google Pine Island, MN (Feb 24, 2026 — pre-pledge, no ratepayer block)
    {
        "id": "google-pine-island-mn",
        "company_slug": "google",
        "name": "Google Pine Island Data Center",
        "city": "Pine Island",
        "state": "MN",
        "country": "US",
        "lat": 44.2003,
        "lon": -92.6451,
        "status": "announced",
        "announced_year": 2026,
        "claimed_investment_usd": None,
        "claimed_jobs": 100,
        "notes": (
            "Announced February 24, 2026. 480-acre campus in Pine Island Township, "
            "Goodhue County, served by Xcel Energy. Google committed to finance 1,900 MW "
            "of new clean energy resources for the Minnesota grid (solar, wind, battery "
            "storage). $25M community investment fund over 20 years, benefiting Pine Island "
            "schools. Google covers 100% of new grid infrastructure costs. ~500 construction "
            "trades during build phase."
        ),
        "source_url": "https://blog.google/innovation-and-ai/infrastructure-and-cloud/global-network/data-center-pine-island/",
        "source_title": "Google Blog — Pine Island, Minnesota data center announcement (Feb 2026)",
        "captured_at": "2026-06-01",
        "published_at": "2026-02-24",
        "acreage": 480.0,
        "offtaker": "Google",
    },
    # Google Hermantown, MN (confirmed Mar 3, 2026 — pre-pledge, no ratepayer block)
    {
        "id": "google-hermantown-mn",
        "company_slug": "google",
        "name": "Google Hermantown Data Center",
        "city": "Hermantown",
        "state": "MN",
        "country": "US",
        "lat": 46.8258,
        "lon": -92.2416,
        "status": "announced",
        "announced_year": 2026,
        "claimed_investment_usd": 650000000,
        "claimed_jobs": None,
        "notes": (
            "Confirmed as Google March 3, 2026 (project initially codename 'Project Birch'). "
            "403-acre campus adjacent to Minnesota Power's Arrowhead substation, St. Louis County. "
            "Partnership with Minnesota Power to enable 700 MW of new clean energy "
            "(300 MW wind + 400 MW battery storage) — no cost increases to existing customers. "
            "$5M energy affordability fund for low-income customers. "
            "As of May 2026, Hermantown City Council tabled a key zoning vote (May 5, 2026) "
            "amid ongoing permitting and utility agreement negotiations."
        ),
        "source_url": "https://www.datacenterdynamics.com/en/news/google-confirms-it-is-behind-403-acre-data-center-campus-in-hermantown-minnesota/",
        "source_title": "Data Center Dynamics — Google confirms 403-acre Hermantown, Minnesota campus",
        "captured_at": "2026-06-01",
        "acreage": 403.0,
        "offtaker": "Google",
    },
    # Google Wilbarger County, TX (Feb 24, 2026 — pre-pledge, no ratepayer block)
    {
        "id": "google-wilbarger-tx",
        "company_slug": "google",
        "name": "Google Wilbarger County Data Center",
        "city": "Vernon",
        "state": "TX",
        "country": "US",
        "lat": 34.1551,
        "lon": -99.2982,
        "status": "announced",
        "announced_year": 2026,
        "claimed_investment_usd": None,
        "claimed_jobs": 50,
        "notes": (
            "Part of Google's $40B Texas investment package announced February 24, 2026. "
            "Air-cooled campus in Wilbarger County, Texas Panhandle. "
            "Co-located with AES clean energy generation under a 20-year power purchase agreement. "
            "On ERCOT grid."
        ),
        "source_url": "https://blog.google/innovation-and-ai/infrastructure-and-cloud/global-network/data-center-wilbarger-county/",
        "source_title": "Google Blog — Wilbarger County, Texas data center announcement (Feb 2026)",
        "captured_at": "2026-06-01",
        "published_at": "2026-02-24",
        "offtaker": "Google",
    },
    # Google Armstrong County, TX (Nov 2025 — pre-pledge, no ratepayer block)
    {
        "id": "google-armstrong-tx",
        "company_slug": "google",
        "name": "Google Armstrong County Data Center",
        "city": "Claude",
        "state": "TX",
        "country": "US",
        "lat": 34.9737,
        "lon": -101.3559,
        "status": "construction",
        "announced_year": 2025,
        "claimed_investment_usd": None,
        "claimed_jobs": None,
        "notes": (
            "Part of Google's $40B Texas investment package. 1,300-acre site in Armstrong County, "
            "Texas Panhandle (near Claude, TX). Wind energy-powered via ERCOT. "
            "Closed-loop cooling for minimal water use. Crusoe Energy assisting with site "
            "preparation; construction underway as of early 2026."
        ),
        "source_url": "https://abc7amarillo.com/news/local/google-announces-new-data-center-in-armstrong-county-texas",
        "source_title": "ABC7 Amarillo — Google Armstrong County data center announcement",
        "captured_at": "2026-06-01",
        "acreage": 1300.0,
        "offtaker": "Google",
    },
    # Google Haskell County, TX (Nov 2025 — pre-pledge, no ratepayer block)
    {
        "id": "google-haskell-tx",
        "company_slug": "google",
        "name": "Google Haskell County Data Center",
        "city": "Haskell",
        "state": "TX",
        "country": "US",
        "lat": 33.1568,
        "lon": -99.7342,
        "status": "construction",
        "announced_year": 2025,
        "claimed_investment_usd": None,
        "claimed_jobs": None,
        "notes": (
            "Part of Google's $40B Texas investment package. Two data center campuses in "
            "Haskell County, West Texas. One campus co-located with a solar plus battery "
            "storage project. On ERCOT grid. Construction underway as of early 2026."
        ),
        "source_url": "https://ktxs.com/news/local/googles-40-billion-data-center-investment-to-transform-texas-town",
        "source_title": "KTXS — Google $40B data center investment in Haskell County, Texas",
        "captured_at": "2026-06-01",
        "offtaker": "Google",
    },
    # Microsoft La Porte, IN — second campus (approved May 2026 — post-pledge)
    {
        "id": "microsoft-la-porte-in",
        "company_slug": "microsoft",
        "name": "Microsoft La Porte Data Center (2nd Campus)",
        "city": "La Porte",
        "state": "IN",
        "country": "US",
        "lat": 41.6100,
        "lon": -86.7200,
        "status": "announced",
        "announced_year": 2026,
        "claimed_investment_usd": None,
        "claimed_jobs": None,
        "notes": (
            "Second Microsoft campus in La Porte County, adjacent to the original 2024 campus "
            "(489 acres, 6 buildings, $1B). April 14, 2026: La Porte voted to annex ~1,000 acres "
            "in Pleasant Township. May 18, 2026: City council approved annexation and rezoning "
            "for 11 additional data center buildings on the expanded footprint. "
            "Original La Porte campus announced June 2024; this second campus is a distinct "
            "post-pledge expansion."
        ),
        "source_url": "https://www.datacenterdynamics.com/en/news/microsoft-expands-plans-for-la-porte-indiana-data-center-campus/",
        "source_title": "Data Center Dynamics — Microsoft expands La Porte, Indiana data center plans (2026)",
        "captured_at": "2026-06-01",
        "acreage": 1000.0,
        "offtaker": "Microsoft",
        "ratepayer": {
            "status": "pledge_only",
            "summary": (
                "Covered by Microsoft's national pledge signature; the May 2026 La Porte "
                "expansion approval focused on annexation and zoning with no site-specific "
                "ratepayer commitment captured for this campus."
            ),
            "assessed_at": "2026-06-01",
        },
    },
]


# ---------------------------------------------------------------------------
# Apply all changes
# ---------------------------------------------------------------------------

def main() -> None:
    # Load
    pdata = json.loads(PROJECTS_PATH.read_text())
    cdata = json.loads(CLAIMS_PATH.read_text())

    projects: list[dict] = pdata["projects"]
    claims: list[dict] = cdata["claims"]

    existing_claim_ids = {c["id"] for c in claims}
    existing_project_ids = {p["id"] for p in projects}

    # 1. Add new claims (skip if already present)
    added_claims = 0
    for claim in NEW_CLAIMS:
        if claim["id"] in existing_claim_ids:
            print(f"  SKIP claim (exists): {claim['id']}")
            continue
        claims.append(claim)
        existing_claim_ids.add(claim["id"])
        added_claims += 1
        print(f"  ADD  claim: {claim['id']}")

    # 2. Update ratepayer assessments on existing projects
    updated_projects = 0
    proj_by_id = {p["id"]: p for p in projects}
    for pid, rp in RATEPAYER_UPDATES.items():
        if pid not in proj_by_id:
            print(f"  WARN project not found: {pid}")
            continue
        proj_by_id[pid]["ratepayer"] = rp
        updated_projects += 1
        print(f"  SET  ratepayer on {pid}: {rp['status']}")

    # 3. Add new projects (skip if already present)
    added_projects = 0
    for proj in NEW_PROJECTS:
        if proj["id"] in existing_project_ids:
            print(f"  SKIP project (exists): {proj['id']}")
            continue
        projects.append(proj)
        existing_project_ids.add(proj["id"])
        added_projects += 1
        print(f"  ADD  project: {proj['id']}")

    # Save
    PROJECTS_PATH.write_text(json.dumps(pdata, indent=2, ensure_ascii=False) + "\n")
    CLAIMS_PATH.write_text(json.dumps(cdata, indent=2, ensure_ascii=False) + "\n")

    print(f"\nDone: {added_claims} claims added, {updated_projects} projects updated, {added_projects} projects added.")


if __name__ == "__main__":
    main()
