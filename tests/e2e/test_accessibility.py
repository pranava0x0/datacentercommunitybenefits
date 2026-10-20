"""axe-core on every view (desktop + phone) plus a Nu-validator error ceiling.

Views are derived from app.js VIEWS, so a new tab is covered the day it lands.
Both checks need the network (axe from cdnjs, Nu from w3.org) and skip offline.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from playwright.sync_api import Page

from .conftest import DOCS

E2E_WAIT = int(os.environ.get("E2E_WAIT_MS", "6000")) * 2

AXE_URL = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js"
# Subresource-integrity pin: a changed or tampered CDN file fails, never runs.
AXE_SRI = "sha384-3NYxCdpLKVHfNs2FHPtg3qqaYuhq85m4mMnlHBlN0JzSpKYKct2PMGYfsKGaKIj4"
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
        body = _fetch(AXE_URL)
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:  # offline
        pytest.skip(f"axe-core unavailable: {exc}")
    got = "sha384-" + base64.b64encode(hashlib.sha384(body).digest()).decode()
    assert got == AXE_SRI, f"axe-core at {AXE_URL} does not match the pinned integrity hash"
    return body.decode()


def test_views_were_derived():
    assert len(VIEW_HASHES) >= 9


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("size", [(1366, 900), (390, 844)], ids=["desktop", "phone"])
@pytest.mark.parametrize("hash_", VIEW_HASHES)
def test_no_serious_axe_violations(page: Page, base_url: str, axe_source: str, hash_: str, size, theme):
    page.set_viewport_size({"width": size[0], "height": size[1]})
    page.goto(base_url + "/?a11y=1" + hash_)
    page.wait_for_function("() => state._booted", timeout=E2E_WAIT)
    page.wait_for_load_state("networkidle")
    # Freeze transitions first: a theme swap mid-transition makes axe sample
    # half-blended colours and report contrast failures that a reader never sees.
    page.add_style_tag(content="*,*::before,*::after{transition:none!important;animation:none!important}")
    if theme == "dark":
        page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
    page.evaluate(axe_source)
    res = page.evaluate(
        "async () => (await axe.run(document, {resultTypes: ['violations']})).violations"
        ".filter(v => ['serious','critical'].includes(v.impact))"
        ".map(v => ({id: v.id, impact: v.impact, nodes: v.nodes.slice(0, 4).map(n => n.target.join(' '))}))"
    )
    assert not res, json.dumps(res, indent=1)


def test_sites_list_has_no_axe_violations_of_any_impact(page: Page, base_url: str, axe_source: str):
    """#project-list must keep real list semantics: any impact level fails
    (aria-allowed-role is only 'minor', so the serious/critical gate misses it)."""
    page.goto(base_url + "/?a11y=1#explorer")
    page.wait_for_selector("#project-list .project-card", timeout=E2E_WAIT)
    page.wait_for_load_state("networkidle")
    page.evaluate(axe_source)
    res = page.evaluate(
        "async () => (await axe.run('#project-list', {resultTypes: ['violations']})).violations"
        ".map(v => ({id: v.id, impact: v.impact, nodes: v.nodes.slice(0, 4).map(n => n.target.join(' '))}))"
    )
    assert not res, json.dumps(res, indent=1)
    assert page.evaluate("document.querySelector('#project-list').getAttribute('role')") is None
    assert page.locator("#project-list > li.project-card[role]").count() == 0


def _nu_request() -> list:
    req = urllib.request.Request(
        "https://validator.w3.org/nu/?out=json",
        data=(DOCS / "index.html").read_bytes(),
        headers={"Content-Type": "text/html; charset=utf-8", "User-Agent": "dcb-a11y-test"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=60).read())["messages"]


def test_nu_validator_errors_do_not_grow():
    import time

    msgs = None
    for attempt in range(2):
        try:
            msgs = _nu_request()
            break
        except urllib.error.HTTPError as exc:  # 429/503 etc: the service answered
            if attempt == 0:
                time.sleep(10)
                continue
            pytest.xfail(f"Nu validator rate-limited or down (HTTP {exc.code}); accessibility not verified")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:  # genuinely offline
            pytest.skip(f"Nu validator unreachable: {exc}")
    assert msgs is not None
    errors = [m for m in msgs if m["type"] == "error"]
    assert len(errors) <= NU_ERROR_CEILING, [(m["lastLine"], m["message"]) for m in errors]
