"""Elapsed path time includes navigation but never changes interaction budgets."""

from tools import interaction_cost as ic


class FakePage:
    def __init__(self, fail_navigation: bool = False) -> None:
        self.events: list[str] = []
        self.fail_navigation = fail_navigation

    def goto(self, url: str, **kwargs: object) -> None:
        self.events.append("navigation")
        if self.fail_navigation:
            raise RuntimeError("Home unavailable")

    def wait_for_selector(self, selector: str, **kwargs: object) -> None:
        self.events.append("wait")

    def locator(self, selector: str) -> "FakePage":
        return self

    @property
    def first(self) -> "FakePage":
        return self

    def click(self) -> None:
        self.events.append("click")

    def fill(self, value: str) -> None:
        self.events.append("fill")

    def select_option(self, value: str) -> None:
        self.events.append("select")


def test_elapsed_time_wraps_cold_navigation_without_changing_counts(monkeypatch) -> None:
    page = FakePage()
    ticks = iter([12.0, 15.125])

    def clock() -> float:
        page.events.append("clock")
        return next(ticks)

    monkeypatch.setattr(ic, "perf_counter", clock)
    monkeypatch.setattr(ic, "_settle", lambda page: None)
    monkeypatch.setattr(ic, "_reveal", lambda *args: None)
    task = ic.Task("mixed", "Reach information", [
        ("tap", "#one"), ("select", "#two", "option"),
        ("type", "#three", "query"), ("see", "#answer")])
    cost = ic.run_task(page, "http://local.test", task, expanded=False)
    assert page.events[:2] == ["clock", "navigation"]
    assert page.events[-1] == "clock"
    assert cost.elapsed_seconds == 3.125
    assert (cost.taps, cost.types, cost.total) == (4, 1, 5)
    assert cost.as_dict()["elapsed_seconds"] == 3.125
    assert cost.error is None


def test_failed_home_navigation_returns_elapsed_error_instead_of_aborting(monkeypatch) -> None:
    ticks = iter([2.0, 4.5])
    monkeypatch.setattr(ic, "perf_counter", ticks.__next__)
    cost = ic.run_task(FakePage(fail_navigation=True), "http://local.test",
                       ic.Task("unavailable", "Reach information", []), expanded=False)
    assert cost.elapsed_seconds == 2.5
    assert cost.error == "RuntimeError: Home unavailable"
    assert cost.total == 0


def test_history_keeps_existing_totals_and_adds_both_context_times() -> None:
    result = {"date": "2026-11-04", "devices": {"mobile": {"one": {
        "default": {"total": 4, "elapsed_seconds": 2.5},
        "expanded": {"total": 6, "elapsed_seconds": 3.75}}}}}
    history = ic.summary_line(result)
    assert history["mobile"] == {"one": 4}
    assert history["elapsed_seconds"]["mobile"]["one"] == {"default": 2.5, "expanded": 3.75}
