"""Tests for safety checks in session actions."""

from pathlib import Path

import pytest

from deja_claude.actions import delete_session
from deja_claude.models import SessionInfo


def test_delete_refuses_outside_claude_dir(tmp_path):
    """delete_session should refuse to delete files outside ~/.claude/."""
    rogue_file = tmp_path / "important-file.jsonl"
    rogue_file.write_text("important data\n")

    session = SessionInfo(
        session_id="rogue",
        project_path="p",
        project_name="p",
        file_path=rogue_file,
        file_size=100,
        mtime=0,
    )

    with pytest.raises(ValueError, match="Refusing to delete"):
        delete_session(session)

    # File should still exist
    assert rogue_file.exists()


def test_delete_allows_inside_claude_dir(tmp_path, monkeypatch):
    """delete_session should allow deletion within ~/.claude/."""
    # Mock home to tmp_path so ~/.claude/ resolves to tmp_path/.claude/
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

    claude_dir = tmp_path / ".claude" / "projects" / "test-project"
    claude_dir.mkdir(parents=True)
    session_file = claude_dir / "test-session.jsonl"
    session_file.write_text('{"type":"user"}\n')

    session = SessionInfo(
        session_id="test-session",
        project_path="test-project",
        project_name="test",
        file_path=session_file,
        file_size=100,
        mtime=0,
    )

    delete_session(session)
    assert not session_file.exists()
