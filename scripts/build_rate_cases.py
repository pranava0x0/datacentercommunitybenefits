"""Build data/seed/rate_cases.json — the regulatory-proceeding layer under the tariffs.

Idempotent: re-running regenerates the seed byte-identically. Every record below
was verified against its source_url on 2026-08-03 (fetched directly — .gov order
PDFs were text-extracted and grepped for the stated facts; bot-walled-but-live
pages were loaded in a real browser). Do not add a record here from search-result
synthesis alone; see CLAUDE.md's "A live source_url is not the same as a
verified claim".

Usage:
    python3 scripts/build_rate_cases.py     # writes data/seed/rate_cases.json
    python3 refresh.py                      # validates + mirrors to docs/data/
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from schema import RateCasesPayload  # noqa: E402

GENERATED_AT = "2026-08-03"

RATE_CASES: list[dict] = [
    # ------------------------------------------------------------------ VA
    {
        "id": "va-scc-dominion-biennial-2025",
        "state_code": "VA",
        "utility": "Dominion Energy Virginia",
        "regulator": "Virginia State Corporation Commission (SCC)",
        "docket_number": "PUR-2025-00058",
        "title": "Dominion 2025 biennial review — GS-5 data-center rate class",
        "case_type": "general_rate_case",
        "status": "approved",
        "filed_date": None,
        "decided_date": "2025-11-25",
        "effective_date": "2027-01-01",
        "next_milestone": (
            "GS-5 rate class takes effect for new 25 MW+ customers on "
            "January 1, 2027; SCC is separately weighing data-center "
            "transmission cost allocation"
        ),
        "next_milestone_date": "2027-01-01",
        "related_tariff_id": "dominion-virginia-gs5-rate-class",
        "related_project_ids": ["google-chesterfield-va"],
        "summary": (
            "The SCC's final order created a new GS-5 rate class for customers "
            "demanding 25 MW or more (effective January 1, 2027), requiring a "
            "minimum of 85% of contracted distribution and transmission demand "
            "and 60% of generation demand, 14-year agreements, and collateral — "
            "in the Commission's words, \"to help insulate ratepayers from the "
            "costs around the rapid build-out and construction of infrastructure "
            "to support businesses such as data centers.\" The order granted "
            "$565.7M (2026) and $209.9M (2027) of Dominion's requested $822M / "
            "$345M base-rate increases at a 9.8% ROE."
        ),
        "source_url": (
            "https://www.scc.virginia.gov/about-the-scc/newsreleases/release/"
            "scc-issues-order-on-dev-biennial-review-2025/"
            "scc-rules-in-dev-biennial-review-case.html"
        ),
        "source_title": "Virginia SCC — SCC Issues Order on DEV Biennial Review 2025",
        "resources": [
            {
                "url": (
                    "https://www.scc.virginia.gov/media/sccvirginiagov-home/"
                    "about-the-scc/fact-sheets/scc-data-center-initiatives-02-2026.pdf"
                ),
                "title": "SCC fact sheet — Data Center Initiatives: Ensuring Data Centers Pay Their Own Costs (Feb 2026)",
            }
        ],
        "captured_at": "2026-08-03",
    },
    # ------------------------------------------------------------------ LA
    {
        "id": "la-lpsc-entergy-meta-2025",
        "state_code": "LA",
        "utility": "Entergy Louisiana",
        "regulator": "Louisiana Public Service Commission (LPSC)",
        "docket_number": None,
        "title": "Entergy Louisiana infrastructure for Meta's Richland Parish campus",
        "case_type": "special_contract",
        "status": "approved",
        "filed_date": None,
        "decided_date": "2025-08-20",
        "effective_date": None,
        "next_milestone": (
            "LPSC response to the 2026 Earthjustice/UCS request to investigate "
            "the Meta financing arrangement's stranded-asset risk"
        ),
        "next_milestone_date": None,
        "related_tariff_id": None,
        "related_project_ids": ["meta-richland-la"],
        "summary": (
            "The LPSC approved Entergy Louisiana's plan to build three combined-"
            "cycle gas plants (two in Richland Parish online late 2028, one at "
            "Waterford by end of 2029) plus transmission, and to procure up to "
            "1,500 MW of solar through expedited certification, to serve Meta's "
            "Richland Parish data center. Entergy states that \"Meta is paying "
            "its share of the costs for the infrastructure needed to support its "
            "operations, ensuring that other customers are protected from those "
            "expenses.\" In 2026, Earthjustice and the Union of Concerned "
            "Scientists asked the LPSC to investigate whether the financing "
            "arrangement could leave households exposed to stranded costs."
        ),
        "source_url": (
            "https://www.entergy.com/news/entergy-louisiana-receives-lpsc-approval-"
            "for-major-infrastructure-investments-to-support-metas-data-center-"
            "and-improve-reliability"
        ),
        "source_title": "Entergy — LPSC approval for infrastructure supporting Meta's data center",
        "resources": [
            {
                "url": (
                    "https://earthjustice.org/press/2026/louisiana-regulators-asked-"
                    "to-investigate-shady-meta-financing-deal-that-could-leave-"
                    "households-paying-for-tech-giants-electricity"
                ),
                "title": "Earthjustice — request that the LPSC investigate the Meta financing deal (2026)",
            },
            {
                "url": "https://www.ucs.org/about/news/metas-new-data-center-agreement-increases-risk-stranded-assets",
                "title": "Union of Concerned Scientists — stranded-asset risk analysis",
            },
        ],
        "captured_at": "2026-08-03",
    },
    # ------------------------------------------------------------------ GA
    {
        "id": "ga-psc-rate-freeze-2025",
        "state_code": "GA",
        "utility": "Georgia Power",
        "regulator": "Georgia Public Service Commission (PSC)",
        "docket_number": "44280",
        "title": "Georgia Power base-rate freeze through 2028",
        "case_type": "general_rate_case",
        "status": "approved",
        "filed_date": None,
        "decided_date": "2025-07-01",
        "effective_date": None,
        "next_milestone": (
            "Storm-cost recovery handled in a separate proceeding; large-load "
            "growth scrutiny continues in the 2026 IRP round"
        ),
        "next_milestone_date": None,
        "related_tariff_id": "georgia-power-large-load-rules",
        "related_project_ids": None,
        "summary": (
            "The Georgia PSC approved a stipulation freezing Georgia Power base "
            "rates through at least 2028 — filed under docket 44280, the 2022 "
            "rate-case docket the stipulation extends — with storm costs moved "
            "to a separate proceeding. Georgia Power frames the freeze as "
            "\"balancing the mutual benefits of extraordinary economic growth "
            "among all stakeholders\"; consumer and environmental intervenors "
            "argued the plan leans on projected data-center revenue that may "
            "not materialize."
        ),
        "source_url": "https://www.georgiapower.com/about/company/filings/rate-request.html",
        "source_title": "Georgia Power — Rate Request Information (2025 base-rate freeze)",
        "resources": [
            {
                "url": "https://psc.ga.gov/search/facts-docket/?docketId=44280",
                "title": "Georgia PSC — Docket 44280",
            },
            {
                "url": (
                    "https://www.sierraclub.org/press-releases/2025/12/"
                    "sierra-club-reacts-georgia-s-utility-regulator-rushes-deal-georgia-power"
                ),
                "title": "Sierra Club — reaction to the Georgia Power deal (Dec 2025)",
            },
        ],
        "captured_at": "2026-08-03",
    },
    # ------------------------------------------------------------------ AZ
    {
        "id": "az-acc-aps-rate-case-2025",
        "state_code": "AZ",
        "utility": "Arizona Public Service (APS)",
        "regulator": "Arizona Corporation Commission (ACC)",
        "docket_number": "E-01345A-25-0105",
        "title": "APS 2025 rate case — extra-high-load-factor (data center) provisions",
        "case_type": "general_rate_case",
        "status": "pending",
        "filed_date": None,
        "decided_date": None,
        "effective_date": None,
        "next_milestone": (
            "Administrative law judge's recommended opinion and ACC open-meeting "
            "vote, following the eight-week evidentiary hearing that began "
            "May 18, 2026"
        ),
        "next_milestone_date": None,
        "related_tariff_id": "aps-arizona-large-load-rate-case-2025",
        "related_project_ids": None,
        "summary": (
            "APS requested a $579.5M (13.99%) net base-rate increase effective "
            "no earlier than July 8, 2026, including changes to minimum-bill "
            "requirements and eligibility in the Extra High Load Factor (XHLF) "
            "rate classes so large high-load-factor customers such as data "
            "centers carry the cost of serving their growth. The evidentiary "
            "hearing before an ALJ began May 18, 2026 and was scheduled to run "
            "roughly eight weeks; a recommended opinion and Commission vote "
            "follow."
        ),
        "source_url": "https://azcc.gov/news/home/2026/02/19/what-s-next-in-the-aps-rate-case",
        "source_title": "Arizona Corporation Commission — What's Next in the APS Rate Case?",
        "resources": [
            {
                "url": "https://www.aps.com/en/Utility/Regulatory-and-Legal/Rate-case",
                "title": "APS — 2025 rate case filing page",
            }
        ],
        "captured_at": "2026-08-03",
    },
    # ------------------------------------------------------------------ MO
    {
        "id": "mo-psc-ameren-large-load-2025",
        "state_code": "MO",
        "utility": "Ameren Missouri (Union Electric)",
        "regulator": "Missouri Public Service Commission (PSC)",
        "docket_number": "ET-2025-0184",
        "title": "Ameren Missouri Large Load Customer rate plan",
        "case_type": "large_load_tariff",
        "status": "approved",
        "filed_date": "2025-05-14",
        "decided_date": "2025-11-24",
        "effective_date": "2025-12-04",
        "next_milestone": None,
        "next_milestone_date": None,
        "related_tariff_id": None,
        "related_project_ids": ["google-new-florence-mo", "amazon-montgomery-city-mo"],
        "summary": (
            "The PSC approved a non-unanimous global stipulation (filed "
            "November 20, 2025; Public Counsel not a signatory) creating a "
            "Large Load Customer Service rate for new customers at or above "
            "75 MW of monthly demand — the class that covers the Warrenton and "
            "Montgomery County data-center projects. Filed under Senate Bill 4's "
            "large-load provisions (Section 393.130.7, RSMo); Amazon Data "
            "Services, Google, and Evergy intervened and signed the stipulation. "
            "The order issued November 24, 2025 and took effect December 4, 2025."
        ),
        "source_url": "https://efis.psc.mo.gov/Document/Display/858399",
        "source_title": "Missouri PSC — Order approving Large Load Customer rate plan (File No. ET-2025-0184)",
        "resources": None,
        "captured_at": "2026-08-03",
    },
    {
        "id": "mo-psc-ameren-grc-2026",
        "state_code": "MO",
        "utility": "Ameren Missouri (Union Electric)",
        "regulator": "Missouri Public Service Commission (PSC)",
        "docket_number": "ER-2026-0291",
        "title": "Ameren Missouri 2026 general rate case",
        "case_type": "general_rate_case",
        "status": "pending",
        "filed_date": "2026-04-24",
        "decided_date": None,
        "effective_date": None,
        "next_milestone": (
            "Contested-case schedule approved July 22, 2026 runs toward a "
            "decision in 2027; requested rates would take effect mid-2027"
        ),
        "next_milestone_date": None,
        "related_tariff_id": None,
        "related_project_ids": None,
        "summary": (
            "Ameren Missouri filed to adjust electric revenues (an average "
            "residential increase of roughly $13/month per press coverage), its "
            "first general rate case since the large-load rate plan took "
            "effect. The Commission suspended the tariff on July 8, 2026, "
            "established contested-case status, and approved a procedural "
            "schedule on July 22, 2026; intervenors include consumer advocates, "
            "environmental groups, and major data-center operators."
        ),
        "source_url": "https://efis.psc.mo.gov/Case/Display/105725",
        "source_title": "Missouri PSC EFIS — Case ER-2026-0291 docket sheet",
        "resources": None,
        "captured_at": "2026-08-03",
    },
    # ------------------------------------------------------------------ MN
    {
        "id": "mn-puc-xcel-large-load-2026",
        "state_code": "MN",
        "utility": "Xcel Energy (Northern States Power — Minnesota)",
        "regulator": "Minnesota Public Utilities Commission (PUC)",
        "docket_number": None,
        "title": "Xcel Minnesota large-load tariff approval",
        "case_type": "large_load_tariff",
        "status": "approved",
        "filed_date": None,
        "decided_date": "2026-05-15",
        "effective_date": None,
        "next_milestone": (
            "Xcel must file a separate clean energy and capacity tariff for "
            "very large customers by December 1, 2026"
        ),
        "next_milestone_date": "2026-12-01",
        "related_tariff_id": "xcel-minnesota-large-load-tariff",
        "related_project_ids": None,
        "summary": (
            "The Minnesota PUC approved Xcel Energy's large-load tariff for "
            "customers of 100 MW or more: 15-year minimum contracts, an 80% "
            "demand-charge obligation on early exit, and a new dedicated rate "
            "class so data-center costs are assigned transparently in future "
            "rate cases. The Commission also directed Xcel to file a separate "
            "clean energy and capacity tariff by December 1, 2026. Minnesota "
            "Power and Otter Tail Power have filed similar proposals."
        ),
        "source_url": "https://fresh-energy.org/regulatory-update-commission-approves-xcel-energys-large-load-tariff",
        "source_title": "Fresh Energy — Commission approves Xcel Energy's large load tariff",
        "resources": [
            {
                "url": "https://elpc.org/news/final-order-encourages-affordable-clean-energy-for-minnesotans/",
                "title": "ELPC — Final order encourages affordable, clean energy for Minnesotans",
            },
            {
                "url": (
                    "https://newsroom.xcelenergy.com/news/"
                    "xcel-energy-proposal-protects-customers-from-higher-bills-as-data-center-demand-grows"
                ),
                "title": "Xcel Energy — proposal protects customers from higher bills as data center demand grows",
            },
        ],
        "captured_at": "2026-08-03",
    },
    # ------------------------------------------------------------------ IN
    {
        "id": "in-iurc-nipsco-amazon-2026",
        "state_code": "IN",
        "utility": "NIPSCO (Northern Indiana Public Service Company)",
        "regulator": "Indiana Utility Regulatory Commission (IURC)",
        "docket_number": "Cause No. 46362",
        "title": "NIPSCO / Amazon special contract, GenCo PPA, and generation plan",
        "case_type": "special_contract",
        "status": "approved",
        "filed_date": "2025-11-07",
        "decided_date": "2026-06-17",
        "effective_date": None,
        "next_milestone": (
            "NIPSCO GenCo's separate joint petition (filed April 16, 2026) on "
            "generation financing remains before the IURC"
        ),
        "next_milestone_date": None,
        "related_tariff_id": None,
        "related_project_ids": ["amazon-wheatfield-in"],
        "summary": (
            "The IURC approved NIPSCO's settlement, its special contract with "
            "Amazon Data Services (dated September 18, 2025), and a power "
            "purchase agreement with NIPSCO GenCo, alongside combined-cycle gas "
            "and battery storage resources for northern Indiana data-center "
            "load. NiSource states the framework has data-center customers fund "
            "the generation and transmission infrastructure required to serve "
            "them and projects roughly $1.4 billion in savings for existing "
            "customers."
        ),
        "source_url": "https://secure.in.gov/iurc/files/ord_46362_061726.pdf",
        "source_title": "IURC — Order in Cause No. 46362 (June 17, 2026)",
        "resources": [
            {
                "url": (
                    "https://www.nisource.com/news/article/regulatory-approvals-underscore-"
                    "strength-of-nisource-s-customer-focused-data-center-strategy-"
                    "supporting-growth-in-indiana"
                ),
                "title": "NiSource — regulatory approvals for the data-center strategy",
            }
        ],
        "captured_at": "2026-08-03",
    },
    # ------------------------------------------------------------------ NC
    {
        "id": "nc-ncuc-duke-settlement-2026",
        "state_code": "NC",
        "utility": "Duke Energy Carolinas",
        "regulator": "North Carolina Utilities Commission (NCUC)",
        "docket_number": "E-7, Sub 1329",
        "title": "Duke rate-case settlement — expedited large-load tariff track",
        "case_type": "large_load_tariff",
        "status": "pending",
        "filed_date": None,
        "decided_date": None,
        "effective_date": None,
        "next_milestone": (
            "Duke and Public Staff must submit the special large-load tariff by "
            "the end of September 2026; a final NCUC order on the settlement is "
            "expected in fall 2026, with new rates beginning January 1, 2027 if "
            "approved"
        ),
        "next_milestone_date": "2026-09-30",
        "related_tariff_id": "duke-nc-large-load-rate-case-2025",
        "related_project_ids": None,
        "summary": (
            "Duke Energy's proposed 2026 rate-case settlement commits it to an "
            "expedited proceeding to establish a formal Large Load Tariff "
            "before new rates take effect. Governor Josh Stein and Attorney "
            "General Jeff Jackson are pressing Duke — a Ratepayer Protection "
            "Pledge signatory — to make the federal pledge binding: \"Now, Duke "
            "Energy must make that voluntary pledge real. The North Carolina "
            "Utilities Commission and Duke Energy must create a legally binding "
            "large-load tariff to charge data centers their full freight\" "
            "(Stein). Duke's spokesperson responds that \"data centers and "
            "other large-load customers must pay the costs required to serve "
            "them while creating long-term value for existing customers.\""
        ),
        "source_url": "https://www.wral.com/news/nccapitol/duke-energy-data-center-pledge-north-carolina-july-2026/",
        "source_title": "WRAL — NC leaders push Duke Energy to make federal data center pledge legally binding",
        "resources": [
            {
                "url": (
                    "https://blogs.edf.org/climate411/2026/07/23/"
                    "duke-energy-settlement-beginning-north-carolina-data-center-energy-policy/"
                ),
                "title": "EDF — The Duke Energy settlement is just the beginning for NC data center energy policy",
            }
        ],
        "captured_at": "2026-08-03",
    },
    # ------------------------------------------------------------------ NV
    {
        "id": "nv-pucn-google-esa-2026",
        "state_code": "NV",
        "utility": "NV Energy (Sierra Pacific Power)",
        "regulator": "Public Utilities Commission of Nevada (PUCN)",
        "docket_number": "26-06023",
        "title": "Second NV Energy / Google (Callisto) energy supply agreement",
        "case_type": "special_contract",
        "status": "pending",
        "filed_date": "2026-06-26",
        "decided_date": None,
        "effective_date": None,
        "next_milestone": (
            "Procedural schedule and hearing follow the July 28, 2026 "
            "prehearing conference"
        ),
        "next_milestone_date": None,
        "related_tariff_id": "nv-energy-callisto-esa",
        "related_project_ids": None,
        "summary": (
            "Sierra Pacific Power (NV Energy) and Callisto Enterprises — "
            "identified in the Commission's own notice as \"Google\" — filed a "
            "joint application for approval of a second energy supply "
            "agreement. The public notice set an intervention deadline of "
            "July 22, 2026 and a prehearing conference for July 28, 2026. The "
            "first Callisto ESA (Docket 24-06014) was approved by stipulation "
            "in April 2026 after adopting the PUCN's model methodologies for "
            "large-customer market pricing."
        ),
        "source_url": "https://www.nevadaappeal.com/news/2026/jul/14/carson-city-legal-63311/",
        "source_title": "PUCN legal notice (Nevada Appeal) — Docket No. 26-06023 application and prehearing conference",
        "resources": None,
        "captured_at": "2026-08-03",
    },
    # ------------------------------------------------------------- Federal
    {
        "id": "ferc-rm26-4-large-loads",
        "state_code": "US",
        "jurisdiction_level": "federal",
        "utility": "All FERC-jurisdictional transmission providers",
        "regulator": "Federal Energy Regulatory Commission (FERC)",
        "docket_number": "RM26-4-000",
        "title": "Large-load interconnection rulemaking (DOE-directed ANOPR)",
        "case_type": "rulemaking",
        "status": "pending",
        "filed_date": "2025-10-23",
        "decided_date": None,
        "effective_date": None,
        "next_milestone": (
            "Grid operators respond to the Commission's June 2026 directive to "
            "reform large-load interconnection procedures"
        ),
        "next_milestone_date": None,
        "related_tariff_id": None,
        "related_project_ids": None,
        "summary": (
            "On October 23, 2025 the Secretary of Energy directed FERC to "
            "consider reforms for interconnecting large loads (generally over "
            "20 MW) to the interstate transmission system. On April 16, 2026 "
            "FERC committed to act by June 2026, citing its December 2025 PJM "
            "co-located-load order, approval of SPP's High Impact Large Load "
            "protocols, and the President's Ratepayer Protection Pledge among "
            "recent developments; in June 2026 it directed grid operators to "
            "reform large-load interconnection procedures, with compliance "
            "work ongoing."
        ),
        "source_url": "https://www.ferc.gov/rm26-4",
        "source_title": "FERC — Interconnection of Large Loads to the Interstate Transmission System (RM26-4-000)",
        "resources": [
            {
                "url": "https://www.ferc.gov/news-events/news/ferc-act-large-load-interconnection-docket-june-2026",
                "title": "FERC — FERC to Act on Large Load Interconnection Docket by June 2026",
            }
        ],
        "captured_at": "2026-08-03",
    },
    {
        "id": "ferc-pjm-colocated-el25-49",
        "state_code": "US",
        "jurisdiction_level": "federal",
        "utility": "PJM Interconnection",
        "regulator": "Federal Energy Regulatory Commission (FERC)",
        "docket_number": "EL25-49-000",
        "title": "PJM co-located load rules (data centers at power plants)",
        "case_type": "rulemaking",
        "status": "pending",
        "filed_date": None,
        "decided_date": None,
        "effective_date": None,
        "next_milestone": (
            "Further PJM compliance filings after FERC's April 2026 partial "
            "acceptance"
        ),
        "next_milestone_date": None,
        "related_tariff_id": "ferc-talen-amazon-susquehanna-isa",
        "related_project_ids": None,
        "summary": (
            "In December 2025 FERC found PJM's tariff unjust and unreasonable "
            "for lacking clear rules on co-located load — data centers sited at "
            "generators — and ordered transparent rules, the question first "
            "raised by the rejected Talen/Amazon Susquehanna amended ISA. In "
            "April 2026 FERC partially accepted PJM's compliance filing, "
            "keeping interconnection-pathway clarity while rejecting PJM's "
            "attempt to redefine 'Co-Located Load' and to alter behind-the-"
            "meter application requirements."
        ),
        "source_url": "https://www.ferc.gov/news-events/news/ferc-act-large-load-interconnection-docket-june-2026",
        "source_title": "FERC — April 2026 release recapping the December 2025 PJM co-located-load order",
        "resources": [
            {
                "url": (
                    "https://www.bdlaw.com/publications/"
                    "ferc-orders-pjm-to-create-clear-rules-for-co-located-data-centers-and-large-loads/"
                ),
                "title": "Beveridge & Diamond — FERC orders PJM to create clear rules for co-located data centers",
            },
            {
                "url": (
                    "https://www.bakerbotts.com/thought-leadership/publications/2025/december/"
                    "ferc-issues-order-providing-guidance-for-co-locating-power-plants-with-data-centers-within-pjm"
                ),
                "title": "Baker Botts — FERC order providing guidance for co-locating power plants with data centers in PJM",
            },
        ],
        "captured_at": "2026-08-03",
    },
]


def main() -> int:
    payload = {"generated_at": GENERATED_AT, "rate_cases": RATE_CASES}
    validated = RateCasesPayload.model_validate(payload)
    out = ROOT / "data" / "seed" / "rate_cases.json"
    out.write_text(
        json.dumps(json.loads(validated.model_dump_json()), indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {out} with {len(validated.rate_cases)} rate cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
