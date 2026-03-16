"""Tests for the Textual app."""

import pytest

from deja_claude.app import DejaClaudeApp
from deja_claude.settings import DEFAULT_SETTINGS, save_settings


@pytest.fixture
def app_with_data(tmp_claude_dir):
    """Configure settings to use test data, return app instance."""
    save_settings(
        {
            **DEFAULT_SETTINGS,
            "claude_projects_path": str(tmp_claude_dir / "projects"),
            "claude_history_path": str(tmp_claude_dir / "history.jsonl"),
            "claude_sessions_path": str(tmp_claude_dir / "sessions"),
        }
    )
    return DejaClaudeApp()


@pytest.mark.asyncio
async def test_app_loads_sessions(app_with_data):
    async with app_with_data.run_test(size=(120, 40)) as pilot:
        for _ in range(5):
            await pilot.pause()
        assert len(app_with_data._sessions) == 3


@pytest.mark.asyncio
async def test_app_search_filters(app_with_data):
    async with app_with_data.run_test(size=(120, 40)) as pilot:
        for _ in range(5):
            await pilot.pause()

        # Open search
        await pilot.press("slash")
        await pilot.pause()

        # Type search term
        from textual.widgets import Input

        inp = app_with_data.query_one("#search-input", Input)
        inp.value = "health"
        await pilot.pause()

        table = app_with_data.query_one("#session-table")
        assert table.session_count == 1


@pytest.mark.asyncio
async def test_app_escape_clears_search(app_with_data):
    async with app_with_data.run_test(size=(120, 40)) as pilot:
        for _ in range(5):
            await pilot.pause()

        await pilot.press("slash")
        await pilot.pause()
        from textual.widgets import Input

        inp = app_with_data.query_one("#search-input", Input)
        inp.value = "health"
        await pilot.pause()

        await pilot.press("escape")
        await pilot.pause()

        table = app_with_data.query_one("#session-table")
        assert table.session_count == 3


@pytest.mark.asyncio
async def test_app_help_screen(app_with_data):
    async with app_with_data.run_test(size=(120, 40)) as pilot:
        for _ in range(5):
            await pilot.pause()

        await pilot.press("question_mark")
        await pilot.pause()
        assert len(app_with_data.screen_stack) > 1

        await pilot.press("escape")
        await pilot.pause()
        assert len(app_with_data.screen_stack) == 1


@pytest.mark.asyncio
async def test_app_left_right_navigation(app_with_data):
    async with app_with_data.run_test(size=(120, 40)) as pilot:
        for _ in range(5):
            await pilot.pause()

        # Focus sessions first
        app_with_data.query_one("#session-table").focus()
        await pilot.pause()

        # Press left -> projects
        await pilot.press("left")
        await pilot.pause()
        await pilot.pause()
        idx = app_with_data._get_focused_panel_index()
        assert idx == 0  # project-tree

        # Press right -> sessions
        await pilot.press("right")
        await pilot.pause()
        await pilot.pause()
        idx = app_with_data._get_focused_panel_index()
        assert idx == 1  # session-table
