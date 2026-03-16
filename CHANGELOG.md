# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Type checking with mypy in CI
- Test coverage reporting
- Pre-commit hooks for linting and formatting
- PyPI publishing workflow
- `CHANGELOG.md`, `CONTRIBUTING.md`, and issue templates
- `py.typed` marker for PEP 561 compliance
- Safety check in delete action to prevent deletion outside `~/.claude/`

### Changed
- CI now tests on macOS in addition to Ubuntu
- CI now validates formatting with `ruff format --check`
- Expanded `pyproject.toml` with classifiers, URLs, and mypy config

## [0.1.0] - 2026-03-16

### Added
- Three-panel TUI: project tree, session list, conversation preview
- Fast index scan (~100ms startup) reading head + tail of JSONL files
- Efficient preview rendering for 40MB+ sessions via tail-chunk reading
- Session management: delete, export to Markdown, rename, open in Claude Code
- Display toggles for tool calls and thinking blocks
- Keyboard-driven navigation with vim-like bindings
- Search and filter functionality
- Session name persistence in `~/.config/deja-claude/metadata.json`

[Unreleased]: https://github.com/alpamayo-solutions/deja-claude/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/alpamayo-solutions/deja-claude/releases/tag/v0.1.0
