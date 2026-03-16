# deja-claude

[![CI](https://github.com/alpamayo-solutions/deja-claude/actions/workflows/ci.yml/badge.svg)](https://github.com/alpamayo-solutions/deja-claude/actions/workflows/ci.yml)

A keyboard-driven TUI for browsing, previewing, and managing [Claude Code](https://docs.anthropic.com/en/docs/claude-code) conversation sessions.

Claude Code stores every conversation as JSONL files in `~/.claude/projects/`. With hundreds of sessions, there's no good way to browse, search, preview, or manage them. **deja-claude** gives you a lazydocker-style interface to navigate your session history.

## Installation

**With pipx (recommended):**

```bash
pipx install git+https://github.com/alpamayo-solutions/deja-claude.git
```

**With pip:**

```bash
pip install git+https://github.com/alpamayo-solutions/deja-claude.git
```

**From source:**

```bash
git clone https://github.com/alpamayo-solutions/deja-claude.git
cd deja-claude
pip install -e .
```

## Usage

```bash
deja-claude                          # browse all sessions
deja-claude /path/to/project         # filter to sessions from that folder
```

The optional path argument filters sessions to only those whose working directory matches the given folder. Without it, the `default_folder` from settings is used (defaults to `~`, which shows everything).

The interface has three panels:

- **Left:** Project tree with session counts -- navigate to filter instantly
- **Center:** Session list -- searchable, shows last message from each session
- **Right:** Conversation preview with styled text

## Keyboard Shortcuts

### Navigation

| Key | Action |
|-----|--------|
| `Left` / `Right` | Move focus between panels |
| `Tab` | Cycle focus between panels |
| `1` `2` `3` | Focus panel directly |
| `Up` / `Down` | Navigate within a panel |

### Actions

| Key | Action |
|-----|--------|
| `o` / `Enter` | Open session in Claude Code (resumes in the original directory) |
| `d` | Delete session (with confirmation) |
| `e` | Export session as Markdown |
| `r` | Rename session (persisted across restarts) |
| `/` | Search / filter sessions |
| `Escape` | Clear search / close dialog |

### Display

| Key | Action |
|-----|--------|
| `t` | Toggle tool calls in preview |
| `w` | Toggle thinking blocks in preview |
| `R` | Refresh (rescan sessions) |
| `?` | Help |
| `q` | Quit |

## Configuration

Settings are stored in `~/.config/deja-claude/settings.json`:

```json
{
    "default_folder": "~",
    "show_tool_messages": false,
    "show_thinking": false,
    "sort_by": "date",
    "sort_descending": true,
    "export_dir": "~/Desktop"
}
```

| Setting | Description |
|---------|-------------|
| `default_folder` | Default project folder to filter sessions (overridden by CLI argument) |
| `show_tool_messages` | Show tool calls in preview by default |
| `show_thinking` | Show thinking blocks in preview by default |
| `export_dir` | Directory for exported Markdown files |

Session names (set with `r`) are stored in `~/.config/deja-claude/metadata.json` and persist across restarts.

## How It Works

**Index scan (~100ms at startup):**
- Walks `~/.claude/projects/*/` for JSONL files
- Reads head + tail of each file to extract metadata and last message
- Cross-references with `~/.claude/history.jsonl` for fallback display text

**Preview (on session select):**
- Reads the last 512KB of the file (handles 40MB+ sessions without lag)
- Renders the last 40 turns as styled text in a single widget
- Debounced to stay responsive during rapid scrolling

**Open in terminal:**
- `cd`s into the session's original working directory
- Runs `claude -r {session_id}` via Textual's `app.suspend()`
- When the Claude session ends, deja-claude resumes automatically

## Requirements

- Python 3.10+
- [Textual](https://textual.textualize.io/) (installed automatically)

## License

MIT
