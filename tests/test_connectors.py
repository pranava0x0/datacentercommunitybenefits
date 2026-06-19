"""Offline tests for the research connectors. No network — fixture HTML only."""

from __future__ import annotations

import hashlib
import json

import pytest

from connectors import extract
from connectors.http import CachedSession, FetchError

# --- fixtures ---------------------------------------------------------------

NEWS_JSONLD = """
<html><head>
<title>Google runs Nevada's thirstiest data center | RJ</title>
<meta property="og:title" content="Google runs Nevada's thirstiest data center" />
<script type="application/ld+json">
{"@context":"https://schema.org","@graph":[
  {"@type":"WebSite"},
  {"@type":"NewsArticle","datePublished":"2025-12-05T06:00:00-08:00","headline":"x"}
]}
</script>
</head><body>
<p>Google's Henderson data center consumed 352 million gallons of water in 2024,
records obtained by the Review-Journal show.</p>
</body></html>
"""

NEWS_META = """
<html><head><title>Data centers guzzled water</title>
<meta name="article:published_time" content="2025-07-30T09:15:00Z">
</head><body><p>San Antonio data centers used 463 million gallons during drought.</p></body></html>
"""

NEWS_TIME_TAG = """
<html><head><title>SC water</title></head><body>
<time datetime="2026-02-13T12:00:00Z">Feb 13, 2026</time>
<p>Berkeley County disclosed 853.8 million gallons withdrawn in 2024.</p>
</body></html>
"""

FIRST_PARTY = """
<html><head><title>Hello Kuna! - Meta Data Centers</title></head><body>
<blockquote>Meta worked closely with Idaho Power to develop and implement a new
green tariff that will allow companies like us to support their operations with
100% renewable energy.</blockquote>
<p>We will restore 200% of the water our data center consumes into local watersheds.
This site supports the community.</p>
<p>Short.</p>
</body></html>
"""


# --- extract: dates ---------------------------------------------------------

def test_pub_date_from_jsonld_graph():
    assert extract.extract_pub_date(NEWS_JSONLD) == "2025-12-05"


def test_pub_date_from_meta_tag():
    assert extract.extract_pub_date(NEWS_META) == "2025-07-30"


def test_pub_date_from_time_tag():
    assert extract.extract_pub_date(NEWS_TIME_TAG) == "2026-02-13"


def test_pub_date_absent_returns_none_never_guesses():
    assert extract.extract_pub_date("<html><body>no date here</body></html>") is None


def test_norm_date_rejects_impossible_calendar_date():
    assert extract._norm_date("2025-13-45") is None


# --- extract: title / classification ---------------------------------------

def test_extract_title_prefers_og():
    assert "thirstiest" in extract.extract_title(NEWS_JSONLD)


def test_is_first_party_classification():
    assert extract.is_first_party("https://datacenters.atmeta.com/2022/02/hello-kuna/")
    assert extract.first_party_company("https://datacenters.google/locations/x/") == "google"
    assert not extract.is_first_party("https://www.reviewjournal.com/news/x")


def test_outlet_lookup_and_fallback():
    assert extract.outlet_for("https://www.rollingstone.com/x") == "Rolling Stone"
    assert extract.outlet_for("https://unknown-paper.example/x") == "unknown-paper.example"


# --- extract: quotes --------------------------------------------------------

def test_quotes_include_blockquote_and_commitment_sentence():
    quotes = extract.extract_quotes(FIRST_PARTY)
    assert any("green tariff" in q for q in quotes)
    assert any(q.startswith("We will restore 200%") for q in quotes)


def test_quotes_drop_too_short_fragments():
    assert all(len(q) >= 40 for q in extract.extract_quotes(FIRST_PARTY))


def test_quotes_from_plain_text_capture_stat_sentences():
    """Chrome-MCP get_page_text returns plain text — stat sentences still surface."""
    text = (
        "Lenoir, North Carolina\n\n"
        "Since the Lenoir data center was built in 2007, Google has invested more "
        "than $4 billion in the region and state.\n\n"
        "Grow with Google has collaborated with hundreds of organizations in North "
        "Carolina to train more than 512,000 North Carolinians on digital skills.\n"
    )
    quotes = extract.extract_quotes(text)
    assert any("$4 billion" in q for q in quotes)
    assert any("512,000" in q for q in quotes)


def test_lede_is_first_substantial_paragraph():
    lede = extract.extract_lede(NEWS_JSONLD)
    assert lede.startswith("Google's Henderson")


# --- http: cache + offline --------------------------------------------------

def test_cached_session_serves_and_records(tmp_path):
    sess = CachedSession(cache_dir=tmp_path, offline=True)
    url = "https://example.com/article"
    digest = hashlib.sha256(url.encode()).hexdigest()[:24]
    (tmp_path / f"{digest}.json").write_text(
        json.dumps({"url": url, "final_url": url, "status": 200, "text": NEWS_META})
    )
    rec = sess.get(url)
    assert rec["status"] == 200
    assert extract.extract_pub_date(rec["text"]) == "2025-07-30"


def test_offline_cache_miss_raises(tmp_path):
    sess = CachedSession(cache_dir=tmp_path, offline=True)
    with pytest.raises(FetchError):
        sess.get("https://example.com/never-fetched")


# --- SPA detection + Chrome-MCP bridge -------------------------------------

def test_needs_browser_for_known_spa_domain():
    assert extract.needs_browser("https://datacenters.google/locations/north-carolina/")


def test_needs_browser_for_tiny_shell():
    assert extract.needs_browser("https://news.example/x", "<html><body>loading</body></html>")


def test_needs_browser_false_for_real_content():
    assert not extract.needs_browser("https://news.example/x", FIRST_PARTY + "x" * 600)


def test_harvest_html_file_bridge_extracts_quotes():
    """Rendered-DOM override (what Chrome MCP saves) yields verbatim quotes."""
    from connectors.research import _harvest_url

    cand = _harvest_url(
        None,
        "https://datacenters.google/locations/north-carolina/",
        "google-lenoir-nc",
        page_override=FIRST_PARTY,
    )
    assert cand["kind"] == "claim_candidates"
    assert cand["company_slug"] == "google"
    assert any("green tariff" in q for q in cand["quote_candidates"])
