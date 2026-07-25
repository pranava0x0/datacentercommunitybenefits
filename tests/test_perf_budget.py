"""First-paint weight budget.

The dashboard's whole performance story is "no web fonts, no images, code-split
per tab". That only holds if someone counts. Before v2 the landing view was
Comparison, which needed two small payloads; v2 makes Ratepayer the landing
view, and Ratepayer needs projects + responses + the signatory roster too. That
took first paint from ~141 KB to ~237 KB gzipped — inside the 250 KB budget, but
with little room left.

So this test is deliberately tight. If it fails, the fix is almost never to
raise the ceiling: it is to make the new payload lazy (loaded by the view that
needs it, like moratoriums and tariffs are) rather than part of the landing.

Sizes are gzipped because that is how GitHub Pages serves them; raw bytes would
flatter JSON enormously (signatories.json is 121 KB raw and 8 KB gzipped).
"""

from __future__ import annotations

import gzip
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# Everything the browser must fetch before the landing view is usable.
FIRST_PAINT = [
    "index.html",
    "styles.css",
    "app.js",
    "data/companies.json",  # preloaded
    "data/claims.json",  # preloaded
    "data/projects.json",  # Ratepayer scorecard + principle tallies
    "data/responses.json",  # conflict surfacing on the scorecard cards
    "data/signatories.json",  # roster counts + coverage
]

# Payloads that must NOT be part of first paint — they belong to a tab the
# visitor has not opened yet.
LAZY_ONLY = ["data/moratoriums.json", "data/tariffs.json"]

MAX_FIRST_PAINT_KB = 250
MAX_FIRST_PAINT_REQUESTS = 8


def gzipped_kb(rel: str) -> float:
    return len(gzip.compress((DOCS / rel).read_bytes(), 9)) / 1024


def test_first_paint_stays_within_budget() -> None:
    sizes = {rel: gzipped_kb(rel) for rel in FIRST_PAINT}
    total = sum(sizes.values())
    breakdown = "\n".join(f"    {k:26} {v:7.1f} KB" for k, v in sorted(sizes.items()))
    assert total <= MAX_FIRST_PAINT_KB, (
        f"First paint is {total:.1f} KB gzipped, over the {MAX_FIRST_PAINT_KB} KB "
        f"budget:\n{breakdown}\n"
        "Make the newest payload lazy (fetched by the view that needs it) rather "
        "than raising this ceiling."
    )


def test_first_paint_request_count() -> None:
    assert len(FIRST_PAINT) <= MAX_FIRST_PAINT_REQUESTS


def test_heavy_tab_payloads_are_not_preloaded() -> None:
    """Moratoriums + tariffs are per-tab; a <link rel=preload> would undo that."""
    index = (DOCS / "index.html").read_text()
    for rel in LAZY_ONLY:
        name = rel.split("/")[-1]
        assert name not in index, (
            f"{name} appears in index.html — it must stay lazy-loaded by its own tab"
        )


def test_no_web_fonts() -> None:
    """A display face is the easiest way to blow the budget; the serif is a system stack."""
    css = (DOCS / "styles.css").read_text()
    index = (DOCS / "index.html").read_text()
    assert "@font-face" not in css, "web font added to styles.css — see the perf baseline"
    for needle in ("fonts.googleapis.com", "fonts.gstatic.com", "typekit"):
        assert needle not in css and needle not in index, f"external font host {needle}"


def test_no_external_stylesheets_or_blocking_scripts() -> None:
    """Leaflet + html2pdf are lazy-loaded on demand; nothing may block the head."""
    index = (DOCS / "index.html").read_text()
    head = index.split("</head>")[0]
    for tag in re.findall(r"<script[^>]*>", head):
        if "src=" in tag:
            assert "defer" in tag or "async" in tag, f"blocking script in <head>: {tag}"
    for tag in re.findall(r'<link[^>]+rel="stylesheet"[^>]*>', head):
        assert "//" not in tag.split("href=")[1][:40], f"external stylesheet: {tag}"


@pytest.mark.parametrize("rel", FIRST_PAINT)
def test_first_paint_files_exist(rel: str) -> None:
    assert (DOCS / rel).exists(), f"{rel} is in the first-paint list but missing"
