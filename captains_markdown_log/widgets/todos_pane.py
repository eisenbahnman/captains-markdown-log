from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Label
from textual.containers import VerticalScroll

from ..renderer import render_todo_line
from ..parser import TodoItem, _TODO_RE
from .base_editor import BaseEditor


class TodosEditor(BaseEditor):
    """TextArea with auto-bullet for todo entries."""

    def _handle_enter(self) -> None:
        row, col = self.cursor_location
        line = self.document.get_line(row)
        stripped = line.lstrip()
        leading_ws = line[: len(line) - len(stripped)]
        prefix = f"\n{leading_ws}- [ ] "
        self.insert(prefix)


def toggle_todo_in_raw(raw: str, index: int, check: bool) -> str:
    """Toggle the Nth todo item (0-indexed) in raw section text."""
    lines = raw.splitlines(keepends=True)
    count = 0
    result = []
    for line in lines:
        m = _TODO_RE.match(line)
        if m and count == index:
            new_check = "x" if check else " "
            new_line = f"{m.group(1)}- [{new_check}] {m.group(3)}"
            if line.endswith("\n"):
                new_line += "\n"
            result.append(new_line)
            count += 1
            continue
        if m:
            count += 1
        result.append(line)
    return "".join(result)


class TodosPane(Widget):
    """Right pane: scrollable todo list with navigation, toggle, and edit modes."""

    DEFAULT_CSS = """
    TodosPane {
        layout: vertical;
        height: 100%;
    }
    TodosPane #todos-label {
        height: 1;
        color: $text-muted;
        padding: 0 1;
    }
    TodosPane.active #todos-label {
        color: $warning;
        text-style: bold;
    }
    TodosPane #todos-box {
        border: solid $surface-lighten-2;
        height: 1fr;
    }
    TodosPane.active #todos-box {
        border: solid $warning;
    }
    TodosPane #todos-scroll {
        height: 1fr;
        padding: 0 1;
    }
    TodosPane #todos-editor {
        height: 1fr;
        display: none;
    }
    .todo-item-widget {
        padding: 0;
    }
    .todo-item-widget.todo-cursor {
        background: $surface;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cursor_index: int = 0
        self._todo_count: int = 0

    def compose(self) -> ComposeResult:
        yield Label("Todos", id="todos-label")
        with Widget(id="todos-box"):
            with VerticalScroll(id="todos-scroll"):
                yield Static("", id="todos-empty-msg")
            yield TodosEditor("", id="todos-editor", language=None, show_line_numbers=False, tab_behavior="indent")

    def load_todos(self, items: list[TodoItem], raw_todos: str) -> None:
        """Render todo items in view mode."""
        self._todo_count = len(items)
        self._cursor_index = min(self._cursor_index, max(0, len(items) - 1))
        scroll = self.query_one("#todos-scroll", VerticalScroll)
        for child in list(scroll.query(".todo-item-widget")):
            child.remove()
        empty_msg = self.query_one("#todos-empty-msg", Static)
        if not items:
            empty_msg.update("[dim]No todos.[/dim]")
            return
        empty_msg.update("")
        for i, item in enumerate(items):
            rich_text = render_todo_line(item.checked, item.text, item.indent)
            w = Static(rich_text, classes="todo-item-widget")
            if i == self._cursor_index:
                w.add_class("todo-cursor")
            scroll.mount(w)

    def show_empty_state(self, date_str: str) -> None:
        scroll = self.query_one("#todos-scroll", VerticalScroll)
        for child in list(scroll.query(".todo-item-widget")):
            child.remove()
        msg = self.query_one("#todos-empty-msg", Static)
        msg.update(f"[dim]No log for {date_str}.\nPress [bold]n[/bold] to create it.[/dim]")

    def move_cursor_up(self) -> None:
        if self._todo_count == 0:
            return
        old_idx = self._cursor_index
        self._cursor_index = max(0, self._cursor_index - 1)
        self._update_cursor(old_idx, self._cursor_index)

    def move_cursor_down(self) -> None:
        if self._todo_count == 0:
            return
        old_idx = self._cursor_index
        self._cursor_index = min(self._todo_count - 1, self._cursor_index + 1)
        self._update_cursor(old_idx, self._cursor_index)

    def _update_cursor(self, old_idx: int, new_idx: int) -> None:
        items = list(self.query(".todo-item-widget"))
        if 0 <= old_idx < len(items):
            items[old_idx].remove_class("todo-cursor")
        if 0 <= new_idx < len(items):
            items[new_idx].add_class("todo-cursor")
            items[new_idx].scroll_visible()

    def get_cursor_index(self) -> int:
        return self._cursor_index

    def enter_edit(self, raw_todos: str) -> None:
        editor = self.query_one("#todos-editor", TodosEditor)
        scroll = self.query_one("#todos-scroll", VerticalScroll)
        editor.load_text(raw_todos)
        scroll.display = False
        editor.display = True
        editor.focus()
        editor.move_cursor(editor.document.end)

    def exit_edit(self) -> str:
        editor = self.query_one("#todos-editor", TodosEditor)
        scroll = self.query_one("#todos-scroll", VerticalScroll)
        text = editor.text
        scroll.display = True
        editor.display = False
        return text

    def is_editing(self) -> bool:
        return self.query_one("#todos-editor", TodosEditor).display
