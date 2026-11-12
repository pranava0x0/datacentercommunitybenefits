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
    page.get_by_role('button', name='County and state drafts', exact=True).click()
    expect(page.locator('#draft-plan-decision')).to_be_visible()
    assert page.url.endswith('#policies/agreements/drafts')
    expect(page.locator('#cba-stats')).to_be_visible()
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
    assert page.url.endswith('#policies/agreements/evidence')
    page.get_by_text('Water permission and water use', exact=True).click()
    expect(page.locator('[data-evidence-answer]').first).to_have_text('Actual water consumption is not established.')
    expect(page.locator('[data-evidence-status]').first).to_contain_text('actual use')
    expect(page.locator('[data-evidence-limit]').first).to_contain_text('does not show actual withdrawal')
    expect(page.locator('#subpane-cba-evidence')).to_contain_text('were not authenticated')
    expect(page.locator('#subpane-cba-evidence')).to_contain_text('does not show actual withdrawal')
    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
    assert page.locator('#subpane-pol-agreements > .subtabs').evaluate('(e) => e.scrollWidth <= e.clientWidth + 1')
    page.get_by_role('tab', name='Terms', exact=False).click()
    expect(page.locator('#cba-stats')).to_be_visible()
    assert not errors


def test_guide_deep_link_and_keyboard(page, base_url):
    page.goto(base_url + '/#agreements/drafts')
    expect(page.locator('#draft-plan-decision')).to_be_visible()
    page.locator('#subtab-cba-drafts').focus()
    page.keyboard.press('ArrowRight')
    expect(page.locator('#subtab-cba-evidence')).to_be_focused()
    expect(page.locator('#impact-evidence-rule')).to_be_visible()
    page.reload()
    expect(page.locator('#impact-evidence-rule')).to_be_visible()
    assert page.url.endswith('#policies/agreements/evidence')


def test_guide_import_failure_can_retry(page, base_url):
    page.route('**/community-plans.js', lambda route: route.abort(), times=1)
    page.goto(base_url)
    page.get_by_role('button', name='County and state drafts', exact=True).click()
    expect(page.locator('#subpane-cba-drafts')).to_contain_text("Couldn't load")
    page.get_by_role('tab', name='Terms', exact=False).click()
    page.get_by_role('tab', name='Draft plans', exact=True).click()
    expect(page.locator('#draft-plan-decision')).to_be_visible()


@pytest.mark.parametrize("width", [375, 1366])
def test_blueprint_share_links_and_complete_downloads(page, base_url, width, tmp_path):
    page.set_viewport_size({"width": width, "height": 812})
    page.goto(base_url)
    entry = page.get_by_role("link", name="Community benefits plans", exact=True)
    expect(entry).to_be_in_viewport(ratio=1)
    page.get_by_role("tab", name="Policy", exact=True).click()
    expect(entry).to_be_in_viewport(ratio=1)
    entry.click()
    assert page.url.endswith("/community-benefits.html")
    for key, label in [("rural", "rural county"), ("town", "growing town or suburb"),
                       ("urban", "dense urban neighborhood"), ("corridor", "multi-campus corridor")]:
        page.locator(f'#choose a[href="#{key}"]').click()
        page.reload()
        article = page.locator(f"article#{key}")
        expect(article.locator("h2")).to_be_in_viewport()
        with page.expect_download() as event:
            article.get_by_role("button", name=f"Download {label} draft (.txt)", exact=True).click()
        path = tmp_path / event.value.suggested_filename
        event.value.save_as(path)
        draft = path.read_text()
        assert article.locator("h2").inner_text() in draft
        assert all(s in draft for s in ("Terms every draft", "If your community has a moratorium", "What informed"))
        assert "https://pranava0x0.github.io/datacenterpolicytracker/index.html?" in draft
        assert "(.txt)" not in draft and "Fill in one row" in draft
        article.get_by_role("link", name="Choose another draft").click()
    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")


def test_blueprint_print_urls_fit_the_page(page, base_url):
    page.set_viewport_size({"width": 650, "height": 900})
    page.goto(base_url + "/community-benefits.html")
    page.emulate_media(media="print")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
