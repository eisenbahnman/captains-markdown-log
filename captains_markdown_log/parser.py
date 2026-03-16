"""Parse YYYY-MM-DD.md files into structured data."""
from __future__ import annotations
import re
from dataclasses import dataclass, field


# Matches UL bullet: optional whitespace (spaces/tabs), then - + or *, then space
_BULLET_RE = re.compile(r"^([ \t]*)[-+*] (.*)$")
# Matches todo bullet: optional whitespace (spaces/tabs), then - [ ] or - [x], then space
_TODO_RE = re.compile(r"^([ \t]*)[-+*] \[( |x|X)\] (.*)$", re.IGNORECASE)
# Matches timestamp at start of text: HH:MM
_TIME_RE = re.compile(r"^(\d{1,2}:\d{2}) (.*)$")
# Matches heading
_HEADING_RE = re.compile(r"^#{1,6} (.+)$")


@dataclass
class LogEntry:
    time: str | None  # "HH:MM" or None for indented/sub entries
    text: str         # Raw text including any inline markdown
    indent: int       # 0 = top level


@dataclass
class TodoItem:
    checked: bool
    text: str         # Raw text including any inline markdown
    indent: int       # 0 = top level


@dataclass
class DailyContent:
    logs: list[LogEntry] = field(default_factory=list)
    todos: list[TodoItem] = field(default_factory=list)
    raw_logs: str = ""   # Raw lines under ## Logs (excluding heading)
    raw_todos: str = ""  # Raw lines under ## Todos (excluding heading)


def _detect_indent_unit(lines: list[str]) -> int:
    """Detect the minimum indent unit (in spaces) used in lines.

    Only examines space-based indentation; tab indentation is handled
    separately in _indent_level().
    """
    indents = set()
    for line in lines:
        m = re.match(r"^( +)", line)
        if m:
            indents.add(len(m.group(1)))
    if not indents:
        return 2
    min_indent = min(indents)
    return max(min_indent, 2)


def _indent_level(whitespace: str, unit: int) -> int:
    """Calculate indent level from leading whitespace.

    Each tab counts as one indent level.  For spaces the detected
    *unit* (2, 3 or 4) is used to derive the level.
    """
    if "\t" in whitespace:
        return whitespace.count("\t")
    return len(whitespace) // unit


def _extract_section(content: str, heading: str) -> tuple[str, list[str]]:
    """Extract raw text and lines under a given ## heading.

    Stops at the next ## heading or end of file.
    Returns (raw_text, lines).
    """
    lines = content.splitlines()
    in_section = False
    section_lines: list[str] = []
    for line in lines:
        if re.match(rf"^## {re.escape(heading)}\s*$", line, re.IGNORECASE):
            in_section = True
            continue
        if in_section:
            # Stop at any ## heading
            if re.match(r"^#{1,2} ", line):
                break
            section_lines.append(line)
    raw = "\n".join(section_lines)
    return raw, section_lines


def parse_logs(lines: list[str]) -> list[LogEntry]:
    """Parse log section lines into LogEntry objects."""
    if not lines:
        return []
    unit = _detect_indent_unit(lines)
    entries: list[LogEntry] = []
    for line in lines:
        if not line.strip():
            continue
        m = _BULLET_RE.match(line)
        if not m:
            continue
        spaces, text = m.group(1), m.group(2)
        indent = _indent_level(spaces, unit)
        # Check for timestamp on top-level lines
        time_val: str | None = None
        if indent == 0:
            tm = _TIME_RE.match(text)
            if tm:
                time_val = tm.group(1)
                text = tm.group(2)
        entries.append(LogEntry(time=time_val, text=text, indent=indent))
    return entries


def parse_todos(lines: list[str]) -> list[TodoItem]:
    """Parse todo section lines into TodoItem objects."""
    if not lines:
        return []
    unit = _detect_indent_unit(lines)
    items: list[TodoItem] = []
    for line in lines:
        if not line.strip():
            continue
        m = _TODO_RE.match(line)
        if not m:
            continue
        spaces, check_char, text = m.group(1), m.group(2), m.group(3)
        indent = _indent_level(spaces, unit)
        checked = check_char.lower() == "x"
        items.append(TodoItem(checked=checked, text=text, indent=indent))
    return items


def parse_daily(content: str) -> DailyContent:
    """Parse full daily file content into DailyContent."""
    raw_logs, log_lines = _extract_section(content, "Logs")
    raw_todos, todo_lines = _extract_section(content, "Todos")
    return DailyContent(
        logs=parse_logs(log_lines),
        todos=parse_todos(todo_lines),
        raw_logs=raw_logs,
        raw_todos=raw_todos,
    )


def reconstruct_file(raw_logs: str, raw_todos: str) -> str:
    """Reconstruct the full file content from edited sections."""
    logs_part = raw_logs.strip("\n")
    todos_part = raw_todos.strip("\n")
    parts = ["## Logs"]
    if logs_part:
        parts.append(logs_part)
    parts.append("")
    parts.append("## Todos")
    if todos_part:
        parts.append(todos_part)
    parts.append("")
    return "\n".join(parts)
