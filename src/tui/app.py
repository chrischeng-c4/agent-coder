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
        from src.agent.core import create_agent
        from src.models import AgentMode, AgentConfig
        
        config = AgentConfig(
            model_name=self.model_name,
            mode=AgentMode(self.mode)
        )
        
        self.agent = create_agent(
            config=config,
            confirmation_callback=self.confirm_action
        )

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        message = event.value
        if message:
            log = self.query_one("#chat_log", RichLog)
            log.write(f"[bold blue]You:[/bold blue] {message}")
            self.query_one("#chat_input", Input).value = ""
            
            # Check for slash commands
            if message.startswith("/"):
                await self.handle_slash_command(message)
                self.query_one("#status_bar", Label).update("")
                return

            # Call agent asynchronously
            self.query_one("#status_bar", Label).update("Thinking...")
            self.get_response(message)

    async def handle_slash_command(self, command: str) -> None:
        """Handle slash commands."""
        log = self.query_one("#chat_log", RichLog)
        parts = command.strip().split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd == "/help":
            help_text = """
            [bold]Available Commands:[/bold]
            /help       - Show this help message
            /clear      - Clear the chat log
            /exit       - Exit the application
            /model      - Show current model
            /mode       - Show current mode
            /memory     - Manage project memory
            /doctor     - Check system health
            """
            log.write(help_text)
        
        elif cmd == "/clear":
            log.clear()
            log.write("[bold yellow]Chat cleared.[/bold yellow]")
            
        elif cmd in ("/exit", "/quit"):
            self.exit()
            
        elif cmd == "/model":
            log.write(f"Current model: [bold]{self.model_name}[/bold]")
            
        elif cmd == "/mode":
            log.write(f"Current mode: [bold]{self.mode}[/bold]")
            
        elif cmd == "/doctor":
            log.write("Checking system health...")
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://localhost:11434/") as resp:
                        if resp.status == 200:
                            log.write("[bold green]Ollama is running and accessible.[/bold green]")
                        else:
                            log.write(f"[bold red]Ollama returned status {resp.status}[/bold red]")
            except Exception as e:
                log.write(f"[bold red]Error connecting to Ollama: {e}[/bold red]")

        elif cmd == "/memory":
            import os
            memory_path = "CLAUDE.md"
            if not args:
                # Show memory
                if os.path.exists(memory_path):
                    try:
                        with open(memory_path, "r") as f:
                            content = f.read()
                        log.write(f"[bold]Project Memory ({memory_path}):[/bold]\n{content}")
                    except Exception as e:
                        log.write(f"[bold red]Error reading memory: {e}[/bold red]")
                else:
                    log.write("[yellow]No project memory found (CLAUDE.md). Use '/memory <text>' to add one.[/yellow]")
            else:
                # Add to memory
                new_memory = " ".join(args)
                try:
                    with open(memory_path, "a") as f:
                        f.write(f"\n- {new_memory}")
                    log.write(f"[green]Added to memory:[/green] {new_memory}")
                    # Re-initialize agent to pick up new memory? 
                    # Ideally yes, but for now let's just inform user.
                    log.write("[dim]Note: Restart session or run /init (not impl) to apply changes to agent context immediately.[/dim]")
                except Exception as e:
                    log.write(f"[bold red]Error writing memory: {e}[/bold red]")
                
        else:
            log.write(f"[bold red]Unknown command: {cmd}[/bold red]")

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
