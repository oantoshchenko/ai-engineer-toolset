"""First-run setup wizard for services with missing required configuration."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static

from cli.screens.config_editor import load_env_file, save_env_file
from cli.services.models import EnvVarConfig, ServiceConfig


class WizardEnvInput(Static):
    """A single environment variable input for the wizard."""

    def __init__(
        self, env_config: EnvVarConfig, current_value: str, input_id: str
    ) -> None:
        super().__init__()
        self.env_config = env_config
        self.current_value = current_value
        self.input_id = input_id

    def compose(self) -> ComposeResult:
        label_text = f"[bold]{self.env_config.name}[/bold]"
        if self.env_config.description:
            label_text += f"\n[dim]{self.env_config.description}[/dim]"
        yield Label(label_text)
        yield Input(
            value=self.current_value,
            placeholder=self.env_config.default or "Enter value...",
            password=self.env_config.secret,
            id=self.input_id,
        )


class SetupWizardScreen(Screen[bool]):
    """Wizard screen for initial service setup when required env vars are missing."""

    CSS = """
    SetupWizardScreen {
        background: $surface;
    }

    #wizard-container {
        padding: 2 4;
        max-width: 80;
    }

    #title {
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }

    #subtitle {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }

    WizardEnvInput {
        height: auto;
        margin-bottom: 1;
        padding: 1;
        border: solid $primary-darken-2;
    }

    WizardEnvInput Label {
        margin-bottom: 0;
    }

    WizardEnvInput Input {
        margin-top: 1;
    }

    #button-container {
        margin-top: 2;
        height: auto;
        align: center middle;
    }

    Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "save", "Save & Continue"),
    ]

    def __init__(self, config: ServiceConfig, missing_vars: list[str]) -> None:
        super().__init__()
        self.config = config
        self.missing_vars = missing_vars
        self.env_path = config.path / ".env"
        self.current_env = load_env_file(self.env_path)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Center(
            VerticalScroll(
                Static(f"🔧 Setup {self.config.name}", id="title"),
                Static(
                    "The following configuration is required before starting:",
                    id="subtitle",
                ),
                *self._compose_missing_inputs(),
                Center(
                    Button("Save & Continue", variant="primary", id="save-btn"),
                    Button("Cancel", variant="default", id="cancel-btn"),
                    id="button-container",
                ),
                id="wizard-container",
            )
        )
        yield Footer()

    def _compose_missing_inputs(self) -> list[WizardEnvInput]:
        """Create input widgets for missing required env vars."""
        inputs: list[WizardEnvInput] = []
        for env_config in self.config.env_vars:
            if env_config.name in self.missing_vars:
                current_value = self.current_env.get(env_config.name, "")
                input_id = f"wizard-{env_config.name}"
                inputs.append(WizardEnvInput(env_config, current_value, input_id))
        return inputs

    async def on_mount(self) -> None:
        """Set the screen title."""
        self.sub_title = "Initial Setup"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save-btn":
            self.action_save()
        elif event.button.id == "cancel-btn":
            self.action_cancel()

    def _get_wizard_values(self) -> dict[str, str]:
        """Collect values from wizard input fields."""
        values: dict[str, str] = {}
        for var_name in self.missing_vars:
            input_id = f"wizard-{var_name}"
            try:
                input_widget = self.query_one(f"#{input_id}", Input)
                value = input_widget.value.strip()
                if value:
                    values[var_name] = value
            except Exception:
                pass
        return values

    def action_save(self) -> None:
        """Save the configuration and continue."""
        values = self._get_wizard_values()
        still_missing = [v for v in self.missing_vars if v not in values]
        if still_missing:
            self.notify(
                f"Still missing: {', '.join(still_missing)}",
                severity="error",
                timeout=5,
            )
            return
        # Merge with existing
        merged = dict(self.current_env)
        merged.update(values)
        save_env_file(self.env_path, merged)
        self.notify("Configuration saved!", timeout=2)
        self.dismiss(True)

    def action_cancel(self) -> None:
        """Cancel setup."""
        self.dismiss(False)

