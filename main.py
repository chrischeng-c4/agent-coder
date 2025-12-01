import typer
from src.tui.app import AgentCoderApp

app = typer.Typer()

@app.callback()
def callback():
    """
    Agent Coder CLI.
    """

@app.command()
def start(model: str = typer.Option("gpt-oss:20b", help="Name of the Ollama model to use")):
    """Start the Agent Coder TUI."""
    tui = AgentCoderApp(model_name=model)
    tui.run()

def main():
    app()

if __name__ == "__main__":
    main()
