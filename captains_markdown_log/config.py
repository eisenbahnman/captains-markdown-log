"""Config loading from ~/.config/captains-markdown-log/config.toml"""
from __future__ import annotations
import tomllib
from dataclasses import dataclass
from pathlib import Path


CONFIG_PATH = Path.home() / ".config" / "captains-markdown-log" / "config.toml"
DEFAULT_LOGS_DIR = Path.home() / "captains-markdown-log"

DEFAULT_CONFIG_CONTENT = '''\
# Captain's Markdown Log configuration

# Path to the directory where daily log files are stored
logs_dir = "{logs_dir}"
'''


@dataclass
class Config:
    logs_dir: Path


def load_config() -> Config:
    """Load config from ~/.config/captains-markdown-log/config.toml.

    Creates default config if it doesn't exist.
    Returns Config with logs_dir set.
    """
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(
            DEFAULT_CONFIG_CONTENT.format(logs_dir=str(DEFAULT_LOGS_DIR))
        )
        return Config(logs_dir=DEFAULT_LOGS_DIR)

    with open(CONFIG_PATH, "rb") as f:
        data = tomllib.load(f)

    logs_dir = Path(data.get("logs_dir", str(DEFAULT_LOGS_DIR))).expanduser()
    logs_dir.mkdir(parents=True, exist_ok=True)
    return Config(logs_dir=logs_dir)
