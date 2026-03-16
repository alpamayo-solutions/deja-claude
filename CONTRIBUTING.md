# Contributing to deja-claude

## Development Setup

```bash
git clone https://github.com/alpamayo-solutions/deja-claude.git
cd deja-claude
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Running Checks

```bash
make lint        # ruff check + format check
make typecheck   # mypy
make test        # pytest with coverage
make all         # lint + typecheck + test
```

## Code Style

- Python 3.10+ with type annotations on all public functions
- Formatted and linted with [ruff](https://docs.astral.sh/ruff/)
- Type-checked with [mypy](https://mypy-lang.org/)
- Line length: 110 characters

## Pull Requests

1. Fork the repository and create a feature branch
2. Make your changes
3. Ensure all checks pass: `make all`
4. Write tests for new functionality
5. Submit a PR with a clear description of the change

## Architecture

```
src/deja_claude/
├── __main__.py      # CLI entry point, argument parsing
├── app.py           # Main Textual App, keybindings, panel layout
├── scanner.py       # JSONL parsing: fast index scan + lazy full parse
├── models.py        # Data models: SessionInfo, ConversationTurn, ContentBlock
├── actions.py       # Session operations: delete, export, open
├── settings.py      # Config + metadata persistence (~/.config/deja-claude/)
├── screens/         # Modal dialogs (help, confirm, rename, export result)
└── widgets/         # Textual widgets (preview pane, session table, project tree, footer)
```

**Key design decisions:**
- **Index scan** reads only the first ~50 lines and last 64KB of each JSONL file for fast startup
- **Preview** reads only the last 512KB, rendering the last 40 turns
- **Worker threads** keep the UI responsive during file I/O
- **Debounced preview loading** prevents unnecessary parsing during rapid scrolling

## Reporting Issues

Use [GitHub Issues](https://github.com/alpamayo-solutions/deja-claude/issues) with the provided templates.
