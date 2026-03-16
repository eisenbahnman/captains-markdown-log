"""Captain's Log — TUI daily journal and task manager."""
from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from pathlib import Path

# SSH doesn't forward COLORTERM — force truecolor so Rich renders hex colors faithfully
if not os.environ.get("COLORTERM"):
    os.environ["COLORTERM"] = "truecolor"

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Footer

from .config import load_config, Config
from .storage import (
    read_file,
    write_file,
    create_daily_file,
    file_exists,
    get_prev_existing,
    get_next_existing,
)
from .parser import parse_daily, reconstruct_file, DailyContent
from .widgets.nav_bar import NavBar
from .widgets.logs_pane import LogsPane
from .widgets.todos_pane import TodosPane, toggle_todo_in_raw
from .renderer import apply_theme


class CaptainsLogApp(App):
    """The main captains-markdown-log application."""

    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("h", "prev_day", "prev day", show=True),
        Binding("left", "prev_day", "prev day", show=False),
        Binding("l", "next_day", "next day", show=True),
        Binding("right", "next_day", "next day", show=False),
        Binding("[", "prev_existing", "◀ nearest", show=True),
        Binding("]", "next_existing", "nearest ▶", show=True),
        Binding("tab", "cycle_pane", "switch", show=True, priority=True),
        Binding("e", "enter_edit", "edit", show=True),
        Binding("escape", "exit_edit", "done", show=False),
        Binding("f", "toggle_fullscreen", "fullscreen", show=True),
        Binding("n", "create_daily", "new", show=True),
        Binding("up", "todo_up", "↑", show=False),
        Binding("k", "todo_up", "↑", show=False),
        Binding("down", "todo_down", "↓", show=False),
        Binding("j", "todo_down", "↓", show=False),
        Binding("space", "toggle_todo", "toggle", show=False),
        Binding("plus", "expand_logs", "logs +", show=False),
        Binding("equals", "expand_logs", "logs +", show=False),
        Binding("minus", "shrink_logs", "logs -", show=False),
        Binding("t", "jump_today", "today", show=True),
        Binding("q", "quit", "quit", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._config: Config = load_config()
        self._current_date: date = date.today()
        self._daily_content: DailyContent | None = None
        self._raw_logs: str = ""
        self._raw_todos: str = ""
        self._active_pane: str = "logs"  # "logs" or "todos"
        self._editing: bool = False
        self._logs_width_pct: int = 50
        self._fullscreen_pane: str | None = None  # None, "logs", or "todos"

    def compose(self) -> ComposeResult:
        yield NavBar(id="nav-bar")
        with Horizontal(id="main-area"):
            yield LogsPane(id="logs-pane")
            yield TodosPane(id="todos-pane")
        yield Footer()

    def on_mount(self) -> None:
        self.theme = "tokyo-night"
        self._sync_renderer_theme()
        self._load_date(self._current_date)
        self._set_active_pane("logs")
        # Heartbeat so expired toasts are visually dismissed without requiring input
        self.set_interval(0.5, lambda: None)

    def watch_theme(self, old_theme: str, new_theme: str) -> None:
        self._sync_renderer_theme()
        if self._daily_content is not None:
            self._refresh_panes()

    def _sync_renderer_theme(self) -> None:
        t = self.current_theme
        apply_theme(
            warning=t.warning or "#E0AF68",
            success=t.success or "#9ECE6A",
            error=t.error or "#F7768E",
            secondary=t.secondary or "#7AA2F7",
            accent=t.accent or "#FF9E64",
            background=t.background or "#1a1b26",
        )

    # ── Data loading ────────────────────────────────────────────────────────

    def _load_date(self, d: date) -> None:
        self._current_date = d
        nav = self.query_one("#nav-bar", NavBar)
        nav.set_date(d)

        content = read_file(self._config.logs_dir, d)
        if content is None:
            self._daily_content = None
            self._raw_logs = ""
            self._raw_todos = ""
            date_str = d.isoformat()
            self.query_one("#logs-pane", LogsPane).show_empty_state(date_str)
            self.query_one("#todos-pane", TodosPane).show_empty_state(date_str)
        else:
            self._daily_content = parse_daily(content)
            self._raw_logs = self._daily_content.raw_logs
            self._raw_todos = self._daily_content.raw_todos
            self._refresh_panes()

    def _refresh_panes(self) -> None:
        if self._daily_content is None:
            return
        self.query_one("#logs-pane", LogsPane).load_logs(
            self._daily_content.logs, self._raw_logs
        )
        self.query_one("#todos-pane", TodosPane).load_todos(
            self._daily_content.todos, self._raw_todos
        )

    def _save_and_reload(self) -> None:
        content = reconstruct_file(self._raw_logs, self._raw_todos)
        write_file(self._config.logs_dir, self._current_date, content)
        self._daily_content = parse_daily(content)
        self._refresh_panes()

    # ── Pane focus management ────────────────────────────────────────────────

    def _set_active_pane(self, pane: str) -> None:
        self._active_pane = pane
        logs_pane = self.query_one("#logs-pane", LogsPane)
        todos_pane = self.query_one("#todos-pane", TodosPane)
        if pane == "logs":
            logs_pane.add_class("active")
            todos_pane.remove_class("active")
        else:
            todos_pane.add_class("active")
            logs_pane.remove_class("active")

    def _apply_widths(self) -> None:
        logs = self.query_one("#logs-pane", LogsPane)
        todos = self.query_one("#todos-pane", TodosPane)
        if self._fullscreen_pane == "logs":
            logs.styles.width = "100%"
            todos.display = False
        elif self._fullscreen_pane == "todos":
            todos.styles.width = "100%"
            logs.display = False
        else:
            todos.display = True
            logs.display = True
            logs.styles.width = f"{self._logs_width_pct}%"
            todos.styles.width = f"{100 - self._logs_width_pct}%"

    # ── Actions ──────────────────────────────────────────────────────────────

    def action_prev_day(self) -> None:
        if self._editing:
            return
        self._load_date(self._current_date - timedelta(days=1))

    def action_next_day(self) -> None:
        if self._editing:
            return
        self._load_date(self._current_date + timedelta(days=1))

    def action_prev_existing(self) -> None:
        if self._editing:
            return
        d = get_prev_existing(self._config.logs_dir, self._current_date)
        if d:
            self._load_date(d)

    def action_next_existing(self) -> None:
        if self._editing:
            return
        d = get_next_existing(self._config.logs_dir, self._current_date)
        if d:
            self._load_date(d)

    def action_jump_today(self) -> None:
        if self._editing:
            return
        self._load_date(date.today())

    def action_cycle_pane(self) -> None:
        if self._editing:
            return
        new_pane = "todos" if self._active_pane == "logs" else "logs"
        self._set_active_pane(new_pane)

    def action_enter_edit(self) -> None:
        if self._editing:
            return
        if self._daily_content is None:
            return
        self._editing = True
        if self._active_pane == "logs":
            self.query_one("#logs-pane", LogsPane).enter_edit(self._raw_logs)
        else:
            self.query_one("#todos-pane", TodosPane).enter_edit(self._raw_todos)

    def action_exit_edit(self) -> None:
        if not self._editing:
            return
        self._editing = False
        if self._active_pane == "logs":
            logs_pane = self.query_one("#logs-pane", LogsPane)
            if logs_pane.is_editing():
                self._raw_logs = logs_pane.exit_edit()
        else:
            todos_pane = self.query_one("#todos-pane", TodosPane)
            if todos_pane.is_editing():
                self._raw_todos = todos_pane.exit_edit()
        self._save_and_reload()
        # Restore focus to app so keybindings work
        self.set_focus(None)

    def action_toggle_fullscreen(self) -> None:
        if self._editing:
            return
        if self._fullscreen_pane is None:
            self._fullscreen_pane = self._active_pane
        else:
            self._fullscreen_pane = None
        self._apply_widths()

    def action_create_daily(self) -> None:
        if self._editing:
            return
        if not file_exists(self._config.logs_dir, self._current_date):
            create_daily_file(self._config.logs_dir, self._current_date)
            self._load_date(self._current_date)

    def action_todo_up(self) -> None:
        if self._editing:
            return
        if self._active_pane == "todos":
            self.query_one("#todos-pane", TodosPane).move_cursor_up()
        elif self._active_pane == "logs":
            self.query_one("#logs-pane", LogsPane).scroll_up()

    def action_todo_down(self) -> None:
        if self._editing:
            return
        if self._active_pane == "todos":
            self.query_one("#todos-pane", TodosPane).move_cursor_down()
        elif self._active_pane == "logs":
            self.query_one("#logs-pane", LogsPane).scroll_down()

    def action_toggle_todo(self) -> None:
        if self._editing or self._active_pane != "todos":
            return
        if self._daily_content is None:
            return
        todos_pane = self.query_one("#todos-pane", TodosPane)
        idx = todos_pane.get_cursor_index()
        if 0 <= idx < len(self._daily_content.todos):
            current = self._daily_content.todos[idx].checked
            self._raw_todos = toggle_todo_in_raw(self._raw_todos, idx, not current)
            self._save_and_reload()

    def action_expand_logs(self) -> None:
        if self._fullscreen_pane:
            return
        self._logs_width_pct = min(80, self._logs_width_pct + 5)
        self._apply_widths()

    def action_shrink_logs(self) -> None:
        if self._fullscreen_pane:
            return
        self._logs_width_pct = max(20, self._logs_width_pct - 5)
        self._apply_widths()


    def deliver_screenshot(self, filename=None, path=None, time_format=None):
        """Save an SVG screenshot directly to disk (bypasses browser delivery)."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = Path(path) if path else Path.home()
        save_path.mkdir(parents=True, exist_ok=True)
        out = save_path / (filename or f"cml-{ts}.svg")
        try:
            out.write_text(self.export_screenshot(), encoding="utf-8")
            self.notify(f"Screenshot: {out}", timeout=4)
        except Exception as exc:
            self.notify(f"Screenshot failed: {exc}", severity="error", timeout=4)


def main() -> None:
    app = CaptainsLogApp()
    app.run()


if __name__ == "__main__":
    main()
