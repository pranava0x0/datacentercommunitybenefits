"""Draft navigation, evidence limits and the editable artifact users receive."""
import pytest
from playwright.sync_api import expect


@pytest.mark.parametrize('width', [375, 390, 1366])
def test_plans_and_evidence(page, base_url, width, tmp_path):
    page.set_viewport_size({'width': width, 'height': 844})
    errors = []
    page.on('pageerror', lambda err: errors.append(str(err)))
    requests = []
    page.on('request', lambda req: requests.append(req.url))
    page.goto(base_url)
    expect(page.locator('#home-latest-list .feed-item').first).to_be_visible()
    assert not any('community-plans.js' in url for url in requests)
    page.get_by_role('button', name='Draft a benefit plan', exact=True).click()
    expect(page.locator('#draft-plan-decision')).to_be_visible()
    assert page.url.endswith('#policies/drafts')
    expect(page.locator('#policy-stats')).to_be_hidden()
    expect(page.locator('.guide-notice')).to_contain_text('example numbers are invented')
    for key, heading, sections in [('county', 'County plan', 8), ('state', 'State framework', 6)]:
        page.locator('#draft-plan-kind').select_option(key)
        expect(page.locator('#draft-plan-content h3')).to_contain_text(heading)
        assert page.locator('#draft-plan-content .guide-clause').count() == sections + 2
        with page.expect_download() as event:
            page.get_by_role('button', name='Download draft (.md)').click()
        download = event.value
        assert download.suggested_filename == f'{key}-community-benefits-draft.md'
        path = tmp_path / download.suggested_filename
        download.save_as(path)
        text = path.read_text()
        assert 'not adopted policies' in text and 'invented negotiation examples' in text
        assert text.count('- Owner:') == sections
        assert text.count('- Remedy:') == sections
        assert '## Before signing' in text and '## Sources and adaptation' in text
        assert 'regs.maryland.gov' in text and 'nj.gov' in text
    page.get_by_role('tab', name='Evidence', exact=True).click()
    expect(page.locator('#impact-evidence-rule')).to_be_visible()
    assert page.url.endswith('#policies/evidence')
    page.get_by_text('Water permission and water use', exact=True).click()
    expect(page.locator('[data-evidence-answer]').first).to_have_text('Actual water consumption is not established.')
    expect(page.locator('[data-evidence-status]').first).to_contain_text('actual use')
    expect(page.locator('[data-evidence-limit]').first).to_contain_text('does not show actual withdrawal')
    expect(page.locator('#subpane-pol-evidence')).to_contain_text('were not authenticated')
    expect(page.locator('#subpane-pol-evidence')).to_contain_text('does not show actual withdrawal')
    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
    assert page.locator('#view-policies > .subtabs').evaluate('(e) => e.scrollWidth <= e.clientWidth + 1')
    page.get_by_role('tab', name='Principles', exact=False).click()
    expect(page.locator('#policy-stats')).to_be_visible()
    assert not errors


def test_guide_deep_link_and_keyboard(page, base_url):
    page.goto(base_url + '/#policies/drafts')
    expect(page.locator('#draft-plan-decision')).to_be_visible()
    page.locator('#subtab-pol-drafts').focus()
    page.keyboard.press('ArrowRight')
    expect(page.locator('#subtab-pol-evidence')).to_be_focused()
    expect(page.locator('#impact-evidence-rule')).to_be_visible()
    page.reload()
    expect(page.locator('#impact-evidence-rule')).to_be_visible()
    assert page.url.endswith('#policies/evidence')


def test_guide_import_failure_can_retry(page, base_url):
    page.route('**/community-plans.js', lambda route: route.abort(), times=1)
    page.goto(base_url)
    page.get_by_role('button', name='Draft a benefit plan', exact=True).click()
    expect(page.locator('#subpane-pol-drafts')).to_contain_text("Couldn't load")
    page.get_by_role('tab', name='Principles', exact=False).click()
    page.get_by_role('tab', name='Draft plans', exact=True).click()
    expect(page.locator('#draft-plan-decision')).to_be_visible()
