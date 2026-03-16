"""Rename session dialog."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class RenameScreen(ModalScreen[str]):
    """Modal dialog for renaming a session."""

    DEFAULT_CSS = """
    RenameScreen {
        align: center middle;
    }
    RenameScreen > Vertical {
        width: 60;
        height: auto;
        max-height: 14;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    RenameScreen .title {
        text-style: bold;
        margin-bottom: 1;
    }
    RenameScreen Input {
        margin-bottom: 1;
    }
    RenameScreen Horizontal {
        align: right middle;
        height: 3;
    }
    RenameScreen Button {
        margin-left: 1;
    }
    """

    def __init__(self, current_name: str, **kwargs):
        super().__init__(**kwargs)
        self._current_name = current_name

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Rename Session", classes="title")
            yield Input(value=self._current_name, placeholder="Enter session name...", id="name-input")
            with Horizontal():
                yield Button("Cancel", variant="default", id="cancel")
                yield Button("Clear", variant="warning", id="clear")
                yield Button("Save", variant="primary", id="save")

    def on_mount(self) -> None:
        self.query_one("#name-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            value = self.query_one("#name-input", Input).value
            self.dismiss(value)
        elif event.button.id == "clear":
            self.dismiss("")
        else:
            self.dismiss(self._current_name)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    def key_escape(self) -> None:
        self.dismiss(self._current_name)
