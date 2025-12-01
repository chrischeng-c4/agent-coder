import typer
from src.tui.app import AgentCoderApp

from src.agent.core import AgentMode

app = typer.Typer()

@app.callback()
def callback():
    """
    Agent Coder CLI.
    """

@app.command()
def start(
    model: str = typer.Option("gpt-oss:20b", help="Name of the Ollama model to use"),
    mode: AgentMode = typer.Option(AgentMode.AUTO, help="Agent mode: auto, plan, ask")
):
    """Start the Agent Coder TUI."""
    tui = AgentCoderApp(model_name=model, mode=mode.value)
    tui.run()

def main():
    app()

if __name__ == "__main__":
    main()
