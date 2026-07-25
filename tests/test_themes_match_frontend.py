"""Schema THEMES vocabulary must match frontend THEMES vocabulary.

Two copies, one source of truth — but they live in different runtimes (Python /
JS). This test reads both and asserts equality so they can't drift silently.
Per CLAUDE.md > "Theme constants live in one place".
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from schema import (
    COMPANY_SLUGS,
    SIGNATORY_CATEGORIES,
    SIGNATORY_CATEGORY_LABELS,
    SIGNATORY_TRACK_LABELS,
    SIGNATORY_TRACKS,
    DELIVERED_LABELS,
    DELIVERED_STATUSES,
    RATEPAYER_LABELS,
    RATEPAYER_STATUSES,
    TARIFF_PARAMETER_GROUP_OF,
    TARIFF_PARAMETER_LABELS,
    TARIFF_PARAMETERS,
    TARIFF_STATUS_LABELS,
    TARIFF_STATUSES,
    THEME_LABELS,
    THEMES,
)

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


def test_ratepayer_statuses_match(js: str) -> None:
    js_statuses = _extract_array(js, "RATEPAYER_STATUSES")
    assert tuple(js_statuses) == RATEPAYER_STATUSES, (
        f"RATEPAYER_STATUSES drift between schema.py {RATEPAYER_STATUSES} and "
        f"app.js {tuple(js_statuses)}. Update both files together."
    )


def test_ratepayer_labels_keys_match(js: str) -> None:
    js_keys = _extract_object_keys(js, "RATEPAYER_LABELS")
    assert js_keys == set(RATEPAYER_LABELS.keys()), (
        "RATEPAYER_LABELS keys differ between schema.py and app.js: "
        f"py-only={set(RATEPAYER_LABELS.keys()) - js_keys}, "
        f"js-only={js_keys - set(RATEPAYER_LABELS.keys())}"
    )


# --- Utility tariff vocabulary parity (v1.17) ---------------------------------


def test_tariff_statuses_match(js: str) -> None:
    js_statuses = _extract_array(js, "TARIFF_STATUSES")
    assert tuple(js_statuses) == TARIFF_STATUSES, (
        f"TARIFF_STATUSES drift between schema.py {TARIFF_STATUSES} and "
        f"app.js {tuple(js_statuses)}. Update both files together."
    )


def test_tariff_parameters_match(js: str) -> None:
    js_params = _extract_array(js, "TARIFF_PARAMETERS")
    assert tuple(js_params) == TARIFF_PARAMETERS, (
        f"TARIFF_PARAMETERS drift between schema.py {TARIFF_PARAMETERS} and "
        f"app.js {tuple(js_params)}. The LBL element taxonomy is frozen — update "
        "both files together (and add a BACKLOG entry)."
    )


def test_tariff_status_labels_keys_match(js: str) -> None:
    js_keys = _extract_object_keys(js, "TARIFF_STATUS_LABELS")
    assert js_keys == set(TARIFF_STATUS_LABELS.keys()), (
        "TARIFF_STATUS_LABELS keys differ between schema.py and app.js: "
        f"py-only={set(TARIFF_STATUS_LABELS.keys()) - js_keys}, "
        f"js-only={js_keys - set(TARIFF_STATUS_LABELS.keys())}"
    )


def test_tariff_parameter_labels_keys_match(js: str) -> None:
    js_keys = _extract_object_keys(js, "TARIFF_PARAMETER_LABELS")
    assert js_keys == set(TARIFF_PARAMETER_LABELS.keys()), (
        "TARIFF_PARAMETER_LABELS keys differ between schema.py and app.js: "
        f"py-only={set(TARIFF_PARAMETER_LABELS.keys()) - js_keys}, "
        f"js-only={js_keys - set(TARIFF_PARAMETER_LABELS.keys())}"
    )


def test_tariff_parameter_group_of_keys_match(js: str) -> None:
    js_keys = _extract_object_keys(js, "TARIFF_PARAMETER_GROUP_OF")
    assert js_keys == set(TARIFF_PARAMETER_GROUP_OF.keys()), (
        "TARIFF_PARAMETER_GROUP_OF keys differ between schema.py and app.js: "
        f"py-only={set(TARIFF_PARAMETER_GROUP_OF.keys()) - js_keys}, "
        f"js-only={js_keys - set(TARIFF_PARAMETER_GROUP_OF.keys())}"
    )


# ---------------------------------------------------------------------------
# Pledge roster vocabulary (v2)
# ---------------------------------------------------------------------------
# SIGNATORY_TRACK_LABELS is keyed on dashed strings ("white-house-2026-03-04"),
# which JS must quote — _extract_object_keys only matches bare identifiers, so
# these need their own extractor rather than a shared one.


def _extract_quoted_or_bare_keys(js_text: str, name: str) -> set[str]:
    """Extract keys from `const NAME = {...}`, quoted or bare."""
    pattern = rf"const\s+{re.escape(name)}\s*=\s*\{{(.*?)\n\}}\s*;"
    m = re.search(pattern, js_text, re.DOTALL)
    if not m:
        raise AssertionError(f"Could not find `const {name} = {{...}}` in app.js")
    body = m.group(1)
    return set(
        re.findall(r'^\s*"([^"]+)"\s*:', body, re.MULTILINE)
    ) | set(re.findall(r"^\s*([A-Za-z_][A-Za-z_0-9]*)\s*:", body, re.MULTILINE))


def test_signatory_categories_match(js: str) -> None:
    js_cats = _extract_array(js, "SIGNATORY_CATEGORIES")
    assert tuple(js_cats) == SIGNATORY_CATEGORIES, (
        f"SIGNATORY_CATEGORIES drift between schema.py {SIGNATORY_CATEGORIES} "
        f"and app.js {tuple(js_cats)}. Update both files together."
    )


def test_signatory_tracks_match(js: str) -> None:
    js_tracks = _extract_array(js, "SIGNATORY_TRACKS")
    assert tuple(js_tracks) == SIGNATORY_TRACKS, (
        f"SIGNATORY_TRACKS drift between schema.py {SIGNATORY_TRACKS} "
        f"and app.js {tuple(js_tracks)}. Update both files together."
    )


def test_signatory_category_labels_keys_match(js: str) -> None:
    js_keys = _extract_quoted_or_bare_keys(js, "SIGNATORY_CATEGORY_LABELS")
    assert js_keys == set(SIGNATORY_CATEGORY_LABELS.keys()), (
        "SIGNATORY_CATEGORY_LABELS keys differ between schema.py and app.js: "
        f"py-only={set(SIGNATORY_CATEGORY_LABELS.keys()) - js_keys}, "
        f"js-only={js_keys - set(SIGNATORY_CATEGORY_LABELS.keys())}"
    )


def test_signatory_track_labels_keys_match(js: str) -> None:
    js_keys = _extract_quoted_or_bare_keys(js, "SIGNATORY_TRACK_LABELS")
    assert js_keys == set(SIGNATORY_TRACK_LABELS.keys()), (
        "SIGNATORY_TRACK_LABELS keys differ between schema.py and app.js: "
        f"py-only={set(SIGNATORY_TRACK_LABELS.keys()) - js_keys}, "
        f"js-only={js_keys - set(SIGNATORY_TRACK_LABELS.keys())}"
    )


def test_every_category_has_a_short_label(js: str) -> None:
    """Filter chips use the short form; a missing one renders `undefined`."""
    js_keys = _extract_quoted_or_bare_keys(js, "SIGNATORY_CATEGORY_SHORT")
    assert js_keys == set(SIGNATORY_CATEGORIES), (
        "SIGNATORY_CATEGORY_SHORT must cover every category: "
        f"missing={set(SIGNATORY_CATEGORIES) - js_keys}, extra={js_keys - set(SIGNATORY_CATEGORIES)}"
    )
