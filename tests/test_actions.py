"""Tests for session actions."""

from pathlib import Path

from deja_claude.actions import delete_session, export_session_markdown
from deja_claude.models import ContentBlock, ConversationTurn, SessionInfo


def test_export_creates_markdown(tmp_path):
    session = SessionInfo(
        session_id="test-123",
        project_path="-Users-test-Projects-app",
        project_name="app",
        file_path=Path("/tmp/fake.jsonl"),
        file_size=1000,
        mtime=0,
        first_prompt="Hello",
        model="claude-opus-4-6",
    )
    turns = [
        ConversationTurn(
            role="user",
            content_blocks=[ContentBlock(block_type="text", text="Hello Claude")],
        ),
        ConversationTurn(
            role="assistant",
            content_blocks=[ContentBlock(block_type="text", text="Hello! How can I help?")],
            model="claude-opus-4-6",
        ),
    ]

    from deja_claude.settings import DEFAULT_SETTINGS, save_settings

    save_settings({**DEFAULT_SETTINGS, "export_dir": str(tmp_path)})

    path = export_session_markdown(session, turns)

    assert path.exists()
    content = path.read_text()
    assert "# Session:" in content
    assert "Hello Claude" in content
    assert "Hello! How can I help?" in content
    assert "**Project:** app" in content


def test_delete_session_removes_file(tmp_path, monkeypatch):
    # Place files under a fake ~/.claude/ so the safety check passes
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

    claude_dir = tmp_path / ".claude" / "projects" / "test-project"
    claude_dir.mkdir(parents=True)
    jsonl_file = claude_dir / "test-session.jsonl"
    jsonl_file.write_text('{"type":"user"}\n')

    companion_dir = claude_dir / "test-session"
    companion_dir.mkdir()
    (companion_dir / "subagent.jsonl").write_text("{}\n")

    session = SessionInfo(
        session_id="test-session",
        project_path="p",
        project_name="p",
        file_path=jsonl_file,
        file_size=100,
        mtime=0,
    )

    delete_session(session)

    assert not jsonl_file.exists()
    assert not companion_dir.exists()


def test_delete_session_missing_file_no_error(tmp_path, monkeypatch):
    # Place the path under a fake ~/.claude/ so safety check passes
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

    claude_dir = tmp_path / ".claude" / "projects"
    claude_dir.mkdir(parents=True)

    session = SessionInfo(
        session_id="missing",
        project_path="p",
        project_name="p",
        file_path=claude_dir / "does-not-exist.jsonl",
        file_size=0,
        mtime=0,
    )
    # Should not raise
    delete_session(session)
