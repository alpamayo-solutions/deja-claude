"""Tests for data models."""

from datetime import datetime, timezone
from pathlib import Path

from deja_claude.models import ContentBlock, ConversationTurn, SessionInfo


def test_session_display_name_custom():
    s = SessionInfo(
        session_id="abc", project_path="p", project_name="proj",
        file_path=Path("/tmp/x.jsonl"), file_size=100, mtime=0,
        custom_name="My Session",
    )
    assert s.display_name == "My Session"


def test_session_display_name_last_summary():
    s = SessionInfo(
        session_id="abc", project_path="p", project_name="proj",
        file_path=Path("/tmp/x.jsonl"), file_size=100, mtime=0,
        last_summary="The latest thing that happened",
    )
    assert s.display_name == "The latest thing that happened"


def test_session_display_name_first_prompt_fallback():
    s = SessionInfo(
        session_id="abc", project_path="p", project_name="proj",
        file_path=Path("/tmp/x.jsonl"), file_size=100, mtime=0,
        first_prompt="How do I do X?",
    )
    assert s.display_name == "How do I do X?"


def test_session_display_name_slug_fallback():
    s = SessionInfo(
        session_id="abc", project_path="p", project_name="proj",
        file_path=Path("/tmp/x.jsonl"), file_size=100, mtime=0,
        slug="happy-dancing-penguin",
    )
    assert s.display_name == "happy-dancing-penguin"


def test_session_display_name_id_fallback():
    s = SessionInfo(
        session_id="abc123def456", project_path="p", project_name="proj",
        file_path=Path("/tmp/x.jsonl"), file_size=100, mtime=0,
    )
    assert s.display_name == "abc123def456"


def test_session_size_display():
    assert SessionInfo(
        session_id="a", project_path="p", project_name="p",
        file_path=Path("/tmp/x"), file_size=500, mtime=0,
    ).size_display == "500B"

    assert SessionInfo(
        session_id="a", project_path="p", project_name="p",
        file_path=Path("/tmp/x"), file_size=2048, mtime=0,
    ).size_display == "2KB"

    assert SessionInfo(
        session_id="a", project_path="p", project_name="p",
        file_path=Path("/tmp/x"), file_size=5_242_880, mtime=0,
    ).size_display == "5.0MB"


def test_session_display_date_from_timestamp():
    s = SessionInfo(
        session_id="a", project_path="p", project_name="p",
        file_path=Path("/tmp/x"), file_size=0, mtime=0,
        timestamp=datetime(2026, 3, 16, 10, 30, tzinfo=timezone.utc),
    )
    assert "2026-03-16" in s.display_date


def test_conversation_turn_plain_text():
    turn = ConversationTurn(
        role="assistant",
        content_blocks=[
            ContentBlock(block_type="text", text="Hello"),
            ContentBlock(block_type="tool_use", tool_name="Bash"),
            ContentBlock(block_type="text", text="World"),
        ],
    )
    assert turn.plain_text == "Hello\nWorld"


def test_conversation_turn_has_tool_calls():
    turn_with = ConversationTurn(
        role="assistant",
        content_blocks=[ContentBlock(block_type="tool_use", tool_name="Read")],
    )
    turn_without = ConversationTurn(
        role="user",
        content_blocks=[ContentBlock(block_type="text", text="hi")],
    )
    assert turn_with.has_tool_calls is True
    assert turn_without.has_tool_calls is False
