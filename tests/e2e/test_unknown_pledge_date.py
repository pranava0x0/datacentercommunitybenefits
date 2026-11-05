"""Rolling roster membership must not invent a signing date or dated cohort."""

import csv
import io

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def test_unknown_signing_date_stays_explicit_in_card_and_csv(page: Page, base_url: str) -> None:
    page.goto(base_url + "/#ratepayer")
    page.wait_for_function("state.signatoriesLoaded && state.projects.length > 0")
    timing = page.evaluate("""() => {
      const p = state.projects.find(p => p.id === 'sb-energy-piketon-oh');
      return {date: projectPledgeDate(p), pre: isPrePledgeProject(p),
        unassessed: ratepayerUnassessedProjects().some(x => x.id === p.id)};
    }""")
    assert timing == {"date": None, "pre": False, "unassessed": True}
    page.locator("#subtab-rp-sites-unassessed").click()
    card = page.locator("#rp-unassessed .rp-pre-card").filter(has_text="PORTS")
    expect(card).to_have_count(1)
    expect(card).to_contain_text("Signing date unpublished")
    expect(card).not_to_contain_text("Pledge era")
    rows = list(csv.DictReader(io.StringIO(page.evaluate("buildRatepayerCSV()"))))
    row = next(r for r in rows if "PORTS" in r["Project Name"])
    assert row["Company Signed Date"] == ""
    assert "Signing date unpublished" in row["Assessment Summary"]
    assert "during the pledge era" not in row["Assessment Summary"]


def test_unloaded_original_roster_keeps_fallback_but_loaded_unknown_does_not(page: Page, base_url: str) -> None:
    page.goto(base_url + "/#ratepayer")
    page.wait_for_function("state.signatoriesLoaded && state.projects.length > 0")
    assert page.evaluate("""() => {
      state.signatoriesLoaded = false;
      state.signatoryByCompany = new Map();
      return projectPledgeDate({company_slug: 'google'});
    }""") == "2026-03-04"
    assert page.evaluate("""() => {
      state.signatoriesLoaded = true;
      state.signatoryByCompany.set('sb-energy', {signed_date: null});
      return projectPledgeDate({company_slug: 'sb-energy'});
    }""") is None
