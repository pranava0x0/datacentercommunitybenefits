"""Interaction-cost UAT: how many taps, swipes and keystrokes a reader needs
to reach a specific piece of information, per device.

Each task starts cold on Home (`/`), the way a reader arrives, and follows the
shortest realistic path a reader would take. The harness counts:

  taps    every click/tap, including tapping a collapsed <details> open
  swipes  vertical scrolls, in units of SWIPE_FRACTION of the scrolling area
  hswipes horizontal scrolls (the tab bar on a phone)
  types   typing a query into a search box (one per query; tapping into
          the box first is counted as a tap)

Two contexts per device:

  default   the page as shipped (collapsed accordions stay collapsed until
            the path needs them, which costs a tap each)
  expanded  every <details> forced open before each step, i.e. a reader who
            already opened everything. No expand taps, but longer pages.

Devices are measured separately, mobile first, because a path that is one
screen on a desktop can be five swipes on a phone.

    python3 tools/interaction_cost.py              # all devices, writes uat/
    python3 tools/interaction_cost.py --device mobile --task moratorium_raleigh
    python3 tools/interaction_cost.py --no-write   # print only

Results: uat/interaction_costs.json (latest run, committed) and one summary
line appended to uat/interaction_costs_history.jsonl per run. Budgets live in
uat/interaction_budgets.json and are enforced by
tests/e2e/test_interaction_cost.py.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import logging
import math
import socketserver
import threading
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
UAT = ROOT / "uat"
RESULTS = UAT / "interaction_costs.json"
HISTORY = UAT / "interaction_costs_history.jsonl"
BUDGETS = UAT / "interaction_budgets.json"

log = logging.getLogger("interaction_cost")

# One swipe or wheel flick moves about three quarters of the visible area.
SWIPE_FRACTION = 0.75

DEVICES: dict[str, dict[str, Any]] = {
    "mobile": {
        "viewport": {"width": 390, "height": 844},
        "device_scale_factor": 3,
        "is_mobile": True,
        "has_touch": True,
    },
    "tablet": {
        "viewport": {"width": 820, "height": 1180},
        "device_scale_factor": 2,
        "is_mobile": True,
        "has_touch": True,
    },
    "desktop": {"viewport": {"width": 1366, "height": 900}},
}
CONTEXTS = ("default", "expanded")


# ---------------------------------------------------------------------------
# Tasks. Steps: ("tap", selector) | ("type", selector, text) | ("see", selector)
# The final step is always a "see": the information the reader came for.
# Selectors use :first-of-type / attribute matches so a data refresh that adds
# records does not change which element is measured, only where it sits.
# ---------------------------------------------------------------------------
@dataclass
class Task:
    key: str
    question: str
    steps: list[tuple]


TASKS: list[Task] = [
    Task("home_latest", "What changed most recently?",
         [("see", "#home-latest-list .feed-item")]),
    Task("home_coming_up", "What is the next scheduled hearing or deadline?",
         [("see", "#whats-next-list .feed-item")]),
    Task("home_sections", "Where do I go to explore a topic?",
         [("see", "#home-cards .home-card:last-child")]),
    Task("latest_item_record", "Open the newest moratorium in the Latest feed.",
         [("tap", '#home-latest-list .feed-btn[data-kind="moratorium"]'),
          ("see", "#moratorium-modal:not([hidden]) #md-status")]),
    Task("pledge_signatory", "Did Entergy sign the ratepayer pledge?",
         [("tap", "#tab-ratepayer"),
          ("type", "#rp-roster-q", "entergy"),
          ("see", "#rp-roster > li")]),
    Task("pledge_site_score", "How does an assessed site score on the five commitments?",
         [("tap", "#tab-ratepayer"),
          ("see", "#subpane-rp-sites-assessed .rp-card")]),
    Task("state_panel", "What is happening in Virginia?",
         [("tap", "#tab-ratepayer"),
          ("tap", '.pledge-state-cell[data-state-code="VA"]'),
          ("see", "#sd-body > *")]),
    Task("policy_cba", "Find a signed community benefits agreement.",
         [("tap", "#tab-policies"),
          ("tap", "#subtab-pol-directory"),
          ("tap", "#policy-cbf-filter"),
          ("see", "#policies-tbody tr")]),
    Task("agreement_terms", "What did the most complete signed agreement commit to?",
         [("tap", "#tab-agreements"),
          ("see", "#cba-strongest .cba-card .cba-terms")]),
    Task("moratorium_raleigh", "What did Raleigh pass, and when?",
         [("tap", "#tab-moratoriums"),
          ("tap", '#moratoriums-tbody tr[data-id="raleigh-nc-2026-09"]'),
          ("see", "#md-status")]),
    Task("ratecase_milestone", "When is the next step in a pending rate case?",
         [("tap", "#tab-tariffs"),
          ("see", "#rate-cases-list .rc-item .rc-next")]),
    Task("company_water", "What has Google said about water?",
         [("tap", "#tab-comparison"),
          ("tap", "#subtab-co-commitments"),
          ("tap", '#matrix-body td[data-company="google"][data-theme="water"]'),
          ("see", "#theme-quotes-list > li")]),
    Task("contested_timeline", "What hearings or votes are coming at a contested site?",
         [("tap", "#tab-explorer"),
          ("tap", "#subtab-sites-contested"),
          ("see", "#contested-list .contested-card .timeline .tl-item")]),
    Task("site_comment", "What did residents say about a specific site?",
         [("tap", "#tab-explorer"),
          ("type", "#f-q", "memphis"),
          ("tap", '#project-list .project-card[data-project-id="xai-memphis-tn"]'),
          ("tap", "#dtab-responses"),
          ("see", "#d-responses .response-card")]),
]


# ---------------------------------------------------------------------------
# Geometry, evaluated in the page: how far is `el` from being in view?
# ---------------------------------------------------------------------------
_MEASURE_JS = """
(sel) => {
  const el = document.querySelector(sel);
  if (!el) return {missing: true};
  // Closed <details> ancestors the reader must open first, outermost first.
  const closed = [];
  for (let n = el.parentElement; n; n = n.parentElement) {
    if (n.tagName === 'DETAILS' && !n.open && !(el.tagName === 'SUMMARY' && el.parentElement === n)) closed.unshift(n);
  }
  if (closed.length) {
    const d = closed[0];
    d.setAttribute('data-ic-closed', '1');
    return {closed: true, summary: 'details[data-ic-closed="1"] > summary'};
  }
  // Nearest scrolling ancestor on each axis; the document when none.
  const scroller = (axis) => {
    for (let n = el.parentElement; n && n !== document.body; n = n.parentElement) {
      const cs = getComputedStyle(n);
      const ov = axis === 'y' ? cs.overflowY : cs.overflowX;
      const big = axis === 'y' ? n.scrollHeight > n.clientHeight + 1 : n.scrollWidth > n.clientWidth + 1;
      if (big && (ov === 'auto' || ov === 'scroll')) return n;
    }
    return null;
  };
  const r = el.getBoundingClientRect();
  if (r.width === 0 && r.height === 0) return {invisible: true};
  const vh = window.innerHeight, vw = window.innerWidth;
  // Sticky chrome at the top eats part of the visible area.
  let top = 0;
  const sticky = document.querySelector('.tabbar-sticky');
  if (sticky) { const sr = sticky.getBoundingClientRect(); if (sr.top <= 0 && sr.bottom > 0) top = sr.bottom; }
  const ys = scroller('y');
  let lo = top, hi = vh;
  if (ys) { const b = ys.getBoundingClientRect(); lo = Math.max(lo, b.top); hi = Math.min(hi, b.bottom); }
  // A scroller pushed mostly off-screen is not the reader's viewport.
  if (hi - lo < 120) { lo = top; hi = vh; }
  const span = hi - lo;
  // In view = its first line is inside the visible band.
  const line = Math.min(r.height, 24);
  let dy = 0;
  if (r.top < lo) dy = r.top - lo - 8;
  else if (r.top + line > hi) dy = r.top - (lo + span * 0.25);
  const xs = scroller('x');
  let dx = 0, wspan = vw;
  if (xs) {
    const b = xs.getBoundingClientRect(); wspan = b.width;
    // Reachable once its leading edge is on screen: a wide table row whose
    // tail overflows is still tappable without a side-swipe.
    const lead = Math.min(r.width, 40);
    if (r.left < b.left) dx = r.left - b.left - 8;
    else if (r.left + lead > b.right) dx = r.left + lead - b.right + 8;
  }
  return {dy, span, dx, wspan, yScroller: !!ys};
}
"""

# Section accordions only. Per-card disclosures (a scorecard card's evidence)
# stay closed: no reader opens 39 of them, and forcing them open measures a
# page nobody sees.
_FORCE_OPEN_JS = "() => document.querySelectorAll('details.acc').forEach(d => { d.open = true; })"


@dataclass
class Cost:
    taps: int = 0
    swipes: int = 0
    hswipes: int = 0
    types: int = 0
    path: list[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def total(self) -> int:
        return self.taps + self.swipes + self.hswipes + self.types

    def as_dict(self) -> dict[str, Any]:
        d = {"taps": self.taps, "swipes": self.swipes, "hswipes": self.hswipes,
             "types": self.types, "total": self.total, "path": self.path}
        if self.error:
            d["error"] = self.error
        return d


def _settle(page) -> None:
    # Lazy payloads land after a tap; measuring before they render undercounts
    # (or wildly overcounts) the scroll that follows.
    try:
        page.wait_for_load_state("networkidle", timeout=4000)
    except Exception:
        log.warning("network did not go idle; measuring anyway")
    page.wait_for_timeout(250)


def _reveal(page, sel: str, cost: Cost, expanded: bool) -> None:
    """Bring `sel` into view the way a reader would, counting the effort."""
    for _ in range(6):  # nested accordions: at most a few levels
        if expanded:
            page.evaluate(_FORCE_OPEN_JS)
        m = page.evaluate(_MEASURE_JS, sel)
        if m.get("missing"):
            page.wait_for_selector(sel, state="attached", timeout=8000)
            continue
        if m.get("closed"):
            summary = m["summary"]
            _reveal(page, summary, cost, expanded)
            page.click(summary)
            page.evaluate("() => document.querySelectorAll('[data-ic-closed]').forEach(d => d.removeAttribute('data-ic-closed'))")
            cost.taps += 1
            cost.path.append("tap: expand section")
            _settle(page)
            continue
        if m.get("invisible"):
            raise RuntimeError(f"{sel} is attached but not rendered")
        n = math.ceil(abs(m["dy"]) / (m["span"] * SWIPE_FRACTION)) if m["dy"] else 0
        h = math.ceil(abs(m["dx"]) / (m["wspan"] * SWIPE_FRACTION)) if m["dx"] else 0
        if n:
            cost.swipes += n
            cost.path.append(f"swipe x{n}")
        if h:
            cost.hswipes += h
            cost.path.append(f"side-swipe x{h}")
        page.locator(sel).first.scroll_into_view_if_needed()
        if n or h:
            # Land it where the reader's thumb would: comfortably below the bar.
            page.evaluate("(s) => document.querySelector(s).scrollIntoView({block: 'center', inline: 'nearest'})", sel)
        _settle(page)
        return
    raise RuntimeError(f"could not reveal {sel}")


def run_task(page, base: str, task: Task, expanded: bool) -> Cost:
    cost = Cost()
    page.goto(base + "/", wait_until="load")
    page.wait_for_selector("#home-latest-list .feed-item", state="attached", timeout=10000)
    _settle(page)
    try:
        for step in task.steps:
            kind, sel = step[0], step[1]
            page.wait_for_selector(sel, state="attached", timeout=10000)
            _reveal(page, sel, cost, expanded)
            if kind == "tap":
                page.locator(sel).first.click()
                cost.taps += 1
                cost.path.append(f"tap: {sel}")
                _settle(page)
            elif kind == "type":
                page.locator(sel).first.click()
                page.locator(sel).first.fill(step[2])
                cost.taps += 1
                cost.types += 1
                cost.path.append(f"type: {step[2]!r}")
                _settle(page)
            elif kind == "see":
                cost.path.append(f"see: {sel}")
    except Exception as exc:  # one broken task must not end the run
        cost.error = f"{type(exc).__name__}: {str(exc).splitlines()[0][:200]}"
        log.error("%s (%s): %s", task.key, "expanded" if expanded else "default", cost.error)
    return cost


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args: Any) -> None:
        pass


def serve_docs() -> tuple[socketserver.TCPServer, str]:
    handler = functools.partial(_QuietHandler, directory=str(DOCS))
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def measure(devices: list[str], tasks: list[Task], base: Optional[str] = None) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    srv = None
    if base is None:
        srv, base = serve_docs()
    out: dict[str, Any] = {"date": date.today().isoformat(),
                           "swipe_fraction": SWIPE_FRACTION, "devices": {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for dev in devices:
                ctx = browser.new_context(**DEVICES[dev])
                # Map tiles are irrelevant to reach and slow the run.
                ctx.route("**/*arcgisonline*/**", lambda r: r.fulfill(status=204))
                page = ctx.new_page()
                res: dict[str, Any] = {}
                for t in tasks:
                    res[t.key] = {"question": t.question}
                    for c in CONTEXTS:
                        cost = run_task(page, base, t, expanded=(c == "expanded"))
                        res[t.key][c] = cost.as_dict()
                        log.info("%-8s %-20s %-8s total=%d %s", dev, t.key, c, cost.total,
                                 cost.error or "")
                out["devices"][dev] = res
                ctx.close()
            browser.close()
    finally:
        if srv:
            srv.shutdown()
    return out


def summary_line(result: dict[str, Any]) -> dict[str, Any]:
    line: dict[str, Any] = {"date": result["date"]}
    for dev, tasks in result["devices"].items():
        line[dev] = {k: v["default"]["total"] for k, v in tasks.items()}
    return line


def print_table(result: dict[str, Any]) -> None:
    for dev, tasks in result["devices"].items():
        print(f"\n{dev}: task / default (taps+swipes+side+type) / expanded")
        for k, v in tasks.items():
            d, e = v["default"], v["expanded"]
            flag = "  ERROR " + d.get("error", e.get("error", "")) if ("error" in d or "error" in e) else ""
            print(f"  {k:<20} {d['total']:>3} ({d['taps']}+{d['swipes']}+{d['hswipes']}+{d['types']})"
                  f"   {e['total']:>3} ({e['taps']}+{e['swipes']}+{e['hswipes']}+{e['types']}){flag}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--device", choices=list(DEVICES), action="append")
    ap.add_argument("--task", action="append", help="task key; repeatable")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--base", help="measure an already-running server instead of serving docs/")
    ap.add_argument("--json-out", type=Path, help="write the result here (tests use this)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    devices = args.device or list(DEVICES)  # mobile first
    tasks = [t for t in TASKS if not args.task or t.key in args.task]
    result = measure(devices, tasks, base=args.base)
    if args.json_out:
        args.json_out.write_text(json.dumps(result), encoding="utf-8")
        return
    print_table(result)
    if args.no_write or args.task or args.device:
        return
    UAT.mkdir(exist_ok=True)
    RESULTS.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(json.dumps(summary_line(result), ensure_ascii=False) + "\n")
    log.info("wrote %s and appended %s", RESULTS.relative_to(ROOT), HISTORY.relative_to(ROOT))


if __name__ == "__main__":
    main()
