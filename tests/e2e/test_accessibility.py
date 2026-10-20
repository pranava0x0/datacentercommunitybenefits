"""axe-core on every view (desktop + phone) plus a Nu-validator error ceiling.

Views are derived from app.js VIEWS, so a new tab is covered the day it lands.
Both checks need the network (axe from cdnjs, Nu from w3.org) and skip offline.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

import pytest
from playwright.sync_api import Page

from .conftest import DOCS

E2E_WAIT = int(os.environ.get("E2E_WAIT_MS", "6000")) * 2

AXE_URL = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js"
_APP = (DOCS / "app.js").read_text()
VIEW_HASHES = re.findall(r'\{ name: "[a-z]+", tab: "[^"]+", section: "[^"]+", hash: "(#[a-z]+)" \}', _APP)
NU_ERROR_CEILING = 0  # may only go down
BLOCKING = ("serious", "critical")


def _fetch(url: str, **kw) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "dcb-a11y-test"}, **kw)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


@pytest.fixture(scope="module")
def axe_source() -> str:
    try:
        return _fetch(AXE_URL).decode()
    except Exception as exc:  # offline
        pytest.skip(f"axe-core unavailable: {exc}")


def test_views_were_derived():
    assert len(VIEW_HASHES) >= 9


@pytest.mark.parametrize("size", [(1366, 900), (390, 844)], ids=["desktop", "phone"])
@pytest.mark.parametrize("hash_", VIEW_HASHES)
def test_no_serious_axe_violations(page: Page, base_url: str, axe_source: str, hash_: str, size):
    page.set_viewport_size({"width": size[0], "height": size[1]})
    page.goto(base_url + "/?a11y=1" + hash_)
    page.wait_for_function("() => state._booted", timeout=E2E_WAIT)
    page.wait_for_load_state("networkidle")
    page.evaluate(axe_source)
    res = page.evaluate(
        "async () => (await axe.run(document, {resultTypes: ['violations']})).violations"
        ".filter(v => ['serious','critical'].includes(v.impact))"
        ".map(v => ({id: v.id, impact: v.impact, nodes: v.nodes.slice(0, 4).map(n => n.target.join(' '))}))"
    )
    assert not res, json.dumps(res, indent=1)


def test_nu_validator_errors_do_not_grow():
    try:
        req = urllib.request.Request(
            "https://validator.w3.org/nu/?out=json",
            data=(DOCS / "index.html").read_bytes(),
            headers={"Content-Type": "text/html; charset=utf-8", "User-Agent": "dcb-a11y-test"},
        )
        msgs = json.loads(urllib.request.urlopen(req, timeout=60).read())["messages"]
    except Exception as exc:
        pytest.skip(f"Nu validator unavailable: {exc}")
    errors = [m for m in msgs if m["type"] == "error"]
    assert len(errors) <= NU_ERROR_CEILING, [(m["lastLine"], m["message"]) for m in errors]
