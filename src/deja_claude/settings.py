"""Settings and metadata persistence for deja-claude."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CONFIG_DIR = Path.home() / ".config" / "deja-claude"
SETTINGS_FILE = CONFIG_DIR / "settings.json"
METADATA_FILE = CONFIG_DIR / "metadata.json"

DEFAULT_SETTINGS = {
    "claude_projects_path": str(Path.home() / ".claude" / "projects"),
    "claude_history_path": str(Path.home() / ".claude" / "history.jsonl"),
    "claude_sessions_path": str(Path.home() / ".claude" / "sessions"),
    "open_command": "claude -r {session_id}",
    "default_folder": str(Path.home()),  # path = filter sessions by cwd on startup
    "show_tool_messages": False,
    "show_thinking": False,
    "sort_by": "date",
    "sort_descending": True,
    "export_dir": str(Path.home() / "Desktop"),
}


def _ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_settings() -> dict[str, Any]:
    _ensure_config_dir()
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE) as f:
                saved = json.load(f)
            merged = {**DEFAULT_SETTINGS, **saved}
            return merged
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict[str, Any]) -> None:
    _ensure_config_dir()
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def load_metadata() -> dict[str, Any]:
    _ensure_config_dir()
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"sessions": {}}


def save_metadata(metadata: dict[str, Any]) -> None:
    _ensure_config_dir()
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)


def get_session_name(session_id: str) -> str:
    """Get custom name for a session, or empty string."""
    meta = load_metadata()
    return meta.get("sessions", {}).get(session_id, {}).get("name", "")


def set_session_name(session_id: str, name: str) -> None:
    """Set a custom name for a session."""
    meta = load_metadata()
    if "sessions" not in meta:
        meta["sessions"] = {}
    if name:
        meta["sessions"][session_id] = {"name": name}
    elif session_id in meta["sessions"]:
        del meta["sessions"][session_id]
    save_metadata(meta)
