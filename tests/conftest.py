"""Shared test fixtures."""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolate_config(tmp_path, monkeypatch):
    """Prevent tests from reading/writing the real ~/.config/deja-claude/."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    monkeypatch.setattr("deja_claude.settings.CONFIG_DIR", config_dir)
    monkeypatch.setattr("deja_claude.settings.SETTINGS_FILE", config_dir / "settings.json")
    monkeypatch.setattr("deja_claude.settings.METADATA_FILE", config_dir / "metadata.json")


@pytest.fixture
def tmp_claude_dir(tmp_path):
    """Create a temporary .claude directory with sample session data."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()

    history_file = tmp_path / "history.jsonl"
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()

    # Create two project directories with sessions
    proj_a = projects_dir / "-Users-test-Projects-myapp"
    proj_a.mkdir()
    proj_b = projects_dir / "-Users-test-Projects-backend"
    proj_b.mkdir()

    # Session 1: a normal conversation in myapp
    _write_session(proj_a, "aaaa1111-0000-0000-0000-000000000001", [
        _user_msg("How do I add a login page?", "2026-01-10T10:00:00Z"),
        _assistant_msg("You can create a LoginView component...", "2026-01-10T10:00:05Z"),
        _user_msg("Can you show me the code?", "2026-01-10T10:01:00Z"),
        _assistant_msg("Here's a basic implementation:\n\n```vue\n<template>...</template>\n```", "2026-01-10T10:01:10Z"),
    ])

    # Session 2: short session in myapp
    _write_session(proj_a, "aaaa2222-0000-0000-0000-000000000002", [
        _user_msg("Fix the CSS on the navbar", "2026-02-15T14:00:00Z"),
        _assistant_msg("I'll update the styles.", "2026-02-15T14:00:10Z", model="claude-sonnet-4-6"),
    ])

    # Session 3: session in backend
    _write_session(proj_b, "bbbb3333-0000-0000-0000-000000000003", [
        _user_msg("Add a health check endpoint", "2026-03-01T09:00:00Z"),
        _assistant_msg("I'll add a /health route.", "2026-03-01T09:00:05Z"),
        _assistant_msg_with_tool("Bash", {"command": "python manage.py runserver"}, "2026-03-01T09:00:15Z"),
        _user_msg("Looks good, thanks", "2026-03-01T09:01:00Z"),
    ])

    # Session 4: empty/tiny session (should be skipped)
    (proj_a / "cccc4444-0000-0000-0000-000000000004.jsonl").write_text("{}\n")

    # History index
    history_lines = [
        json.dumps({"display": "How do I add a login page?", "sessionId": "aaaa1111-0000-0000-0000-000000000001",
                     "project": "/Users/test/Projects/myapp", "timestamp": 1736503200000}),
        json.dumps({"display": "Fix the CSS on the navbar", "sessionId": "aaaa2222-0000-0000-0000-000000000002",
                     "project": "/Users/test/Projects/myapp", "timestamp": 1739624400000}),
    ]
    history_file.write_text("\n".join(history_lines) + "\n")

    return tmp_path


def _user_msg(text, timestamp, cwd="/Users/test/Projects/myapp"):
    return json.dumps({
        "type": "user",
        "cwd": cwd,
        "sessionId": "test",
        "gitBranch": "main",
        "timestamp": timestamp,
        "message": {"role": "user", "content": text},
    })


def _assistant_msg(text, timestamp, model="claude-opus-4-6"):
    return json.dumps({
        "type": "assistant",
        "timestamp": timestamp,
        "message": {
            "role": "assistant",
            "model": model,
            "content": [{"type": "text", "text": text}],
        },
    })


def _assistant_msg_with_tool(tool_name, tool_input, timestamp):
    return json.dumps({
        "type": "assistant",
        "timestamp": timestamp,
        "message": {
            "role": "assistant",
            "model": "claude-opus-4-6",
            "content": [{"type": "tool_use", "name": tool_name, "input": tool_input}],
        },
    })


def _write_session(project_dir, session_id, lines):
    path = project_dir / f"{session_id}.jsonl"
    path.write_text("\n".join(lines) + "\n")
