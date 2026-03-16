"""Center panel: session DataTable with sorting and filtering."""

from __future__ import annotations

from textual.widgets import DataTable

from ..models import SessionInfo


class SessionTable(DataTable):
    """DataTable showing sessions with date, project, and first prompt."""

    BORDER_TITLE = "Sessions"

    def __init__(self, **kwargs):
        super().__init__(cursor_type="row", zebra_stripes=True, **kwargs)
        self._sessions: list[SessionInfo] = []
        self._filtered: list[SessionInfo] = []
        self._project_filter: str | None = None
        self._search_filter: str = ""

    def on_mount(self) -> None:
        self.add_column("Date", key="date", width=18)
        self.add_column("Project", key="project", width=14)
        self.add_column("Session", key="session")

    def set_sessions(self, sessions: list[SessionInfo]) -> None:
        self._sessions = sessions
        self._apply_filters()

    def filter_by_project(self, project_name: str | None) -> None:
        self._project_filter = project_name
        self._apply_filters()

    def filter_by_search(self, search: str) -> None:
        self._search_filter = search.lower().strip()
        self._apply_filters()

    def _apply_filters(self) -> None:
        filtered = self._sessions

        if self._project_filter:
            filtered = [s for s in filtered if s.project_name == self._project_filter]

        if self._search_filter:
            term = self._search_filter
            filtered = [
                s for s in filtered
                if term in s.display_name.lower()
                or term in s.first_prompt.lower()
                or term in s.last_summary.lower()
                or term in s.project_name.lower()
                or term in s.slug.lower()
                or term in s.custom_name.lower()
            ]

        self._filtered = filtered
        self._rebuild_table()

    def _rebuild_table(self) -> None:
        self.clear()
        for session in self._filtered:
            label = session.display_name
            if session.is_active:
                label = f"* {label}"
            elif session.last_role == "user":
                label = f"> {label}"
            elif session.last_role == "assistant":
                label = f"< {label}"
            self.add_row(
                session.display_date,
                session.project_name,
                label,
                key=session.session_id,
            )

    def get_selected_session(self) -> SessionInfo | None:
        if not self._filtered:
            return None
        try:
            row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
            for s in self._filtered:
                if s.session_id == row_key.value:
                    return s
        except Exception:
            pass
        # Fallback to cursor row index
        idx = self.cursor_coordinate.row
        if 0 <= idx < len(self._filtered):
            return self._filtered[idx]
        return None

    @property
    def session_count(self) -> int:
        return len(self._filtered)
