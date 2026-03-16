"""Data models for deja-claude."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class SessionInfo:
    """Lightweight session metadata from index scan."""

    session_id: str
    project_path: str  # encoded path e.g. "-Users-till-Projects-prekit"
    project_name: str  # human-readable e.g. "prekit"
    file_path: Path
    file_size: int
    mtime: float
    first_prompt: str = ""
    last_summary: str = ""  # last message from either side
    last_role: str = ""  # "user" or "assistant"
    timestamp: Optional[datetime] = None
    model: str = ""
    git_branch: str = ""
    slug: str = ""
    cwd: str = ""
    custom_name: str = ""
    is_active: bool = False

    @property
    def display_name(self) -> str:
        if self.custom_name:
            return self.custom_name
        if self.last_summary:
            return self.last_summary[:80]
        if self.first_prompt:
            return self.first_prompt[:80]
        if self.slug:
            return self.slug
        return self.session_id[:12]

    @property
    def display_date(self) -> str:
        if self.timestamp:
            return self.timestamp.strftime("%Y-%m-%d %H:%M")
        return datetime.fromtimestamp(self.mtime).strftime("%Y-%m-%d %H:%M")

    @property
    def size_display(self) -> str:
        if self.file_size < 1024:
            return f"{self.file_size}B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.0f}KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f}MB"


@dataclass
class ContentBlock:
    """A single content block within a conversation turn."""

    block_type: str  # "text", "tool_use", "tool_result", "thinking"
    text: str = ""
    tool_name: str = ""
    tool_input: str = ""
    tool_description: str = ""  # for Bash: command, for Read: file_path, etc.
    is_error: bool = False


@dataclass
class ConversationTurn:
    """A single turn in a conversation (user or assistant message)."""

    role: str  # "user", "assistant", "system"
    content_blocks: list[ContentBlock] = field(default_factory=list)
    model: str = ""
    timestamp: str = ""
    subtype: str = ""  # for system messages: "compact_boundary" etc.

    @property
    def plain_text(self) -> str:
        """Get concatenated text content only."""
        return "\n".join(b.text for b in self.content_blocks if b.block_type == "text" and b.text)

    @property
    def has_tool_calls(self) -> bool:
        return any(b.block_type in ("tool_use", "tool_result") for b in self.content_blocks)
