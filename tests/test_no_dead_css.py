"""Project-owned CSS selectors must have markup behind them.

Two selector-cleanup misses in a single PR is what earned this file. Removing a
renderer orphaned ten `.rp-roster-*` rules, and converting the pledge band to
the shared accordion orphaned `.rp-band-inner` and `.rp-toggle` -- none of it
caught by anything, because CSS class names are not type-checked and dead rules
are invisible: the page renders correctly, the bytes just ship forever.

Scope is deliberately narrow -- only classes carrying a project-owned prefix, so
library classes (Leaflet), utilities, and state classes stay out of it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# Prefixes this project owns. A class outside these is somebody else's problem.
OWNED_PREFIXES = (
    "rp-",
    "acc-",
    "subtab",
    "pledge-",
    "mor-",
    "mtl-",
    "tariff-",
    "agg-",
    "dtab",
    "dpane",
)


def _strip_comments(css: str) -> str:
    """Drop /* ... */ blocks.

    Load-bearing: this file's own header comments name retired classes while
    explaining why they were retired, and a scan that reads comments would
    report those as live and mask a genuinely dead rule.
    """
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


@pytest.fixture(scope="module")
def sources() -> tuple[str, str]:
    css = _strip_comments((DOCS / "styles.css").read_text())
    markup = (DOCS / "index.html").read_text() + (DOCS / "app.js").read_text()
    return css, markup


def test_extractor_finds_a_meaningful_number_of_classes(sources) -> None:
    """Guard against a vacuous pass.

    If the regex or the prefix list ever stops matching, `dead` becomes empty
    and the real test below passes forever while checking nothing.
    """
    css, _ = sources
    owned = {
        c
        for c in re.findall(r"\.([a-zA-Z][\w-]*)", css)
        if c.startswith(OWNED_PREFIXES)
    }
    assert len(owned) > 100, (
        f"only {len(owned)} project-owned classes found in styles.css -- the "
        "extractor is probably broken, which would make the dead-CSS test vacuous"
    )


def test_no_orphaned_project_selectors(sources) -> None:
    css, markup = sources
    owned = sorted(
        {
            c
            for c in re.findall(r"\.([a-zA-Z][\w-]*)", css)
            if c.startswith(OWNED_PREFIXES)
        }
    )

    # A class built as `foo-${x}` never appears literally in the source, so
    # accept any class whose hyphen-boundary stem is followed by an
    # interpolation (`tariff-status-approved` <- `tariff-status-${t.status}`).
    interpolated_stems = set(re.findall(r"([a-zA-Z][\w-]*-)\$\{", markup))

    def is_template_built(cls: str) -> bool:
        return any(cls.startswith(stem) for stem in interpolated_stems)

    dead = [c for c in owned if c not in markup and not is_template_built(c)]
    assert dead == [], (
        "styles.css defines project-owned selectors with no markup behind them.\n"
        "Delete the rules, or (if a class is built dynamically) confirm the "
        "template-literal stem is detectable:\n  "
        + "\n  ".join(f".{c}" for c in dead)
    )
