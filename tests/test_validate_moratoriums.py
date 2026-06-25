"""Unit tests for scripts/validate_moratoriums.py.

Tests cover the pure logic functions (text search, date/vote/bill variants,
claim checking) without making any network requests.  The integration path
(--dry-run) is smoke-tested against the live seed file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from validate_moratoriums import (
    _bill_variants,
    _date_variants,
    _search,
    _search_any,
    _snippet,
    _sponsor_last_names,
    _vote_variants,
    _check,
    _check_sponsors,
    audit_record,
)

SEED_PATH = ROOT / "data" / "seed" / "moratoriums.json"


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

class TestSnippet:
    def test_middle_of_text(self):
        text = "a" * 100 + "TARGET" + "b" * 100
        s = _snippet(text, 100)
        assert "TARGET" in s

    def test_start_of_text(self):
        s = _snippet("Hello world", 0, radius=5)
        assert "Hello" in s
        assert not s.startswith("…")

    def test_end_of_text(self):
        s = _snippet("Hello world", 11, radius=5)
        assert "world" in s
        assert not s.endswith("…")


class TestSearch:
    def test_exact_match(self):
        assert _search("The bill passed 37-0", "37-0") is not None

    def test_case_insensitive(self):
        assert _search("Governor janet mills signed", "Janet Mills") is not None

    def test_no_match_returns_none(self):
        assert _search("nothing here", "SB232") is None

    def test_empty_needle_returns_none(self):
        assert _search("some text", "") is None

    def test_search_any_first_match(self):
        snip = _search_any("The vote was 108 to 39", ["108-39", "108 to 39"])
        assert snip is not None
        assert "108" in snip


# ---------------------------------------------------------------------------
# Variant generators
# ---------------------------------------------------------------------------

class TestDateVariants:
    def test_iso_date_present(self):
        variants = _date_variants("2026-05-07")
        assert "2026-05-07" in variants

    def test_long_form_present(self):
        variants = _date_variants("2026-05-07")
        assert "May 7, 2026" in variants

    def test_short_month_present(self):
        variants = _date_variants("2026-05-07")
        assert "May 7, 2026" in variants

    def test_invalid_date_returns_original(self):
        variants = _date_variants("not-a-date")
        assert "not-a-date" in variants

    def test_none_returns_empty(self):
        assert _date_variants(None) == []

    def test_june_9(self):
        variants = _date_variants("2026-06-09")
        assert "June 9, 2026" in variants


class TestVoteVariants:
    def test_simple_vote(self):
        variants = _vote_variants("37-0")
        assert "37-0" in variants
        assert "37 to 0" in variants

    def test_compound_vote_extracts_all_pairs(self):
        variants = _vote_variants("Senate 37-0, House 92-16")
        assert "37-0" in variants
        assert "92-16" in variants

    def test_en_dash_variant(self):
        variants = _vote_variants("4-1")
        assert any("–" in v or "-" in v for v in variants)


class TestBillVariants:
    def test_no_space(self):
        variants = _bill_variants("LD307")
        assert "LD307" in variants
        assert "LD 307" in variants

    def test_with_space(self):
        variants = _bill_variants("SB 1018")
        assert "SB 1018" in variants
        assert "SB1018" in variants

    def test_already_spaced_and_unspaced_both_included(self):
        v1 = _bill_variants("SB484")
        v2 = _bill_variants("SB 484")
        assert "SB 484" in v1
        assert "SB484" in v2


class TestSponsorLastNames:
    def test_simple_last_name(self):
        names = _sponsor_last_names(["Rep. Victoria Foley (D-LD5)"])
        assert "Foley" in names

    def test_multiple_sponsors(self):
        names = _sponsor_last_names([
            "Sen. Avila (primary)",
            "Rep. Gaetz (co-introducer)",
        ])
        assert "Avila" in names
        assert "Gaetz" in names

    def test_empty_list(self):
        assert _sponsor_last_names([]) == []


# ---------------------------------------------------------------------------
# Claim checks (offline — synthetic source text)
# ---------------------------------------------------------------------------

FAKE_SOURCES = [
    ("https://example.gov/bill", (
        "SB 484 was signed by Governor Ron DeSantis on May 7, 2026. "
        "The Senate voted 37-0 and the House voted 92-16. "
        "Senator Avila and Rep. Gaetz introduced the bill."
    )),
]


class TestCheckFunction:
    def test_found_bill_number(self):
        result = _check("SB484", FAKE_SOURCES, _bill_variants)
        assert result["status"] == "found"
        assert "context" in result
        assert "SB 484" in result["context"] or "484" in result["context"]

    def test_found_enacted_date(self):
        result = _check("2026-05-07", FAKE_SOURCES, _date_variants)
        assert result["status"] == "found"

    def test_found_vote(self):
        result = _check("Senate 37-0, House 92-16", FAKE_SOURCES, _vote_variants)
        assert result["status"] == "found"

    def test_no_claim_for_none(self):
        result = _check(None, FAKE_SOURCES, _bill_variants)
        assert result["status"] == "no_claim"

    def test_not_found_returns_not_found(self):
        result = _check("SB9999", FAKE_SOURCES, _bill_variants)
        assert result["status"] == "not_found"

    def test_fetch_failed_when_no_text(self):
        result = _check("SB484", [("https://x.com", "")], _bill_variants)
        assert result["status"] == "fetch_failed"


class TestCheckSponsors:
    def test_all_found(self):
        # Both "Avila" and "Gaetz" appear in FAKE_SOURCES
        sponsors = ["Sen. Avila (primary)", "Rep. Gaetz"]
        result = _check_sponsors(sponsors, FAKE_SOURCES)
        assert result["status"] == "found"
        assert "Sen. Avila (primary)" in result["found"]
        assert "Rep. Gaetz" in result["found"]

    def test_partial_found(self):
        sponsors = ["Sen. Avila (primary)", "Sen. NotThere"]
        result = _check_sponsors(sponsors, FAKE_SOURCES)
        assert result["status"] == "partial"
        assert "Sen. Avila (primary)" in result["found"]
        assert "Sen. NotThere" in result["not_found"]

    def test_none_found(self):
        sponsors = ["Sen. Nobody", "Rep. Ghost"]
        result = _check_sponsors(sponsors, FAKE_SOURCES)
        assert result["status"] == "not_found"

    def test_empty_sponsors(self):
        result = _check_sponsors([], FAKE_SOURCES)
        assert result["status"] == "no_claim"

    def test_fetch_failed_when_no_text(self):
        result = _check_sponsors(["Sen. Avila"], [("https://x.com", "")])
        assert result["status"] == "fetch_failed"


# ---------------------------------------------------------------------------
# audit_record (offline — cached_only so no network)
# ---------------------------------------------------------------------------

class TestAuditRecordOffline:
    """Run audit_record with cached_only=True so no HTTP calls are made."""

    MINIMAL_RECORD = {
        "id": "test-offline-record",
        "jurisdiction": "TestCity",
        "jurisdiction_type": "city",
        "status": "enacted",
        "summary": "Test moratorium.",
        "source_url": "https://example.gov/bill",
        "source_title": "Example Bill",
        "captured_at": "2026-06-25",
        "duration_description": "1 year",
        "key_reasons": [],
    }

    def test_returns_required_keys(self):
        a = audit_record(self.MINIMAL_RECORD, cached_only=True)
        assert "id" in a
        assert "checks" in a
        assert "score" in a
        assert "gov_source_present" in a

    def test_gov_source_detected(self):
        a = audit_record(self.MINIMAL_RECORD, cached_only=True)
        assert a["gov_source_present"] is True
        assert a["primary_is_gov"] is True

    def test_non_gov_source(self):
        rec = {**self.MINIMAL_RECORD, "source_url": "https://localnews.com/story"}
        a = audit_record(rec, cached_only=True)
        assert a["gov_source_present"] is False
        assert a["primary_is_gov"] is False

    def test_fetch_failed_status_when_no_cache(self):
        """All checks that have a value should be fetch_failed, not not_found."""
        rec = {
            **self.MINIMAL_RECORD,
            "bill_number": "HB123",
            "sponsors": ["Rep. Smith"],
            "legislative_votes": "50-0",
        }
        a = audit_record(rec, cached_only=True)
        # With no cache, fetch_failed
        assert a["checks"]["bill_number"]["status"] == "fetch_failed"
        assert a["checks"]["sponsors"]["status"] == "fetch_failed"

    def test_no_claim_for_null_fields(self):
        a = audit_record(self.MINIMAL_RECORD, cached_only=True)
        assert a["checks"]["bill_number"]["status"] == "no_claim"
        assert a["checks"]["sponsors"]["status"] == "no_claim"
        assert a["checks"]["failure_reason"]["status"] == "no_claim"

    def test_failure_reason_checked_only_on_failed_status(self):
        enacted = {**self.MINIMAL_RECORD, "status": "enacted", "failure_reason": "some reason"}
        failed = {**self.MINIMAL_RECORD, "status": "failed", "failure_reason": "Tabled 5-3"}
        a_enacted = audit_record(enacted, cached_only=True)
        a_failed = audit_record(failed, cached_only=True)
        assert a_enacted["checks"]["failure_reason"]["status"] == "no_claim"
        assert a_failed["checks"]["failure_reason"]["status"] in ("fetch_failed", "not_found", "found")


# ---------------------------------------------------------------------------
# Smoke test: --dry-run against live seed
# ---------------------------------------------------------------------------

class TestDryRunSmoke:
    def test_dry_run_exits_zero(self):
        from validate_moratoriums import main
        rc = main(["--dry-run"])
        assert rc == 0

    def test_all_records_have_required_schema_fields(self):
        """Every moratorium record has fields the auditor depends on."""
        data = json.loads(SEED_PATH.read_text())
        required = ["id", "jurisdiction", "status", "source_url", "captured_at", "summary"]
        for m in data["moratoriums"]:
            for field in required:
                assert field in m, f"{m['id']} missing field: {field}"

    def test_failure_records_have_failure_reason(self):
        """All failed moratoriums should have a failure_reason."""
        data = json.loads(SEED_PATH.read_text())
        missing = [
            m["id"] for m in data["moratoriums"]
            if m["status"] == "failed" and not m.get("failure_reason")
        ]
        assert missing == [], f"Failed records missing failure_reason: {missing}"

    def test_enacted_records_have_enacted_date(self):
        """All enacted moratoriums should have an enacted_date."""
        data = json.loads(SEED_PATH.read_text())
        # Allow permanent-ban records where date may be approximate
        missing = [
            m["id"] for m in data["moratoriums"]
            if m["status"] == "enacted" and not m.get("enacted_date")
        ]
        assert missing == [], f"Enacted records missing enacted_date: {missing}"

    def test_no_duplicate_ids(self):
        data = json.loads(SEED_PATH.read_text())
        ids = [m["id"] for m in data["moratoriums"]]
        dupes = [i for i in set(ids) if ids.count(i) > 1]
        assert dupes == [], f"Duplicate ids: {dupes}"
