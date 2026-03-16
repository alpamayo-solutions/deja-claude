"""Session actions — delete, export, open-in-terminal."""

from __future__ import annotations

import shutil
from pathlib import Path

from .models import ConversationTurn, SessionInfo
from .settings import load_settings


def export_session_markdown(session: SessionInfo, turns: list[ConversationTurn]) -> Path:
    """Export a session as a Markdown file. Returns the output path."""
    settings = load_settings()
    export_dir = Path(settings["export_dir"])
    export_dir.mkdir(parents=True, exist_ok=True)

    name_slug = session.display_name.replace(" ", "-").replace("/", "-")[:50]
    filename = f"claude-session-{name_slug}-{session.session_id[:8]}.md"
    output_path = export_dir / filename

    lines: list[str] = []
    lines.append(f"# Session: {session.display_name}")
    lines.append("")

    meta_parts = []
    if session.project_name:
        meta_parts.append(f"**Project:** {session.project_name}")
    if session.display_date:
        meta_parts.append(f"**Date:** {session.display_date}")
    if session.model:
        meta_parts.append(f"**Model:** {session.model}")
    if meta_parts:
        lines.append(" | ".join(meta_parts))
        lines.append("")

    lines.append("---")
    lines.append("")

    for turn in turns:
        if turn.role == "user":
            lines.append("## You")
            lines.append("")
            for block in turn.content_blocks:
                if block.block_type == "text":
                    lines.append(block.text)
                    lines.append("")
        elif turn.role == "assistant":
            lines.append("## Claude")
            lines.append("")
            for block in turn.content_blocks:
                if block.block_type == "text":
                    lines.append(block.text)
                    lines.append("")
                elif block.block_type == "tool_use":
                    lines.append(f"> **Tool: {block.tool_name}** `{block.tool_description}`")
                    lines.append("")
                elif block.block_type == "thinking":
                    lines.append("<details><summary>Thinking</summary>")
                    lines.append("")
                    lines.append(block.text)
                    lines.append("")
                    lines.append("</details>")
                    lines.append("")
        elif turn.role == "tool_result":
            for block in turn.content_blocks:
                if block.block_type == "tool_result" and block.text:
                    lines.append("```")
                    lines.append(block.text[:2000])
                    lines.append("```")
                    lines.append("")
        elif turn.role == "system":
            lines.append("---")
            lines.append("")

    output_path.write_text("\n".join(lines))
    return output_path


def delete_session(session: SessionInfo) -> None:
    """Delete a session JSONL file and its companion directory if present."""
    # Delete the JSONL file
    if session.file_path.exists():
        session.file_path.unlink()

    # Delete companion directory (subagent data, tool outputs)
    companion_dir = session.file_path.parent / session.session_id
    if companion_dir.exists() and companion_dir.is_dir():
        shutil.rmtree(companion_dir)


def get_open_command(session: SessionInfo) -> str:
    """Build the command to open a session in Claude."""
    settings = load_settings()
    cmd = settings["open_command"]
    return cmd.format(session_id=session.session_id)
