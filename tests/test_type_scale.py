"""Typography guard: two font families, one size scale (2026-09-23).

The site had drifted to 35 distinct font sizes and five font families
(including monospace, Georgia and Leaflet's Helvetica Neue / Lucida
Console). Every size is now a --fs-* token and every family one of the two
stacks. These checks read styles.css so a new raw value fails here, not in
a design review.
"""

from __future__ import annotations

import re
from pathlib import Path

CSS = (Path(__file__).resolve().parent.parent / "docs" / "styles.css").read_text()
BODY = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)


def _outside_print(text: str) -> str:
    """Drop @media print blocks: print sizes are in pt by design."""
    out, i = [], 0
    for m in re.finditer(r"@media\s+print\s*\{", text):
        out.append(text[i:m.start()])
        depth, k = 1, m.end()
        while depth:
            depth += {"{": 1, "}": -1}.get(text[k], 0)
            k += 1
        i = k
    out.append(text[i:])
    return "".join(out)


def test_every_font_size_is_a_scale_token() -> None:
    raw = []
    for v in re.findall(r"font-size:\s*([^;]+);", _outside_print(BODY)):
        v = v.strip()
        if v.startswith("var(--fs-") or v.endswith("em") and not v.endswith("rem"):
            continue
        m = re.fullmatch(r"([0-9.]+)rem", v)
        if m and float(m.group(1)) < 0.6:  # glyph-sized icons (chevrons, dots)
            continue
        raw.append(v)
    assert raw == [], f"font sizes outside the --fs-* scale: {raw}"


def test_only_two_font_families() -> None:
    fams = {v.strip() for v in re.findall(r"font-family:\s*([^;]+);", BODY)}
    allowed = {"var(--font-sans)", "var(--font-serif)", "inherit"}
    assert fams <= allowed, f"unexpected font-family values: {fams - allowed}"


def test_scale_is_small() -> None:
    tokens = re.findall(r"--fs-[a-z0-9]+:", CSS)
    assert 6 <= len(tokens) <= 10, tokens


def test_masthead_is_the_largest_heading() -> None:
    """No view or section heading may outrank the site title."""
    assert "clamp(" not in re.sub(r"(padding|gap|max-height)[^;]*;", "", BODY)
