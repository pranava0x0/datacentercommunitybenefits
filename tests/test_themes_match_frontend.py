"""Schema THEMES vocabulary must match frontend THEMES vocabulary.

Two copies, one source of truth — but they live in different runtimes (Python /
JS). This test reads both and asserts equality so they can't drift silently.
Per CLAUDE.md > "Theme constants live in one place".
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from schema import COMPANY_SLUGS, DELIVERED_LABELS, DELIVERED_STATUSES, THEME_LABELS, THEMES

ROOT = Path(__file__).resolve().parent.parent
APP_JS = ROOT / "docs" / "app.js"


def _extract_array(js_text: str, name: str) -> list[str]:
    """Extract `const NAME = [ "a", "b", ... ]` from app.js as a Python list."""
    pattern = rf"const\s+{re.escape(name)}\s*=\s*\[(.*?)\]\s*;"
    m = re.search(pattern, js_text, re.DOTALL)
    if not m:
        raise AssertionError(f"Could not find `const {name} = [...]` in app.js")
    items = re.findall(r'"([^"]+)"', m.group(1))
    return items


def _extract_object_keys(js_text: str, name: str) -> set[str]:
    """Extract keys from `const NAME = { foo: ..., bar: ... }`."""
    pattern = rf"const\s+{re.escape(name)}\s*=\s*\{{(.*?)\}}\s*;"
    m = re.search(pattern, js_text, re.DOTALL)
    if not m:
        raise AssertionError(f"Could not find `const {name} = {{...}}` in app.js")
    body = m.group(1)
    keys = re.findall(r"^\s*([A-Za-z_][A-Za-z_0-9]*)\s*:", body, re.MULTILINE)
    return set(keys)


@pytest.fixture(scope="module")
def js() -> str:
    return APP_JS.read_text(encoding="utf-8")


def test_themes_exact_match(js: str) -> None:
    js_themes = _extract_array(js, "THEMES")
    assert tuple(js_themes) == THEMES, (
        f"THEMES drift between schema.py {THEMES} and app.js {tuple(js_themes)}. "
        "Update both files together."
    )


def test_theme_labels_keys_match(js: str) -> None:
    js_keys = _extract_object_keys(js, "THEME_LABELS")
    assert js_keys == set(THEME_LABELS.keys()), (
        "THEME_LABELS keys differ between schema.py and app.js: "
        f"py-only={set(THEME_LABELS.keys()) - js_keys}, "
        f"js-only={js_keys - set(THEME_LABELS.keys())}"
    )


def test_company_slugs_match(js: str) -> None:
    js_slugs = _extract_array(js, "COMPANY_SLUGS")
    assert tuple(js_slugs) == COMPANY_SLUGS, (
        f"COMPANY_SLUGS drift: py={COMPANY_SLUGS}, js={tuple(js_slugs)}"
    )


def test_delivered_statuses_match(js: str) -> None:
    js_statuses = _extract_array(js, "DELIVERED_STATUSES")
    assert tuple(js_statuses) == DELIVERED_STATUSES, (
        f"DELIVERED_STATUSES drift between schema.py {DELIVERED_STATUSES} and "
        f"app.js {tuple(js_statuses)}. Update both files together."
    )


def test_delivered_labels_keys_match(js: str) -> None:
    js_keys = _extract_object_keys(js, "DELIVERED_LABELS")
    assert js_keys == set(DELIVERED_LABELS.keys()), (
        "DELIVERED_LABELS keys differ between schema.py and app.js: "
        f"py-only={set(DELIVERED_LABELS.keys()) - js_keys}, "
        f"js-only={js_keys - set(DELIVERED_LABELS.keys())}"
    )
