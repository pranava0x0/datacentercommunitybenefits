"""Project-owned CSS selectors must have markup behind them.

Two selector-cleanup misses in a single PR earned this file. Removing a
renderer orphaned ten `.rp-roster-*` rules, and converting the pledge band to
the shared accordion orphaned `.rp-band-inner` and `.rp-toggle` -- none of it
caught by anything, because CSS class names are not type-checked and dead rules
are invisible: the page renders correctly, the bytes just ship forever.

**The first version of this guard was itself broken**, and Codex caught it in
review. It asked "does this class name appear anywhere in index.html/app.js?",
which a plain substring answers `True` for an *id* of the same name, a mention
in a comment, or an unrelated string. Concretely: `.rp-commitments` had three
orphaned rule blocks and the test passed, because `id="rp-commitments"` exists
on an element whose class is `rp-commit-list`. A guard that accepts an id as
evidence of a class is worse than no guard -- it certifies what it cannot see.

So this parses actual class *application* sites instead:

  * `class="..."` attributes (in HTML, and in JS template strings)
  * `className = "..."` / `className: "..."`
  * `classList.add/remove/toggle/contains("...")`
  * this project's `el(tag, "classes", ...)` helper

Interpolated names (`` `rp-met-pill--${level}` ``) can't be resolved
statically, so the literal prefix is kept as a *stem* and any class starting
with it is accepted. That is a deliberate hole, and a narrow one: the stem has
to appear in a real class position, not anywhere in the file.

Scope is deliberately narrow -- only classes carrying a project-owned prefix,
so library classes (Leaflet), utilities, and state classes stay out of it.
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

# Stands in for a `${...}` interpolation while tokenizing.
_INTERP = "\x00"


def _strip_comments(css: str) -> str:
    """Drop /* ... */ blocks.

    Load-bearing: this file's own header comments name retired classes while
    explaining why they were retired, and a scan that reads comments would
    report those as live and mask a genuinely dead rule.
    """
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def _tokenize(value: str) -> tuple[set[str], set[str]]:
    """Split one class-attribute value into (exact names, interpolation stems).

    Handles `${...}` that never closes inside the captured span. That happens
    constantly here, because the interpolation contains its own quotes:

        class="mor-toggle-btn${active ? " is-active" : ""}"

    The `class="..."` regex stops at the quote before ` is-active`, so the
    captured value ends mid-expression. Substituting only well-formed `${...}`
    left `mor-toggle-btn${active` as a literal class name and reported the
    perfectly live `.mor-toggle-btn` as dead. Any residual `${` therefore
    truncates the token to a stem.
    """
    exact: set[str] = set()
    stems: set[str] = set()
    for token in re.sub(r"\$\{[^}]*\}", _INTERP, value).split():
        # Unterminated interpolation: keep whatever preceded it as a stem.
        if "${" in token:
            head = token.split("${")[0].split(_INTERP)[0]
            if head:
                stems.add(head)
        elif _INTERP in token:
            head = token.split(_INTERP)[0]
            if head:
                stems.add(head)
        elif token:
            exact.add(token)
    return exact, stems


def _applied_classes(html: str, js: str) -> tuple[set[str], set[str]]:
    """Every class this codebase actually puts on an element."""
    exact: set[str] = set()
    stems: set[str] = set()

    def absorb(value: str) -> None:
        e, s = _tokenize(value)
        exact.update(e)
        stems.update(s)

    both = html + "\n" + js
    # class="..." — HTML attributes and JS template strings alike.
    for m in re.finditer(r"""class\s*=\s*(["'`])(.*?)\1""", both, re.DOTALL):
        absorb(m.group(2))
    # className = "..." / className: "..."
    for m in re.finditer(r"""className\s*[=:]\s*(["'`])(.*?)\1""", js, re.DOTALL):
        absorb(m.group(2))
    # classList.add("a", "b") and friends
    for m in re.finditer(r"classList\.(?:add|remove|toggle|contains)\(([^)]*)\)", js):
        for literal in re.findall(r"""["'`]([^"'`]*)["'`]""", m.group(1)):
            absorb(literal)
    # el(tag, "classes", ...) — this project's element helper
    for m in re.finditer(r"""\bel\(\s*["'][\w-]+["']\s*,\s*["'`]([^"'`]*)["'`]""", js):
        absorb(m.group(1))
    return exact, stems


@pytest.fixture(scope="module")
def scan() -> tuple[list[str], set[str], set[str]]:
    css = _strip_comments((DOCS / "styles.css").read_text())
    html = (DOCS / "index.html").read_text()
    js = (DOCS / "app.js").read_text()
    owned = sorted(
        {
            c
            for c in re.findall(r"\.([a-zA-Z][\w-]*)", css)
            if c.startswith(OWNED_PREFIXES)
        }
    )
    exact, stems = _applied_classes(html, js)
    return owned, exact, stems


def test_extractor_finds_a_meaningful_number_of_classes(scan) -> None:
    """Guard against a vacuous pass on BOTH sides of the comparison.

    If the CSS regex or the prefix list breaks, `owned` empties and the real
    test passes while checking nothing. If the markup parser breaks, `exact`
    empties and it fails on everything -- noisy, but at least loud.
    """
    owned, exact, _ = scan
    assert len(owned) > 100, (
        f"only {len(owned)} project-owned classes found in styles.css -- the "
        "CSS extractor is probably broken, which would make the dead-CSS test "
        "vacuous"
    )
    assert len(exact) > 100, (
        f"only {len(exact)} applied classes parsed from index.html/app.js -- "
        "the markup parser is probably broken"
    )


def test_an_id_is_not_evidence_of_a_class(scan) -> None:
    """Pins the specific hole Codex found.

    `id="rp-commitments"` sits on an element whose class is `rp-commit-list`.
    A substring-based guard reported `.rp-commitments` as live on the strength
    of that id and hid three orphaned rule blocks.
    """
    _, exact, _ = scan
    html = (DOCS / "index.html").read_text()
    assert 'id="rp-commitments"' in html, "fixture drifted -- the id is gone"
    assert "rp-commitments" not in exact, (
        "the parser is treating an id as a class application again"
    )


def test_no_orphaned_project_selectors(scan) -> None:
    owned, exact, stems = scan
    dead = [
        c for c in owned if c not in exact and not any(c.startswith(st) for st in stems)
    ]
    assert dead == [], (
        "styles.css defines project-owned selectors that are never applied to "
        "any element.\nDelete the rules, or (if a class is built dynamically) "
        "check the template-literal stem is detectable:\n  "
        + "\n  ".join(f".{c}" for c in dead)
    )
