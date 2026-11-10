"""Guards from the 2026-11-09 UX audit (notes/ux/2026-11-09/UX_AUDIT.md).

A reader who clicks a Home card must meet the same number and the same name
on the tab it opens; the masthead keeps its full name on a phone; the
moratorium directory says where and when; the Pledge tab answers its own
question before its reference sections.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

E2E_WAIT = int(os.environ.get("E2E_WAIT_MS", "6000"))
ROOT = Path(__file__).resolve().parents[2]


def _home_cards(page: Page, base_url: str) -> list[dict]:
    page.goto(base_url + "/")
    page.wait_for_function(
        "() => [...document.querySelectorAll('#home-cards .home-card-num')].every(n => /\\d/.test(n.textContent))",
        timeout=E2E_WAIT,
    )
    return page.evaluate(
        """() => [...document.querySelectorAll('#home-cards .home-card')].map(c => ({
              target: c.dataset.pathTarget,
              title: c.querySelector('.home-card-title').textContent.trim(),
              num: c.querySelector('.home-card-num').textContent.trim(),
            }))"""
    )


def test_home_card_numbers_match_their_tab(page: Page, base_url: str):
    """Each card's number appears on the tab it opens, where a reader looks
    first (stat row, sub-tab pills, dek or the first section count)."""
    cards = _home_cards(page, base_url)
    assert cards, "no home cards"
    for card in cards:
        page.goto(base_url + "/")
        page.wait_for_selector(f".home-card[data-path-target='{card['target']}']", timeout=E2E_WAIT)
        page.locator(f".home-card[data-path-target='{card['target']}']").click()
        num = card["num"]
        page.wait_for_function(
            """(num) => {
                const v = document.querySelector('.view:not([hidden])');
                if (!v) return false;
                const lead = [...v.querySelectorAll('.rp-stat-value, .subtab-count, .hero-dek, .acc-count, .election-totals strong')]
                  .map(e => e.textContent).join(' | ');
                return new RegExp('(^|[^\\\\d,])' + num.replace(/,/g, ',?') + '([^\\\\d,]|$)').test(lead);
            }""",
            arg=num,
            timeout=E2E_WAIT,
        )


def test_tab_name_is_the_same_everywhere(page: Page, base_url: str):
    """Tab label = Home card title = the tab's heading = llms.txt section name."""
    cards = {c["target"]: c["title"] for c in _home_cards(page, base_url)}
    tabs = page.evaluate(
        """() => VIEWS.map(v => ({
              name: v.name,
              label: document.getElementById(v.tab).textContent.trim().replace(/\\s+/g, ' '),
              aria: document.getElementById(v.tab).getAttribute('aria-label'),
              hero: (document.querySelector('#' + v.section + ' .hero-title') || {}).textContent || null,
            }))"""
    )
    target_of = {"ratepayer": "pledge", "comparison": "companies"}
    llms = (ROOT / "docs" / "llms.txt").read_text(encoding="utf-8")
    for t in tabs:
        if t["aria"]:
            assert t["aria"] == t["label"], t
        card = cards.get(target_of.get(t["name"], t["name"]))
        if t["name"] != "overview":
            assert card == t["label"], (t, card)
            assert f"[{t['label']}](" in llms, f"llms.txt names {t['name']} differently"
        if t["hero"] is not None and t["name"] != "elections":
            assert t["hero"].strip() == t["label"], t
    # Elections renders its heading from a lazy module.
    page.goto(base_url + "/#elections")
    expect(page.locator("#view-elections .hero-title")).to_have_text("Elections", timeout=E2E_WAIT)


@pytest.mark.parametrize("width", [360, 390])
def test_phone_masthead_keeps_the_full_name(browser, base_url: str, width: int):
    ctx = browser.new_context(viewport={"width": width, "height": 800}, is_mobile=True, has_touch=True)
    page = ctx.new_page()
    try:
        page.goto(base_url + "/")
        h1 = page.locator(".topbar h1")
        expect(h1).to_have_text("Data Center Policy Tracker")
        assert page.evaluate("() => document.querySelector('.topbar h1').innerText.replace(/\\s+/g, ' ').trim()") == "Data Center Policy Tracker"
        # Full tab names must fit their grid cell, not spill into a neighbour
        # (Codex on #117: the tabbar scroll width never caught this overlap).
        spill = page.evaluate(
            """() => VIEWS.map(v => document.getElementById(v.tab))
                 .filter(t => t.scrollWidth > t.clientWidth + 1).map(t => t.id)"""
        )
        assert not spill, spill
    finally:
        ctx.close()


def test_moratorium_rows_show_state_and_date_and_page(page: Page, base_url: str):
    page.set_viewport_size({"width": 1366, "height": 900})
    page.goto(base_url + "/#moratoriums")
    page.wait_for_selector("#moratoriums-tbody tr[data-id]", timeout=E2E_WAIT)
    total = page.evaluate("() => state.moratoriums.length")
    rows = page.locator("#moratoriums-tbody tr[data-id]")
    assert rows.count() < total, "desktop directory is not paged"
    assert page.locator("#moratoriums-tbody .project-list-more, #moratoriums-tbody button").count() >= 1
    checks = page.evaluate(
        """() => [...document.querySelectorAll('#moratoriums-tbody tr[data-id]')].map(tr => {
              const m = state.moratoriums.find(x => x.id === tr.dataset.id);
              return {type: m.jurisdiction_type, code: m.state_code, place: tr.cells[0].textContent,
                      date: tr.cells[1].textContent.trim(), hasDate: Boolean(m.enacted_date || m.effective_date)};
            })"""
    )
    for c in checks:
        if c["type"] in ("city", "county") and c["code"]:
            assert f", {c['code']}" in c["place"], c
        if c["hasDate"]:
            assert re.search(r"\d{4}", c["date"]), c
        else:
            assert c["date"] == "Not stated", c


def test_pledge_tab_shows_sites_before_reference_sections(browser, base_url: str):
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    page = ctx.new_page()
    try:
        page.goto(base_url + "/#ratepayer")
        page.wait_for_selector("#rp-scorecard-section", state="attached", timeout=E2E_WAIT)
        order = page.evaluate(
            """() => ['rp-roster-section', 'rp-coverage-section', 'rp-scorecard-section', 'rp-category-section', 'rp-utility-section']
                 .map(id => document.getElementById(id).getBoundingClientRect().top + scrollY)"""
        )
        assert order == sorted(order), order
        # Reference sections above the sites stay collapsed to one bar each.
        assert page.evaluate("() => document.getElementById('rp-scorecard-section').open && !document.getElementById('rp-coverage-section').open && !document.getElementById('rp-roster-details').open")
        top = order[2] / 844
        assert top < 1.0, f"Tracked sites starts {top:.2f} screens down on a phone"
    finally:
        ctx.close()


def test_no_generated_summary_block():
    html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    assert "static-summary" not in html and "record at a glance" not in html.lower()


def test_phone_moratorium_rows_keep_duration_and_hide_reasons(browser, base_url: str):
    """Codex on #117: inserting Date shifted a positional :nth-child rule, so
    phones hid Duration and showed the badge column meant to be hidden."""
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    page = ctx.new_page()
    try:
        page.goto(base_url + "/#moratoriums")
        page.wait_for_selector("#moratoriums-tbody tr[data-id]", timeout=E2E_WAIT)
        headers = page.evaluate(
            """() => [...document.querySelectorAll('#moratoriums-table th')]
                 .filter(th => getComputedStyle(th).display !== 'none').map(th => th.textContent.trim())"""
        )
        assert "Duration" in headers and "Key Reasons" not in headers, headers
    finally:
        ctx.close()
