"""Connector framework for the Data Center Community Benefits Dashboard.

In v1 the dashboard is fully curated — `data/seed/*.json` is the source of truth
and `refresh.py` validates and emits it. This package exists as the scaffolding
for v2, where per-company scrapers will fetch claims directly from each
company's published community-impact page.

See `connectors/base.py` for the (intentionally minimal) base class. Per
CLAUDE.md, ad-hoc news / community-response sources will stay curated in v2 —
no automated sentiment classification.
"""

from connectors.base import Connector

__all__ = ["Connector"]
