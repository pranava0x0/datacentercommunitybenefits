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
  * `classList.add("...")` / `classList.toggle("...")` -- ADDING operations
    only. `remove()` and `contains()` are not evidence that anything can ever
    carry the class.
  * this project's `el(tag, "classes", ...)` helper

Interpolated names (`` `rp-met-pill--${level}` ``) can't be resolved
statically, so the literal prefix is kept as a *stem* and any class starting
with it is accepted. That is a deliberate hole, and a narrow one: the stem has
to appear in a real class position, not anywhere in the file.

Scope is every class in styles.css except third-party prefixes (Leaflet).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# Everything in styles.css is ours EXCEPT these. An allowlist of owned prefixes
# was the first design and it silently omitted whole families -- `claims-` and
# `chip-` were missing, so `.claims-section` and `.chip-row` sat dead and
# certified clean. A guard whose scope is hand-maintained rots exactly like the
# hand-written lists CLAUDE.md warns about; a denylist of foreign prefixes is
# short, obvious when it needs an entry, and fails loudly rather than silently.
THIRD_PARTY_PREFIXES = ("leaflet",)

# Stands in for a `${...}` interpolation while tokenizing.
_INTERP = "\x00"


def _strip_comments(css: str) -> str:
    """Drop /* ... */ blocks.

    Load-bearing: this file's own header comments name retired classes while
    explaining why they were retired, and a scan that reads comments would
    report those as live and mask a genuinely dead rule.
    """
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def _strip_source_comments(html: str, js: str) -> tuple[str, str]:
    """Remove comments so retired-by-commenting-out markup isn't read as live.

    The CSS side has always been stripped; the markup side was not, so
    `<!-- <div class="retired"> -->` kept its selector certified. Same
    false-negative this file exists to close, one input over.

    The JS stripper is context-aware ON PURPOSE. A `//`-matching regex cannot
    tell a comment from the `//` inside `"https://example.com"` and will
    silently eat half a URL -- see the base CLAUDE.md's rule about never
    regex-stripping comments from JS. This walks the source tracking string,
    template and regex-literal context, and `test_comment_stripper_preserves_string_literals`
    proves it leaves a known URL intact.
    """
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

    out: list[str] = []
    i, n = 0, len(js)
    quote: str | None = None
    while i < n:
        ch = js[i]
        nxt = js[i + 1] if i + 1 < n else ""
        if quote:
            if ch == "\\":
                out.append(js[i : i + 2])
                i += 2
                continue
            if ch == quote:
                quote = None
            out.append(ch)
            i += 1
            continue
        if ch in "\"'`":
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == "/" and nxt == "/":
            while i < n and js[i] != "\n":
                i += 1
            continue
        if ch == "/" and nxt == "*":
            end = js.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue
        out.append(ch)
        i += 1
    return html, "".join(out)


def _class_attr_values(text: str) -> list[str]:
    """Every complete `class="..."` value, interpolations included.

    A regex cannot do this, and two false positives proved it. These attribute
    values routinely contain their own quotes inside a `${...}`:

        class="mor-toggle-btn${active ? " is-active" : ""}"
        class="at-a-glance-text${isCurated ? " curator-override" : ""}"

    A `class="(.*?)"` match stops at the quote before ` is-active`, capturing a
    fragment that ends mid-expression. That reported `.mor-toggle-btn` as dead
    (its name became `mor-toggle-btn${active`) AND `.curator-override` as dead
    (its name lives in a segment the match never reached) -- both perfectly
    live. So walk the value, tracking `${}` depth, and only let a quote at
    depth 0 close it.
    """
    values: list[str] = []
    for m in re.finditer(r"""class\s*=\s*(["'`])""", text):
        quote = m.group(1)
        i = m.end()
        depth = 0
        start = i
        while i < len(text):
            ch = text[i]
            if text.startswith("${", i):
                depth += 1
                i += 2
                continue
            if ch == "}" and depth:
                depth -= 1
            elif ch == quote and depth == 0:
                values.append(text[start:i])
                break
            i += 1
    return values


def _tokenize(value: str) -> tuple[set[str], set[str]]:
    """Split one class-attribute value into (exact names, interpolation stems).

    Class names that live *inside* an interpolation's string literals are real
    application sites (`${isCurated ? " curator-override" : ""}`), so those
    literals are harvested before the `${...}` blocks are collapsed away.
    """
    exact: set[str] = set()
    stems: set[str] = set()

    # Names contributed from within the interpolation's own string literals.
    for expr in re.findall(r"\$\{(.*?)\}", value, re.DOTALL):
        for literal in re.findall(r"""["'`]([^"'`]*)["'`]""", expr):
            exact.update(literal.split())

    for token in re.sub(r"\$\{.*?\}", _INTERP, value, flags=re.DOTALL).split():
        if "${" in token:  # unbalanced remnant
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
    for value in _class_attr_values(both):
        absorb(value)
    # className = "..." / className: "..."
    for m in re.finditer(r"""className\s*[=:]\s*(["'`])(.*?)\1""", js, re.DOTALL):
        absorb(m.group(2))
    # classList.add("a", "b") / .toggle("a") -- ADDING operations only.
    # `remove()` and `contains()` were in this list and are not evidence of
    # anything: if the code that applied a class is deleted and only the
    # cleanup or the query survives, no element can ever carry it, yet the
    # selector would still be certified live. That is the same false-negative
    # this whole file exists to close.
    for m in re.finditer(r"classList\.(?:add|toggle)\(([^)]*)\)", js):
        for literal in re.findall(r"""["'`]([^"'`]*)["'`]""", m.group(1)):
            absorb(literal)
    # el(tag, "classes", ...) — this project's element helper — and Leaflet's
    # L.DomUtil.create(tag, "classes"), which builds the map legend. Missing
    # the latter reported the perfectly live .map-legend as dead.
    for pattern in (
        r"""\bel\(\s*["'][\w-]+["']\s*,\s*["'`]([^"'`]*)["'`]""",
        r"""DomUtil\.create\(\s*["'][\w-]+["']\s*,\s*["'`]([^"'`]*)["'`]""",
    ):
        for m in re.finditer(pattern, js):
            absorb(m.group(1))
    return exact, stems


@pytest.fixture(scope="module")
def scan() -> tuple[list[str], set[str], set[str]]:
    css = _strip_comments((DOCS / "styles.css").read_text())
    html, js = _strip_source_comments(
        (DOCS / "index.html").read_text(), (DOCS / "app.js").read_text()
    )
    owned = sorted(
        {
            c
            for c in re.findall(r"\.([a-zA-Z][\w-]*)", css)
            if not c.startswith(THIRD_PARTY_PREFIXES)
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
        f"only {len(owned)} project classes found in styles.css -- the "
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


def test_comment_stripper_preserves_string_literals() -> None:
    """The JS stripper must not eat `//` inside a string.

    A regex-based stripper silently corrupts `"https://..."` into `"https:` --
    the failure the base CLAUDE.md rule was written about. This asserts a real
    URL from app.js survives, and that a genuine comment does not.
    """
    js_raw = (DOCS / "app.js").read_text()
    marker = "https://www.whitehouse.gov"
    assert marker in js_raw, "fixture drifted -- pick another literal"
    _, js = _strip_source_comments("", js_raw)
    assert marker in js, "the stripper ate a URL inside a string literal"

    _, stripped = _strip_source_comments(
        "", 'const a = "keep://this"; // drop-this\n/* and-this */ const b = 1;'
    )
    assert "keep://this" in stripped
    assert "drop-this" not in stripped
    assert "and-this" not in stripped


def test_commented_out_markup_is_not_a_live_class() -> None:
    """Pins the hole Codex found: retiring markup by commenting it out must not
    keep its CSS certified."""
    html, js = _strip_source_comments(
        '<!-- <div class="zz-retired-html"></div> -->',
        '// el("div", "zz-retired-js")\n',
    )
    exact, _ = _applied_classes(html, js)
    assert "zz-retired-html" not in exact
    assert "zz-retired-js" not in exact
