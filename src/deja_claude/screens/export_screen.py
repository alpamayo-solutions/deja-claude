"""Export confirmation/status screen."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class ExportResultScreen(ModalScreen[None]):
    """Shows the result of an export operation."""

    DEFAULT_CSS = """
    ExportResultScreen {
        align: center middle;
    }
    ExportResultScreen > Vertical {
        width: 70;
        height: auto;
        max-height: 12;
        border: thick $success;
        background: $surface;
        padding: 1 2;
    }
    ExportResultScreen .title {
        text-style: bold;
        margin-bottom: 1;
    }
    ExportResultScreen .path {
        color: $accent;
        margin-bottom: 1;
    }
    ExportResultScreen Button {
        margin-top: 1;
    }
    """

    def __init__(self, output_path: Path, **kwargs):
        super().__init__(**kwargs)
        self._output_path = output_path

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Exported Successfully", classes="title")
            yield Static(str(self._output_path), classes="path")
            yield Button("OK", variant="primary", id="ok")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def key_escape(self) -> None:
        self.dismiss(None)

    def key_enter(self) -> None:
        self.dismiss(None)
