from textual.app import App, ComposeResult
from textual import work
from textual.widgets import Header, Footer, Input, RichLog, Label, Button, TextArea, Select
from textual.containers import Vertical, Grid
from textual.screen import ModalScreen
from textual import events
from textual.message import Message
from src.tui.settings_screen import SettingsScreen

class ChatInput(TextArea):
    """Custom TextArea for chat input."""
    
    class Submitted(Message):
        """Posted when the enter key is pressed."""
        def __init__(self, value: str):
            self.value = value
            super().__init__()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.show_line_numbers = False

    async def _on_key(self, event: events.Key) -> None:
        if event.key == "enter" and not event.shift and not event.ctrl and not event.alt:
            event.stop()
            value = self.text.strip()
            if value:
                self.post_message(self.Submitted(value))
                self.clear()
        return await super()._on_key(event)

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
    ChatInput {
        dock: bottom;
        height: 3;
        border: solid gray;
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
    SettingsScreen {
        align: center middle;
    }
    #settings_dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 1fr 1fr 1fr;
        padding: 1 2;
        width: 60;
        height: 25;
        border: thick $background 80%;
        background: $surface;
    }
    .label {
        content-align: left middle;
        height: 100%;
    }
    """

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("s", "open_settings", "Settings"),
        ("ctrl+c", "quit_app", "Quit"),
        ("ctrl+d", "quit_app", "Quit"),
        ("ctrl+l", "clear_log", "Clear Log"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            RichLog(id="chat_log", highlight=True, markup=True),
            Label("", id="status_bar"),
            ChatInput(id="chat_input"),
        )
        yield Footer()

    def __init__(self, model_name: str = "gpt-oss:20b", model_provider: str = "ollama", mode: str = "auto", initial_query: str = None):
        super().__init__()
        self.model_name = model_name
        self.model_provider = model_provider
        self.mode = mode
        self.initial_query = initial_query
        self.agent = None

    async def confirm_action(self, message: str) -> bool:
        """Request confirmation from user."""
        return await self.push_screen(ConfirmationScreen(message))

    def on_mount(self) -> None:
        """Initialize the agent on mount."""
        from src.agent.core import create_agent
        from src.models import AgentMode
        from src.config import Settings
        
        # Initialize settings with CLI overrides
        settings = Settings(
            model=self.model_name,
            model_provider=self.model_provider,
            mode=AgentMode(self.mode)
        )
        
        # Initialize MCP Manager
        from src.agent.mcp_manager import MCPManager
        self.mcp_manager = MCPManager(settings)
        self.mcp_manager.load_config()
        
        # We need to connect to MCP servers asynchronously.
        # Since on_mount is synchronous (or at least we want to block until ready),
        # we'll do this in a worker or just await it if on_mount can be async.
        # Textual's on_mount can be async.
        
        # However, create_agent is synchronous in our current design.
        # We'll connect first, then create agent.
        
        self.run_worker(self.initialize_agent(settings))

    async def initialize_agent(self, settings):
        """Initialize agent with MCP tools."""
        status = self.query_one("#status_bar", Label)
        status.update("Connecting to MCP servers...")
        
        await self.mcp_manager.connect_all()
        
        status.update("Initializing agent...")
        from src.agent.core import create_agent
        from src.agent.hooks import HookEvent
        
        self.agent = create_agent(
            settings=settings,
            confirmation_callback=self.confirm_action,
            extra_tools=self.mcp_manager.tools
        )
        
        if hasattr(self.agent, 'hook_manager'):
            await self.agent.hook_manager.trigger(HookEvent.SESSION_START, {"session_id": "tui_session"})
        
        status.update("Ready.")
        
        if self.initial_query:
            self.query_one("#chat_log", RichLog).write(f"[bold blue]You:[/bold blue] {self.initial_query}")
            status.update("Thinking...")
            self.get_response(self.initial_query)

    async def on_unmount(self) -> None:
        """Cleanup resources."""
        from src.agent.hooks import HookEvent
        if self.agent and hasattr(self.agent, 'hook_manager'):
            await self.agent.hook_manager.trigger(HookEvent.SESSION_END, {"session_id": "tui_session"})

        if hasattr(self, 'mcp_manager'):
            await self.mcp_manager.cleanup()

    def action_quit_app(self) -> None:
        """Quit the application."""
        self.exit()

    def action_clear_log(self) -> None:
        """Clear the chat log."""
        self.query_one("#chat_log", RichLog).clear()
        self.query_one("#chat_log", RichLog).write("[bold yellow]Chat cleared.[/bold yellow]")

    def action_open_settings(self) -> None:
        """Open settings dialog."""
        def on_dismiss(result):
            if result:
                provider, model, mode = result
                self.update_settings(provider, model, mode)
        
        self.push_screen(
            SettingsScreen(self.model_provider, self.model_name, self.mode),
            on_dismiss
        )

    def update_settings(self, provider, model, mode):
        self.model_provider = provider
        self.model_name = model
        self.mode = mode
        
        log = self.query_one("#chat_log", RichLog)
        log.write(f"[bold]Settings updated:[/bold] Provider={provider}, Model={model}, Mode={mode}")
        
        # Re-initialize agent
        from src.config import Settings
        from src.models import AgentMode
        settings = Settings(
            model=self.model_name,
            model_provider=self.model_provider,
            mode=AgentMode(self.mode)
        )
        self.run_worker(self.initialize_agent(settings))

    async def on_chat_input_submitted(self, event: ChatInput.Submitted) -> None:
        """Handle input submission."""
        message = event.value
        if message:
            log = self.query_one("#chat_log", RichLog)
            log.write(f"[bold blue]You:[/bold blue] {message}")
            # self.query_one("#chat_input", ChatInput).clear() # Already cleared in ChatInput
            
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
            /settings   - Open settings dialog (or press 's')
            /model      - Show or set current model
            /provider   - Show or set current provider
            /mode       - Show or set current mode
            /memory     - Manage project memory
            /doctor     - Check system health
            /statusline - Configure status line
            /speckit    - Run SpecKit commands
            """
            log.write(help_text)
        
        elif cmd == "/settings":
            self.action_open_settings()
        
        elif cmd == "/clear":
            log.clear()
            log.write("[bold yellow]Chat cleared.[/bold yellow]")
            
        elif cmd in ("/exit", "/quit"):
            self.exit()
            
        elif cmd == "/model":
            if args:
                new_model = args[0]
                self.model_name = new_model
                log.write(f"Switching model to: [bold]{self.model_name}[/bold]")
                
                # Update settings
                from src.config import Settings
                from src.models import AgentMode
                settings = Settings(
                    model=self.model_name,
                    model_provider=self.model_provider,
                    mode=AgentMode(self.mode)
                )
                self.run_worker(self.initialize_agent(settings))
            else:
                log.write(f"Current model: [bold]{self.model_name}[/bold]")
                log.write("Usage: /model <model_name>")

        elif cmd == "/provider":
            if args:
                new_provider = args[0].lower()
                if new_provider not in ["ollama", "anthropic", "claude", "google", "gemini", "openai", "gpt"]:
                    log.write(f"[bold red]Invalid provider: {new_provider}[/bold red]")
                    log.write("Valid providers: ollama, anthropic, google, openai")
                    return
                    
                self.model_provider = new_provider
                log.write(f"Switching provider to: [bold]{self.model_provider}[/bold]")
                
                # Update settings
                from src.config import Settings
                from src.models import AgentMode
                settings = Settings(
                    model=self.model_name,
                    model_provider=self.model_provider,
                    mode=AgentMode(self.mode)
                )
                self.run_worker(self.initialize_agent(settings))
            else:
                log.write(f"Current provider: [bold]{self.model_provider}[/bold]")
                log.write("Usage: /provider <provider_name>")
                
        elif cmd == "/mode":
            if args:
                new_mode = args[0].lower()
                try:
                    from src.models import AgentMode
                    mode_enum = AgentMode(new_mode)
                    self.mode = mode_enum.value
                    log.write(f"Switching mode to: [bold]{self.mode}[/bold]")
                    
                    # Update settings
                    from src.config import Settings
                    settings = Settings(
                        model=self.model_name,
                        model_provider=self.model_provider,
                        mode=mode_enum
                    )
                    self.run_worker(self.initialize_agent(settings))
                except ValueError:
                    log.write(f"[bold red]Invalid mode: {new_mode}[/bold red]")
                    log.write("Valid modes: auto, plan, ask")
            else:
                log.write(f"Current mode: [bold]{self.mode}[/bold]")
                log.write("Usage: /mode <mode>")
            
        elif cmd == "/doctor":
            log.write("Checking system health...")
            log.write(f"Current Provider: [bold]{self.model_provider}[/bold]")
            
            if self.model_provider == "ollama":
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
            elif self.model_provider in ("anthropic", "claude"):
                if "ANTHROPIC_API_KEY" in os.environ:
                    log.write("[bold green]ANTHROPIC_API_KEY found in environment.[/bold green]")
                else:
                    log.write("[bold red]ANTHROPIC_API_KEY not found in environment.[/bold red]")
            elif self.model_provider in ("google", "gemini"):
                if "GEMINI_API_KEY" in os.environ:
                    log.write("[bold green]GEMINI_API_KEY found in environment.[/bold green]")
                else:
                    log.write("[bold red]GEMINI_API_KEY not found in environment.[/bold red]")
            elif self.model_provider in ("openai", "gpt"):
                if "OPENAI_API_KEY" in os.environ:
                    log.write("[bold green]OPENAI_API_KEY found in environment.[/bold green]")
                else:
                    log.write("[bold red]OPENAI_API_KEY not found in environment.[/bold red]")
            else:
                log.write(f"[yellow]No specific health check for provider: {self.model_provider}[/yellow]")

        elif cmd == "/memory":
            import os
            memory_path = "AGENT_MEMORY.md"
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
                    log.write("[yellow]No project memory found (AGENT_MEMORY.md). Use '/memory <text>' to add one.[/yellow]")
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
                
        elif cmd == "/statusline":
            log.write("[bold]Status Line Configuration:[/bold]")
            log.write("To configure a custom status line, you can update your settings or use environment variables.")
            log.write("Currently, the status line shows the agent's thinking status.")
            log.write("Future versions will support custom shell commands for status line.")
            
        elif cmd == "/speckit":
            if not args:
                log.write("[bold]SpecKit Commands:[/bold]")
                log.write("Usage: /speckit <command>")
                log.write("Commands: init, plan, specify, tasks, implement, analyze, clarify, constitution, checklist")
                return

            subcmd = args[0].lower()
            
            if subcmd == "init":
                from src.agent.speckit import install_speckit
                try:
                    import os
                    install_speckit(os.getcwd())
                    log.write("[bold green]SpecKit initialized successfully.[/bold green]")
                    log.write("Skills have been installed to .agent-coder/skills/")
                    log.write("You may need to restart the session to load the new skills.")
                except Exception as e:
                    log.write(f"[bold red]Error initializing SpecKit: {e}[/bold red]")
            else:
                # Check if skill exists
                skill_name = f"speckit-{subcmd}"
                # We need access to the agent's tools to check for get_skill
                # But we can just try to invoke the agent with the skill prompt if we can find it.
                # Or better, we can read the skill file directly if we know where it is.
                
                import os
                skill_path = os.path.join(os.getcwd(), ".agent-coder", "skills", f"{skill_name}.md")
                if os.path.exists(skill_path):
                    # Read skill content
                    with open(skill_path, "r") as f:
                        content = f.read()
                        # Strip frontmatter
                        if content.startswith("---"):
                            parts = content.split("---", 2)
                            if len(parts) >= 3:
                                content = parts[2].strip()
                    
                    # Send to agent
                    log.write(f"[bold blue]Executing SpecKit command: {subcmd}[/bold blue]")
                    self.query_one("#chat_log", RichLog).write(f"[bold blue]You:[/bold blue] /speckit {subcmd}")
                    self.query_one("#status_bar", Label).update("Thinking...")
                    
                    # We append the user's extra args if any
                    user_args = " ".join(args[1:])
                    prompt = f"{content}\n\nUser Input:\n{user_args}"
                    
                    self.get_response(prompt)
                else:
                    log.write(f"[bold red]SpecKit command '{subcmd}' not found or not initialized.[/bold red]")
                    log.write("Run '/speckit init' to initialize SpecKit.")
            
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
