"""Tests for settings and metadata persistence."""

from deja_claude.settings import (
    get_session_name,
    load_settings,
    save_settings,
    set_session_name,
)


def test_load_default_settings():
    settings = load_settings()
    assert settings["show_tool_messages"] is False
    assert settings["sort_descending"] is True


def test_save_and_load_settings():
    save_settings({"show_tool_messages": True, "sort_by": "name"})
    loaded = load_settings()
    assert loaded["show_tool_messages"] is True
    assert loaded["sort_by"] == "name"
    # Defaults should still be present for unset keys
    assert "sort_descending" in loaded


def test_session_name_roundtrip():
    set_session_name("abc-123", "My Session")
    assert get_session_name("abc-123") == "My Session"

    set_session_name("abc-123", "")
    assert get_session_name("abc-123") == ""


def test_get_session_name_missing():
    assert get_session_name("nonexistent") == ""
