"""scan_sources.py: offline tests with a fake fetcher."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import scan_sources as ss  # noqa: E402

RSS = """<?xml version="1.0"?><rss><channel>
<item><title>City council pauses new data center permits</title><link>https://news.example/a</link></item>
<item><title>Local bakery wins award</title><link>https://news.example/b</link></item>
<item><title>부산 데이터센터 주민 반대</title><link>https://kr.example/c</link></item>
</channel></rss>"""

LISTING = """<html><body><a href="/x">Home</a>
<a href="/2026/10/data-centre-water-row">Residents object to data centre water use</a>
<a href="https://news.example/a">City council pauses new data center permits</a></body></html>"""


def fake(pages):
    return lambda url: (200, url, pages[url]) if url in pages else (404, url, "")


def test_relevance_is_multilingual() -> None:
    assert ss.is_relevant("Nuevo centro de datos en Querétaro")
    assert ss.is_relevant("データセンター建設に住民反対")
    assert not ss.is_relevant("Bakery wins award")


def test_rss_and_listing_parse_and_dedupe_across_sources() -> None:
    srcs = [
        {"name": "R", "country": "US", "url": "https://news.example/rss", "kind": "rss"},
        {"name": "L", "country": "GB", "url": "https://uk.example/news", "kind": "listing"},
    ]
    rep = ss.scan(srcs, fetcher=fake({"https://news.example/rss": RSS, "https://uk.example/news": LISTING}),
                  sleep=lambda s: None)
    urls = [l["url"] for l in rep["leads"]]
    assert "https://news.example/a" in urls and urls.count("https://news.example/a") == 1
    assert "https://kr.example/c" in urls
    assert "https://uk.example/2026/10/data-centre-water-row" in urls
    assert not any("b" == u.rsplit("/", 1)[-1] for u in urls)


def test_urls_the_seed_already_cites_are_not_leads() -> None:
    srcs = [{"name": "R", "country": "US", "url": "https://news.example/rss", "kind": "rss"}]
    rep = ss.scan(srcs, fetcher=fake({"https://news.example/rss": RSS}),
                  known={ss._norm_url("https://www.news.example/a/")}, sleep=lambda s: None)
    assert "https://news.example/a" not in [l["url"] for l in rep["leads"]]


def test_seen_leads_are_marked_old_on_the_next_run() -> None:
    srcs = [{"name": "R", "country": "US", "url": "https://news.example/rss", "kind": "rss"}]
    seen: set = set()
    f = fake({"https://news.example/rss": RSS})
    first = ss.scan(srcs, fetcher=f, seen=seen, sleep=lambda s: None)
    second = ss.scan(srcs, fetcher=f, seen=seen, sleep=lambda s: None)
    assert all(l["new"] for l in first["leads"]) and not any(l["new"] for l in second["leads"])


def test_a_source_that_lists_nothing_is_reported_not_silently_skipped() -> None:
    srcs = [{"name": "Gone", "country": "US", "url": "https://gone.example/news", "kind": "listing"}]
    rep = ss.scan(srcs, fetcher=fake({}), sleep=lambda s: None)
    assert rep["dead_sources"] and rep["dead_sources"][0]["status"] == 404
    assert not rep["failed_fetches"]


def test_committed_sources_file_is_valid() -> None:
    srcs = ss.load_sources()
    assert srcs and all(s["kind"] in ("rss", "listing") for s in srcs)
    assert len({s["url"] for s in srcs}) == len(srcs)


def test_seed_urls_are_collected_at_any_depth() -> None:
    urls = ss.seed_urls()
    assert len(urls) > 500


def test_google_news_outlet_is_kept_for_search() -> None:
    feed = """<rss><channel><item><title>Data center vote delayed</title>
<link>https://news.google.com/rss/articles/abc</link><source url="https://x.example">Example Times</source></item></channel></rss>"""
    assert ss.parse_feed(feed) == [("Data center vote delayed [Example Times]", "https://news.google.com/rss/articles/abc")]


def test_transient_failures_are_retried_and_not_reported_as_dead() -> None:
    calls = []
    def flaky(url):
        calls.append(url)
        return (503, url, "") if len(calls) == 1 else (200, url, RSS)
    srcs = [{"name": "R", "country": "US", "url": "https://news.example/rss", "kind": "rss"}]
    rep = ss.scan(srcs, fetcher=flaky, sleep=lambda s: None)
    assert len(calls) == 2 and rep["leads"] and not rep["dead_sources"]
    always = ss.scan(srcs, fetcher=lambda u: (429, u, ""), sleep=lambda s: None)
    assert not always["dead_sources"] and always["failed_fetches"][0]["status"] == 429


def test_malformed_feed_is_a_failed_fetch_not_an_empty_one() -> None:
    srcs = [{"name": "R", "country": "US", "url": "https://news.example/rss", "kind": "rss"}]
    bad = ss.scan(srcs, fetcher=lambda u: (200, u, "<html>captcha</html"), sleep=lambda s: None)
    assert bad["failed_fetches"] and not bad["dead_sources"]
    empty = ss.scan(srcs, fetcher=lambda u: (200, u, "<rss><channel></channel></rss>"), sleep=lambda s: None)
    assert empty["dead_sources"] and empty["dead_sources"][0]["reason"] == "lists nothing"


def test_identity_query_params_are_kept_and_tracking_params_dropped() -> None:
    a = ss._norm_url("https://www.aboutamazon.com/news/aws/x?p=111&utm_source=feed")
    b = ss._norm_url("https://aboutamazon.com/news/aws/x?p=222")
    assert a != b
    assert a == ss._norm_url("https://aboutamazon.com/news/aws/x?p=111")


def test_check_sources_does_not_consume_leads(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(ss, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(ss, "load_sources", lambda country=None: [{"name": "R", "country": "US", "url": "https://news.example/rss", "kind": "rss"}])
    monkeypatch.setattr(ss, "_raw_fetch", lambda url: (200, url, RSS))
    monkeypatch.setattr(ss, "seed_urls", lambda: set())
    monkeypatch.setattr(ss.scan, "__defaults__", (ss._raw_fetch, None, None, lambda s: None))
    ss.main(["--check-sources"])
    assert not (tmp_path / "seen.json").exists()
    ss.main([])
    assert (tmp_path / "seen.json").exists()


def test_amp_prefix_only_strips_the_amp_segment() -> None:
    assert ss._norm_url("https://x.example/amp/story/a") == ss._norm_url("https://x.example/story/a")
    assert ss._norm_url("https://x.example/ampere-data-center").endswith("/ampere-data-center")


def test_feed_declaring_latin1_is_not_double_decoded() -> None:
    body = '<?xml version="1.0" encoding="ISO-8859-1"?><rss><channel><item><title>Centre de données à Paris café</title><link>https://x.example/a</link></item></channel></rss>'
    assert ss.parse_feed(body)[0][0].endswith("café")
