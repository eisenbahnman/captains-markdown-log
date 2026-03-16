from __future__ import annotations
from datetime import date, datetime

from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Label

from ..constants import CET_TZ


class NavBar(Widget):
    """Top bar: date + CET/CEST clock."""

    DEFAULT_CSS = """
    NavBar {
        height: 1;
        padding: 0 1;
        layout: horizontal;
        align: left middle;
        background: $panel;
    }
    NavBar Label { width: auto; }
    #nav-arrows { color: $text-muted; margin-right: 1; }
    #nav-date { color: $text; text-style: bold; }
    #nav-time { color: $text-muted; margin-left: 3; }
    """

    def compose(self) -> ComposeResult:
        yield Label("←  →", id="nav-arrows")
        yield Label("", id="nav-date")
        yield Label("", id="nav-time")

    def on_mount(self) -> None:
        self._refresh_time()
        self.set_interval(1.0, self._refresh_time)

    def set_date(self, d: date) -> None:
        self.query_one("#nav-date", Label).update(d.strftime("%Y-%m-%d  %A"))

    def _refresh_time(self) -> None:
        now = datetime.now(CET_TZ)
        tz_abbr = now.tzname() or "CET"
        self.query_one("#nav-time", Label).update(
            f"{now.strftime('%H:%M:%S')} {tz_abbr}"
        )
