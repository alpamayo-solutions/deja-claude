"""Right panel: conversation preview rendered as a single Static."""

from __future__ import annotations

from rich.text import Text

from textual.containers import VerticalScroll
from textual.widgets import Label, Static

from ..models import ConversationTurn

MAX_RENDERED_TURNS = 40


class PreviewPane(VerticalScroll):
    """Scrollable preview pane rendering conversation as styled text."""

    BORDER_TITLE = "Preview"

    DEFAULT_CSS = """
    PreviewPane {
        overflow-y: auto;
    }
    PreviewPane .empty-state {
        color: $text-muted;
        text-style: italic;
        margin: 2 1;
    }
    PreviewPane Static {
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._show_tools = False
        self._show_thinking = False

    def show_empty(self, message: str = "Select a session to preview") -> None:
        self.remove_children()
        self.mount(Label(message, classes="empty-state"))

    def show_loading(self) -> None:
        self.remove_children()
        self.mount(Label("Loading...", classes="empty-state"))

    def render_turns(self, turns: list[ConversationTurn]) -> None:
        self.remove_children()

        if not turns:
            self.mount(Label("Empty session", classes="empty-state"))
            return

        # Filter turns
        visible = [t for t in turns if t.role in ("user", "assistant", "system")]
        total = len(visible)
        truncated = total > MAX_RENDERED_TURNS
        if truncated:
            visible = visible[-MAX_RENDERED_TURNS:]

        # Build a single Rich Text object
        output = Text()

        if truncated:
            output.append(f"[showing last {MAX_RENDERED_TURNS} of {total} turns]\n\n", style="italic dim")

        for turn in visible:
            if turn.role == "user":
                self._append_user(output, turn)
            elif turn.role == "assistant":
                self._append_assistant(output, turn)
            elif turn.role == "system":
                output.append("---\n\n", style="dim")

        self.mount(Static(output))
        self.scroll_home(animate=False)

    def _append_user(self, output: Text, turn: ConversationTurn) -> None:
        output.append("You\n", style="bold cyan")
        for block in turn.content_blocks:
            if block.block_type == "text":
                text = block.text[:2000]
                output.append(text)
                if not text.endswith("\n"):
                    output.append("\n")
        output.append("\n")

    def _append_assistant(self, output: Text, turn: ConversationTurn) -> None:
        label = f"Claude ({turn.model})\n" if turn.model else "Claude\n"
        output.append(label, style="bold green")
        for block in turn.content_blocks:
            if block.block_type == "text":
                text = block.text[:3000]
                output.append(text)
                if not text.endswith("\n"):
                    output.append("\n")
            elif block.block_type == "tool_use" and self._show_tools:
                desc = block.tool_description or "..."
                output.append(f"  [{block.tool_name}] {desc}\n", style="dim italic")
            elif block.block_type == "thinking" and self._show_thinking:
                output.append(f"  (thinking) {block.text[:200]}...\n", style="dim italic")
        output.append("\n")

    def toggle_tools(self) -> bool:
        self._show_tools = not self._show_tools
        return self._show_tools

    def toggle_thinking(self) -> bool:
        self._show_thinking = not self._show_thinking
        return self._show_thinking
