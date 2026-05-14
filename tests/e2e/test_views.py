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

    def test_matrix_renders_at_least_eight_companies_eight_themes(
        self, page: Page, base_url: str
    ):
        # 8 hyperscalers + non-hyperscaler entities (e.g. Wonder Valley).
        # Themes are still 8 (frozen vocabulary).
        page.goto(base_url + "/")
        page.wait_for_selector("#matrix-body tr", timeout=10_000)
        rows = page.locator("#matrix-body tr")
        n = rows.count()
        assert n >= 8, f"Matrix should have at least 8 company rows, got {n}"

        head_cells = page.locator("#matrix-head-row .col-theme-head")
        expect(head_cells).to_have_count(8)

    def test_theme_legend_renders_eight_chips(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.wait_for_selector("#theme-legend .theme-chip", timeout=10_000)
        chips = page.locator("#theme-legend .theme-chip")
        expect(chips).to_have_count(8)

    def test_no_global_claims_list_on_comparison(self, page: Page, base_url: str):
        # v1.3: the comparison view dropped the global claims list + filter
        # chip. Claims live exclusively in the project-detail Claims tab.
        page.goto(base_url + "/")
        page.wait_for_selector("#matrix-body tr", timeout=10_000)
        assert page.locator("#claims-list").count() == 0
        assert page.locator("#claims-filter").count() == 0
        assert page.locator("#claims-section").count() == 0

    def test_clicking_company_name_opens_popout(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.wait_for_selector("#matrix-body tr", timeout=10_000)
        page.locator('#matrix-body tr[data-company="meta"] th.col-company').click()
        expect(page.locator("#company-detail")).to_be_visible()
        expect(page.locator("#cd-name")).to_have_text("Meta")

    def test_clicking_populated_cell_opens_popout(self, page: Page, base_url: str):
        # The cell is also a "tell me more about this company" affordance.
        page.goto(base_url + "/")
        page.wait_for_selector("#matrix-body tr", timeout=10_000)
        cell = page.locator(
            '#comparison-matrix td[data-company="google"][data-theme="energy"]'
        )
        cell.click()
        expect(page.locator("#company-detail")).to_be_visible()
        expect(page.locator("#cd-name")).to_have_text("Google")

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


class TestCompanyPopout:
    """v1.3: Comparison view's per-company summary pop-out."""

    def _open(self, page: Page, base_url: str, slug: str) -> None:
        page.goto(base_url + "/")
        page.wait_for_selector("#matrix-body tr", timeout=10_000)
        page.locator(
            f'#matrix-body tr[data-company="{slug}"] th.col-company'
        ).click()
        expect(page.locator("#company-detail")).to_be_visible()

    def test_popout_starts_hidden(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.wait_for_selector("#matrix-body tr", timeout=10_000)
        bbox = page.locator("#company-detail").bounding_box()
        assert bbox is None, "company-detail should have no layout box on first paint"

    def test_popout_shows_summary_text(self, page: Page, base_url: str):
        self._open(page, base_url, "microsoft")
        summary = page.locator("#cd-summary")
        text = summary.text_content() or ""
        assert "Datacenter Community Pledge" in text, (
            f"Microsoft summary should reference the Pledge: {text!r}"
        )
        # Muted styling (placeholder text) shouldn't apply when real summary loads.
        cls = summary.get_attribute("class") or ""
        assert "muted" not in cls, f"Real summary shouldn't be muted: {cls!r}"

    def test_popout_links_to_official_page(self, page: Page, base_url: str):
        self._open(page, base_url, "google")
        link = page.locator("#cd-page-link a")
        expect(link).to_have_count(1)
        href = link.get_attribute("href") or ""
        assert href.startswith("http"), f"Bad official-page href: {href!r}"

    def test_popout_handles_missing_official_page(
        self, page: Page, base_url: str
    ):
        # Anthropic has dedicated_page_url=null in seed.
        self._open(page, base_url, "anthropic")
        # The dd renders the placeholder via setKvLink null branch.
        dd = page.locator("#cd-page-link")
        text = dd.text_content() or ""
        assert "—" in text, f"Expected — placeholder for missing URL: {text!r}"

    def test_popout_shows_claim_and_project_counts(
        self, page: Page, base_url: str
    ):
        self._open(page, base_url, "meta")
        claim_text = page.locator("#cd-claim-count").text_content() or ""
        # Meta has many claims in seed.
        import re
        m = re.match(r"^(\d+)\s+claim", claim_text)
        assert m and int(m.group(1)) >= 1, (
            f"Expected numeric claim count for Meta: {claim_text!r}"
        )

    def test_popout_close_button_hides_panel(self, page: Page, base_url: str):
        self._open(page, base_url, "amazon")
        page.locator("#company-detail-close").click()
        expect(page.locator("#company-detail")).to_be_hidden()

    def test_escape_closes_popout(self, page: Page, base_url: str):
        self._open(page, base_url, "amazon")
        page.keyboard.press("Escape")
        expect(page.locator("#company-detail")).to_be_hidden()

    def test_active_row_class_tracks_selection(self, page: Page, base_url: str):
        self._open(page, base_url, "xai")
        row = page.locator('#matrix-body tr[data-company="xai"]')
        expect(row).to_have_class("active")

    def test_view_projects_button_switches_to_explorer_with_filter(
        self, page: Page, base_url: str
    ):
        self._open(page, base_url, "microsoft")
        page.locator("#cd-view-projects").click()
        # Should land on Explorer view with company filter pre-set.
        expect(page.locator("#view-explorer")).to_be_visible()
        page.wait_for_selector(
            "#project-list .project-card", timeout=15_000
        )
        # Filter dropdown should reflect the pre-set value.
        assert page.locator("#f-company").input_value() == "microsoft"
        # Project list should only contain Microsoft projects.
        cards = page.locator("#project-list .project-card")
        n = cards.count()
        assert n >= 1
        for i in range(n):
            txt = cards.nth(i).text_content() or ""
            assert "Microsoft" in txt, f"Card {i} not Microsoft: {txt!r}"

    def test_wonder_valley_summary_mentions_oleary(
        self, page: Page, base_url: str
    ):
        self._open(page, base_url, "wonder-valley")
        summary = page.locator("#cd-summary").text_content() or ""
        assert "O'Leary" in summary, f"Wonder Valley summary missing O'Leary ref: {summary!r}"


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
        # Matrix should still render every company row even if it's compressed.
        n = page.locator("#matrix-body tr").count()
        assert n >= 8, f"Mobile matrix should render >=8 rows, got {n}"
        # Tab to explorer still works.
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        expect(page.locator("#view-explorer")).to_be_visible()


class TestDetailTabs:
    """The project detail panel is split into Overview / Claims / Community tabs."""

    def _open_first_project(self, page: Page, base_url: str) -> None:
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        page.locator("#project-list .project-card").first.click()
        expect(page.locator("#project-detail")).to_be_visible()

    def test_three_tabs_render(self, page: Page, base_url: str):
        self._open_first_project(page, base_url)
        for slug in ("overview", "claims", "responses"):
            expect(page.locator(f"#dtab-{slug}")).to_be_visible()

    def test_overview_active_by_default(self, page: Page, base_url: str):
        self._open_first_project(page, base_url)
        expect(page.locator("#dtab-overview")).to_have_attribute(
            "aria-selected", "true"
        )
        expect(page.locator("#dpane-overview")).to_be_visible()
        expect(page.locator("#dpane-claims")).to_be_hidden()
        expect(page.locator("#dpane-responses")).to_be_hidden()

    def test_clicking_claims_tab_swaps_panes(self, page: Page, base_url: str):
        self._open_first_project(page, base_url)
        page.locator("#dtab-claims").click()
        expect(page.locator("#dtab-claims")).to_have_attribute(
            "aria-selected", "true"
        )
        expect(page.locator("#dpane-claims")).to_be_visible()
        expect(page.locator("#dpane-overview")).to_be_hidden()
        expect(page.locator("#dpane-responses")).to_be_hidden()
        # Claim cards are now visible.
        expect(page.locator("#d-claims .claim-card").first).to_be_visible()

    def test_clicking_responses_tab_swaps_panes(self, page: Page, base_url: str):
        # Memphis xAI has known responses; pick it explicitly.
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        page.evaluate("window.__dcb.selectProject('xai-memphis-tn')")
        expect(page.locator("#project-detail")).to_be_visible()
        page.locator("#dtab-responses").click()
        expect(page.locator("#dpane-responses")).to_be_visible()
        expect(page.locator("#d-responses .response-card").first).to_be_visible()

    def test_tab_counts_render_when_data_present(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        page.evaluate("window.__dcb.selectProject('xai-memphis-tn')")
        expect(page.locator("#project-detail")).to_be_visible()
        # Memphis has at least one claim (company-level) and at least 2 responses.
        claims_badge = page.locator("#dtab-claims-count")
        resp_badge = page.locator("#dtab-responses-count")
        expect(claims_badge).to_be_visible()
        expect(resp_badge).to_be_visible()
        # Counts are stringified integers.
        assert int(claims_badge.text_content()) >= 1
        assert int(resp_badge.text_content()) >= 2

    def test_active_tab_persists_across_project_selections(
        self, page: Page, base_url: str
    ):
        # User explicitly switches to Claims, then opens a different project.
        # Claims should remain active — they're scanning the same view across sites.
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        page.locator("#project-list .project-card").first.click()
        page.locator("#dtab-claims").click()
        expect(page.locator("#dpane-claims")).to_be_visible()
        # Open a different project.
        page.evaluate("window.__dcb.selectProject('aws-loudoun-va')")
        expect(page.locator("#dpane-claims")).to_be_visible()
        expect(page.locator("#dtab-claims")).to_have_attribute(
            "aria-selected", "true"
        )

    def test_active_tab_resets_on_page_reload(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        page.locator("#project-list .project-card").first.click()
        page.locator("#dtab-responses").click()
        # Reload — module state resets.
        page.reload()
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        page.locator("#project-list .project-card").first.click()
        expect(page.locator("#dtab-overview")).to_have_attribute(
            "aria-selected", "true"
        )

    def test_hidden_pane_truly_not_in_layout(self, page: Page, base_url: str):
        # Regression for the [hidden] trap (CLAUDE.md). A hidden pane MUST
        # have no bounding box — otherwise display:none is being overridden.
        self._open_first_project(page, base_url)
        bbox_claims = page.locator("#dpane-claims").bounding_box()
        bbox_responses = page.locator("#dpane-responses").bounding_box()
        assert bbox_claims is None, "Hidden claims pane should have no layout box"
        assert bbox_responses is None, "Hidden responses pane should have no layout box"

    def test_count_badges_hidden_when_no_data(self, page: Page, base_url: str):
        # google-mesa-az has no community responses captured in seed.
        # Pick a project deliberately because seed coverage drives this contract.
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        page.evaluate("window.__dcb.selectProject('google-mesa-az')")
        expect(page.locator("#project-detail")).to_be_visible()
        resp_badge = page.locator("#dtab-responses-count")
        # Badge should be hidden (zero responses for this project).
        assert (
            resp_badge.bounding_box() is None
        ), "Responses badge should hide when count is 0"


class TestMatrixGlyphs:
    """Every populated cell renders a checkmark — volume goes in the claims list."""

    def test_all_populated_cells_render_check(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.wait_for_selector("#matrix-body tr", timeout=10_000)
        non_empty = page.locator("#comparison-matrix td.cell:not(.empty)").count()
        check_cells = page.locator("#comparison-matrix .count.check").count()
        assert non_empty >= 1, "Seed should have at least one populated matrix cell"
        assert (
            check_cells == non_empty
        ), f"Every non-empty cell should render a check; got {check_cells}/{non_empty}"

    def test_no_digit_only_cells_remain(self, page: Page, base_url: str):
        # Regression for the v1.2 simplification: there must be NO `.count`
        # spans without the `.check` class — that was the digit branch and
        # it's been removed.
        page.goto(base_url + "/")
        page.wait_for_selector("#matrix-body tr", timeout=10_000)
        digit_only = page.locator("#comparison-matrix .count:not(.check)").count()
        assert digit_only == 0, (
            f"Found {digit_only} digit-style cells; the matrix should be "
            "checkmarks-only after v1.2."
        )

    def test_check_glyph_is_check_mark(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.wait_for_selector("#matrix-body tr", timeout=10_000)
        # Pick the first checkmark cell and verify its text is the U+2713 glyph.
        first_check = page.locator("#comparison-matrix .count.check").first
        text = first_check.text_content()
        assert text and text.strip() == "✓", f"Expected ✓ in check cell, got {text!r}"

    def test_check_cell_aria_label_carries_numeric_count(
        self, page: Page, base_url: str
    ):
        # Aria label must spell out the count even when the visual is a glyph,
        # so screen readers convey the same info as sighted users.
        page.goto(base_url + "/")
        page.wait_for_selector("#matrix-body tr", timeout=10_000)
        check_cell_td = page.locator(
            "#comparison-matrix td.cell:has(.count.check)"
        ).first
        label = check_cell_td.get_attribute("aria-label") or ""
        # Label format: "<N> <Company> <Theme> claim(s) — click to filter"
        import re

        m = re.match(r"^(\d+)\s+\S", label)
        assert m, f"Aria-label should start with a numeric count: {label!r}"
        assert int(m.group(1)) >= 1, f"Numeric count should be >= 1: {label!r}"
        assert "claim" in label.lower(), f"Aria-label should mention 'claim': {label!r}"


class TestWonderValley:
    """Wonder Valley (Kevin O'Leary) is the first non-hyperscaler entity tracked."""

    def test_wonder_valley_row_in_matrix(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.wait_for_selector("#matrix-body tr", timeout=10_000)
        row = page.locator('#matrix-body tr[data-company="wonder-valley"]')
        expect(row).to_have_count(1)

    def test_wonder_valley_project_in_explorer(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        page.locator("#f-company").select_option("wonder-valley")
        page.wait_for_timeout(150)
        cards = page.locator("#project-list .project-card")
        assert cards.count() >= 1

    def test_wonder_valley_negative_responses_present(
        self, page: Page, base_url: str
    ):
        # Sierra Club + Utah Clean Energy responses are tagged negative.
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        page.evaluate(
            "window.__dcb.selectProject('wonder-valley-box-elder-ut')"
        )
        expect(page.locator("#project-detail")).to_be_visible()
        page.locator("#dtab-responses").click()
        negs = page.locator("#d-responses .response-card.negative")
        assert negs.count() >= 2, "Wonder Valley should have negative NGO responses"


class TestProjectPageUrl:
    """Each project carries an optional project_page_url surfaced in the detail Overview."""

    def test_project_page_link_renders(self, page: Page, base_url: str):
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        page.evaluate("window.__dcb.selectProject('meta-prineville-or')")
        expect(page.locator("#project-detail")).to_be_visible()
        link = page.locator("#d-project-page a")
        expect(link).to_have_count(1)
        href = link.get_attribute("href")
        assert href and href.startswith("http"), f"Bad project page href: {href!r}"


class TestProjectPhysicalMetrics:
    """v1.2: acreage, power_mw, gpu_count, offtaker render in the Overview tab."""

    def _open(self, page: Page, base_url: str, project_id: str) -> None:
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        page.evaluate(f"window.__dcb.selectProject('{project_id}')")
        expect(page.locator("#project-detail")).to_be_visible()

    def test_acreage_renders_with_unit(self, page: Page, base_url: str):
        # meta-richland-la has acreage=2250 in seed.
        self._open(page, base_url, "meta-richland-la")
        text = page.locator("#d-acreage").text_content() or ""
        assert "acres" in text.lower(), f"Expected 'acres' in {text!r}"
        assert "2,250" in text or "2250" in text, f"Expected 2250 in {text!r}"

    def test_power_renders_in_mw_or_gw(self, page: Page, base_url: str):
        # xai-memphis-tn has power_mw=300 → "300 MW"
        self._open(page, base_url, "xai-memphis-tn")
        text = page.locator("#d-power").text_content() or ""
        assert "MW" in text, f"Expected MW unit in {text!r}"

    def test_power_renders_as_gw_at_1000_plus(self, page: Page, base_url: str):
        # wonder-valley-box-elder-ut has power_mw=1500 → "1.5 GW"
        self._open(page, base_url, "wonder-valley-box-elder-ut")
        text = page.locator("#d-power").text_content() or ""
        assert "GW" in text, f"Expected GW unit at >=1000 MW: {text!r}"
        assert "1.5" in text, f"Expected 1.5 GW: {text!r}"

    def test_gpu_count_renders_for_disclosed_sites(self, page: Page, base_url: str):
        # openai-abilene-tx has gpu_count=450000 → "450K"
        self._open(page, base_url, "openai-abilene-tx")
        text = page.locator("#d-gpus").text_content() or ""
        assert "450K" in text or "450,000" in text, f"Expected GPU count: {text!r}"

    def test_offtaker_renders(self, page: Page, base_url: str):
        # aws-new-carlisle-in has offtaker="Anthropic" (Project Rainier).
        self._open(page, base_url, "aws-new-carlisle-in")
        text = page.locator("#d-offtaker").text_content() or ""
        assert "Anthropic" in text, f"Expected Anthropic offtaker: {text!r}"

    def test_offtaker_disambiguates_stargate(self, page: Page, base_url: str):
        # oracle-abilene-tx has offtaker="OpenAI" (Oracle hosts, OpenAI uses).
        # This is the field that disambiguates "who is the compute for?"
        self._open(page, base_url, "oracle-abilene-tx")
        text = page.locator("#d-offtaker").text_content() or ""
        assert "OpenAI" in text, f"Expected OpenAI offtaker: {text!r}"

    def test_undisclosed_metrics_show_placeholder(self, page: Page, base_url: str):
        # aws-loudoun-va has no acreage in seed (distributed across 50+ parcels).
        self._open(page, base_url, "aws-loudoun-va")
        cell = page.locator("#d-acreage")
        # setKv() renders "Not disclosed" + .muted-cell class for null.
        text = cell.text_content() or ""
        assert "not disclosed" in text.lower(), f"Expected placeholder: {text!r}"


class TestSourceAttribution:
    """Per CLAUDE.md > 'Source attribution is non-negotiable'."""

    def test_every_claim_card_in_project_detail_has_source_link(
        self, page: Page, base_url: str
    ):
        # v1.3: claim cards are exclusively in the project-detail Claims tab,
        # since the comparison view's global claims list was removed.
        page.goto(base_url + "/")
        page.locator("#tab-explorer").click()
        page.wait_for_selector("#project-list .project-card", timeout=15_000)
        # meta-richland-la has many site-specific + company-level claims.
        page.evaluate("window.__dcb.selectProject('meta-richland-la')")
        page.locator("#dtab-claims").click()
        page.wait_for_selector(
            "#d-claims .claim-card", state="attached", timeout=5_000
        )
        cards = page.locator("#d-claims .claim-card")
        n = cards.count()
        assert n >= 5, f"Expected several claims for Meta Richland: got {n}"
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
        # Cards are inside the Community tab pane, which is hidden by default.
        # Wait for DOM presence (state="attached"), not visibility.
        page.wait_for_selector("#d-responses .response-card", state="attached", timeout=5_000)
        cards = page.locator("#d-responses .response-card")
        n = cards.count()
        for i in range(n):
            link = cards.nth(i).locator(".response-source a")
            assert (
                link.count() == 1
            ), f"Response card {i} missing source link"
