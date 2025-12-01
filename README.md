# Agent Coder

Agent Coder is a powerful Terminal User Interface (TUI) coding assistant powered by local LLMs via [Ollama](https://ollama.com/). It is designed to help you write, debug, and understand code directly from your terminal, with agentic capabilities to interact with your file system.

## Features

- **Local LLM Powered**: Uses `gpt-oss:20b` by default via Ollama for privacy and offline capability.
- **Interactive TUI**: Built with [Textual](https://textual.textualize.io/) for a rich terminal experience.
- **Agent Modes**:
  - **Auto** (`--mode auto`): The agent can freely read and write files to complete tasks. (Default)
  - **Plan** (`--mode plan`): The agent can only read files and propose plans, but cannot modify files.
  - **Ask** (`--mode ask`): The agent must ask for user confirmation before writing to any file.
- **Project Memory**:
  - Automatically reads `AGENT_MEMORY.md` in the current directory to understand project context and conventions.
  - Use `/memory` slash command to manage persistent memory.
- **Slash Commands**: Built-in commands for quick actions like clearing chat, checking health, etc.

## Prerequisites

- **Python 3.10+**
- **Ollama**: Installed and running.
  - Pull the default model: `ollama pull gpt-oss:20b` (or any other model you wish to use).

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/chrischeng-c4/agent-coder.git
   cd agent-coder
   ```

2. Install dependencies using `uv` (recommended) or `pip`:
   ```bash
   # Using uv
   uv sync
   
   # Or using pip
   pip install -r requirements.txt
   ```

## Usage

### Starting the Agent

Run the application using the CLI entry point:

```bash
# Start with default settings (Auto mode, gpt-oss:20b)
python main.py start

# Start in Plan mode (Read-only)
python main.py start --mode plan

# Start in Ask mode (Confirmation required for writes)
python main.py start --mode ask

# Use a different model
python main.py start --model llama3
```

### Slash Commands

Inside the TUI, you can use the following commands:

- `/help`: Show available commands.
- `/clear`: Clear the chat history.
- `/model`: Show the current model being used.
- `/mode`: Show the current agent mode.
- `/doctor`: Check the connection to the Ollama server.
- `/memory`: View the current project memory (`AGENT_MEMORY.md`).
- `/memory <text>`: Add a new item to the project memory.
- `/exit` or `/quit`: Exit the application.

### Subagents and Skills

Agent Coder supports subagents and skills, compatible with Claude Code configuration.

- **Subagents**: Place YAML definitions in `.agent-coder/agents/` (or `.claude/agents/`).
- **Skills**: Place Markdown definitions in `.agent-coder/skills/` (or `.claude/skills/`).

See [Claude Code documentation](https://code.claude.com/docs) for file format details.

Create a `AGENT_MEMORY.md` file in your project root to provide persistent context to the agent. This is useful for:
- Coding style guidelines.
- Architecture overviews.
- Frequently used commands.

The agent will automatically read this file on startup. You can also add to it dynamically using `/memory <instruction>`.

## Development

To run the tests:

```bash
uv run tests/test_agent.py
```

## License

[Apache 2.0](LICENSE)
