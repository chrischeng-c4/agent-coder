from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, Select
from textual.containers import Grid
from textual.screen import ModalScreen

class SettingsScreen(ModalScreen):
    """Screen for configuring settings."""

    def __init__(self, current_provider: str, current_model: str, current_mode: str):
        super().__init__()
        self.provider = current_provider
        self.model = current_model
        self.mode = current_mode

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Provider:", classes="label"),
            Select(
                [(p, p) for p in ["ollama", "anthropic", "google", "openai"]],
                value=self.provider,
                id="provider_select",
                allow_blank=False
            ),
            Label("Model:", classes="label"),
            Input(value=self.model, id="model_input"),
            Label("Mode:", classes="label"),
            Select(
                [(m, m) for m in ["auto", "plan", "ask"]],
                value=self.mode,
                id="mode_select",
                allow_blank=False
            ),
            Button("Save", variant="success", id="save"),
            Button("Cancel", variant="error", id="cancel"),
            id="settings_dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            provider = self.query_one("#provider_select", Select).value
            model = self.query_one("#model_input", Input).value
            mode = self.query_one("#mode_select", Select).value
            self.dismiss((provider, model, mode))
        else:
            self.dismiss(None)
