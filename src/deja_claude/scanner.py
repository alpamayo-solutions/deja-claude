"""Session scanner — index scan (fast) and full parse (lazy)."""

from __future__ import annotations

import contextlib
import json
import logging
import re
from datetime import datetime
from pathlib import Path

from .models import ContentBlock, ConversationTurn, SessionInfo
from .settings import load_metadata, load_settings

logger = logging.getLogger(__name__)

# IDE-injected prefixes we want to skip when extracting the first prompt
IDE_TAG_RE = re.compile(r"<ide_\w+>.*?</ide_\w+>", re.DOTALL)
SYSTEM_REMINDER_RE = re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL)


def _decode_project_path(encoded: str) -> str:
    """Convert encoded path like '-Users-till-Projects-prekit' to human name.

    The encoding replaces '/' with '-', so '-Users-till-Projects-prekit' is
    the path /Users/till/Projects/prekit. We reconstruct the path and take
    the last 1-2 meaningful directory segments.
    """
    if not encoded or encoded == "-":
        return "(root)"

    # Reconstruct the original path: leading - is /, internal - could be / or literal
    # The pattern is: -{segment}-{segment}-... where each segment is a directory name
    # Heuristic: known top-level dirs help us split correctly
    # Common pattern: -Users-{user}-Projects-{project-name} or -Users-{user}-Downloads-...
    path = encoded.lstrip("-")

    # Try to find Projects/ or Downloads/ boundary
    for marker in ("Projects-", "Downloads-"):
        idx = path.find(marker)
        if idx >= 0:
            remainder = path[idx + len(marker) :]
            if remainder:
                # The remainder might contain sub-paths with hyphens
                # e.g. "prekit-prekit" means prekit/prekit, "composable-edge-node" could be
                # a single dir name or multi-level. Without the real filesystem, just return as-is.
                return remainder
            return marker.rstrip("-").lower()

    # Try after last known username segment
    for marker in ("till-",):
        idx = path.find(marker)
        if idx >= 0:
            remainder = path[idx + len(marker) :]
            if remainder:
                return remainder

    # Fallback: return last segment after splitting on common prefixes
    parts = path.split("-")
    skip = {
        "Users",
        "till",
        "Projects",
        "var",
        "folders",
        "private",
        "tmp",
        "Downloads",
        "home",
        "Volumes",
        "sr",
        "9dhvt",
        "5906qd9fq63btyh43r0000gn",
        "T",
    }
    meaningful = [p for p in parts if p and p not in skip]
    if meaningful:
        return "-".join(meaningful[-2:]) if len(meaningful) > 1 else meaningful[-1]
    return encoded


def _extract_first_prompt(content: list) -> str:
    """Extract first human-readable prompt from message content blocks."""
    for block in content:
        if isinstance(block, str):
            cleaned = block.strip()
            if cleaned:
                return cleaned[:200]
        elif isinstance(block, dict) and block.get("type") == "text":
            text = block.get("text", "")
            # Skip IDE-injected tags
            cleaned = IDE_TAG_RE.sub("", text).strip()
            cleaned = SYSTEM_REMINDER_RE.sub("", cleaned).strip()
            if cleaned and not cleaned.startswith("<"):
                return cleaned[:200]
        elif isinstance(block, dict) and block.get("type") == "tool_result":
            continue
    return ""


def _extract_tool_description(tool_name: str, tool_input: dict) -> str:  # type: ignore[type-arg]
    """Extract a short description for a tool call."""
    if tool_name == "Bash":
        return str(tool_input.get("command", ""))[:120]
    elif tool_name == "Read" or tool_name in ("Write", "Edit"):
        return str(tool_input.get("file_path", ""))
    elif tool_name in ("Glob", "Grep"):
        return str(tool_input.get("pattern", ""))
    elif tool_name == "Agent":
        return str(tool_input.get("description", ""))[:80]
    elif tool_name == "WebSearch":
        return str(tool_input.get("query", ""))[:80]
    elif tool_name == "WebFetch":
        return str(tool_input.get("url", ""))[:80]
    return ""


def _read_last_message(file_path: Path, file_size: int) -> tuple[str, str]:
    """Read the last user or assistant text message from a JSONL file.

    Seeks to the tail of the file to avoid reading the whole thing.
    Returns (summary_text, role).
    """
    chunk_size = min(file_size, 64 * 1024)  # last 64KB
    try:
        with open(file_path, "rb") as f:
            f.seek(max(0, file_size - chunk_size))
            tail = f.read().decode("utf-8", errors="replace")
    except OSError:
        return ("", "")

    # Parse lines in reverse to find the last real message
    lines = tail.splitlines()
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg_type = obj.get("type", "")
        if msg_type not in ("user", "assistant"):
            continue

        msg = obj.get("message", {})
        content = msg.get("content", [])

        if isinstance(content, str):
            cleaned = IDE_TAG_RE.sub("", content)
            cleaned = SYSTEM_REMINDER_RE.sub("", cleaned).strip()
            if cleaned and not cleaned.startswith("<"):
                return (cleaned[:200], msg_type)
            continue

        # For list content, find the last text block (skip tool_results)
        for block in reversed(content):
            if isinstance(block, dict):
                if block.get("type") == "text":
                    text = block.get("text", "")
                    cleaned = IDE_TAG_RE.sub("", text)
                    cleaned = SYSTEM_REMINDER_RE.sub("", cleaned).strip()
                    if cleaned and not cleaned.startswith("<"):
                        return (cleaned[:200], msg_type)
                elif block.get("type") == "tool_result":
                    continue
            elif isinstance(block, str) and block.strip():
                return (block.strip()[:200], msg_type)

    return ("", "")


def scan_sessions() -> list[SessionInfo]:
    """Fast index scan — reads first ~50 lines of each JSONL file."""
    settings = load_settings()
    metadata = load_metadata()
    projects_path = Path(settings["claude_projects_path"])
    history_path = Path(settings["claude_history_path"])
    sessions_path = Path(settings["claude_sessions_path"])
    session_names = metadata.get("sessions", {})

    # Load active session IDs
    active_sessions: set[str] = set()
    if sessions_path.exists():
        for f in sessions_path.iterdir():
            if f.suffix == ".json":
                try:
                    data = json.loads(f.read_text())
                    if sid := data.get("sessionId"):
                        active_sessions.add(sid)
                except (json.JSONDecodeError, OSError):
                    pass

    # Load history index for fallback display text
    history_index: dict[str, str] = {}
    if history_path.exists():
        try:
            with open(history_path) as hf:
                for line in hf:
                    try:
                        entry = json.loads(line)
                        sid = entry.get("sessionId", "")
                        display = entry.get("display", "")
                        if sid and display and sid not in history_index:
                            # Store first display text per session
                            cleaned = display.strip()
                            if cleaned and not cleaned.startswith("<"):
                                history_index[sid] = cleaned[:200]
                    except json.JSONDecodeError:
                        continue
        except OSError:
            pass

    sessions: list[SessionInfo] = []

    if not projects_path.exists():
        return sessions

    for project_dir in projects_path.iterdir():
        if not project_dir.is_dir():
            continue

        project_encoded = project_dir.name
        project_name = _decode_project_path(project_encoded)

        for jsonl_file in project_dir.glob("*.jsonl"):
            session_id = jsonl_file.stem
            # Skip non-UUID filenames
            if len(session_id) < 30:
                continue

            try:
                stat = jsonl_file.stat()
            except OSError:
                continue

            # Skip tiny/empty files
            if stat.st_size < 100:
                continue

            info = SessionInfo(
                session_id=session_id,
                project_path=project_encoded,
                project_name=project_name,
                file_path=jsonl_file,
                file_size=stat.st_size,
                mtime=stat.st_mtime,
                is_active=session_id in active_sessions,
            )

            # Read first ~50 lines to extract metadata
            try:
                with open(jsonl_file) as jf:
                    for i, line in enumerate(jf):
                        if i >= 50:
                            break
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        msg_type = obj.get("type", "")

                        if msg_type == "user" and not info.first_prompt:
                            msg = obj.get("message", {})
                            content = msg.get("content", [])
                            # content can be a plain string or a list of blocks
                            if isinstance(content, str):
                                cleaned = IDE_TAG_RE.sub("", content)
                                cleaned = SYSTEM_REMINDER_RE.sub("", cleaned).strip()
                                if cleaned and not cleaned.startswith("<"):
                                    info.first_prompt = cleaned[:200]
                            else:
                                info.first_prompt = _extract_first_prompt(content)
                            if not info.cwd:
                                info.cwd = obj.get("cwd", "")
                            if not info.git_branch:
                                info.git_branch = obj.get("gitBranch", "")
                            if not info.slug:
                                info.slug = obj.get("slug", "")
                            if not info.timestamp and obj.get("timestamp"):
                                ts = obj["timestamp"]
                                if isinstance(ts, str):
                                    with contextlib.suppress(ValueError):
                                        info.timestamp = datetime.fromisoformat(ts.replace("Z", "+00:00"))

                        elif msg_type == "assistant" and not info.model:
                            msg = obj.get("message", {})
                            info.model = msg.get("model", "")
                            if not info.timestamp and obj.get("timestamp"):
                                ts = obj["timestamp"]
                                if isinstance(ts, str):
                                    with contextlib.suppress(ValueError):
                                        info.timestamp = datetime.fromisoformat(ts.replace("Z", "+00:00"))

                        elif msg_type == "system":
                            if not info.slug:
                                info.slug = obj.get("slug", "")

                        # Early exit if we have everything
                        if info.first_prompt and info.model and info.timestamp:
                            break
            except OSError:
                continue

            # Read tail of file for last message summary
            info.last_summary, info.last_role = _read_last_message(jsonl_file, stat.st_size)

            # Fallback to history index
            if not info.first_prompt and session_id in history_index:
                info.first_prompt = history_index[session_id]

            # Apply custom name
            if session_id in session_names:
                info.custom_name = session_names[session_id].get("name", "")

            sessions.append(info)

    # Sort by timestamp/mtime descending
    sessions.sort(key=lambda s: s.timestamp.timestamp() if s.timestamp else s.mtime, reverse=True)
    return sessions


TAIL_CHUNK_SIZE = 512 * 1024  # 512KB — enough for ~100 recent turns


def parse_session(file_path: Path) -> list[ConversationTurn]:
    """Parse recent turns from a session JSONL file.

    For files larger than TAIL_CHUNK_SIZE, only the tail is read.
    """
    turns: list[ConversationTurn] = []

    try:
        file_size = file_path.stat().st_size
        if file_size > TAIL_CHUNK_SIZE:
            lines = _read_tail_lines(file_path, file_size)
        else:
            with open(file_path) as f:
                lines = f.readlines()

        for line in lines:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = obj.get("type", "")

            if msg_type == "user":
                turn = _parse_user_message(obj)
                if turn:
                    turns.append(turn)

            elif msg_type == "assistant":
                turn = _parse_assistant_message(obj)
                if turn:
                    turns.append(turn)

            elif msg_type == "system":
                turn = _parse_system_message(obj)
                if turn:
                    turns.append(turn)

    except OSError as e:
        logger.error(f"Failed to parse session {file_path}: {e}")

    return turns


def _read_tail_lines(file_path: Path, file_size: int) -> list[str]:
    """Read the last TAIL_CHUNK_SIZE bytes and return complete lines."""
    with open(file_path, "rb") as f:
        f.seek(max(0, file_size - TAIL_CHUNK_SIZE))
        data = f.read().decode("utf-8", errors="replace")
    lines = data.splitlines(keepends=True)
    # Drop the first line (likely partial)
    if lines and file_size > TAIL_CHUNK_SIZE:
        lines = lines[1:]
    return lines


def _parse_user_message(obj: dict) -> ConversationTurn | None:
    """Parse a user-type JSONL entry."""
    msg = obj.get("message", {})
    content = msg.get("content", [])
    blocks: list[ContentBlock] = []

    # content can be a plain string
    if isinstance(content, str):
        cleaned = IDE_TAG_RE.sub("", content)
        cleaned = SYSTEM_REMINDER_RE.sub("", cleaned).strip()
        if cleaned:
            blocks.append(ContentBlock(block_type="text", text=cleaned))
        if not blocks:
            return None
        return ConversationTurn(role="user", content_blocks=blocks, timestamp=obj.get("timestamp", ""))

    is_only_tool_results = True

    for block in content:
        if isinstance(block, str):
            is_only_tool_results = False
            blocks.append(ContentBlock(block_type="text", text=block))
        elif isinstance(block, dict):
            btype = block.get("type", "")
            if btype == "text":
                text = block.get("text", "")
                # Skip IDE tags and system reminders for display
                cleaned = IDE_TAG_RE.sub("", text)
                cleaned = SYSTEM_REMINDER_RE.sub("", cleaned).strip()
                if cleaned:
                    is_only_tool_results = False
                    blocks.append(ContentBlock(block_type="text", text=cleaned))
            elif btype == "tool_result":
                tool_content = block.get("content", "")
                if isinstance(tool_content, list):
                    text_parts = []
                    for part in tool_content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            text_parts.append(part.get("text", ""))
                    tool_content = "\n".join(text_parts)
                elif not isinstance(tool_content, str):
                    tool_content = str(tool_content)
                blocks.append(
                    ContentBlock(
                        block_type="tool_result",
                        text=tool_content[:5000],  # Truncate very long outputs
                        is_error=block.get("is_error", False),
                    )
                )

    # Skip turns that are only tool results (they belong to the previous assistant turn)
    if is_only_tool_results and blocks:
        # Still include them but mark appropriately
        return ConversationTurn(
            role="tool_result",
            content_blocks=blocks,
            timestamp=obj.get("timestamp", ""),
        )

    if not blocks:
        return None

    return ConversationTurn(
        role="user",
        content_blocks=blocks,
        timestamp=obj.get("timestamp", ""),
    )


def _parse_assistant_message(obj: dict) -> ConversationTurn | None:
    """Parse an assistant-type JSONL entry."""
    msg = obj.get("message", {})
    content = msg.get("content", [])
    blocks: list[ContentBlock] = []

    # content can be a plain string
    if isinstance(content, str):
        if content.strip():
            blocks.append(ContentBlock(block_type="text", text=content))
        if not blocks:
            return None
        return ConversationTurn(
            role="assistant",
            content_blocks=blocks,
            model=msg.get("model", ""),
            timestamp=obj.get("timestamp", ""),
        )

    for block in content:
        if isinstance(block, str):
            blocks.append(ContentBlock(block_type="text", text=block))
        elif isinstance(block, dict):
            btype = block.get("type", "")
            if btype == "text":
                text = block.get("text", "")
                if text.strip():
                    blocks.append(ContentBlock(block_type="text", text=text))
            elif btype == "tool_use":
                tool_name = block.get("name", "unknown")
                tool_input = block.get("input", {})
                if isinstance(tool_input, dict):
                    desc = _extract_tool_description(tool_name, tool_input)
                    input_str = json.dumps(tool_input, indent=2)
                else:
                    desc = ""
                    input_str = str(tool_input)
                blocks.append(
                    ContentBlock(
                        block_type="tool_use",
                        tool_name=tool_name,
                        tool_input=input_str[:3000],
                        tool_description=desc,
                    )
                )
            elif btype == "thinking":
                text = block.get("thinking") or block.get("text") or ""
                if isinstance(text, str) and text.strip():
                    blocks.append(ContentBlock(block_type="thinking", text=text))

    if not blocks:
        return None

    return ConversationTurn(
        role="assistant",
        content_blocks=blocks,
        model=msg.get("model", ""),
        timestamp=obj.get("timestamp", ""),
    )


def _parse_system_message(obj: dict) -> ConversationTurn | None:
    """Parse a system-type JSONL entry."""
    subtype = obj.get("subtype", "")

    if subtype == "compact_boundary":
        return ConversationTurn(
            role="system",
            subtype=subtype,
            content_blocks=[ContentBlock(block_type="text", text="--- Conversation compacted ---")],
            timestamp=obj.get("timestamp", ""),
        )

    return None
