"""Configuration editor screen for service environment variables."""

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Label, Static

from cli.services.models import EnvVarConfig, ServiceConfig


def load_env_file(path: Path) -> dict[str, str]:
    """Load environment variables from a .env file."""
    env_vars: dict[str, str] = {}
    if not path.exists():
        return env_vars
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                # Remove quotes if present
                value = value.strip()
                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]
                env_vars[key.strip()] = value
    return env_vars


def save_env_file(path: Path, env_vars: dict[str, str]) -> None:
    """Save environment variables to a .env file."""
    lines: list[str] = []
    for key, value in sorted(env_vars.items()):
        # Quote values with spaces or special characters
        if " " in value or "=" in value or '"' in value:
            value = f'"{value}"'
        lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n")


def mask_value(value: str) -> str:
    """Mask a secret value for display."""
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return value[:4] + "*" * (len(value) - 8) + value[-4:]


class EnvVarInput(Static):
    """A single environment variable input row."""

    def __init__(
        self, env_config: EnvVarConfig, current_value: str, input_id: str
    ) -> None:
        super().__init__()
        self.env_config = env_config
        self.current_value = current_value
        self.input_id = input_id

    def compose(self) -> ComposeResult:
        required_marker = "[red]*[/red]" if self.env_config.required else ""
        label_text = f"{self.env_config.name}{required_marker}"
        if self.env_config.description:
            label_text += f" [dim]({self.env_config.description})[/dim]"
        yield Label(label_text)
        yield Input(
            value=self.current_value,
            placeholder=self.env_config.default or "",
            password=self.env_config.secret,
            id=self.input_id,
        )


class ConfigEditorScreen(Screen[bool]):
    """Screen for editing service configuration (.env file)."""

    CSS = """
    ConfigEditorScreen {
        background: $surface;
    }

    #config-container {
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

    EnvVarInput {
        height: auto;
        margin-bottom: 1;
    }

    EnvVarInput Label {
        margin-bottom: 0;
    }

    EnvVarInput Input {
        margin-top: 0;
    }

    #button-row {
        margin-top: 1;
        height: auto;
    }

    Button {
        margin-right: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "save", "Save"),
    ]

    def __init__(self, config: ServiceConfig) -> None:
        super().__init__()
        self.config = config
        self.env_path = config.path / ".env"
        self.current_env = load_env_file(self.env_path)

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(
            Static(
                f"[bold]Configure {self.config.name}[/bold]",
                id="header-text",
            ),
            *self._compose_env_inputs(),
            Static(
                "[dim]Ctrl+S to save, Escape to cancel. [red]*[/red] = required[/dim]",
                id="help-text",
            ),
            id="config-container",
        )
        yield Footer()

    def _compose_env_inputs(self) -> list[EnvVarInput]:
        """Create input widgets for each env var."""
        inputs: list[EnvVarInput] = []
        for env_config in self.config.env_vars:
            current_value = self.current_env.get(env_config.name, "")
            input_id = f"env-{env_config.name}"
            inputs.append(EnvVarInput(env_config, current_value, input_id))
        return inputs

    async def on_mount(self) -> None:
        """Set the screen title."""
        self.sub_title = f"{self.config.name} Configuration"

    def _get_env_values(self) -> dict[str, str]:
        """Collect current values from all input fields."""
        values: dict[str, str] = {}
        for env_config in self.config.env_vars:
            input_id = f"env-{env_config.name}"
            try:
                input_widget = self.query_one(f"#{input_id}", Input)
                value = input_widget.value.strip()
                if value:
                    values[env_config.name] = value
            except Exception:
                pass
        return values

    def _validate_required(self) -> list[str]:
        """Check that all required env vars have values. Returns missing var names."""
        missing: list[str] = []
        values = self._get_env_values()
        for env_config in self.config.env_vars:
            if env_config.required and not values.get(env_config.name):
                missing.append(env_config.name)
        return missing

    def action_save(self) -> None:
        """Save the configuration."""
        missing = self._validate_required()
        if missing:
            self.notify(
                f"Missing required: {', '.join(missing)}", severity="error", timeout=5
            )
            return

        values = self._get_env_values()
        # Merge with existing env vars (preserve vars not in service.yaml)
        merged = dict(self.current_env)
        for env_config in self.config.env_vars:
            if env_config.name in values:
                merged[env_config.name] = values[env_config.name]
            elif env_config.name in merged and env_config.name not in values:
                # Remove if cleared
                del merged[env_config.name]

        save_env_file(self.env_path, merged)
        self.notify(f"Saved to {self.env_path.name}", timeout=3)
        self.dismiss(True)

    def action_cancel(self) -> None:
        """Cancel and go back."""
        self.dismiss(False)

