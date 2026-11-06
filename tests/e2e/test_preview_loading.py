"""The local HTML preview needs its data and lazy modules bundled together."""

from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from tools import build_preview

pytestmark = pytest.mark.e2e


@pytest.mark.parametrize("width", [375, 1366])
def test_offline_preview_elections_and_legal_link(page: Page, tmp_path: Path, monkeypatch, width: int) -> None:
    monkeypatch.setattr(build_preview, "OUT_DIR", tmp_path)
    monkeypatch.setattr(build_preview, "OUT", tmp_path / "dashboard.html")
    preview = build_preview.build()
    requests = []
    errors = []
    page.on("request", lambda request: requests.append(request.url))
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_viewport_size({"width": width, "height": 812})
    page.context.set_offline(True)
    page.goto(preview.as_uri() + "#elections")
    expect(page.locator(".election-row").first).to_be_visible()
    expect(page.locator("#meta")).not_to_contain_text("Couldn't load")
    page.locator("#elections-q").fill("Sabattus")
    page.locator('[data-related-record="sabattus-me-2026-11"]').click()
    expect(page.locator("#moratorium-detail")).to_be_visible()
    expect(page.locator("#md-jurisdiction")).to_have_text("Sabattus")
    page.keyboard.press("Escape")
    page.locator("#tab-overview").click()
    expect(page.locator("#home-latest-list .feed-item").first).to_be_visible()
    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
    assert not errors
    assert requests == [preview.as_uri()]


@pytest.mark.parametrize("hashpart, ready", [("", "#home-latest-list .feed-item"), ("#elections", ".election-row")])
def test_startup_does_not_fetch_other_views(page: Page, base_url: str, hashpart: str, ready: str) -> None:
    # Force idle callbacks to run promptly, so hidden startup prefetch cannot
    # evade the check just because this browser happened to be busy.
    page.add_init_script("window.requestIdleCallback = fn => setTimeout(fn, 0)")
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    page.goto(base_url + "/" + hashpart)
    expect(page.locator(ready).first).to_be_visible()
    page.wait_for_timeout(150)
    for name in ("projects.json", "responses.json", "claims.json", "international.json"):
        assert not any(name in url for url in requests), name
    page.locator("#tab-comparison").click()
    expect(page.locator(".co-card").first).to_be_visible()
    assert any("claims.json" in url for url in requests)
