"""Main Textual application for deja-claude."""

from __future__ import annotations

import os
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Input

from .actions import delete_session, export_session_markdown, get_open_command
from .models import SessionInfo
from .scanner import parse_session, scan_sessions
from .screens.confirm_screen import ConfirmScreen
from .screens.export_screen import ExportResultScreen
from .screens.help_screen import HelpScreen
from .screens.rename_screen import RenameScreen
from .settings import set_session_name
from .widgets.footer_bar import FooterBar
from .widgets.preview_pane import PreviewPane
from .widgets.project_tree import ProjectTree
from .widgets.session_table import SessionTable

CSS = """
#main-panels {
    layout: horizontal;
    height: 1fr;
}

#project-tree {
    width: 24;
    border: solid $surface-lighten-2;
}

#session-table {
    width: 1fr;
    border: solid $surface-lighten-2;
}

#preview-pane {
    width: 1fr;
    border: solid $surface-lighten-2;
}

#search-bar {
    height: 3;
    display: none;
    padding: 0 1;
    dock: bottom;
}

#search-bar.visible {
    display: block;
}

#search-input {
    width: 100%;
}

FooterBar {
    dock: bottom;
    height: 1;
}
"""


class DejaClaudeApp(App):
    """TUI session browser for Claude Code."""

    TITLE = "deja-claude"
    CSS = CSS

    BINDINGS = [
        Binding("q", "quit", "Quit", show=False),
        Binding("o", "open_session", "Open", show=False),
        Binding("enter", "open_session", "Open", show=False),
        Binding("d", "delete_session", "Delete", show=False),
        Binding("e", "export_session", "Export", show=False),
        Binding("r", "rename_session", "Rename", show=False),
        Binding("slash", "start_search", "Search", show=False),
        Binding("escape", "clear_search", "Clear", show=False),
        Binding("t", "toggle_tools", "Tools", show=False),
        Binding("w", "toggle_thinking", "Thinking", show=False),
        Binding("R", "refresh", "Refresh", show=False, key_display="R"),
        Binding("question_mark", "show_help", "Help", show=False),
        Binding("1", "focus_projects", "Projects", show=False),
        Binding("2", "focus_sessions", "Sessions", show=False),
        Binding("3", "focus_preview", "Preview", show=False),
    ]

    PANEL_IDS = ["project-tree", "session-table", "preview-pane"]

    def __init__(self, folder_filter: str = "", **kwargs):
        super().__init__(**kwargs)
        self._sessions: list[SessionInfo] = []
        self._current_session: SessionInfo | None = None
        self._search_active = False
        self._preview_timer = None
        self._ui_loaded = False
        self._folder_filter = folder_filter

    def compose(self) -> ComposeResult:
        with Horizontal(id="main-panels"):
            yield ProjectTree(id="project-tree")
            yield SessionTable(id="session-table")
            yield PreviewPane(id="preview-pane")
        yield Horizontal(
            Input(placeholder="Search sessions...", id="search-input"),
            id="search-bar",
        )
        yield FooterBar()

    def on_key(self, event) -> None:
        """Intercept left/right arrows for panel navigation."""
        if self._search_active:
            return
        if event.key == "left":
            idx = self._get_focused_panel_index()
            target = max(0, idx - 1) if idx > 0 else 0
            event.prevent_default()
            event.stop()
            self.set_timer(0.01, lambda: self.query_one(f"#{self.PANEL_IDS[target]}").focus())
        elif event.key == "right":
            idx = self._get_focused_panel_index()
            last = len(self.PANEL_IDS) - 1
            target = min(last, idx + 1) if idx >= 0 else 0
            event.prevent_default()
            event.stop()
            self.set_timer(0.01, lambda: self.query_one(f"#{self.PANEL_IDS[target]}").focus())

    def on_mount(self) -> None:
        self.run_worker(self._load_sessions, thread=True)  # type: ignore[arg-type]
        preview = self.query_one("#preview-pane", PreviewPane)
        preview.show_empty()

    async def _load_sessions(self) -> None:
        sessions = scan_sessions()
        self.call_from_thread(self._populate_ui, sessions)

    def _populate_ui(self, sessions: list[SessionInfo]) -> None:
        self._sessions = sessions

        # Apply folder filter if set
        if self._folder_filter:
            folder = os.path.realpath(self._folder_filter)
            sessions = [s for s in sessions if s.cwd and os.path.realpath(s.cwd).startswith(folder)]

        tree = self.query_one("#project-tree", ProjectTree)
        table = self.query_one("#session-table", SessionTable)
        tree.populate(sessions)
        table.set_sessions(sessions)
        if sessions:
            table.focus()
        self._ui_loaded = True

    def on_project_tree_project_selected(self, event: ProjectTree.ProjectSelected) -> None:
        """Handle project tree selection."""
        table = self.query_one("#session-table", SessionTable)
        table.filter_by_project(event.project_name)

    def on_data_table_row_highlighted(self, event: SessionTable.RowHighlighted) -> None:
        """Load preview when a row is highlighted, with debounce."""
        if not self._ui_loaded:
            return
        table = self.query_one("#session-table", SessionTable)
        session = table.get_selected_session()
        if session and session != self._current_session:
            self._current_session = session
            # Cancel pending preview load — debounce rapid scrolling
            if self._preview_timer is not None:
                self._preview_timer.stop()
            self._preview_timer = self.set_timer(  # type: ignore[assignment]
                0.15, lambda: self._start_preview_worker(session)
            )

    def _start_preview_worker(self, session: SessionInfo) -> None:
        """Start a worker to parse and render a session preview."""

        async def load() -> None:
            turns = parse_session(session.file_path)
            self.call_from_thread(self._render_preview, turns)

        self.run_worker(load, thread=True, exclusive=True, group="preview")  # type: ignore[arg-type]

    def _render_preview(self, turns) -> None:
        preview = self.query_one("#preview-pane", PreviewPane)
        preview.render_turns(turns)

    # --- Actions ---

    def action_open_session(self) -> None:
        table = self.query_one("#session-table", SessionTable)
        session = table.get_selected_session()
        if not session:
            self.notify("No session selected", severity="warning")
            return
        cmd = get_open_command(session)
        cwd = session.cwd if session.cwd and os.path.isdir(session.cwd) else None
        with self.suspend():
            if cwd:
                os.system(f"cd {cwd!r} && {cmd}")
            else:
                os.system(cmd)

    def action_delete_session(self) -> None:
        table = self.query_one("#session-table", SessionTable)
        session = table.get_selected_session()
        if not session:
            self.notify("No session selected", severity="warning")
            return

        name = session.display_name
        size = session.size_display

        def on_confirm(confirmed: bool) -> None:
            if confirmed:
                delete_session(session)
                self._sessions = [s for s in self._sessions if s.session_id != session.session_id]
                self._populate_ui(self._sessions)
                self.notify(f"Deleted: {name}")

        self.push_screen(
            ConfirmScreen(
                title="Delete Session",
                message=f"Delete '{name}'? ({size})\nThis cannot be undone.",
            ),
            on_confirm,  # type: ignore[arg-type]
        )

    def action_export_session(self) -> None:
        table = self.query_one("#session-table", SessionTable)
        session = table.get_selected_session()
        if not session:
            self.notify("No session selected", severity="warning")
            return

        async def do_export() -> None:
            turns = parse_session(session.file_path)
            path = export_session_markdown(session, turns)
            self.call_from_thread(self._show_export_result, path)

        self.run_worker(do_export, thread=True)  # type: ignore[arg-type]

    def _show_export_result(self, path) -> None:
        self.push_screen(ExportResultScreen(path))

    def action_rename_session(self) -> None:
        table = self.query_one("#session-table", SessionTable)
        session = table.get_selected_session()
        if not session:
            self.notify("No session selected", severity="warning")
            return

        def on_rename(new_name: str) -> None:
            if new_name != session.custom_name:
                set_session_name(session.session_id, new_name)
                session.custom_name = new_name
                # Rebuild table to show new name
                table = self.query_one("#session-table", SessionTable)
                table._apply_filters()
                self.notify(f"Renamed to: {new_name}" if new_name else "Name cleared")

        self.push_screen(
            RenameScreen(current_name=session.custom_name or session.display_name),
            on_rename,  # type: ignore[arg-type]
        )

    def action_start_search(self) -> None:
        search_bar = self.query_one("#search-bar")
        search_bar.add_class("visible")
        search_input = self.query_one("#search-input", Input)
        search_input.focus()
        self._search_active = True

    def action_clear_search(self) -> None:
        if self._search_active:
            search_bar = self.query_one("#search-bar")
            search_bar.remove_class("visible")
            search_input = self.query_one("#search-input", Input)
            search_input.value = ""
            self._search_active = False
            table = self.query_one("#session-table", SessionTable)
            table.filter_by_search("")
            table.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input":
            table = self.query_one("#session-table", SessionTable)
            table.filter_by_search(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "search-input":
            # Move focus to session table
            table = self.query_one("#session-table", SessionTable)
            table.focus()

    def action_toggle_tools(self) -> None:
        preview = self.query_one("#preview-pane", PreviewPane)
        showing = preview.toggle_tools()
        self.notify(f"Tool calls: {'shown' if showing else 'hidden'}")
        if self._current_session:
            self._start_preview_worker(self._current_session)

    def action_toggle_thinking(self) -> None:
        preview = self.query_one("#preview-pane", PreviewPane)
        showing = preview.toggle_thinking()
        self.notify(f"Thinking blocks: {'shown' if showing else 'hidden'}")
        if self._current_session:
            self._start_preview_worker(self._current_session)

    def action_refresh(self) -> None:
        self.notify("Scanning sessions...")
        self._current_session = None
        preview = self.query_one("#preview-pane", PreviewPane)
        preview.show_empty("Refreshing...")
        self.run_worker(self._load_sessions, thread=True)  # type: ignore[arg-type]

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_focus_projects(self) -> None:
        self.query_one("#project-tree", ProjectTree).focus()

    def action_focus_sessions(self) -> None:
        self.query_one("#session-table", SessionTable).focus()

    def action_focus_preview(self) -> None:
        self.query_one("#preview-pane", PreviewPane).focus()

    def _get_focused_panel_index(self) -> int:
        focused = self.focused
        if focused is None:
            return -1
        # Walk up the DOM to find which panel contains the focused widget
        node: Any = focused
        while node is not None:
            if hasattr(node, "id") and node.id in self.PANEL_IDS:
                return self.PANEL_IDS.index(node.id)
            node = node.parent
        return -1

    def action_focus_left(self) -> None:
        idx = self._get_focused_panel_index()
        target = max(0, idx - 1) if idx > 0 else 0
        self.query_one(f"#{self.PANEL_IDS[target]}").focus()

    def action_focus_right(self) -> None:
        idx = self._get_focused_panel_index()
        last = len(self.PANEL_IDS) - 1
        target = min(last, idx + 1) if idx >= 0 else 0
        self.query_one(f"#{self.PANEL_IDS[target]}").focus()
