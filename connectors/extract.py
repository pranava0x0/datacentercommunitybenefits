"""HTML -> candidate-record fields. Stdlib only (no bs4 dependency).

Two jobs, mirroring the manual research loop this package replaces:

1. `extract_pub_date` — the tedious bit. Getting a news article's publication
   date by hand (and eating 429s) was the slow step; this pulls it from
   JSON-LD / OpenGraph / <time> automatically so a CommunityResponse.date is
   never guessed.
2. `extract_quotes` — surface candidate *verbatim* statements from a company's
   first-party page so a Claim.statement is quoted, not paraphrased (CLAUDE.md).

Everything here produces *candidates* for a human/agent curator. Stance and
constituency are never inferred — that stays editorial (CLAUDE.md).
"""

from __future__ import annotations

import html as _html
import json
import re
from datetime import datetime
from urllib.parse import urlparse

# Company first-party domains — a hit here means "treat as Claim/Project source",
# a miss means "treat as community-feedback (Response) source".
FIRST_PARTY_DOMAINS: dict[str, str] = {
    "datacenters.atmeta.com": "meta",
    "datacenters.google": "google",
    "www.google.com": "google",  # /about/datacenters/locations/...
    "local.microsoft.com": "microsoft",
    "azure.microsoft.com": "microsoft",
    "aboutamazon.com": "amazon",
    "www.aboutamazon.com": "amazon",
}

# First-party domains that render client-side (SPA). `requests` gets an empty
# shell, so these must be fetched with a JS-capable browser (Chrome MCP) and the
# rendered HTML fed back via `harvest --html-file`.
JS_RENDERED_DOMAINS: set[str] = {"datacenters.google", "www.google.com"}


def needs_browser(url: str, page: str | None = None) -> bool:
    """True if this URL needs JS rendering (Chrome MCP) to yield content.

    Either the host is a known SPA, or we fetched a 200 that has almost no
    extractable body text (the SPA-shell signature).
    """
    if urlparse(url).netloc in JS_RENDERED_DOMAINS:
        return True
    if page is not None and len(_clean(page)) < 600:
        return True
    return False


# Domain -> human outlet name for source_title scaffolding. Fallback = domain.
OUTLETS: dict[str, str] = {
    "nytimes.com": "The New York Times",
    "rollingstone.com": "Rolling Stone",
    "reviewjournal.com": "Las Vegas Review-Journal",
    "sacurrent.com": "San Antonio Current",
    "postandcourier.com": "The Post and Courier",
    "govtech.com": "GovTech",
    "datacenterdynamics.com": "Data Center Dynamics",
    "reuters.com": "Reuters",
    "bloomberg.com": "Bloomberg",
    "apnews.com": "Associated Press",
    "texasmonthly.com": "Texas Monthly",
    "newsweek.com": "Newsweek",
}


def _strip(netloc: str) -> str:
    return netloc[4:] if netloc.startswith("www.") else netloc


def is_first_party(url: str) -> bool:
    return urlparse(url).netloc in FIRST_PARTY_DOMAINS


def first_party_company(url: str) -> str | None:
    return FIRST_PARTY_DOMAINS.get(urlparse(url).netloc)


def outlet_for(url: str) -> str:
    host = _strip(urlparse(url).netloc)
    return OUTLETS.get(host, host)


# -- title -------------------------------------------------------------------
# Backreference (\2 / \1) so an apostrophe inside the value (e.g. "Nevada's")
# doesn't prematurely close the attribute.
_OG_TITLE = re.compile(
    r'<meta[^>]+property=["\']og:title["\'][^>]+content=(["\'])(.*?)\1', re.I | re.S
)
_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)


def extract_title(page: str) -> str | None:
    m = _OG_TITLE.search(page)
    if m:
        return _clean(m.group(2))
    m = _TITLE.search(page)
    if m:
        return _clean(m.group(1))
    return None


# -- publication date --------------------------------------------------------
_LD_BLOCK = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.I | re.S
)
_META_DATE = re.compile(
    r'<meta[^>]+(?:property|name|itemprop)=["\']'
    r'(?:article:published_time|og:published_time|publish-date|publishdate|'
    r'datePublished|date|sailthru\.date|parsely-pub-date)["\']'
    r'[^>]+content=(["\'])(.*?)\1',
    re.I,
)
_TIME_TAG = re.compile(
    r'<time[^>]+datetime=["\'](\d{4}-\d{2}-\d{2}[^"\']*)["\']', re.I
)
_ISO_PREFIX = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
_HUMAN_FORMATS = ("%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%m/%d/%Y", "%Y/%m/%d")


def _norm_date(raw: str | None) -> str | None:
    if not raw:
        return None
    raw = raw.strip()
    m = _ISO_PREFIX.search(raw)
    if m:
        y, mo, d = m.groups()
        try:
            datetime(int(y), int(mo), int(d))  # validate real calendar date
            return f"{y}-{mo}-{d}"
        except ValueError:
            return None
    for fmt in _HUMAN_FORMATS:
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _walk_ld(obj):
    """Yield every dict in a possibly-nested JSON-LD structure."""
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk_ld(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_ld(v)


def extract_pub_date(page: str) -> str | None:
    """Best-effort publication date as 'YYYY-MM-DD', or None. Never guesses."""
    for block in _LD_BLOCK.findall(page):
        try:
            data = json.loads(block.strip())
        except json.JSONDecodeError:
            continue
        for node in _walk_ld(data):
            for key in ("datePublished", "dateCreated", "uploadDate"):
                if key in node:
                    d = _norm_date(str(node[key]))
                    if d:
                        return d
    m = _META_DATE.search(page)
    if m:
        d = _norm_date(m.group(2))
        if d:
            return d
    m = _TIME_TAG.search(page)
    if m:
        return _norm_date(m.group(1))
    return None


# -- text / quotes -----------------------------------------------------------
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_BLOCKQUOTE = re.compile(r"<blockquote[^>]*>(.*?)</blockquote>", re.I | re.S)
_PARA = re.compile(r"<p[^>]*>(.*?)</p>", re.I | re.S)
# Sentences a company uses to make a commitment — good Claim candidates.
_COMMIT_CUE = re.compile(
    r"\b(we['’]ll|we will|we are committed|we['’]ve committed|we have committed|"
    r"we['’]re investing|we are investing|our \w+ pledge|committed to)\b",
    re.I,
)


# A stat sentence: a first-party subject + a number/$ — the investment, jobs,
# training, grant, and economic-activity figures that become Claim.statement.
_STAT_SUBJECT = re.compile(r"\b(we|we['’]ve|our|google|meta|microsoft|aws|amazon|grow with google)\b", re.I)
_STAT_NUMBER = re.compile(r"(\$[\d,.]+|\b[\d,]{2,}\b|\b\d+(?:\.\d+)?\s?(?:million|billion|gw|mw|gallons|jobs|acres))", re.I)


def _clean(fragment: str) -> str:
    return _WS.sub(" ", _html.unescape(_TAG.sub(" ", fragment))).strip()


def _paragraphs(page: str) -> list[str]:
    """Cleaned text blocks, whether `page` is HTML or already plain text.

    HTML -> <blockquote>/<p> contents (cleaned). Plain text (e.g. a Chrome-MCP
    `get_page_text` dump) -> blank-line / newline separated blocks.
    """
    if "<p" in page.lower() or "<blockquote" in page.lower() or "<body" in page.lower():
        blocks = _BLOCKQUOTE.findall(page) + _PARA.findall(page)
        return [_clean(b) for b in blocks]
    return [_clean(b) for b in re.split(r"\n\s*\n|\r\n\s*\r\n", page) if b.strip()]


def _sentences(block: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", block) if s.strip()]


def extract_quotes(page: str, *, min_len: int = 40, max_len: int = 320) -> list[str]:
    """Candidate verbatim statements from a first-party page (HTML or text).

    Surfaces two kinds of sentence the curator can lift into Claim.statement:
    a) commitment-cue pledges ("we'll…", "we are committed…", blockquotes);
    b) stat sentences (a first-party subject + a number/$ figure).
    Deduped, length-bounded. Candidates only — pick the exact verbatim span.
    """
    out: list[str] = []
    seen: set[str] = set()

    def add(text: str) -> None:
        text = text.strip()
        key = text.lower()
        if min_len <= len(text) <= max_len and key not in seen:
            seen.add(key)
            out.append(text)

    for block in _paragraphs(page):
        if _COMMIT_CUE.search(block) and len(block) <= max_len:
            add(block)
        for sentence in _sentences(block):
            if _COMMIT_CUE.search(sentence):
                add(sentence)
            elif _STAT_SUBJECT.search(sentence) and _STAT_NUMBER.search(sentence):
                add(sentence)
    return out


def extract_lede(page: str, *, min_len: int = 60) -> str | None:
    """First substantial paragraph — a starting point for a Response.summary.

    NOTE: the curator must rewrite this into neutral synthesis; it is NOT stored
    verbatim (a Response.summary is a paraphrase, not a quote — CLAUDE.md).
    """
    for frag in _PARA.findall(page):
        text = _clean(frag)
        if len(text) >= min_len:
            return text
    return None
