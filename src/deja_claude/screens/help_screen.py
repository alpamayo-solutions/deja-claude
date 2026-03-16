"""Help screen showing keybindings."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Markdown

HELP_TEXT = """\
# deja-claude -- Keyboard Shortcuts

## Navigation
| Key | Action |
|-----|--------|
| `Tab` | Cycle focus between panels |
| `1` `2` `3` | Focus panel directly |
| `j` / `Down` | Move down |
| `k` / `Up` | Move up |
| `g` | Jump to top |
| `G` | Jump to bottom |

## Actions
| Key | Action |
|-----|--------|
| `o` / `Enter` | Open session in Claude Code |
| `d` | Delete session |
| `e` | Export session as Markdown |
| `r` | Rename session |
| `/` | Search / filter sessions |
| `Escape` | Clear search / close dialog |

## Display
| Key | Action |
|-----|--------|
| `t` | Toggle tool calls in preview |
| `w` | Toggle thinking blocks in preview |
| `R` | Refresh (rescan sessions) |
| `?` | Show this help |
| `q` | Quit |
"""


class HelpScreen(ModalScreen[None]):
    """Modal help screen."""

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }
    HelpScreen > Vertical {
        width: 70;
        height: 30;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    HelpScreen VerticalScroll {
        height: 1fr;
    }
    HelpScreen Button {
        margin-top: 1;
        dock: bottom;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            with VerticalScroll():
                yield Markdown(HELP_TEXT)
            yield Button("Close", variant="primary", id="close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def key_escape(self) -> None:
        self.dismiss(None)

    def key_question_mark(self) -> None:
        self.dismiss(None)
