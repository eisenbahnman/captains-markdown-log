"""Inline markdown renderer: converts markdown text to Rich Text objects."""
from __future__ import annotations
import re
from rich.style import Style
from rich.text import Text


# Mutable style dict — updated by apply_theme() when the Textual theme changes
_s: dict[str, Style] = {}


def apply_theme(
    *,
    warning: str,
    success: str,
    error: str,
    secondary: str,
    accent: str,
) -> None:
    """Rebuild all renderer styles from theme colors."""
    _s["bullet"]    = Style(color=accent)
    _s["time"]      = Style(color=secondary)
    _s["todo_open"] = Style(color=success)
    _s["todo_done"] = Style(color=success)
    _s["base_done"] = Style(dim=True, strike=True)
    _s["bold"]      = Style(bold=True, color=success)
    _s["italic"]    = Style(italic=True, color=error)
    _s["strike"]    = Style(strike=True)
    _s["hl"]        = Style(bgcolor=warning)
    _s["ul"]        = Style(underline=True)
    _s["ul_link"]   = Style(underline=True, color=secondary)


# Fallback so renderer works even before apply_theme() is called
apply_theme(
    warning="#E0AF68",
    success="#9ECE6A",
    error="#F7768E",
    secondary="#7AA2F7",
    accent="#FF9E64",
)


# Combined pattern for finding any inline markdown (order matters — longer patterns first)
_COMBINED = re.compile(
    r"(\*\*(?P<bold_star>.+?)\*\*"
    r"|__(?P<bold_under>.+?)__"
    r"|~~(?P<strike>.+?)~~"
    r"|==(?P<hl_eq>.+?)=="
    r"|::(?P<hl_colon>.+?)::"
    r"|~(?P<underline>[^~]+)~"
    r"|(?<!\*)\*(?!\*)(?P<italic_star>.+?)(?<!\*)\*(?!\*)"
    r"|(?<![_\w])_(?P<italic_under>[^_]+)_(?![_\w])"
    r"|\[(?P<link_text>[^\]]+)\]\((?P<link_url>[^)]+)\)"
    r")"
)


def _style_for_match(m: re.Match) -> Style:
    """Return the Rich Style for a given inline markdown match."""
    if m.group("bold_star") is not None or m.group("bold_under") is not None:
        return _s["bold"]
    if m.group("strike") is not None:
        return _s["strike"]
    if m.group("hl_eq") is not None or m.group("hl_colon") is not None:
        return _s["hl"]
    if m.group("underline") is not None:
        return _s["ul"]
    if m.group("italic_star") is not None or m.group("italic_under") is not None:
        return _s["italic"]
    if m.group("link_text") is not None:
        return _s["ul_link"]
    return Style.null()


def apply_inline_markdown(text: str, base_style: Style = Style.null()) -> Text:
    """Convert a string with inline markdown to a Rich Text object.

    Syntax characters are preserved (visible) but styled.
    base_style is applied to all unstyled portions (used for dim/strike on checked todos).
    """
    result = Text()
    last_end = 0
    for m in _COMBINED.finditer(text):
        start, end = m.start(), m.end()
        if start > last_end:
            result.append(text[last_end:start], style=base_style)
        combined = base_style + _style_for_match(m)
        result.append(m.group(0), style=combined)
        last_end = end
    if last_end < len(text):
        result.append(text[last_end:], style=base_style)
    return result


def render_log_line(time: str | None, text: str, indent: int) -> Text:
    """Render a single log entry line as Rich Text."""
    result = Text(no_wrap=False, overflow="fold")
    result.append("  " * indent)
    result.append("● ", style=_s["bullet"])
    if time is not None:
        result.append(time, style=_s["time"])
        result.append(" ")
    result.append_text(apply_inline_markdown(text))
    return result


def render_todo_line(checked: bool, text: str, indent: int) -> Text:
    """Render a single todo item line as Rich Text."""
    result = Text(no_wrap=False, overflow="fold")
    result.append("  " * indent)
    if checked:
        result.append("● ", style=_s["todo_done"])
        result.append_text(apply_inline_markdown(text, base_style=_s["base_done"]))
    else:
        result.append("○ ", style=_s["todo_open"])
        result.append_text(apply_inline_markdown(text))
    return result
