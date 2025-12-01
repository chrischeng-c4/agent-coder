from textual.app import App, ComposeResult
from textual import work
from textual.widgets import Header, Footer, Input, RichLog, Label
from textual.containers import Vertical

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

    def __init__(self, model_name: str = "gpt-oss:20b"):
        super().__init__()
        self.model_name = model_name
        self.agent = None

    def on_mount(self) -> None:
        """Initialize the agent on mount."""
        from src.agent.core import create_agent
        self.agent = create_agent(self.model_name)

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
