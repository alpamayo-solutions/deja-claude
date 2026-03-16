"""Bottom bar: keybinding hints."""

from __future__ import annotations

from textual.widgets import Static


class FooterBar(Static):
    """Static footer showing available keybindings."""

    DEFAULT_CSS = """
    FooterBar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs):
        hints = (
            " o:open  d:delete  e:export  r:rename  /:search  t:tools  w:thinking  R:refresh  ?:help  q:quit"
        )
        super().__init__(hints, **kwargs)
