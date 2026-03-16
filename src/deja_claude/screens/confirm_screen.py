"""Delete confirmation dialog."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class ConfirmScreen(ModalScreen[bool]):
    """Modal confirmation dialog."""

    DEFAULT_CSS = """
    ConfirmScreen {
        align: center middle;
    }
    ConfirmScreen > Vertical {
        width: 60;
        height: auto;
        max-height: 16;
        border: thick $error;
        background: $surface;
        padding: 1 2;
    }
    ConfirmScreen .title {
        text-style: bold;
        margin-bottom: 1;
    }
    ConfirmScreen .message {
        margin-bottom: 1;
    }
    ConfirmScreen Horizontal {
        align: right middle;
        height: 3;
    }
    ConfirmScreen Button {
        margin-left: 1;
    }
    """

    def __init__(self, title: str, message: str, **kwargs):
        super().__init__(**kwargs)
        self._title = title
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self._title, classes="title")
            yield Static(self._message, classes="message")
            with Horizontal():
                yield Button("Cancel", variant="default", id="cancel")
                yield Button("Delete", variant="error", id="confirm")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm")

    def key_escape(self) -> None:
        self.dismiss(False)

    def key_y(self) -> None:
        self.dismiss(True)

    def key_n(self) -> None:
        self.dismiss(False)
