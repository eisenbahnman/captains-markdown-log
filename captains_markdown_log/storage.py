"""File I/O and date navigation for daily log files."""
from __future__ import annotations
import re
from datetime import date, timedelta
from pathlib import Path


SCAFFOLD = "## Logs\n\n\n## Todos\n\n"


def get_file_path(logs_dir: Path, d: date) -> Path:
    return logs_dir / f"{d.isoformat()}.md"


def file_exists(logs_dir: Path, d: date) -> bool:
    return get_file_path(logs_dir, d).exists()


def read_file(logs_dir: Path, d: date) -> str | None:
    """Return file contents or None if it doesn't exist."""
    path = get_file_path(logs_dir, d)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def write_file(logs_dir: Path, d: date, content: str) -> None:
    path = get_file_path(logs_dir, d)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_daily_file(logs_dir: Path, d: date) -> None:
    """Create a new daily file with the scaffold headings."""
    path = get_file_path(logs_dir, d)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(SCAFFOLD, encoding="utf-8")


def _list_existing_dates(logs_dir: Path) -> list[date]:
    """Return sorted list of dates that have log files."""
    pattern = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")
    dates: list[date] = []
    if not logs_dir.exists():
        return dates
    for p in logs_dir.iterdir():
        m = pattern.match(p.name)
        if m:
            try:
                dates.append(date.fromisoformat(m.group(1)))
            except ValueError:
                pass
    return sorted(dates)


def get_prev_existing(logs_dir: Path, d: date) -> date | None:
    """Return the nearest date before d that has a file, or None."""
    dates = _list_existing_dates(logs_dir)
    candidates = [x for x in dates if x < d]
    return candidates[-1] if candidates else None


def get_next_existing(logs_dir: Path, d: date) -> date | None:
    """Return the nearest date after d that has a file, or None."""
    dates = _list_existing_dates(logs_dir)
    candidates = [x for x in dates if x > d]
    return candidates[0] if candidates else None
