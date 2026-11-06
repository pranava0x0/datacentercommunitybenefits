"""Election flows use deliberately mixed results, offices and legal effects."""

import json
from copy import deepcopy

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def evidence(statement: str, speaker: str = "") -> dict:
    item = {"statement": statement, "source_url": "https://example.org/source",
            "source_title": "Dated source", "captured_at": "2026-11-04"}
    if speaker:
        item["speaker"] = speaker
    return item


@pytest.fixture
def election_data() -> dict:
    race = {"id": "tx-governor-2026", "state_code": "TX", "jurisdiction": "Texas", "office": "Governor",
            "level": "governor", "election_date": "2026-11-03", "captured_at": "2026-11-04",
            "outgoing": {"name": "Alex", "party": "Republican", "evidence": evidence("Alex is the governor."),
                         "statements": [evidence("Approvals depend on completing the audit.", "Alex")]},
            "candidates": [{"name": "Jordan", "party": "Democratic", "review_note": "Campaign page reviewed.",
                            "statements": [evidence("We should pause new approvals.", "Jordan")]},
                           {"name": "Losing challenger", "party": "Republican", "statements": [evidence("Build everywhere.", "Losing challenger")]}],
            "result": {"status": "reported", "winner": "Jordan", "source_type": "news", "evidence": evidence("Jordan won.")},
            "proposed_changes": [{"topic": "Permit pause", "summary": "Jordan proposes a new pause; Alex tied approvals to an audit.",
                                  "source_urls": ["https://example.org/source"]}],
            "related_moratorium_ids": [], "related_policy_ids": []}
    unverified = deepcopy(race)
    unverified.update(id="ak-governor-2026", jurisdiction="Alaska", state_code="AK", result={"status": "unverified"})
    local = deepcopy(race)
    local.update(id="md-county-2026", jurisdiction="A county", state_code="MD", office="County Executive", level="county")
    local["outgoing"] = {"name": "Jordan", "party": "Democratic", "evidence": evidence("Jordan holds the office."), "statements": []}
    measure = {"id": "oh-advisory-2026", "state_code": "OH", "jurisdiction": "One town", "title": "Question 1",
               "election_date": "2026-11-03", "captured_at": "2026-11-04", "effect": "advisory",
               "ballot_evidence": evidence("Should council consider a pause?"),
               "legal_effect": "Advises council; does not change local law.",
               "result": {"status": "reported", "outcome": "passed", "source_type": "official", "evidence": evidence("Yes won.")},
               "related_moratorium_ids": [], "related_policy_ids": []}
    return {"generated_at": "2026-11-05", "election_date": "2026-11-03", "calendar": evidence("Election day November 3."),
            "races": [race, unverified, local], "measures": [measure], "coverage_notes": ["Local races are a selected sample."]}


@pytest.fixture
def elections(page: Page, election_data: dict) -> Page:
    page.route("**/data/elections.json", lambda route: route.fulfill(json=election_data))
    return page


def test_home_does_not_load_election_module_or_payload(page: Page, base_url: str) -> None:
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    page.goto(base_url)
    expect(page.locator("#home-latest-list .feed-item").first).to_be_attached()
    assert not any("elections.js" in url or "data/elections.json" in url for url in requests)


def test_winner_and_actual_prior_policy_visible_without_disclosure(elections: Page, base_url: str) -> None:
    elections.goto(base_url + "/#elections")
    expect(elections.locator(".election-row")).to_have_count(3)
    row = elections.locator("#election-tx-governor-2026")
    expect(row.locator(".election-result")).to_contain_text("Jordan (Democratic)")
    expect(row.locator(".election-transition")).to_contain_text("Alex (Republican)")
    expect(row.locator(".election-summary")).to_contain_text("Jordan proposes a new pause")
    expect(row.locator(".election-summary a")).to_have_attribute("href", "https://example.org/source")
    expect(row.locator(".election-result a")).to_have_attribute("href", "https://example.org/source")
    expect(elections.locator(".election-card")).to_have_count(0)
    expect(elections.locator("blockquote")).to_have_count(0)
    expect(elections.locator("#elections-stats .rp-stat-value")).to_have_text(["2", "1", "1", "1"])
    expect(row).not_to_contain_text("Losing challenger")
    expect(elections.locator("#elections-content")).not_to_contain_text("certified")
    expect(elections.locator("#elections-content")).not_to_contain_text("in this pass")
    expect(elections.locator("#election-ak-governor-2026")).to_have_count(0)
    toggle = row.get_by_role("button", name="Compare details:")
    toggle.focus()
    elections.keyboard.press("Enter")
    expect(toggle).to_have_attribute("aria-expanded", "true")
    detail = elections.locator("#election-details-tx-governor-2026")
    expect(detail.locator(".election-candidate")).to_have_count(2)
    expect(detail.locator("blockquote").last).to_have_text("Approvals depend on completing the audit.")
    expect(detail.locator(".election-evidence").first).to_contain_text("Accessed 2026-11-04")
    elections.keyboard.press("Space")
    expect(toggle).to_have_attribute("aria-expanded", "false")
    expect(detail).to_be_hidden()
    elections.locator("#election-md-county-2026 .election-toggle").click()
    expect(elections.locator("#election-details-md-county-2026 .election-candidate")).to_have_count(1)


def test_filters_and_search_include_prior_and_policy(elections: Page, base_url: str) -> None:
    elections.goto(base_url + "/#elections")
    elections.locator("#election-tx-governor-2026 .election-toggle").click()
    elections.select_option("#elections-status", "party")
    expect(elections.locator(".election-card")).to_have_count(0)
    expect(elections.locator(".election-row")).to_have_count(1)
    elections.select_option("#elections-state", "OH")
    expect(elections.locator(".election-empty")).to_have_text("No matching policies.")
    elections.click("#elections-reset")
    elections.select_option("#elections-status", "reelected")
    expect(elections.locator(".election-row")).to_have_count(1)
    expect(elections.locator(".election-result")).to_contain_text("Re-elected")
    elections.click("#elections-reset")
    for query in ("Jordan Texas", "Alex Texas", "audit Texas", "Permit pause Texas"):
        elections.fill("#elections-q", query)
        expect(elections.locator(".election-row")).to_have_count(1)
    elections.fill("#elections-q", "Losing challenger")
    expect(elections.locator(".election-row")).to_have_count(0)
    elections.fill("#elections-q", "does not change local law")
    expect(elections.locator(".election-row")).to_have_count(1)


def test_advisory_passage_stays_distinct_from_a_law(elections: Page, base_url: str) -> None:
    elections.goto(base_url + "/#elections")
    elections.select_option("#elections-kind", "measure")
    card = elections.locator(".election-row")
    expect(card).to_have_count(1)
    expect(card).to_contain_text("Advisory question")
    expect(card).to_contain_text("does not change local law")
    expect(card.locator(".election-result a")).to_have_attribute("href", "https://example.org/source")
    expect(card.locator("[data-related-record]")).to_have_count(0)


@pytest.mark.parametrize("prior_party", ["Democratic Party", "Unknown"])
def test_party_filter_accepts_aliases_and_preserves_unknown_affiliation(page: Page, base_url: str, election_data: dict, prior_party: str) -> None:
    race = election_data["races"][0]
    race["outgoing"]["party"] = prior_party
    # The winner is Democratic, so an alternate spelling is not a party flip.
    page.route("**/data/elections.json", lambda route: route.fulfill(json=election_data))
    page.goto(base_url + "/#elections")
    page.select_option("#elections-status", "party")
    expect(page.locator(".election-row")).to_have_count(0)
    page.select_option("#elections-status", "changes")
    expect(page.locator(".election-row")).to_have_count(1)


def test_direct_record_url_and_back(elections: Page, base_url: str) -> None:
    elections.goto(base_url + "/#elections/tx-governor-2026")
    expect(elections.locator("#election-details-tx-governor-2026 .election-candidates")).to_be_visible()
    elections.click("#tab-moratoriums")
    expect(elections.locator("#view-moratoriums")).to_be_visible()
    elections.go_back()
    expect(elections.locator("#election-details-tx-governor-2026 .election-candidates")).to_be_visible()
    expect(elections).to_have_url(base_url + "/#elections/tx-governor-2026")


def test_failed_load_can_retry(page: Page, base_url: str, election_data: dict) -> None:
    attempts = []

    def respond(route) -> None:
        attempts.append(1)
        if len(attempts) == 1:
            route.fulfill(status=503, body="Unavailable")
        else:
            route.fulfill(json=election_data)

    page.route("**/data/elections.json", respond)
    page.goto(base_url + "/#elections/tx-governor-2026")
    page.get_by_role("button", name="Retry election records").click()
    expect(page.locator(".election-row")).to_have_count(3)
    expect(page.locator("#election-details-tx-governor-2026 .election-candidates")).to_be_visible()
    expect(page).to_have_url(base_url + "/#elections/tx-governor-2026")
    assert len(attempts) == 2


def test_genuinely_empty_data_is_not_a_failed_request(page: Page, base_url: str, election_data: dict) -> None:
    election_data.update(races=[], measures=[])
    page.route("**/data/elections.json", lambda route: route.fulfill(json=election_data))
    page.goto(base_url + "/#elections")
    expect(page.locator(".election-empty")).to_contain_text("No policy records available.")
    expect(page.get_by_role("button", name="Retry election records")).to_have_count(0)


@pytest.mark.parametrize("width", [360, 375, 390, 1366])
def test_layout_and_keyboard_sources(elections: Page, base_url: str, width: int) -> None:
    elections.set_viewport_size({"width": width, "height": 812})
    elections.goto(base_url + "/#elections/tx-governor-2026")
    expect(elections.locator("#election-details-tx-governor-2026 .election-candidates")).to_be_visible()
    assert elections.evaluate("document.documentElement.scrollWidth <= innerWidth")
    # A wrapping row must not inherit the generic filter bar's column layout:
    # mobile flex-basis values would become 140px-tall empty rows.
    assert elections.locator(".election-filters").evaluate("e => e.getBoundingClientRect().height") < 260
    assert elections.evaluate("new Set([...document.querySelectorAll('.tab')].map(t => Math.round(t.getBoundingClientRect().top))).size") <= 2
    source = elections.locator("#election-tx-governor-2026 .election-summary a")
    source.focus()
    expect(source).to_be_focused()
    expect(source).to_have_attribute("rel", "noopener noreferrer")


def test_missing_positions_and_sourced_positions_without_topics(page: Page, base_url: str, election_data: dict) -> None:
    race = election_data["races"][0]
    race["proposed_changes"] = []
    race["outgoing"]["statements"] = []
    page.route("**/data/elections.json", lambda route: route.fulfill(json=election_data))
    page.goto(base_url + "/#elections")
    summary = page.locator("#election-tx-governor-2026 .election-summary")
    expect(summary).to_contain_text("Jordan: We should pause new approvals.")
    expect(summary).to_contain_text("Alex: no sourced data-center position available.")
    expect(summary.locator("a")).to_have_attribute("href", "https://example.org/source")


def test_live_summary_keeps_all_records_and_texas_topics(page: Page, base_url: str) -> None:
    page.goto(base_url + "/#elections")
    expect(page.locator(".election-row[data-kind='race']")).to_have_count(37)
    expect(page.locator(".election-row[data-kind='measure']")).to_have_count(17)
    expect(page.locator(".election-card")).to_have_count(0)
    row = page.locator(".election-row").first
    expect(row).to_have_attribute("id", "election-tx-governor-2026")
    expect(row.locator(".election-summary")).to_contain_text("immediate moratorium")
    expect(row.locator(".election-summary")).to_contain_text("ERCOT and water-board audits")
    expect(row.locator(".election-summary")).to_contain_text("Residential electricity rates")
    expect(row.locator(".election-summary")).to_contain_text("Tax incentives")
    expect(row.locator(".election-topic")).to_have_count(4)


def test_live_legal_record_opens_from_summary(page: Page, base_url: str) -> None:
    page.goto(base_url + "/#elections")
    page.locator("#elections-q").fill("Sabattus")
    expect(page.locator(".election-card")).to_have_count(0)
    page.locator('.election-row [data-related-record="sabattus-me-2026-11"]').click()
    expect(page.locator("#md-jurisdiction")).to_have_text("Sabattus")
    expect(page.locator(".election-card")).to_have_count(0)
