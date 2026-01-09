"""Main Textual application for Tools CLI."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Footer, Header, ListItem, ListView, Static

from cli.services.health import HealthMonitor
from cli.services.lifecycle import ServiceLifecycle
from cli.services.models import ServiceConfig, ServiceStatus
from cli.services.registry import ServiceRegistry


class ServiceItem(ListItem):
    """A selectable service item in the list."""

    def __init__(self, config: ServiceConfig) -> None:
        super().__init__()
        self.config = config
        self.status = ServiceStatus.NOT_INSTALLED

    def compose(self) -> ComposeResult:
        yield Static(self._format_row(), id=f"row-{self.config.dir_name}")

    def _format_row(self) -> str:
        """Format the service row as a string."""
        symbol = self.status.symbol
        color = self.status.color
        name = self.config.name
        desc = self.config.description
        if len(desc) > 35:
            desc = desc[:35] + "..."
        return f"[{color}]{symbol}[/{color}]  {name:<18} {desc}"

    def update_status(self, status: ServiceStatus) -> None:
        """Update the service status and refresh display."""
        import contextlib

        self.status = status
        with contextlib.suppress(Exception):
            # Widget may not be mounted yet
            self.query_one(f"#row-{self.config.dir_name}", Static).update(
                self._format_row()
            )


class ServiceListView(ListView):
    """ListView of services with selection."""

    def __init__(self) -> None:
        super().__init__()
        self.registry = ServiceRegistry()
        self.health_monitor = HealthMonitor()
        self.lifecycle = ServiceLifecycle()
        self.service_items: dict[str, ServiceItem] = {}

    def compose(self) -> ComposeResult:
        services = self.registry.discover()
        for config in services:
            item = ServiceItem(config)
            self.service_items[config.dir_name] = item
            yield item

    def get_selected_config(self) -> ServiceConfig | None:
        """Get the currently selected service config."""
        if self.highlighted_child is None:
            return None
        if isinstance(self.highlighted_child, ServiceItem):
            return self.highlighted_child.config
        return None

    def get_selected_item(self) -> ServiceItem | None:
        """Get the currently selected service item."""
        if isinstance(self.highlighted_child, ServiceItem):
            return self.highlighted_child
        return None

    async def refresh_status(self) -> None:
        """Refresh health status for all services."""
        services = list(self.registry._cache.values())
        if not services:
            services = self.registry.discover()

        statuses = await self.health_monitor.check_all(services)

        for dir_name, status in statuses.items():
            if dir_name in self.service_items:
                self.service_items[dir_name].update_status(status)



class ToolsApp(App[None]):
    """Tools Manager TUI Application."""

    TITLE = "Tools Manager"
    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        padding: 1 2;
    }

    #header-text {
        text-style: bold;
        margin-bottom: 1;
    }

    #help-text {
        margin-top: 1;
        color: $text-muted;
    }

    ServiceListView {
        height: auto;
        max-height: 20;
        border: solid $primary;
        padding: 0 1;
    }

    ServiceItem {
        padding: 0;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("s", "start", "Start"),
        Binding("S", "stop", "Stop", key_display="S"),
        Binding("R", "restart", "Restart", key_display="R"),
        Binding("i", "install", "Install"),
        Binding("l", "logs", "Logs"),
        Binding("c", "config", "Config"),
        Binding("?", "help", "Help"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("[bold]Services[/bold]", id="header-text"),
            ServiceListView(),
            id="main-container",
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Called when app is mounted - refresh status."""
        self.notify("Loading services...")
        await self._refresh_services()
        self.notify("Ready", timeout=1)

    async def action_refresh(self) -> None:
        """Refresh service status."""
        self.notify("Refreshing...")
        await self._refresh_services()
        self.notify("Refreshed", timeout=1)

    async def _refresh_services(self) -> None:
        """Refresh all service statuses."""
        service_list = self.query_one(ServiceListView)
        await service_list.refresh_status()

    def _get_selected(self) -> tuple[ServiceListView, ServiceConfig | None]:
        """Get the service list and selected config."""
        service_list = self.query_one(ServiceListView)
        config = service_list.get_selected_config()
        return service_list, config

    def _get_missing_required_env_vars(self, config: ServiceConfig) -> list[str]:
        """Check for missing required environment variables."""
        from cli.screens.config_editor import load_env_file

        env_path = config.path / ".env"
        current_env = load_env_file(env_path)
        missing: list[str] = []
        for env_config in config.env_vars:
            if env_config.required and not current_env.get(env_config.name):
                missing.append(env_config.name)
        return missing

    def action_start(self) -> None:
        """Start the selected service."""
        service_list, config = self._get_selected()
        if config is None:
            self.notify("No service selected", severity="warning")
            return

        # Check for missing required env vars
        missing = self._get_missing_required_env_vars(config)
        if missing:
            self._show_setup_wizard(config, missing)
            return

        self.notify(f"Starting {config.name}...", timeout=30)
        self.run_worker(
            self._do_lifecycle_action(service_list, config, "start"),
            name=f"start-{config.dir_name}",
            exclusive=True,
        )

    def _show_setup_wizard(self, config: ServiceConfig, missing: list[str]) -> None:
        """Show the setup wizard for missing configuration."""
        from cli.screens.setup_wizard import SetupWizardScreen

        def on_wizard_complete(result: bool | None) -> None:
            if result:
                # Retry start after successful setup
                self.action_start()

        self.push_screen(SetupWizardScreen(config, missing), on_wizard_complete)

    def action_stop(self) -> None:
        """Stop the selected service."""
        service_list, config = self._get_selected()
        if config is None:
            self.notify("No service selected", severity="warning")
            return

        self.notify(f"Stopping {config.name}...", timeout=30)
        self.run_worker(
            self._do_lifecycle_action(service_list, config, "stop"),
            name=f"stop-{config.dir_name}",
            exclusive=True,
        )

    def action_restart(self) -> None:
        """Restart the selected service."""
        service_list, config = self._get_selected()
        if config is None:
            self.notify("No service selected", severity="warning")
            return

        self.notify(f"Restarting {config.name}...", timeout=30)
        self.run_worker(
            self._do_lifecycle_action(service_list, config, "restart"),
            name=f"restart-{config.dir_name}",
            exclusive=True,
        )

    async def _do_lifecycle_action(
        self,
        service_list: ServiceListView,
        config: ServiceConfig,
        action: str,
    ) -> None:
        """Execute a lifecycle action in a worker."""
        lifecycle = service_list.lifecycle

        if action == "start":
            success, message = await lifecycle.start(config)
        elif action == "stop":
            success, message = await lifecycle.stop(config)
        elif action == "restart":
            success, message = await lifecycle.restart(config)
        else:
            success, message = False, f"Unknown action: {action}"

        if success:
            self.notify(f"✅ {config.name} {action}ed", timeout=3)
        else:
            self.notify(f"❌ Failed: {message}", severity="error", timeout=5)

        await self._refresh_services()

    def action_install(self) -> None:
        """Install/update the selected service."""
        service_list, config = self._get_selected()
        if config is None:
            self.notify("No service selected", severity="warning")
            return

        self.notify(f"Installing {config.name}... (this may take a while)", timeout=120)
        self.run_worker(
            self._do_install(service_list, config),
            name=f"install-{config.dir_name}",
            exclusive=True,
        )

    async def _do_install(
        self, service_list: ServiceListView, config: ServiceConfig
    ) -> None:
        """Execute install in a worker."""
        lines: list[str] = []
        async for line in service_list.lifecycle.install(config):
            lines.append(line)

        if lines:
            last_line = lines[-1]
            if "✅" in last_line:
                self.notify(last_line, timeout=5)
            else:
                self.notify(f"Install: {last_line}", timeout=5)

        await self._refresh_services()

    async def action_logs(self) -> None:
        """View logs for the selected service."""
        from cli.screens.logs import LogScreen

        _, config = self._get_selected()
        if config is None:
            self.notify("No service selected", severity="warning")
            return

        self.push_screen(LogScreen(config))

    async def action_config(self) -> None:
        """Open configuration editor for the selected service."""
        from cli.screens.config_editor import ConfigEditorScreen

        _, config = self._get_selected()
        if config is None:
            self.notify("No service selected", severity="warning")
            return

        if not config.env_vars:
            self.notify(f"{config.name} has no configurable env vars", timeout=3)
            return

        self.push_screen(ConfigEditorScreen(config))

    def action_help(self) -> None:
        """Show help."""
        self.notify(
            "Keys: ↑↓=Navigate s=Start S=Stop R=Restart i=Install l=Logs c=Config q=Quit",
            timeout=5,
        )
