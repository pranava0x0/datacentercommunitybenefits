"""Base class for v2 per-company scrapers.

v1 ships fully curated; this base exists so that adding a connector in v2 is
a one-file drop. The pattern is intentionally a small subset of the connector
framework used in adjacent projects in this org:

- Each connector owns its `slug` (cache key namespace + CLI flag).
- Each connector implements `fetch_claims()` returning a list of `Claim` records.
- The driver (`refresh.py`) handles HTTP infra, schema validation, and output write.

Until v2, the only "connector" is the curated seed loader in `refresh.py` itself.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from schema import Claim


class Connector(ABC):
    """A v2 per-company benefit-claim scraper. Not used in v1."""

    slug: str
    """Stable connector key, e.g. 'meta-community-page'. Used for cache namespacing."""

    company_slug: str
    """The `Company.slug` whose claims this connector emits."""

    @abstractmethod
    def fetch_claims(self) -> Iterable[Claim]:
        """Return Claim records for this company.

        Implementations MUST:
        - Set `source_url` to the page each claim was extracted from.
        - Set `captured_at` to the date of the fetch.
        - Quote `statement` verbatim — never paraphrase. See CLAUDE.md.
        """
        raise NotImplementedError
