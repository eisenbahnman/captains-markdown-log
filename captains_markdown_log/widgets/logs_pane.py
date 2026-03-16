from __future__ import annotations
from datetime import datetime

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Label
from textual.containers import VerticalScroll

from ..constants import CET_TZ
from ..renderer import render_log_line
from ..parser import LogEntry
from .base_editor import BaseEditor


class LogsEditor(BaseEditor):
    """TextArea with auto-bullet and auto-timestamp for log entries."""

    def _handle_enter(self) -> None:
        row, col = self.cursor_location
        line = self.document.get_line(row)
        stripped = line.lstrip()
        indent_len = len(line) - len(stripped)
        if indent_len == 0:
            now = datetime.now(CET_TZ)
            prefix = f"\n- {now.strftime('%H:%M')} "
        else:
            prefix = f"\n{' ' * indent_len}- "
        self.insert(prefix)


class LogsPane(Widget):
    """Left pane: scrollable log entries with edit mode."""

    DEFAULT_CSS = """
    LogsPane {
        layout: vertical;
        height: 100%;
    }
    LogsPane #logs-label {
        height: 1;
        color: $text-muted;
        padding: 0 1;
    }
    LogsPane.active #logs-label {
        color: $warning;
        text-style: bold;
    }
    LogsPane #logs-box {
        border: solid $surface-lighten-2;
        height: 1fr;
    }
    LogsPane.active #logs-box {
        border: solid $warning;
    }
    LogsPane #logs-scroll {
        height: 1fr;
        padding: 0 1;
    }
    LogsPane #logs-editor {
        height: 1fr;
        display: none;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("Logs", id="logs-label")
        with Widget(id="logs-box"):
            with VerticalScroll(id="logs-scroll"):
                yield Static("", id="logs-empty-msg")
            yield LogsEditor("", id="logs-editor", language=None, show_line_numbers=False, tab_behavior="indent")

    def load_logs(self, entries: list[LogEntry], raw_logs: str) -> None:
        """Render log entries in view mode."""
        scroll = self.query_one("#logs-scroll", VerticalScroll)
        for child in list(scroll.query(".log-line")):
            child.remove()
        empty_msg = self.query_one("#logs-empty-msg", Static)
        if not entries:
            empty_msg.update("[dim]No log entries.[/dim]")
            return
        empty_msg.update("")
        for entry in entries:
            rich_text = render_log_line(entry.time, entry.text, entry.indent)
            s = Static(rich_text, classes="log-line")
            scroll.mount(s)

    def show_empty_state(self, date_str: str) -> None:
        """Show empty state when no file exists."""
        scroll = self.query_one("#logs-scroll", VerticalScroll)
        for child in list(scroll.query(".log-line")):
            child.remove()
        msg = self.query_one("#logs-empty-msg", Static)
        msg.update(f"[dim]No log for {date_str}.\nPress [bold]n[/bold] to create it.[/dim]")

    def enter_edit(self, raw_logs: str) -> None:
        """Switch to edit mode."""
        editor = self.query_one("#logs-editor", LogsEditor)
        scroll = self.query_one("#logs-scroll", VerticalScroll)
        editor.load_text(raw_logs)
        scroll.display = False
        editor.display = True
        editor.focus()
        editor.move_cursor(editor.document.end)

    def exit_edit(self) -> str:
        """Switch back to view mode and return edited text."""
        editor = self.query_one("#logs-editor", LogsEditor)
        scroll = self.query_one("#logs-scroll", VerticalScroll)
        text = editor.text
        scroll.display = True
        editor.display = False
        return text

    def is_editing(self) -> bool:
        return self.query_one("#logs-editor", LogsEditor).display
