"""Interaction-cost budgets, per device (tools/interaction_cost.py).

Each task's default-context total (taps + swipes + side-swipes + typed
queries, starting cold on Home) must stay within uat/interaction_budgets.json.
Devices are budgeted separately: a phone path is legitimately longer than a
desktop one, and a regression on one must not hide behind headroom on another.

A failure means a change made some piece of information harder to reach.
Fix the path, or, when the cost is a deliberate trade, re-run the tool,
explain the trade in uat.md, and update the budget in the same commit.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import interaction_cost as ic  # noqa: E402

BUDGETS = json.loads((ROOT / "uat" / "interaction_budgets.json").read_text())


def test_every_task_has_a_budget_on_every_device() -> None:
    for dev in ic.DEVICES:
        assert set(BUDGETS[dev]) == {t.key for t in ic.TASKS}, dev


@pytest.mark.parametrize("device", list(ic.DEVICES))
def test_tasks_stay_within_budget(device: str, base_url: str, tmp_path: Path) -> None:
    # A subprocess: the harness drives its own browser, and Playwright's sync
    # API refuses to start inside the worker that already runs pytest-playwright.
    out = tmp_path / "cost.json"
    subprocess.run(
        [sys.executable, str(ROOT / "tools" / "interaction_cost.py"),
         "--device", device, "--base", base_url, "--json-out", str(out)],
        check=True, capture_output=True, timeout=600,
    )
    result = json.loads(out.read_text())["devices"][device]
    over = []
    for key, r in result.items():
        d = r["default"]
        assert "error" not in d, f"{device}/{key}: {d['error']}"
        if d["total"] > BUDGETS[device][key]:
            over.append(f"{key}: {d['total']} > {BUDGETS[device][key]} ({' > '.join(d['path'])})")
    assert not over, f"{device} over budget:\n" + "\n".join(over)
