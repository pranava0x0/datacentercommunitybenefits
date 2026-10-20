"""scan_sources.py: list new data-center stories from known outlets, token-free.

The research agents kept rediscovering the same outlets by keyword search,
which samples a source instead of enumerating it (CLAUDE.md, 2026-07-27
lesson). This script reads each outlet's own listing or RSS page from
scripts/news_sources.json, keeps links whose title mentions a data center in
any of the site's languages, drops every URL the seed already cites or an
earlier scan already reported, and prints the remainder as a worklist. An
agent then spends tokens only on those leads.

    python3 scripts/scan_sources.py                    # scan every source
    python3 scripts/scan_sources.py --country KR       # one country
    python3 scripts/scan_sources.py --json OUT.json    # machine-readable leads
    python3 scripts/scan_sources.py --check-sources    # report sources that no longer list anything
    python3 scripts/scan_sources.py --all              # include leads seen on earlier runs

Seen leads are remembered in .scan_cache/seen.json (gitignored). Nothing here
verifies a fact: a lead is a reason to read a page, never a record.
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Callable, Iterable, Optional
from urllib.parse import urljoin, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe  # noqa: E402  (shared fetch + UA)

ROOT = Path(__file__).resolve().parent.parent
SOURCES_FILE = ROOT / "scripts" / "news_sources.json"
SEED_DIR = ROOT / "data" / "seed"
CACHE_DIR = ROOT / ".scan_cache"
DELAY = 1.5
# An honest, contactable UA (CLAUDE.md network rules); feeds are public and
# don't need a browser disguise.
SCANNER_UA = "DataCenterCommunityBenefits-scanner/1.0 (+https://github.com/pranava0x0/datacentercommunitybenefits)"
BACKOFF = 10.0
TRANSIENT_STATUSES = {0, 408, 425, 429, 500, 502, 503, 504}
DEAD_STATUSES = {404, 410}

log = logging.getLogger("scan_sources")

# Data center in every language a tracked country publishes in. A title must
# contain one of these (case-insensitive) to become a lead.
KEYWORDS = (
    "data center", "data centre", "datacenter", "datacentre", "data-center",
    "hyperscale", "centro de datos", "centros de datos", "centre de données",
    "centres de données", "rechenzentrum", "datacenter", "datakeskus",
    "κέντρο δεδομένων", "κέντρα δεδομένων", "데이터센터", "데이터 센터",
    "データセンター", "डेटा सेंटर", "डाटा सेंटर", "ডেটা সেন্টার", "datahall",
    "datorhall", "datorhallar", "centro de dados",
)

Fetcher = Callable[[str], "tuple[int, str, str]"]  # (status, final_url, raw_text)


def _raw_fetch(url: str) -> tuple[int, str, str]:
    """Return the raw body (not probe's stripped text): listings need links."""
    import requests

    try:
        r = requests.get(url, headers={"User-Agent": SCANNER_UA}, timeout=25)
    except requests.RequestException as exc:
        return 0, url, f"FETCH-ERROR: {exc}"
    r.encoding = r.encoding or "utf-8"
    if r.apparent_encoding and (r.encoding or "").lower() in ("iso-8859-1", "ascii"):
        r.encoding = r.apparent_encoding
    return r.status_code, r.url, r.text


def is_relevant(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in KEYWORDS)


def _looks_like_feed(body: str) -> bool:
    """A well-formed RSS/Atom document (possibly with zero items)."""
    try:
        root = ET.fromstring(body.encode("utf-8") if isinstance(body, str) else body)
    except ET.ParseError:
        return False
    return root.tag.rsplit("}", 1)[-1] in ("rss", "feed", "RDF")


def parse_feed(body: str) -> list[tuple[str, str]]:
    """(title, link) pairs from RSS 2.0 or Atom. Malformed XML yields [].
    Google News links are redirects that fail when fetched, so its <source>
    outlet is appended to the title as " [outlet]" for the agent to search."""
    # The body is already decoded text; drop the XML declaration so a feed
    # that declares ISO-8859-1 isn't decoded twice (café -> cafÃ©).
    body = re.sub(r"^\s*<\?xml[^>]*\?>", "", body) if isinstance(body, str) else body
    try:
        root = ET.fromstring(body.encode("utf-8") if isinstance(body, str) else body)
    except ET.ParseError:
        return []
    out = []
    for item in root.iter():
        tag = item.tag.rsplit("}", 1)[-1]
        if tag not in ("item", "entry"):
            continue
        title, link, outlet = "", "", ""
        for child in item:
            ctag = child.tag.rsplit("}", 1)[-1]
            if ctag == "title":
                title = (child.text or "").strip()
            elif ctag == "link":
                link = (child.text or "").strip() or child.attrib.get("href", "")
            elif ctag == "source":
                outlet = (child.text or "").strip()
        if outlet and outlet not in title:
            title = f"{title} [{outlet}]"
        if title and link:
            out.append((html.unescape(title), link))
    return out


_A = re.compile(r"<a\b[^>]*?href=[\"']([^\"'#]+)[\"'][^>]*>(.*?)</a>", re.I | re.S)


def parse_listing(body: str, base: str) -> list[tuple[str, str]]:
    """(title, absolute link) for every anchor with visible text on a listing page."""
    out = []
    for href, inner in _A.findall(body):
        text = html.unescape(re.sub(r"<[^>]+>", " ", inner))
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) < 12:  # nav links, "more", icons
            continue
        out.append((text, urljoin(base, href)))
    return out


# Query parameters that only track a click; everything else (e.g. ?p=1234,
# ?id=..., ?article=...) can identify the page and is kept.
_TRACKING_PARAMS = re.compile(r"^(utm_[a-z]+|fbclid|gclid|mc_[a-z]+|ref|ref_src|cmpid|ocid|taid|sr_share|smid|cid)$", re.I)


def _norm_url(u: str) -> str:
    from urllib.parse import parse_qsl, urlencode

    p = urlparse(u)
    host = (p.hostname or "").lower().removeprefix("www.").removeprefix("amp.")
    path = p.path.rstrip("/")
    if path.startswith("/amp/"):  # AMP mirror of the same article, not /ampere-...
        path = path[4:]
    q = sorted((k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not _TRACKING_PARAMS.match(k))
    return f"{host}{path}" + (f"?{urlencode(q)}" if q else "")


def seed_urls(seed_dir: Path = SEED_DIR) -> set[str]:
    """Every URL any seed record cites, normalized, at any depth."""
    urls: set[str] = set()

    def walk(x) -> None:
        if isinstance(x, dict):
            for k, v in x.items():
                if k in ("source_url", "url", "project_page_url", "dedicated_page_url") and isinstance(v, str):
                    urls.add(_norm_url(v))
                else:
                    walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    for f in sorted(seed_dir.glob("*.json")):
        walk(json.loads(f.read_text(encoding="utf-8")))
    return urls


def load_sources(path: Path = SOURCES_FILE, country: Optional[str] = None) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    srcs = data["sources"]
    for s in srcs:
        for k in ("name", "country", "url"):
            if not s.get(k):
                raise ValueError(f"source missing {k}: {s}")
    return [s for s in srcs if not country or s["country"] == country]


def scan(sources: Iterable[dict], fetcher: Fetcher = _raw_fetch, known: Optional[set] = None,
         seen: Optional[set] = None, sleep: Callable[[float], None] = time.sleep) -> dict:
    known = known or set()
    seen = seen if seen is not None else set()
    leads, dead_sources, failed, last_host = [], [], [], {}
    for s in sources:
        host = urlparse(s["url"]).hostname or ""
        if host in last_host:
            sleep(DELAY)
        status, final, body = fetcher(s["url"])
        # A timeout, rate limit or server error is the source having a bad
        # minute, not a dead URL: retry once with backoff, and report it as a
        # failed fetch (not a URL to fix) if it still fails.
        if status in TRANSIENT_STATUSES:
            sleep(BACKOFF)
            status, final, body = fetcher(s["url"])
        last_host[host] = True
        if status in DEAD_STATUSES:
            dead_sources.append({"name": s["name"], "url": s["url"], "status": status, "reason": "gone"})
            continue
        if status != 200:
            failed.append({"name": s["name"], "url": s["url"], "status": status, "reason": "fetch failed"})
            continue
        items = parse_feed(body) if s.get("kind") == "rss" else parse_listing(body, final or s["url"])
        if s.get("kind") == "rss" and not items and not _looks_like_feed(body):
            failed.append({"name": s["name"], "url": s["url"], "status": status, "reason": "not a parseable feed"})
            continue
        if not items:
            dead_sources.append({"name": s["name"], "url": s["url"], "status": status, "reason": "lists nothing"})
            continue
        relevant = [(t, u) for t, u in items if is_relevant(t)]
        for title, url in relevant:
            n = _norm_url(url)
            if n in known:
                continue
            leads.append({"country": s["country"], "source": s["name"], "title": title,
                          "url": url, "new": n not in seen})
            seen.add(n)
    # One lead per URL, even when two sources list it.
    uniq, out = set(), []
    for l in leads:
        n = _norm_url(l["url"])
        if n not in uniq:
            uniq.add(n)
            out.append(l)
    return {"leads": out, "dead_sources": dead_sources, "failed_fetches": failed}


def _load_seen() -> set:
    f = CACHE_DIR / "seen.json"
    try:
        return set(json.loads(f.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return set()


def _save_seen(seen: set) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    tmp = CACHE_DIR / "seen.json.tmp"
    tmp.write_text(json.dumps(sorted(seen), ensure_ascii=False), encoding="utf-8")
    tmp.replace(CACHE_DIR / "seen.json")


def render_worklist(leads: list, report: dict) -> str:
    out = [f"# Scan worklist: {len(leads)} new leads\n"]
    by_country: dict = {}
    for l in leads:
        by_country.setdefault(l["country"], []).append(l)
    for c in sorted(by_country):
        out.append(f"## {c}")
        out += [f"- [{l['title']}]({l['url']}) — {l['source']}" for l in by_country[c]]
        out.append("")
    if report["dead_sources"]:
        out.append("## Sources that are gone or list nothing (fix the URL in scripts/news_sources.json)")
        out += [f"- {d['name']}: HTTP {d['status']}, {d['reason']} — {d['url']}" for d in report["dead_sources"]]
    if report["failed_fetches"]:
        out.append("\n## Fetches that failed this run (retry later; not a URL problem)")
        out += [f"- {d['name']}: HTTP {d['status']}, {d['reason']} — {d['url']}" for d in report["failed_fetches"]]
    return "\n".join(out) + "\n"


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--country")
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--all", action="store_true", help="include leads seen on earlier runs")
    ap.add_argument("--check-sources", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    sources = load_sources(country=args.country)
    seen = _load_seen()
    # --check-sources audits feed health; it must not mark leads as seen, or
    # the next real scan would drop them as old.
    report = scan(sources, known=seed_urls(), seen=set(seen) if args.check_sources else seen)
    leads = [l for l in report["leads"] if args.all or l["new"]]
    if args.json_out:
        Path(args.json_out).write_text(json.dumps({**report, "leads": leads}, indent=1, ensure_ascii=False), encoding="utf-8")
    log.info("scan: %d sources, %d new leads, %d sources gone or empty, %d failed fetches",
             len(sources), len(leads), len(report["dead_sources"]), len(report["failed_fetches"]))
    for d in report["dead_sources"]:
        log.warning("source gone or empty (fix its URL): %s HTTP %s %s", d["name"], d["status"], d["url"])
    for d in report["failed_fetches"]:
        log.warning("fetch failed this run (retry later): %s HTTP %s %s", d["name"], d["status"], d["url"])
    # The worklist itself is the command's product (like a report file), so
    # it goes to stdout as one markdown document; status and problems above
    # go through logging.
    sys.stdout.write(render_worklist(leads, report))
    # Mark leads seen only after the worklist was delivered: if --json or the
    # write above fails, the next run must still show them.
    if not args.check_sources:
        _save_seen(seen)
    return 1 if args.check_sources and report["dead_sources"] else 0


if __name__ == "__main__":
    sys.exit(main())
