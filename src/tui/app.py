from textual.app import App, ComposeResult
from textual import work
from textual.widgets import Header, Footer, Input, RichLog, Label, Button
from textual.containers import Vertical, Grid
from textual.screen import ModalScreen

class ConfirmationScreen(ModalScreen[bool]):
    """Screen for confirming actions."""

    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(self.message, id="question"),
            Button("Yes", variant="success", id="yes"),
            Button("No", variant="error", id="no"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            self.dismiss(True)
        else:
            self.dismiss(False)

class AgentCoderApp(App):
    """A Textual app for the Agent Coder."""

    CSS = """
    Screen {
        layout: vertical;
    }
    RichLog {
        height: 1fr;
        border: solid green;
    }
    Input {
        dock: bottom;
    }
    
    ConfirmationScreen {
        align: center middle;
    }
    #dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        padding: 0 1;
        width: 60;
        height: 11;
        border: thick $background 80%;
        background: $surface;
    }
    #question {
        column-span: 2;
        height: 1fr;
        width: 1fr;
        content-align: center middle;
    }
    Button {
        width: 100%;
    }
    """

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            RichLog(id="chat_log", highlight=True, markup=True),
            Label("", id="status_bar"),
            Input(placeholder="Type your message here...", id="chat_input"),
        )
        yield Footer()

    def __init__(self, model_name: str = "gpt-oss:20b", mode: str = "auto"):
        super().__init__()
        self.model_name = model_name
        self.mode = mode
        self.agent = None

    async def confirm_action(self, message: str) -> bool:
        """Request confirmation from user."""
        return await self.push_screen(ConfirmationScreen(message))

    def on_mount(self) -> None:
        """Initialize the agent on mount."""
        from src.agent.core import create_agent, AgentMode
        self.agent = create_agent(
            self.model_name, 
            mode=AgentMode(self.mode),
            confirmation_callback=self.confirm_action
        )

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        message = event.value
        if message:
            log = self.query_one("#chat_log", RichLog)
            log.write(f"[bold blue]You:[/bold blue] {message}")
            self.query_one("#chat_input", Input).value = ""
            
            # Call agent asynchronously
            self.query_one("#status_bar", Label).update("Thinking...")
            self.get_response(message)

    @work(exclusive=True)
    async def get_response(self, message: str) -> None:
        """Get response from agent."""
        log = self.query_one("#chat_log", RichLog)
        status = self.query_one("#status_bar", Label)
        try:
            from src.agent.core import get_agent_response
            if self.agent:
                response = await get_agent_response(self.agent, message)
                log.write(f"[bold green]Agent:[/bold green] {response}")
            else:
                log.write("[bold red]Error:[/bold red] Agent not initialized.")
        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {str(e)}")
        finally:
            status.update("")

if __name__ == "__main__":
    app = AgentCoderApp()
    app.run()
