"""Tests for the session scanner."""

from deja_claude.scanner import scan_sessions, parse_session
from deja_claude.settings import save_settings, DEFAULT_SETTINGS


def test_scan_finds_all_valid_sessions(tmp_claude_dir):
    settings = {**DEFAULT_SETTINGS,
                "claude_projects_path": str(tmp_claude_dir / "projects"),
                "claude_history_path": str(tmp_claude_dir / "history.jsonl"),
                "claude_sessions_path": str(tmp_claude_dir / "sessions")}
    save_settings(settings)

    sessions = scan_sessions()

    # Should find 3 sessions (the 4th is too small)
    assert len(sessions) == 3


def test_scan_extracts_first_prompt(tmp_claude_dir):
    settings = {**DEFAULT_SETTINGS,
                "claude_projects_path": str(tmp_claude_dir / "projects"),
                "claude_history_path": str(tmp_claude_dir / "history.jsonl"),
                "claude_sessions_path": str(tmp_claude_dir / "sessions")}
    save_settings(settings)

    sessions = scan_sessions()
    by_id = {s.session_id: s for s in sessions}

    assert "login page" in by_id["aaaa1111-0000-0000-0000-000000000001"].first_prompt.lower()
    assert "css" in by_id["aaaa2222-0000-0000-0000-000000000002"].first_prompt.lower()
    assert "health check" in by_id["bbbb3333-0000-0000-0000-000000000003"].first_prompt.lower()


def test_scan_extracts_last_message(tmp_claude_dir):
    settings = {**DEFAULT_SETTINGS,
                "claude_projects_path": str(tmp_claude_dir / "projects"),
                "claude_history_path": str(tmp_claude_dir / "history.jsonl"),
                "claude_sessions_path": str(tmp_claude_dir / "sessions")}
    save_settings(settings)

    sessions = scan_sessions()
    by_id = {s.session_id: s for s in sessions}

    # Session 1: last message is assistant
    s1 = by_id["aaaa1111-0000-0000-0000-000000000001"]
    assert s1.last_role == "assistant"
    assert "implementation" in s1.last_summary.lower()

    # Session 3: last message is user "Looks good, thanks"
    s3 = by_id["bbbb3333-0000-0000-0000-000000000003"]
    assert s3.last_role == "user"
    assert "looks good" in s3.last_summary.lower()


def test_scan_extracts_model(tmp_claude_dir):
    settings = {**DEFAULT_SETTINGS,
                "claude_projects_path": str(tmp_claude_dir / "projects"),
                "claude_history_path": str(tmp_claude_dir / "history.jsonl"),
                "claude_sessions_path": str(tmp_claude_dir / "sessions")}
    save_settings(settings)

    sessions = scan_sessions()
    by_id = {s.session_id: s for s in sessions}

    assert by_id["aaaa1111-0000-0000-0000-000000000001"].model == "claude-opus-4-6"
    assert by_id["aaaa2222-0000-0000-0000-000000000002"].model == "claude-sonnet-4-6"


def test_scan_extracts_project_name(tmp_claude_dir):
    settings = {**DEFAULT_SETTINGS,
                "claude_projects_path": str(tmp_claude_dir / "projects"),
                "claude_history_path": str(tmp_claude_dir / "history.jsonl"),
                "claude_sessions_path": str(tmp_claude_dir / "sessions")}
    save_settings(settings)

    sessions = scan_sessions()
    project_names = {s.project_name for s in sessions}

    assert "myapp" in project_names
    assert "backend" in project_names


def test_scan_sorted_by_date_descending(tmp_claude_dir):
    settings = {**DEFAULT_SETTINGS,
                "claude_projects_path": str(tmp_claude_dir / "projects"),
                "claude_history_path": str(tmp_claude_dir / "history.jsonl"),
                "claude_sessions_path": str(tmp_claude_dir / "sessions")}
    save_settings(settings)

    sessions = scan_sessions()

    # Should be newest first
    assert sessions[0].session_id == "bbbb3333-0000-0000-0000-000000000003"  # March
    assert sessions[1].session_id == "aaaa2222-0000-0000-0000-000000000002"  # February
    assert sessions[2].session_id == "aaaa1111-0000-0000-0000-000000000001"  # January


def test_parse_session_returns_turns(tmp_claude_dir):
    session_file = tmp_claude_dir / "projects" / "-Users-test-Projects-myapp" / "aaaa1111-0000-0000-0000-000000000001.jsonl"
    turns = parse_session(session_file)

    user_turns = [t for t in turns if t.role == "user"]
    assistant_turns = [t for t in turns if t.role == "assistant"]

    assert len(user_turns) == 2
    assert len(assistant_turns) == 2
    assert "login page" in user_turns[0].plain_text.lower()


def test_parse_session_extracts_tool_calls(tmp_claude_dir):
    session_file = tmp_claude_dir / "projects" / "-Users-test-Projects-backend" / "bbbb3333-0000-0000-0000-000000000003.jsonl"
    turns = parse_session(session_file)

    tool_turns = [t for t in turns if t.has_tool_calls]
    assert len(tool_turns) >= 1
    assert tool_turns[0].content_blocks[0].tool_name == "Bash"


def test_parse_string_content(tmp_claude_dir):
    """Test that string content (not list) is parsed correctly."""
    session_file = tmp_claude_dir / "projects" / "-Users-test-Projects-myapp" / "aaaa1111-0000-0000-0000-000000000001.jsonl"
    turns = parse_session(session_file)

    # First user message has string content
    assert turns[0].role == "user"
    assert turns[0].plain_text != ""
