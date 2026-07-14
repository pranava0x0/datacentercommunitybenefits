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
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT_DIR = ROOT / ".preview"
OUT = OUT_DIR / "dashboard.html"
DATA_FILES = ["companies", "claims", "projects", "responses", "moratoriums", "tariffs"]

OLD_FETCH = '''async function fetchJson(url) {
  const res = await fetch(url, { cache: "no-cache" });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return await res.json();
}'''
NEW_FETCH = '''async function fetchJson(url) {
  if (window.__EMBEDDED_DATA__ && window.__EMBEDDED_DATA__[url]) {
    return JSON.parse(JSON.stringify(window.__EMBEDDED_DATA__[url]));
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

    body = html.split("<body>", 1)[1].split("</body>", 1)[0]
    entries = [f'"data/{f}.json": {(DOCS / "data" / f"{f}.json").read_text().strip()}'
               for f in DATA_FILES]
    data_js = "window.__EMBEDDED_DATA__ = {\n" + ",\n".join(entries) + "\n};"

    esc = lambda s: s.replace("</script", "<\\/script")
    out = (
        "<title>Data Center Community Benefits — Dashboard</title>\n"
        f"<style>\n{css}\n</style>\n{body}\n"
        f"<script>\n{esc(data_js)}\n</script>\n"
        f"<script>\n{esc(appjs)}\n</script>\n"
    )
    OUT_DIR.mkdir(exist_ok=True)
    OUT.write_text(out)
    print(f"Wrote {OUT.relative_to(ROOT)}  ({len(out)/1024:.0f} KB)")
    return OUT


def verify() -> int:
    """Headless click-through: assert every tab renders from embedded data."""
    from playwright.sync_api import sync_playwright  # optional dep
    wrapped = ("<!doctype html><html lang=en><head><meta charset=utf-8>"
               "<meta name=viewport content='width=device-width,initial-scale=1'></head>"
               f"<body>{OUT.read_text()}</body></html>")
    tmp = OUT_DIR / "_verify.html"
    tmp.write_text(wrapped)
    errors: list[str] = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_context(viewport={"width": 1280, "height": 1000}).new_page()
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append("PAGEERR: " + str(e)))
        page.goto(f"file://{tmp}", wait_until="networkidle")
        page.wait_for_timeout(700)
        checks = {}
        page.locator("#tab-moratoriums").click()
        page.wait_for_selector("#moratorium-charts .mor-chart", timeout=8000)
        checks["moratorium_rows"] = page.locator("#moratoriums-tbody tr").count()
        page.locator("#tab-ratepayer").click(); page.wait_for_timeout(600)
        checks["ratepayer_cards"] = page.locator("#rp-scorecard .rp-card").count()
        page.locator("#tab-tariffs").click(); page.wait_for_timeout(500)
        checks["tariff_rows"] = page.locator("#tariffs-table tbody tr").count()
        b.close()
    tmp.unlink(missing_ok=True)
    fatal = [e for e in errors if not any(k in e for k in
             ("leaflet", "html2pdf", "cdnjs", "unpkg", "Failed to load resource"))]
    ok = all(v > 0 for v in checks.values()) and not fatal
    print("verify:", checks, "| fatal errors:", fatal or "none", "|", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    build()
    raise SystemExit(verify() if "--verify" in sys.argv else 0)
