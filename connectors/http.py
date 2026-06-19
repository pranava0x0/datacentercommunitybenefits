"""Polite, cached HTTP for the research connectors.

Single source of truth for *how* we hit the network, so every connector inherits
the same manners (CLAUDE.md > "Network Ethics & Rate Limiting"):

- >=1.5s between requests to the same host.
- Informative User-Agent.
- 429 -> exponential backoff starting at 10s (a few tries, then give up + log).
- Every response cached to disk keyed by URL hash; re-runs never re-download.

Uses `requests` (already a pinned dependency) — no new packages.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

log = logging.getLogger("connectors.http")

CACHE_DIR = Path(__file__).resolve().parent / ".cache"
USER_AGENT = (
    "DataCenterCommunityBenefitsBot/1.0 "
    "(+https://github.com/pranava0x0; research/curation; contact via repo)"
)
MIN_HOST_INTERVAL_S = 1.5
BACKOFF_START_S = 10.0
MAX_TRIES = 3


class FetchError(RuntimeError):
    """Raised when a URL cannot be fetched after retries. Fail loud (CLAUDE.md)."""


class CachedSession:
    """A rate-limited, disk-cached HTTP GET helper.

    Not thread-safe; the research flow is deliberately sequential and polite.
    """

    def __init__(
        self,
        cache_dir: Path = CACHE_DIR,
        min_interval_s: float = MIN_HOST_INTERVAL_S,
        offline: bool = False,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.min_interval_s = min_interval_s
        self.offline = offline
        self._last_hit: dict[str, float] = {}
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": USER_AGENT})

    # -- cache ---------------------------------------------------------------
    def _cache_path(self, url: str) -> Path:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
        return self.cache_dir / f"{digest}.json"

    def cached(self, url: str) -> dict | None:
        p = self._cache_path(url)
        if p.exists():
            try:
                return json.loads(p.read_text())
            except (json.JSONDecodeError, OSError):
                return None
        return None

    def _store(self, url: str, status: int, text: str, final_url: str) -> dict:
        rec = {"url": url, "final_url": final_url, "status": status, "text": text}
        self._cache_path(url).write_text(json.dumps(rec))
        return rec

    # -- politeness ----------------------------------------------------------
    def _throttle(self, host: str) -> None:
        last = self._last_hit.get(host)
        if last is not None:
            wait = self.min_interval_s - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
        self._last_hit[host] = time.monotonic()

    # -- public --------------------------------------------------------------
    def get(self, url: str, *, refresh: bool = False) -> dict:
        """Return a cache record {url, final_url, status, text}.

        Serves from disk cache unless `refresh=True`. In `offline` mode a cache
        miss raises FetchError instead of hitting the network.
        """
        if not refresh:
            hit = self.cached(url)
            if hit is not None:
                log.debug("cache hit %s", url)
                return hit
        if self.offline:
            raise FetchError(f"offline and not cached: {url}")

        host = urlparse(url).netloc
        backoff = BACKOFF_START_S
        for attempt in range(1, MAX_TRIES + 1):
            self._throttle(host)
            try:
                resp = self._session.get(url, timeout=30, allow_redirects=True)
            except requests.RequestException as exc:
                log.warning("request error %s (try %d): %s", url, attempt, exc)
                if attempt == MAX_TRIES:
                    raise FetchError(f"network error for {url}: {exc}") from exc
                time.sleep(backoff)
                backoff *= 2
                continue

            if resp.status_code == 429:
                log.warning("429 from %s (try %d); backing off %.0fs", url, attempt, backoff)
                if attempt == MAX_TRIES:
                    # Cache the 429 so callers can see it; don't crash the run.
                    return self._store(url, 429, "", resp.url)
                time.sleep(backoff)
                backoff *= 2
                continue

            # requests defaults to ISO-8859-1 when a text/* response has no
            # charset header, which mangles UTF-8 (em-dashes -> "â"). Prefer the
            # detected encoding in that case.
            if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
                resp.encoding = resp.apparent_encoding or "utf-8"
            return self._store(url, resp.status_code, resp.text, resp.url)

        raise FetchError(f"exhausted retries for {url}")
