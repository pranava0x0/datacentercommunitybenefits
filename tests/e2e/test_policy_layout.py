"""Shared summary strips and policy entries remain readable across navigation."""
import json
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e
ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize('width', [375, 1366])
def test_summary_strips_stay_visible_and_headings_keep_ink(page: Page, base_url: str, width: int) -> None:
    page.set_viewport_size({'width': width, 'height': 812})
    page.goto(base_url + '/#policies')
    expect(page.locator('#policy-stats .rp-stat')).to_have_count(5)
    for group, view, stats in [('pol', 'policies', 'policy-stats')]:
        page.click('#tab-' + view)
        assert page.locator('#view-' + view).evaluate('e => getComputedStyle(e).opacity') == '1'
        strip = page.locator('#' + stats)
        count = strip.locator('.rp-stat').count()
        keys = page.evaluate('(group) => SUBTAB_GROUPS[group]', group)
        for key in keys:
            page.click(f'#subtab-{group}-{key}')
            expect(strip).to_be_visible()
            expect(strip.locator('.rp-stat')).to_have_count(count)
            assert strip.locator('.rp-stat').first.evaluate('e => getComputedStyle(e).borderTopWidth') == '0px'
            assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
    expect(page.locator('#subtab-pol-influence')).to_have_count(0)
    page.click('#tab-elections')
    expect(page.locator('.election-row')).to_have_count(54)
    expect(page.locator('#elections-stats')).to_have_count(0)
    ink = page.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--text").trim()')
    heading_color = page.locator('#view-elections h2').evaluate('e => getComputedStyle(e).color')
    assert heading_color == page.evaluate('(ink) => {const s=document.createElement("span");s.style.color=ink;document.body.append(s);const c=getComputedStyle(s).color;s.remove();return c;}', ink)


def test_framework_gaps_are_source_linked_and_latest_does_not_repeat_same_order(page: Page, base_url: str) -> None:
    policies = json.loads((ROOT / 'data/seed/policies.json').read_text())
    new_ids = {'ny-eo62-data-center-review-community-framework-2026', 'tx-data-center-audit-permit-directives-2026',
               'fayetteville-ga-data-center-zoning-prohibition-2026', 'loudoun-county-va-data-center-special-exception'}
    policies['policies'] = [item for item in policies['policies'] if item['id'] in new_ids]
    moratoriums = json.loads((ROOT / 'data/seed/moratoriums.json').read_text())
    moratoriums['moratoriums'] = [item for item in moratoriums['moratoriums'] if item['id'] in {'ny-state-eo62-2026-07', 'sabattus-me-2026-11'}]
    page.route('**/data/policies.json', lambda route: route.fulfill(json=policies))
    page.route('**/data/moratoriums.json', lambda route: route.fulfill(json=moratoriums))
    page.goto(base_url + '/#policies/latest')
    expect(page.locator('#policy-actions .pb-action')).to_have_count(5)
    expect(page.locator('.pb-action-text').filter(has_text='New York EO 62')).to_have_count(1)
    expect(page.locator('.pb-action-text').filter(has_text='Sabattus')).to_have_count(1)
    page.click('#subtab-pol-rules')
    expect(page.locator('#policies-tbody tr[role="button"]')).to_have_count(4)
    page.locator('#policies-tbody tr').filter(has_text='Loudoun').click()
    expect(page.locator('#pd-date')).to_have_text('2025-03-18')
    expect(page.locator('#pd-terms')).to_contain_text('special-exception')


def test_unknown_dates_and_reasons_do_not_look_like_empty_cells(page: Page, base_url: str) -> None:
    payload = json.loads((ROOT / 'data/seed/moratoriums.json').read_text())
    record = next(r for r in payload['moratoriums'] if r['status'] == 'enacted')
    record.update(enacted_date=None, key_reasons=[])
    payload['moratoriums'] = [record]
    page.route('**/data/moratoriums.json', lambda route: route.fulfill(json=payload))
    page.goto(base_url + '/#moratoriums')
    row = page.locator('#moratoriums-tbody tr[role=button]')
    expect(row.locator('td').last).to_have_text('Not stated')
    row.click()
    expect(page.locator('#md-enacted')).to_have_text('Not stated')


@pytest.mark.parametrize('width', [375, 641, 820, 1100, 1366])
def test_labeled_filters_keep_primary_controls_visible(page: Page, base_url: str, width: int) -> None:
    page.set_viewport_size({'width': width, 'height': 812})
    page.goto(base_url + '/#policies/rules')
    expect(page.locator('#policies-tbody tr[role=button]').first).to_be_visible()
    for field in ['policy-instrument-filter', 'policy-status-filter', 'policy-state-filter', 'policy-cbf-filter']:
        expect(page.locator('#' + field)).to_be_visible()
    expect(page.locator('#policy-scope-filter')).to_be_hidden()
    page.locator('.directory-more-filters summary').click()
    expect(page.locator('#policy-scope-filter')).to_be_visible()
    page.select_option('#policy-scope-filter', 'state')
    assert page.locator('#policies-tbody tr[role=button]').count() > 0
    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
    assert page.locator('.tabbar').evaluate('e=>e.scrollWidth<=e.clientWidth')
    assert page.locator('.tabbar .tab').evaluate_all('nodes=>nodes.every(n=>n.innerText.trim().length > 0)')
    # One name per tab at every width (UX audit 2026-11-09): no short variants.
    expect(page.locator('#tab-world')).to_have_text('International', use_inner_text=True)
    if width <= 1100:
        assert page.locator('.tabbar').evaluate('e=>getComputedStyle(e).gridTemplateColumns.split(" ").length') == 5

@pytest.mark.parametrize(("file", "missing", "unaffected"), [
    ("moratoriums", "pauses", "principles"), ("policies", "rules", "pauses"),
])
def test_latest_keeps_available_actions_when_one_feed_fails(page: Page, base_url: str, file: str, missing: str, unaffected: str) -> None:
    route = f"**/data/{file}.json"
    page.route(route, lambda req: req.abort())
    page.goto(base_url + "/#policies/latest")
    expect(page.locator("#policy-error-message")).to_have_text(f"Could not load {missing}.")
    expect(page.locator("#policy-actions li").first).to_be_visible()
    page.click(f"#subtab-pol-{unaffected}")
    expect(page.locator("#policy-pane-error")).to_be_hidden()
    page.click("#subtab-pol-latest")
    expect(page.locator("#policy-retry")).to_be_visible()
    page.unroute(route)
    page.click("#policy-retry")
    expect(page.locator("#policy-pane-error")).to_be_hidden()
    expect(page.locator("#policy-actions li").first).to_be_visible()


def test_pause_example_retries_and_restores_focus_after_repeated_activation(page: Page, base_url: str) -> None:
    route = "**/data/moratoriums.json"
    page.route(route, lambda req: req.abort())
    page.goto(base_url + "/#policies")
    card = page.locator('[data-principle="incentive_terms"]')
    card.locator("summary").click()
    trigger = card.get_by_role("button", name="HB4084", exact=True)
    trigger.click()
    expect(card).to_contain_text("Could not load record")
    page.unroute(route)
    # Queue two activations before the network can settle.
    trigger.evaluate("btn => { btn.click(); btn.click(); }")
    expect(page.locator("#moratorium-modal")).to_be_visible()
    page.keyboard.press("Escape")
    expect(trigger).to_be_focused()
    expect(card).not_to_contain_text("Could not load record")
