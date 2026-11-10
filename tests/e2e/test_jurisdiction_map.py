"""The map stays lazy, works in the file preview, and links canonical records."""
from pathlib import Path
from urllib.parse import urlparse
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e
ROOT = Path(__file__).resolve().parents[2]


def test_map_data_only_loads_on_map_tab(page: Page, base_url: str) -> None:
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    page.goto(base_url + "/#moratoriums")
    expect(page.locator("#moratoriums-tbody tr").first).to_be_visible()
    assert not any("map_geography" in url or "doe_sites" in url or "jurisdiction-map.js" in url for url in requests)
    page.click("#subtab-pol-map")
    expect(page.locator("#jurisdiction-map-svg")).to_be_visible()
    expect(page.locator("#jurisdiction-map-meta")).to_contain_text("33 DOE sites")
    expect(page.locator(".map-announcements > .map-announcement")).to_have_count(6)
    assert not any("leaflet" in url or "arcgisonline" in url for url in requests)


@pytest.mark.parametrize("width", [360, 375, 1366])
def test_map_filters_and_canonical_records(page: Page, base_url: str, width: int) -> None:
    page.set_viewport_size({"width": width, "height": 812})
    page.goto(base_url + "/#policies/map")
    expect(page.locator("#jurisdiction-map-svg")).to_be_visible()
    page.select_option("#jurisdiction-map-state", "TX")
    page.locator('[data-location-id="states-48"]').click()
    page.locator('.map-record-link[data-record-id="tx-sb6-2025"]').click()
    expect(page.locator("#policy-detail")).to_be_visible()
    page.keyboard.press("Escape")
    page.click("#tab-policies")
    page.click("#subtab-pol-pauses")
    page.click("#subtab-pol-map")
    page.select_option("#jurisdiction-map-state", "SC")
    page.fill("#jurisdiction-map-q", "Savannah River")
    page.locator('[data-location-id="doe-savannah-river"]').click()
    expect(page.locator("#jurisdiction-map-detail")).to_contain_text("phased-lease negotiations")
    page.fill("#jurisdiction-map-q", "")
    page.locator(".map-filters summary").click()
    page.select_option("#jurisdiction-map-topic", "large_load")
    expect(page.locator(".map-announcements > .map-announcement")).to_have_count(2)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert page.locator(".tabbar").evaluate("e=>e.getBoundingClientRect().height") <= 92
    expect(page.locator(".hero-kicker")).to_have_count(0)
    expect(page.locator(".site-footer")).not_to_contain_text("Company claims")


def test_original_index_file_loads_data_and_modules_offline(page: Page) -> None:
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.context.set_offline(True)
    page.goto((ROOT / "docs/index.html").as_uri() + "#comparison")
    expect(page.locator(".co-card").first).to_be_visible()
    expect(page.locator("#meta")).not_to_contain_text("Couldn't load")
    page.click("#tab-elections")
    expect(page.locator(".election-row")).to_have_count(54)
    page.click("#tab-policies")
    page.click("#subtab-pol-pauses")
    page.click("#subtab-pol-map")
    expect(page.locator("#jurisdiction-map-svg")).to_be_visible()
    expect(page.locator("#jurisdiction-map-meta")).to_contain_text("33 DOE sites")
    assert not errors


def test_map_project_search_and_keyboard_site_focus(page: Page, base_url: str) -> None:
    page.goto(base_url + "/#policies/map")
    expect(page.locator("#jurisdiction-map-svg")).to_be_visible()
    sites = page.locator('.map-doe-point')
    expect(sites).to_have_count(33)
    expect(sites.locator('text')).to_have_count(0)
    assert sites.evaluate_all('nodes=>nodes.every(n=>!n.dataset.siteIds.includes(","))')
    expect(page.locator('.map-doe-star')).to_have_count(33)
    sites.first.focus()
    page.keyboard.press("Enter")
    assert page.evaluate('document.activeElement.classList.contains("map-doe-point")')
    page.fill("#jurisdiction-map-q", "Amentum")
    assert page.locator("#jurisdiction-map-results").bounding_box()["y"] < page.locator("#jurisdiction-map-svg").bounding_box()["y"]
    expect(page.locator('.map-announcements > .map-announcement')).to_have_count(1)
    expect(page.locator('[data-location-id="doe-savannah-river"]')).to_be_visible()
    page.fill("#jurisdiction-map-q", "no-such-project")
    expect(page.locator('.map-announcements > .map-announcement')).to_have_count(0)


def test_map_hover_legend_and_keyboard_record_links(page: Page, base_url: str) -> None:
    page.goto(base_url + '/#policies/map')
    expect(page.locator('#jurisdiction-map-svg')).to_be_visible()
    expect(page.locator('#jurisdiction-map-detail')).to_be_hidden()
    expect(page.locator('[data-jurisdiction-id="states-15"]')).to_have_attribute('tabindex', '-1')
    page.get_by_role('button', name='Hawaii', exact=True).click()
    expect(page.locator('[data-jurisdiction-id="states-15"]')).to_have_attribute('tabindex', '0')
    page.get_by_role('button', name='Contiguous United States', exact=True).click()
    legend = page.get_by_role('list', name='Map legend')
    for text in ['Pause / ban', 'Framework', 'Both', 'Proposed: dashed border',
                 'Lifted / failed: dotted border', 'DOE site with announcement']:
        expect(legend).to_contain_text(text)
    site = page.locator('.map-doe-point[data-site-ids="doe-rockies-golden"]')
    site.hover()
    tooltip = page.get_by_role('tooltip')
    expect(tooltip).to_be_visible()
    expect(tooltip).to_contain_text('National Laboratory of the Rockies')
    expect(page.locator('#jurisdiction-map-detail')).to_be_hidden()
    page.mouse.move(0, 0)
    expect(tooltip).to_be_hidden()
    site.hover()
    page.keyboard.press('Escape')
    expect(tooltip).to_be_hidden()
    box = site.bounding_box()
    page.mouse.move(box['x'] + box['width'] / 2 + 1, box['y'] + box['height'] / 2)
    expect(tooltip).to_be_hidden()
    page.mouse.move(0, 0)
    site.focus()
    expect(tooltip).to_be_visible()
    page.keyboard.press('Escape')
    expect(tooltip).to_be_hidden()
    page.keyboard.press('Enter')
    expect(page.locator('#jurisdiction-map-detail')).to_contain_text('National Laboratory of the Rockies')
    expect(page.locator('#jurisdiction-map-detail a').first).to_have_attribute('target', '_blank')
    page.get_by_role('button', name='Close location details').click()
    expect(page.locator('#jurisdiction-map-detail')).to_be_hidden()
    page.select_option('#jurisdiction-map-state', 'TX')
    region = page.locator('[data-jurisdiction-id="states-48"]')
    region.focus()
    expect(tooltip).to_contain_text('Texas')
    page.keyboard.press('Enter')
    page.locator('.map-record-link[data-record-id="tx-sb6-2025"]').click()
    expect(page.locator('#policy-detail')).to_be_visible()


def test_map_path_click_and_pan(page: Page, base_url: str) -> None:
    page.goto(base_url + "/#policies/map")
    expect(page.locator("#jurisdiction-map-svg")).to_be_visible()
    page.select_option("#jurisdiction-map-state", "TX")
    page.locator('[data-jurisdiction-id="states-48"]').click()
    expect(page.locator("#jurisdiction-map-detail")).to_contain_text("Texas")
    expect(page.locator('.map-record-link[data-record-id="tx-sb6-2025"]')).to_be_visible()
    canvas = page.locator("#jurisdiction-map-svg")
    before = canvas.get_attribute("viewBox")
    rect = canvas.bounding_box()
    page.mouse.move(rect["x"] + 100, rect["y"] + 100)
    page.mouse.down()
    page.mouse.move(rect["x"] + 140, rect["y"] + 120, steps=5)
    page.mouse.up()
    assert canvas.get_attribute("viewBox") != before
    expect(page.locator("#jurisdiction-map-detail")).to_contain_text("Texas")


def test_native_preview_uses_classic_assets_when_json_and_modules_are_blocked(page: Page) -> None:
    def serve_preview(route) -> None:
        relative = urlparse(route.request.url).path.lstrip("/") or "index.html"
        path = ROOT / "docs" / relative
        if relative.endswith(".json") or relative in {"elections.js", "jurisdiction-map.js"}:
            route.abort()
        elif path.is_file():
            route.fulfill(path=str(path))
        else:
            route.fulfill(status=404)

    page.route("http://preview.invalid/**", serve_preview)
    page.goto("http://preview.invalid/#elections")
    expect(page.locator(".election-row")).to_have_count(54)
    expect(page.locator("#meta")).not_to_contain_text("Couldn't load")
    page.click("#tab-policies")
    page.click("#subtab-pol-pauses")
    page.click("#subtab-pol-map")
    expect(page.locator("#jurisdiction-map-svg")).to_be_visible()


def test_map_touch_controls_are_at_least_44_pixels(browser, base_url: str) -> None:
    context = browser.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True)
    try:
        page = context.new_page()
        page.goto(base_url + "/#policies/map")
        expect(page.locator("#jurisdiction-map-svg")).to_be_visible()
        boxes = page.locator('.jurisdiction-zoom button, .map-location-link, .map-dot-hit').evaluate_all(
            'els => els.map(e => { const r=e.getBoundingClientRect(); return [r.width, r.height]; })'
        )
        assert boxes
        assert all(width >= 43.9 and height >= 43.9 for width, height in boxes)
    finally:
        context.close()
