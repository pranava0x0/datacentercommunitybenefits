"""End-to-end browser tests for both dashboard views."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# Comparison view
# ---------------------------------------------------------------------------


class TestComparisonView:
    def test_page_loads_with_meta(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        expect(page.locator("h1")).to_have_text("Data Center Community Benefits")
        # Meta line resolves once data loads.
        expect(page.locator("#meta")).to_contain_text("claims across", timeout=10_000)

    def test_matrix_renders_eight_companies_eight_themes(
        self, page: Page, base_url: str
    ):
        page.goto(base_url + "/")
        # Wait for matrix to populate.
        page.wait_for_selector("#matrix-body tr", timeout=10_000)
        rows = page.locator("#matrix-body tr")
        expect(rows).to_have_count(8)

        head_cells = page.locator("#matrix-head-row .col-theme-head")
        expect(head_cells).to_have_count(8)

    def test_theme_legend_renders_eight_chips(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.wait_for_selector("#theme-legend .theme-chip", timeout=10_000)
        chips = page.locator("#theme-legend .theme-chip")
        expect(chips).to_have_count(8)

    def test_claims_list_renders(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.wait_for_selector(".claim-card", timeout=10_000)
        cards = page.locator(".claim-card")
        # Seed has 25 claims.
        assert cards.count() >= 20

    def test_clicking_matrix_cell_filters_claims(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.wait_for_selector("#matrix-body tr", timeout=10_000)
        # Find a non-empty cell (Meta × energy is in seed).
        cell = page.locator(
            '#comparison-matrix td[data-company="meta"][data-theme="energy"]'
        )
        expect(cell).to_be_visible()
        cell.click()
        # A filter chip should appear.
        expect(page.locator("#claims-filter .chip-clear")).to_be_visible()
        # The claims list should narrow.
        cards = page.locator("#claims-list .claim-card")
        # Should have at least 1, and far fewer than the unfiltered 25.
        n = cards.count()
        assert 1 <= n <= 5, f"Expected 1-5 cards after filter, got {n}"
        # Active class on the cell.
        expect(cell).to_have_class("cell active")

    def test_filter_chip_clears(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.wait_for_selector("#matrix-body tr", timeout=10_000)
        page.locator(
            '#comparison-matrix td[data-company="meta"][data-theme="energy"]'
        ).click()
        page.locator("#claims-filter .chip-clear").click()
        expect(page.locator("#claims-filter .chip-clear")).to_have_count(0)
        # Full list back.
        cards = page.locator("#claims-list .claim-card")
        assert cards.count() >= 20

    def test_empty_cell_not_clickable(self, page: Page, base_url: str):
        # Anthropic has no 'water' claim; that cell should be empty + non-button.
        page.goto(base_url + "/")
        page.wait_for_selector("#matrix-body tr", timeout=10_000)
        cell = page.locator(
            '#comparison-matrix td[data-company="anthropic"][data-theme="water"]'
        )
        expect(cell).to_have_class("cell empty")
        # Empty cells should NOT have role=button — confirms they're inert.
        assert cell.get_attribute("role") is None


# ---------------------------------------------------------------------------
# Explorer view
# ---------------------------------------------------------------------------


class TestExplorerView:
    def test_tab_switches_to_explorer(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.wait_for_selector("#matrix-body tr", timeout=10_000)
        page.locator("#tab-explorer").click()
        expect(page.locator("#view-explorer")).to_be_visible()
        expect(page.locator("#view-comparison")).to_be_hidden()
        expect(page.locator("#tab-explorer")).to_have_attribute(
            "aria-selected", "true"
        )

    def test_explorer_loads_projects(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        cards = page.locator("#project-list .project-card")
        # Seed has 15 projects.
        assert cards.count() >= 10

    def test_explorer_meta_shows_count(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        meta = page.locator("#explorer-meta")
        expect(meta).to_contain_text("of")
        expect(meta).to_contain_text("projects")

    def test_company_filter_narrows_projects(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        full = page.locator("#project-list .project-card").count()
        page.locator("#f-company").select_option("microsoft")
        page.wait_for_function(
            "document.querySelectorAll('#project-list .project-card').length < " + str(full),
            timeout=5_000,
        )
        narrowed = page.locator("#project-list .project-card").count()
        assert narrowed < full
        assert narrowed >= 1

    def test_negative_stance_filter_works(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        page.locator("#f-stance").select_option("negative")
        # Wait for refresh.
        page.wait_for_timeout(150)
        cards = page.locator("#project-list .project-card")
        # Each remaining card should carry a negative stance dot.
        n = cards.count()
        assert n >= 1, "Seed includes projects with negative responses"
        for i in range(n):
            assert (
                cards.nth(i).locator(".stance-dot.negative").count() >= 1
            ), f"Project {i} surfaced under 'negative' filter but lacks a negative dot"

    def test_reset_clears_filters(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        full = page.locator("#project-list .project-card").count()
        page.locator("#f-company").select_option("microsoft")
        page.wait_for_timeout(150)
        page.locator("#f-reset").click()
        page.wait_for_timeout(150)
        assert page.locator("#project-list .project-card").count() == full
        # All selects back to "".
        assert page.locator("#f-company").input_value() == ""
        assert page.locator("#f-status").input_value() == ""
        assert page.locator("#f-stance").input_value() == ""

    def test_clicking_project_opens_detail(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        card = page.locator("#project-list .project-card").first
        card.click()
        expect(page.locator("#project-detail")).to_be_visible()
        expect(page.locator("#d-name")).not_to_be_empty()
        expect(page.locator("#d-status")).not_to_be_empty()

    def test_detail_close_hides_panel(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        page.locator("#project-list .project-card").first.click()
        page.locator("#detail-close").click()
        expect(page.locator("#project-detail")).to_be_hidden()

    def test_escape_closes_detail(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        page.locator("#project-list .project-card").first.click()
        page.keyboard.press("Escape")
        expect(page.locator("#project-detail")).to_be_hidden()

    def test_xai_memphis_shows_negative_responses(self, page: Page, base_url: str):
        # Memphis xAI has at least 2 documented negative responses in seed.
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        page.evaluate("window.__dcb.selectProject('xai-memphis-tn')")
        expect(page.locator("#project-detail")).to_be_visible()
        negs = page.locator("#d-responses .response-card.negative")
        assert negs.count() >= 2


# ---------------------------------------------------------------------------
# Cross-cutting / accessibility
# ---------------------------------------------------------------------------


class TestCrossCutting:
    def test_skip_link_focusable(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        skip = page.locator(".skip-link")
        expect(skip).to_have_count(1)

    def test_theme_toggle_swaps_data_theme(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.wait_for_selector("#matrix-body tr", timeout=10_000)
        before = page.evaluate("document.documentElement.getAttribute('data-theme')")
        page.locator("#theme-toggle").click()
        after = page.evaluate("document.documentElement.getAttribute('data-theme')")
        assert before != after

    def test_hidden_attribute_not_overridden(self, page: Page, base_url: str):
        # Project detail uses [hidden] + custom display rules. The CSS should
        # ensure [hidden] wins. Regression for the "[hidden] trap" CLAUDE.md note.
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        # Detail starts hidden.
        bbox = page.locator("#project-detail").bounding_box()
        assert bbox is None, "project-detail should have no layout box while hidden"

    def test_explorer_view_starts_hidden(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.wait_for_selector("#matrix-body tr", timeout=10_000)
        bbox = page.locator("#view-explorer").bounding_box()
        assert bbox is None, "Explorer view should be display:none on first paint"

    def test_no_console_errors_on_first_paint(self, page: Page, base_url: str):
        errors: list[str] = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.goto(base_url + "/")
        page.wait_for_selector("#matrix-body tr", timeout=10_000)
        # Filter known noise (resource hints from external CDNs aren't errors here).
        relevant = [e for e in errors if "favicon" not in e.lower()]
        assert not relevant, f"Console errors on first paint: {relevant}"

    def test_mobile_layout_does_not_break(self, page: Page, base_url: str):
        page.set_viewport_size({"width": 375, "height": 720})
        page.goto(base_url + "/")
        page.wait_for_selector("#matrix-body tr", timeout=10_000)
        # Matrix should still render even if it's compressed.
        expect(page.locator("#matrix-body tr")).to_have_count(8)
        # Tab to explorer still works.
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        expect(page.locator("#view-explorer")).to_be_visible()


class TestSourceAttribution:
    """Per CLAUDE.md > 'Source attribution is non-negotiable'."""

    def test_every_claim_card_has_source_link(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.wait_for_selector(".claim-card", timeout=10_000)
        cards = page.locator(".claim-card")
        n = cards.count()
        for i in range(n):
            link = cards.nth(i).locator(".claim-source a")
            assert (
                link.count() == 1
            ), f"Claim card {i} missing source link — violates source attribution rule"
            href = link.get_attribute("href")
            assert href and href.startswith("http"), f"Card {i} source href invalid: {href!r}"

    def test_every_response_card_has_source_link(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        page.evaluate("window.__dcb.selectProject('xai-memphis-tn')")
        page.wait_for_selector("#d-responses .response-card", timeout=5_000)
        cards = page.locator("#d-responses .response-card")
        n = cards.count()
        for i in range(n):
            link = cards.nth(i).locator(".response-source a")
            assert (
                link.count() == 1
            ), f"Response card {i} missing source link"
