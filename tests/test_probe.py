"""The evidence gate (scripts/probe.py --evidence).

The daily routine merges to main only if this gate passes, so the failure
modes worth pinning are the permissive ones: a changed record that slips
through with no quote, or a quote that half-matches. All offline: `fetch` is
stubbed with canned page text.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("probe", ROOT / "scripts" / "probe.py")
probe = importlib.util.module_from_spec(_spec)
sys.modules["probe"] = probe
_spec.loader.exec_module(probe)

PAGE = (
    "The Madison County Quorum Court has approved a three-year moratorium on data centers. "
    "According to our content partner 40/29 News , the moratorium was approved on Aug. 17 "
    "and will remain in place through Aug. 31, 2029. The PUC approved a 1 - cent per "
    "kilowatt - hour surcharge for customers with 100 megawatts or more. "
) * 3  # long enough to clear the bot-wall length check


@pytest.fixture
def gate(tmp_path, monkeypatch):
    pages = {"https://example.org/story": (200, "https://example.org/story", probe.norm(PAGE)),
             "https://example.org/walled": (403, "https://example.org/walled", "Forbidden")}
    monkeypatch.setattr(probe, "fetch", lambda url: pages[url])

    def run(*rows: dict) -> int:
        path = tmp_path / "evidence.jsonl"
        path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        return probe.check_evidence(path, delay=0)
    return run


def row(**kw) -> dict:
    base = {"id": "rec-1", "action": "added", "source_url": "https://example.org/story"}
    base.update(kw)
    return base


def test_quote_on_the_page_passes(gate) -> None:
    assert gate(row(verbatim="the moratorium was approved on Aug. 17 and will remain in place through Aug. 31, 2029.")) == 0


def test_layout_spacing_does_not_cause_a_false_miss(gate) -> None:
    """'News , the' and '1 - cent' are how the page text actually arrives."""
    assert gate(row(verbatim="According to our content partner 40/29 News, the moratorium was approved on Aug. 17")) == 0
    assert gate(row(verbatim="The PUC approved a 1-cent per kilowatt-hour surcharge")) == 0


def test_ending_a_quoted_sentence_early_is_fine(gate) -> None:
    """'…on data centers.' quotes the front of the page's '…on data centers
    as officials consider…' and should not be a MISS."""
    page_extra = "The Quorum Court acted on data centers as officials consider regulation. " * 8
    probe_fetch = probe.fetch
    probe.fetch = lambda url: (200, url, probe.norm(page_extra))
    try:
        assert gate(row(verbatim="The Quorum Court acted on data centers.")) == 0
        assert gate(row(verbatim="The Quorum Court acted on water towers.")) == 1
    finally:
        probe.fetch = probe_fetch


def test_every_clause_must_be_on_the_page(gate) -> None:
    """The first sentence is on the page and the second contradicts it. The
    old longest-clause check passed this."""
    quote = ("The Madison County Quorum Court has approved a three-year moratorium on data centers. "
             "The vote was 4-3 and the ban is permanent.")
    assert gate(row(verbatim=quote)) == 1


def test_a_long_single_clause_is_checked_in_full(gate) -> None:
    """The old check truncated to 160 characters; an altered tail slipped through."""
    quote = ("According to our content partner 40/29 News, the moratorium was approved on Aug. 17 "
             "and will remain in place through Aug. 31, 2031 unless the court acts sooner to end it early")
    assert gate(row(verbatim=quote)) == 1


def test_ellipsis_joined_passages_are_each_checked(gate) -> None:
    ok = "has approved a three-year moratorium on data centers ... the moratorium was approved on Aug. 17"
    bad = "has approved a three-year moratorium on data centers ... the moratorium was approved on Sept. 9"
    assert gate(row(verbatim=ok)) == 0
    assert gate(row(verbatim=bad)) == 1


@pytest.mark.parametrize("missing", ["source_url", "verbatim"])
def test_a_changed_row_without_its_evidence_fails(gate, missing) -> None:
    rec = row(verbatim="the moratorium was approved on Aug. 17")
    rec.pop(missing)
    assert gate(rec) == 1


def test_a_changed_row_with_a_trivial_quote_fails(gate) -> None:
    assert gate(row(verbatim="Aug. 17")) == 1


@pytest.mark.parametrize("action", ["no_change", "held", "not_found"])
def test_rows_that_changed_nothing_are_skipped(gate, action) -> None:
    assert gate({"id": "x", "action": action}) == 0


def test_a_row_with_no_action_is_treated_as_a_change(gate) -> None:
    assert gate({"id": "x", "source_url": "https://example.org/story"}) == 1


def test_a_bot_walled_page_is_reported_not_failed(gate, capsys) -> None:
    """BLOCKED needs a human or WebFetch read, and the run report lists it.
    It must not pass as a HIT, and it must not fail the gate either."""
    assert gate(row(source_url="https://example.org/walled", verbatim="anything long enough to check here")) == 0
    assert "BLOCKED" in capsys.readouterr().out
