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
    PLEDGE_PRINCIPLE_LABELS,
    PLEDGE_PRINCIPLES,
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


# ---------------------------------------------------------------------------
# The pledge's own words
# ---------------------------------------------------------------------------

# Quoted from https://www.whitehouse.gov/releases/2026/03/ratepayer-protection-pledge/
# (re-fetched and re-verified 2026-07-28). The band renders these under a
# footnote that tells the reader they are verbatim, so they are pinned here:
# re-paraphrasing them has to be a deliberate edit to this file, not a tidy-up
# in app.js.
#
# Until 2026-07-28 they WERE paraphrases, and two drifted in the direction that
# flatters the pledge -- `separate_rate` quoted the section's title back as if
# it were the body's commitment, and `grid_resilience` dropped the source's
# "whenever possible" hedge. Both are called out in app.js.
PLEDGE_COMMITMENT_TEXT = {
    "new_generation": (
        "Companies will build, bring, or buy the new generation resources and "
        "electricity needed to satisfy their new energy demands, paying the full "
        "cost of those resources whether by building, or buying from, new or "
        "otherwise additive power plants."
    ),
    "delivery_infra": (
        "Companies will pay for all new power delivery infrastructure upgrades "
        "required to service their data centers, including adequate network "
        "upgrade costs to ensure that these expenses are not passed on to the "
        "ordinary household."
    ),
    "separate_rate": (
        "Companies will voluntarily negotiate new, separate rate structures with "
        "their utilities and relevant State governments wherever they build data "
        "centers."
    ),
    "local_jobs": (
        "Companies will invest in the local communities in which they build data "
        "centers. This includes hiring from within the local community and "
        "establishing programs to develop relevant skills."
    ),
    "grid_resilience": (
        "Companies will coordinate with grid operators to contribute to a more "
        "reliable grid and, whenever possible, make available their backup "
        "generation resources at times of scarcity to prevent blackouts and power "
        "shortages in their communities."
    ),
}


def _extract_string_values(js_text: str, name: str) -> dict[str, str]:
    """Extract `const NAME = { key: "value", ... }` from app.js."""
    pattern = rf"const\s+{re.escape(name)}\s*=\s*\{{(.*?)\n\}};"
    m = re.search(pattern, js_text, re.DOTALL)
    if not m:
        raise AssertionError(f"Could not find `const {name} = {{...}}` in app.js")
    return dict(re.findall(r'(\w+):\s*\n?\s*"((?:[^"\\]|\\.)*)"', m.group(1)))


def test_commitment_text_is_verbatim_from_the_pledge(js: str) -> None:
    got = _extract_string_values(js, "PLEDGE_PRINCIPLE_DESCRIPTIONS")
    assert set(got) == set(PLEDGE_COMMITMENT_TEXT), (
        "PLEDGE_PRINCIPLE_DESCRIPTIONS must cover exactly the five commitments: "
        f"missing={set(PLEDGE_COMMITMENT_TEXT) - set(got)}, "
        f"extra={set(got) - set(PLEDGE_COMMITMENT_TEXT)}"
    )
    for key, expected in PLEDGE_COMMITMENT_TEXT.items():
        assert got[key] == expected, (
            f"Commitment {key!r} is no longer the pledge's own wording.\n"
            f"  app.js:   {got[key]}\n"
            f"  published: {expected}"
        )


def test_commitment_titles_are_the_pledges_headings(js: str) -> None:
    """Title wording must match the published headings word for word.

    Case is deliberately normalised -- the source uses Title Case, the dashboard
    renders sentence case throughout -- so this compares casefolded text.
    """
    published = {
        "new_generation": "Building, Bringing, or Buying New Power Supply",
        "delivery_infra": "Paying for New Power Delivery Infrastructure Upgrades",
        "separate_rate": "Paying Whether They Use the Power or Not",
        "local_jobs": "Investing in Local Job Creation and Workforce Development",
        "grid_resilience": "Contributing to Electric and Community Resilience",
    }
    got = _extract_string_values(js, "PLEDGE_PRINCIPLE_LABELS")
    for key, expected in published.items():
        assert got[key].casefold() == expected.casefold(), (
            f"Commitment title {key!r} differs from the published heading.\n"
            f"  app.js:    {got[key]}\n"
            f"  published: {expected}"
        )


def test_pledge_principles_match(js: str) -> None:
    """The five commitments are mirrored Python <-> JS with no guard until now.

    Every other mirrored vocabulary here (THEMES, DELIVERED_*, RATEPAYER_*,
    TARIFF_*, SIGNATORY_*) has a parity test; this one did not, which is exactly
    the shape CLAUDE.md keeps warning about -- a hand-written list beside the
    registry it mirrors.
    """
    assert _extract_array(js, "PLEDGE_PRINCIPLES") == list(PLEDGE_PRINCIPLES), (
        "PLEDGE_PRINCIPLES differs between schema.py and app.js"
    )


def test_pledge_principle_labels_match(js: str) -> None:
    got = _extract_string_values(js, "PLEDGE_PRINCIPLE_LABELS")
    assert got == dict(PLEDGE_PRINCIPLE_LABELS), (
        "PLEDGE_PRINCIPLE_LABELS differs between schema.py and app.js:\n"
        f"  py-only={set(PLEDGE_PRINCIPLE_LABELS) - set(got)}\n"
        f"  js-only={set(got) - set(PLEDGE_PRINCIPLE_LABELS)}\n"
        + "".join(
            f"  {k}: py={PLEDGE_PRINCIPLE_LABELS[k]!r} js={got[k]!r}\n"
            for k in set(got) & set(PLEDGE_PRINCIPLE_LABELS)
            if got[k] != PLEDGE_PRINCIPLE_LABELS[k]
        )
    )


# --- Rate cases (v3): the proceeding layer under the tariffs ----------------


def test_rate_case_statuses_match(js: str) -> None:
    from schema import RATE_CASE_STATUSES

    js_statuses = _extract_array(js, "RATE_CASE_STATUSES")
    assert tuple(js_statuses) == RATE_CASE_STATUSES, (
        f"RATE_CASE_STATUSES drift between schema.py {RATE_CASE_STATUSES} and "
        f"app.js {tuple(js_statuses)}. Update both files together."
    )


def test_rate_case_status_labels_keys_match(js: str) -> None:
    from schema import RATE_CASE_STATUS_LABELS

    js_keys = _extract_object_keys(js, "RATE_CASE_STATUS_LABELS")
    assert js_keys == set(RATE_CASE_STATUS_LABELS.keys())


def test_rate_case_types_match(js: str) -> None:
    from schema import RATE_CASE_TYPES

    js_types = _extract_array(js, "RATE_CASE_TYPES")
    assert tuple(js_types) == RATE_CASE_TYPES, (
        f"RATE_CASE_TYPES drift between schema.py {RATE_CASE_TYPES} and "
        f"app.js {tuple(js_types)}. Update both files together."
    )


def test_rate_case_type_labels_keys_match(js: str) -> None:
    from schema import RATE_CASE_TYPE_LABELS

    js_keys = _extract_object_keys(js, "RATE_CASE_TYPE_LABELS")
    assert js_keys == set(RATE_CASE_TYPE_LABELS.keys())


def test_rate_case_badge_class_covers_every_status(js: str) -> None:
    """Every status must render with a real badge class — an unmapped status
    falls back to the bare .badge with no color, the badge-reason-* failure
    shape from v1.19."""
    from schema import RATE_CASE_STATUSES

    js_keys = _extract_object_keys(js, "RATE_CASE_BADGE_CLASS")
    assert js_keys == set(RATE_CASE_STATUSES)
