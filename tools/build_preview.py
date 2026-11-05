"""build_preview.py — bundle the static docs/ SPA into ONE self-contained HTML
file for previewing (the in-app browser pane renders 0x0 in some environments,
so a self-contained artifact is the reliable way to launch/preview).

Inlines styles.css, embeds every data/*.json payload, and patches fetchJson()
to read the embedded data instead of the network — so the result runs with zero
external requests (except the lazy Leaflet map + html2pdf export, which a strict
CSP sandbox blocks; every other tab works).

Usage:
    python3 tools/build_preview.py            # write .preview/dashboard.html
    python3 tools/build_preview.py --verify   # + headless click-through smoke test

Then publish .preview/dashboard.html as an Artifact for an interactive preview.
Run this on every new commit / PR (see CLAUDE.md → "Launch / preview ritual").
"""
from __future__ import annotations
import logging
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT_DIR = ROOT / ".preview"
OUT = OUT_DIR / "dashboard.html"
# Derived from the emitted payloads rather than listed by hand. A literal list
# here silently rots every time a payload lands: signatories.json arrived in v2
# and the bundle shipped without it, so the Ratepayer view — the landing view —
# rendered zero cards while the build still reported success.
DATA_FILES = sorted(f.stem for f in (DOCS / "data").glob("*.json"))
log = logging.getLogger(__name__)

OLD_FETCH = '''async function fetchJson(url) {
  const res = await fetch(url, { cache: "no-cache" });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return await res.json();
}'''
NEW_FETCH = '''async function fetchJson(url) {
  const embedded = document.getElementById("preview-" + url);
  if (embedded) {
    return JSON.parse(embedded.textContent);
  }
  const res = await fetch(url, { cache: "no-cache" });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return await res.json();
}'''


def build() -> Path:
    html = (DOCS / "index.html").read_text()
    css = (DOCS / "styles.css").read_text()
    appjs = (DOCS / "app.js").read_text()
    if OLD_FETCH not in appjs:
        raise SystemExit("fetchJson() shape changed — update build_preview.py OLD_FETCH.")
    appjs = appjs.replace(OLD_FETCH, NEW_FETCH)
    # The normal site loads the guide lazily; the offline preview embeds it.
    guide = (DOCS / "community-plans.js").read_text().replace("export function ", "function ")
    guide_js = "window.__PLANNING_GUIDE__ = (() => {\n" + guide + "\nreturn {renderPlans, renderEvidence};\n})();"
    if "import(path)" not in appjs:
        raise SystemExit("Planning guide import changed — update build_preview.py.")
    appjs = appjs.replace("import(path)", "Promise.resolve(window.__PLANNING_GUIDE__)")
    elections = (DOCS / "elections.js").read_text().replace("export function ", "function ")
    election_js = "window.__ELECTION_VIEW__ = (() => {\n" + elections + "\nreturn {mount};\n})();"
    if "import(modulePath)" not in appjs:
        raise SystemExit("Election import changed — update build_preview.py.")
    appjs = appjs.replace("import(modulePath)", "Promise.resolve(window.__ELECTION_VIEW__)")
    if re.search(r"\bimport\s*\(", appjs):
        raise SystemExit("Unbundled dynamic import — update build_preview.py.")

    esc = lambda s: s.replace("</script", "<\\/script")
    # Inert JSON is parsed only when its tab opens, rather than parsing every
    # payload at startup and serializing/cloning it again on each fetch.
    data = "\n".join(
        f'<script type="application/json" id="preview-data/{f}.json">'
        + esc((DOCS / "data" / f"{f}.json").read_text().strip()) + "</script>"
        for f in DATA_FILES
    )
    html, styles = re.subn(r'<link\b[^>]*rel="stylesheet"[^>]*href="styles\.css[^"\n]*"[^>]*>',
                          lambda _: f"<style>\n{css}\n</style>", html)
    html, scripts = re.subn(r'<script\b[^>]*src="app\.js[^"\n]*"[^>]*></script>', "", html)
    html = re.sub(r'<link\b[^>]*rel="preload"[^>]*>', "", html)
    if styles != 1 or scripts != 1:
        raise SystemExit("Stylesheet/app script markup changed — update build_preview.py.")
    inline = (
        data + "\n"
        f"<script>\n{esc(guide_js)}\n</script>\n"
        f"<script>\n{esc(election_js)}\n</script>\n"
        f"<script>\n{esc(appjs)}\n</script>\n"
    )
    out = html.replace("</body>", inline + "</body>")
    OUT_DIR.mkdir(exist_ok=True)
    OUT.write_text(out)
    log.info("Wrote %s (%d KB)", OUT, len(out.encode()) / 1024)
    return OUT


def verify() -> int:
    """Headless click-through: assert every tab renders from embedded data."""
    from playwright.sync_api import sync_playwright  # optional dep
    errors: list[str] = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_context(viewport={"width": 1280, "height": 1000}).new_page()
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append("PAGEERR: " + str(e)))
        page.goto(OUT.as_uri() + "#elections", wait_until="load")
        checks = {}
        page.wait_for_selector("#elections-directory .election-card", timeout=8000)
        checks["election_records"] = page.locator(".election-card").count()
        page.locator("#elections-q").fill("Sabattus")
        page.locator('[data-related-record="sabattus-me-2026-11"]').click()
        page.wait_for_selector("#moratorium-modal:not([hidden]) #md-status", timeout=8000)
        checks["election_legal_link"] = page.locator("#md-jurisdiction").inner_text() == "Sabattus"
        page.keyboard.press("Escape")
        page.locator("#tab-moratoriums").click()
        page.wait_for_selector("#moratoriums-tbody tr", timeout=8000)
        checks["moratorium_rows"] = page.locator("#moratoriums-tbody tr").count()
        page.locator("#tab-ratepayer").click(); page.wait_for_timeout(600)
        checks["ratepayer_cards"] = page.locator("#rp-scorecard .rp-card").count()
        page.locator("#tab-tariffs").click(); page.wait_for_timeout(500)
        checks["tariff_rows"] = page.locator("#tariffs-table tbody tr").count()
        page.locator("#tab-overview").click()
        page.locator('[data-guide-target="drafts"]').click()
        page.wait_for_selector("#draft-plan-decision", timeout=8000)
        checks["draft_clauses"] = page.locator("#draft-plan-content .guide-clause").count()
        page.locator("#subtab-pol-evidence").click()
        page.wait_for_selector("#impact-evidence-rule", timeout=8000)
        checks["evidence_checks"] = page.locator("#subpane-pol-evidence .guide-clause").count()
        b.close()
    fatal = [e for e in errors if not any(k in e for k in
             ("leaflet", "html2pdf", "cdnjs", "unpkg", "Failed to load resource"))]
    ok = all(v > 0 for v in checks.values()) and not fatal
    log.info("verify: %s | fatal errors: %s | %s", checks, fatal or "none", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    build()
    raise SystemExit(verify() if "--verify" in sys.argv else 0)
