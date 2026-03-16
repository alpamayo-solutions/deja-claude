"""Entry point for deja-claude."""

import argparse

from .app import DejaClaudeApp
from .settings import load_settings


def main():
    parser = argparse.ArgumentParser(description="TUI browser for Claude Code sessions")
    parser.add_argument(
        "folder",
        nargs="?",
        default=None,
        help="Filter sessions to this project folder (default: from settings or show all)",
    )
    args = parser.parse_args()

    folder = args.folder or load_settings().get("default_folder", "")

    app = DejaClaudeApp(folder_filter=folder)
    try:
        app.run()
    except (ValueError, EOFError):
        # Suppress Textual/Rich shutdown serialization errors
        pass


if __name__ == "__main__":
    main()
