"""Log viewing screen."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from cli.services.lifecycle import ServiceLifecycle
from cli.services.models import ServiceConfig


class LogScreen(Screen[None]):
    """Screen for viewing service logs."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("q", "go_back", "Back"),
        Binding("f", "toggle_follow", "Follow"),
    ]

    def __init__(self, config: ServiceConfig) -> None:
        super().__init__()
        self.config = config
        self.lifecycle = ServiceLifecycle()
        self.following = False
        self._log_task: object | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(Static("Loading logs...", id="log-content"))
        yield Footer()

    async def on_mount(self) -> None:
        """Set the screen title and load initial logs."""
        self.sub_title = self.config.name
        await self._load_logs()

    async def _load_logs(self) -> None:
        """Load logs from the service."""
        log_widget = self.query_one("#log-content", Static)
        lines: list[str] = []

        async for line in self.lifecycle.logs(self.config, follow=False, tail=100):
            lines.append(line)

        if lines:
            log_widget.update("\n".join(lines))
        else:
            log_widget.update("[dim]No logs available[/dim]")

    def action_toggle_follow(self) -> None:
        """Toggle log following."""
        self.following = not self.following
        if self.following:
            self.notify("Following logs... (press f to stop)")
        else:
            self.notify("Stopped following logs")

    def action_go_back(self) -> None:
        """Go back to main screen."""
        self.app.pop_screen()

