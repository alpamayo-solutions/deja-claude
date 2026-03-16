"""Edge case tests for the session scanner."""

import json

from deja_claude.scanner import _decode_project_path, parse_session, scan_sessions
from deja_claude.settings import DEFAULT_SETTINGS, save_settings


def _make_settings(tmp_claude_dir):
    settings = {
        **DEFAULT_SETTINGS,
        "claude_projects_path": str(tmp_claude_dir / "projects"),
        "claude_history_path": str(tmp_claude_dir / "history.jsonl"),
        "claude_sessions_path": str(tmp_claude_dir / "sessions"),
    }
    save_settings(settings)
    return settings


def test_scan_handles_corrupted_jsonl(tmp_path):
    """Scanner should skip lines that are not valid JSON."""
    settings = {
        **DEFAULT_SETTINGS,
        "claude_projects_path": str(tmp_path / "projects"),
        "claude_history_path": str(tmp_path / "history.jsonl"),
        "claude_sessions_path": str(tmp_path / "sessions"),
    }
    save_settings(settings)
    (tmp_path / "sessions").mkdir()
    (tmp_path / "history.jsonl").write_text("")

    proj = tmp_path / "projects" / "-Users-test-Projects-app"
    proj.mkdir(parents=True)

    # Write a session with corrupted lines mixed in
    lines = [
        "NOT VALID JSON",
        '{"partial": true',
        json.dumps(
            {
                "type": "user",
                "timestamp": "2026-01-10T10:00:00Z",
                "message": {"role": "user", "content": "Hello"},
            }
        ),
        "\x00\x01\x02binary garbage\xff\xfe",
        json.dumps(
            {
                "type": "assistant",
                "timestamp": "2026-01-10T10:00:05Z",
                "message": {
                    "role": "assistant",
                    "model": "claude-opus-4-6",
                    "content": [{"type": "text", "text": "Hi there"}],
                },
            }
        ),
    ]
    session_file = proj / "aaaa1111-0000-0000-0000-000000000001.jsonl"
    session_file.write_text("\n".join(lines) + "\n")

    sessions = scan_sessions()
    assert len(sessions) == 1
    assert sessions[0].first_prompt == "Hello"


def test_scan_handles_empty_projects_dir(tmp_path):
    """Scanner should return empty list for empty projects dir."""
    settings = {
        **DEFAULT_SETTINGS,
        "claude_projects_path": str(tmp_path / "projects"),
        "claude_history_path": str(tmp_path / "history.jsonl"),
        "claude_sessions_path": str(tmp_path / "sessions"),
    }
    save_settings(settings)
    (tmp_path / "projects").mkdir()
    (tmp_path / "sessions").mkdir()
    (tmp_path / "history.jsonl").write_text("")

    sessions = scan_sessions()
    assert sessions == []


def test_scan_handles_missing_projects_dir(tmp_path):
    """Scanner should return empty list if projects dir doesn't exist."""
    settings = {
        **DEFAULT_SETTINGS,
        "claude_projects_path": str(tmp_path / "nonexistent"),
        "claude_history_path": str(tmp_path / "history.jsonl"),
        "claude_sessions_path": str(tmp_path / "sessions"),
    }
    save_settings(settings)

    sessions = scan_sessions()
    assert sessions == []


def test_parse_empty_file(tmp_path):
    """Parsing an empty file should return no turns."""
    empty_file = tmp_path / "empty.jsonl"
    empty_file.write_text("")
    turns = parse_session(empty_file)
    assert turns == []


def test_parse_nonexistent_file(tmp_path):
    """Parsing a missing file should return no turns, not raise."""
    turns = parse_session(tmp_path / "does-not-exist.jsonl")
    assert turns == []


def test_parse_extremely_long_lines(tmp_path):
    """Scanner should handle lines with very long content."""
    long_text = "x" * 100_000
    lines = [
        json.dumps(
            {
                "type": "user",
                "timestamp": "2026-01-10T10:00:00Z",
                "message": {"role": "user", "content": long_text},
            }
        ),
        json.dumps(
            {
                "type": "assistant",
                "timestamp": "2026-01-10T10:00:05Z",
                "message": {
                    "role": "assistant",
                    "model": "claude-opus-4-6",
                    "content": [{"type": "text", "text": "Short reply"}],
                },
            }
        ),
    ]
    session_file = tmp_path / "long-lines.jsonl"
    session_file.write_text("\n".join(lines) + "\n")

    turns = parse_session(session_file)
    assert len(turns) == 2
    # First prompt should be truncated to 200 chars
    assert len(turns[0].content_blocks[0].text) == 100_000


def test_decode_project_path_edge_cases():
    """Test project path decoding edge cases."""
    assert _decode_project_path("") == "(root)"
    assert _decode_project_path("-") == "(root)"
    # Standard path
    assert _decode_project_path("-Users-test-Projects-myapp") == "myapp"
    # Downloads path
    assert _decode_project_path("-Users-test-Downloads-archive") == "archive"
