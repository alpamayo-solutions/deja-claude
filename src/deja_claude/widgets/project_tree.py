"""Left panel: project tree with session counts."""

from __future__ import annotations

from collections import Counter

from textual.message import Message
from textual.widgets import Tree

from ..models import SessionInfo


class ProjectTree(Tree):
    """Tree widget showing projects and their session counts."""

    BORDER_TITLE = "Projects"

    class ProjectSelected(Message):
        """Posted when a project node is selected."""

        def __init__(self, project_name: str | None) -> None:
            super().__init__()
            self.project_name = project_name

    def __init__(self, **kwargs):
        super().__init__("All", **kwargs)
        self._sessions: list[SessionInfo] = []

    def populate(self, sessions: list[SessionInfo]) -> None:
        self._sessions = sessions
        self.clear()

        project_counts: Counter[str] = Counter()
        for s in sessions:
            project_counts[s.project_name] += 1

        self.root.set_label(f"All ({len(sessions)})")
        self.root.data = None  # None = show all

        for project, count in sorted(project_counts.items(), key=lambda x: -x[1]):
            node = self.root.add(f"{project} ({count})", data=project)
            node.allow_expand = False

        self.root.expand()

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Post a message when cursor moves to a project node."""
        self.post_message(self.ProjectSelected(event.node.data))

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Also filter on Enter for consistency."""
        self.post_message(self.ProjectSelected(event.node.data))
