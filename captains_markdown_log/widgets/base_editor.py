"""Base TextArea with shared indent/dedent logic."""
from __future__ import annotations

from textual.widgets import TextArea
from textual import events


class BaseEditor(TextArea):
    """TextArea subclass with tab indent/dedent. Subclasses override _handle_enter."""

    def _on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            event.prevent_default()
            event.stop()
            self.app.action_exit_edit()
        elif event.key == "enter":
            event.prevent_default()
            self._handle_enter()
        elif event.key == "tab":
            event.prevent_default()
            event.stop()
            self._indent_current_line()
        elif event.key == "shift+tab":
            event.prevent_default()
            event.stop()
            self._dedent_current_line()
        else:
            super()._on_key(event)

    def _handle_enter(self) -> None:
        raise NotImplementedError

    def _indent_current_line(self) -> None:
        row, col = self.cursor_location
        line = self.document.get_line(row)
        self.replace("    " + line, (row, 0), (row, len(line)))
        self.move_cursor((row, col + 4))

    def _dedent_current_line(self) -> None:
        row, col = self.cursor_location
        line = self.document.get_line(row)
        if line.startswith("    "):
            self.replace(line[4:], (row, 0), (row, len(line)))
            self.move_cursor((row, max(0, col - 4)))
        elif line.startswith("  "):
            self.replace(line[2:], (row, 0), (row, len(line)))
            self.move_cursor((row, max(0, col - 2)))
