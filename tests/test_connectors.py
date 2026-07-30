"""Offline tests for the research connectors. No network — fixture HTML only."""

from __future__ import annotations

import hashlib
import json

import pytest

from connectors import extract, scout
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


# --- scout: link extraction --------------------------------------------------

LISTING_PAGE = """
<html><body>
<nav><a href="#top">Skip to content</a> <a href="mailto:x@y.com">Contact</a></nav>
<ul>
<li><a href="/en/news/google-files-to-expand-data-center-campus-in-lagrange-georgia/">
  Google files to expand data center campus in LaGrange, Georgia</a></li>
<li><a href="https://example.com/en/news/unrelated-story/">A totally unrelated story</a></li>
<li><a href="javascript:void(0)">Load more</a></li>
</ul>
</body></html>
"""


def test_extract_links_skips_nav_junk_and_resolves_relative_urls():
    links = scout.extract_links(LISTING_PAGE, "https://example.com/en/news/")
    urls = {l["url"] for l in links}
    assert "https://example.com/en/news/google-files-to-expand-data-center-campus-in-lagrange-georgia/" in urls
    # mailto / javascript / fragment-only anchors are not links to a story
    assert not any(u.startswith(("mailto:", "javascript:")) for u in urls)
    assert not any(u.endswith("#top") for u in urls)


def test_extract_links_dedupes_repeated_title_and_url():
    doubled = LISTING_PAGE + LISTING_PAGE
    links = scout.extract_links(doubled, "https://example.com/")
    titles = [l["title"] for l in links]
    assert titles.count("Google files to expand data center campus in LaGrange, Georgia") == 1


# --- scout: relevance keyword gate -------------------------------------------

def test_relevant_matches_on_keyword():
    assert scout.relevant("Brookfield to develop gigawatt-scale data center campus")
    assert scout.relevant("County considers new data-center moratorium")
    assert not scout.relevant("Company launches new cloud storage pricing tier")


def test_relevant_survives_trailing_punctuation():
    """A phrase keyword must still match when punctuation sits right after it —
    this is the same word-boundary bug that first showed up in match_existing."""
    assert scout.relevant("Data center, moratorium proposed in Anytown.")


# --- scout: seed matching heuristic ------------------------------------------

def test_match_existing_ignores_trailing_comma():
    """Regression: 'LaGrange, Georgia' must match a fingerprint token 'lagrange'
    even though the comma sits directly against the word in the raw title."""
    fps = [{"id": "google-lagrange-ga", "tokens": {"lagrange", "georgia", "google"}}]
    title = "Google files to expand data center campus in LaGrange, Georgia"
    assert scout.match_existing(title, fps) == "google-lagrange-ga"


def test_match_existing_one_distinctive_token_is_enough():
    """Regression (found in the first live run, 2026-07-30): a headline naming
    just the company but not the city -- 'Brookfield to develop gigawatt-scale
    data center campus in Kentucky' has no word in common with a 'paducah'
    token -- must still match, because 'brookfield' alone is distinctive
    (length >= MIN_DISTINCTIVE_LEN). An earlier version required 2 token hits
    unconditionally, which left every single-word jurisdiction (57 of 111 live
    moratorium records) structurally unmatchable no matter how exact the
    headline wording was -- not just imprecise, but impossible to ever match."""
    fps = [{"id": "brookfield-paducah-ky", "tokens": {"brookfield", "paducah"}}]
    title = "Brookfield to develop gigawatt-scale data center campus in Kentucky"
    assert scout.match_existing(title, fps) == "brookfield-paducah-ky"


def test_match_existing_short_token_alone_is_not_enough():
    """A bare state-code-length token must not match on its own -- otherwise
    almost every in-state headline would false-positive against every record
    in that state. Distinctiveness (see test above) is what should carry a
    single-token match, not mere presence."""
    fps = [{"id": "some-fl-record", "tokens": {"fl"}}]
    assert scout.match_existing("Unrelated story about Florida oranges", fps) is None


def test_match_existing_returns_none_for_no_overlap():
    fps = [{"id": "google-lagrange-ga", "tokens": {"lagrange", "georgia", "google"}}]
    assert scout.match_existing("Sky47 inaugurates data center in Islamabad", fps) is None


def test_project_fingerprints_strip_generic_company_words(tmp_path, monkeypatch):
    """'SB Energy' and 'Brookfield' both contain generic words ('Energy',
    'Group') common enough in unrelated headlines to false-positive on their
    own (e.g. an energy-policy story matching purely on 'energy' + 'group').
    Exercises the real function against fixture seed files -- a prior version
    of this test checked `_words(...) - _GENERIC_COMPANY_WORDS` directly
    without ever calling `project_fingerprints()`, so it stayed green even
    with the subtraction deleted from the function itself."""
    seed = tmp_path / "seed"
    seed.mkdir()
    (seed / "companies.json").write_text(json.dumps({"companies": [
        {"slug": "sb-energy", "name": "SB Energy (SoftBank Group)"},
    ]}))
    (seed / "projects.json").write_text(json.dumps({"projects": [
        {"id": "sb-energy-piketon-oh", "company_slug": "sb-energy", "city": "Piketon", "state": "OH"},
    ]}))
    monkeypatch.setattr(scout, "SEED", seed)

    fps = scout.project_fingerprints()
    assert len(fps) == 1
    tokens = fps[0]["tokens"]
    assert "softbank" in tokens
    assert "piketon" in tokens
    assert "energy" not in tokens
    assert "group" not in tokens


def test_tariff_fingerprints_strip_generic_utility_words(tmp_path, monkeypatch):
    """Same class of bug, utility side: a generic Indiana rate-case headline
    must not false-positive against a Duke Energy Indiana tariff purely on
    'energy' + 'indiana' (found in the same review as the test above)."""
    seed = tmp_path / "seed"
    seed.mkdir()
    (seed / "tariffs.json").write_text(json.dumps({"tariffs": [
        {"id": "duke-energy-indiana-meta-esa", "utility": "Duke Energy Indiana", "state": "IN"},
    ]}))
    monkeypatch.setattr(scout, "SEED", seed)

    fps = scout.tariff_fingerprints()
    tokens = fps[0]["tokens"]
    assert "duke" in tokens
    assert "energy" not in tokens
    title = "Indiana regulators weigh new large load energy tariff"
    assert scout.match_existing(title, fps) is None
