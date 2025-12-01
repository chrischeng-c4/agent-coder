import typer
from src.tui.app import AgentCoderApp

from src.models import AgentMode

app = typer.Typer()

@app.callback()
def callback():
    """
    Agent Coder CLI.
    """

@app.command()
def start(
    query: str = typer.Argument(None, help="Optional query to start the session with"),
    model: str = typer.Option("gpt-oss:20b", help="Name of the Ollama model to use"),
    mode: AgentMode = typer.Option(AgentMode.AUTO, help="Agent mode: auto, plan, ask"),
    print_mode: bool = typer.Option(False, "--print", "-p", help="Print response and exit (non-interactive)"),
):
    """Start the Agent Coder."""
    if print_mode:
        if not query:
            typer.echo("Error: --print mode requires a query.")
            raise typer.Exit(code=1)
        
        # Headless mode
        import asyncio
        from src.config import Settings
        from src.agent.core import create_agent, get_agent_response
        
        async def run_headless():
            settings = Settings(model=model, mode=mode)
            agent = create_agent(settings=settings)
            print(f"Running query: {query}")
            response = await get_agent_response(agent, query)
            print(response)

        asyncio.run(run_headless())
    else:
        # TUI mode
        tui = AgentCoderApp(model_name=model, mode=mode.value, initial_query=query)
        tui.run()

def main():
    app()

if __name__ == "__main__":
    main()
