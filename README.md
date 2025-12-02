# Agent Coder

Agent Coder is a powerful Terminal User Interface (TUI) coding assistant powered by AI models. It supports multiple providers including local LLMs via [Ollama](https://ollama.com/), Anthropic Claude, Google Gemini, and OpenAI GPT. It is designed to help you write, debug, and understand code directly from your terminal, with agentic capabilities to interact with your file system.

## Features

- **Multiple AI Providers**: 
  - **Ollama** (default): Local LLM support for privacy and offline capability. Uses `gpt-oss:20b` by default.
  - **Anthropic Claude**: Use Claude 3.5 Sonnet and other models.
  - **Google Gemini**: Use Gemini 1.5 Pro and other models.
  - **OpenAI GPT**: Use GPT-4o and other models.
- **Interactive TUI**: Built with [Textual](https://textual.textualize.io/) for a rich terminal experience.
- **Settings Dialog**: Press `s` or use `/settings` to change provider, model, and mode on the fly.
- **Agent Modes**:
  - **Auto** (`--mode auto`): The agent can freely read and write files to complete tasks. (Default)
  - **Plan** (`--mode plan`): The agent can only read files and propose plans, but cannot modify files.
  - **Ask** (`--mode ask`): The agent must ask for user confirmation before writing to any file.
- **LSP Support**: Integrated Language Server Protocol client for code intelligence (diagnostics, definitions, hover).
  - Default: `pylsp` (Python LSP Server)
  - Configurable via `--lsp-command` or `/lsp` command.
- **Hooks System**: Extensible hook system compatible with Claude Code to run custom scripts on events (PreToolUse, PostToolUse, UserPromptSubmit, etc.).
- **MCP Support**: Model Context Protocol integration for extending capabilities.
- **Project Memory**:
  - Automatically reads `AGENT_MEMORY.md` in the current directory to understand project context and conventions.
  - Use `/memory` slash command to manage persistent memory.
- **Slash Commands**: Built-in commands for quick actions like clearing chat, checking health, etc.

## Prerequisites

- **Python 3.10+**
- **AI Provider Setup** (choose one or more):
  - **Ollama** (default): 
    - Install from [ollama.com](https://ollama.com/)
    - Pull a model: `ollama pull gpt-oss:20b`
  - **Anthropic**: Set `ANTHROPIC_API_KEY` environment variable
  - **Google Gemini**: Set `GEMINI_API_KEY` environment variable
  - **OpenAI**: Set `OPENAI_API_KEY` environment variable
- **LSP Server** (Optional):
  - `python-lsp-server` is installed by default for Python support.
  - Install other language servers (e.g., `pyright`, `gopls`, `rust-analyzer`) to use them.

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
# Start with default settings (Ollama, gpt-oss:20b, Auto mode)
python main.py start

# Enable LSP support (uses pylsp by default)
python main.py start --lsp

# Use a specific LSP server (e.g., pyright)
python main.py start --lsp --lsp-command "pyright-langserver --stdio"

# Use Anthropic Claude
python main.py start --provider anthropic --model claude-3-5-sonnet-latest
```

### Interactive Settings

While in the TUI:
- Press `s` to open the settings dialog
- Use dropdown menus to select provider, enter model name, and choose mode
- Changes take effect immediately

### Slash Commands

Inside the TUI, you can use the following commands:

- `/help`: Show available commands.
- `/settings`: Open the settings dialog (or press `s`).
- `/clear`: Clear the chat history.
- `/compact`: Compact conversation history.
- `/model [name]`: Show current model or change to a new model.
- `/provider [name]`: Show current provider or change provider (ollama, anthropic, google, openai).
- `/mode [mode]`: Show current mode or change mode (auto, plan, ask).
- `/lsp [on|off|<command>]`: Manage LSP support.
- `/doctor`: Check the connection to the AI provider.
- `/memory`: View the current project memory (`AGENT_MEMORY.md`).
- `/memory <text>`: Add a new item to the project memory.
- `/exit` or `/quit`: Exit the application.

### Hooks

Agent Coder supports a hooks system compatible with Claude Code. Configure hooks in `.agent-coder/hooks.json` or `.claude/hooks.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "write_file",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'About to write a file'"
          }
        ]
      }
    ]
  }
}
```

Available hook events:
- `PreToolUse`: Before a tool is executed
- `PostToolUse`: After a tool completes
- `UserPromptSubmit`: When user submits a prompt
- `SessionStart`: When a session starts
- `SessionEnd`: When a session ends
- `SubagentStop`: When a subagent completes

See [Claude Code hooks documentation](https://code.claude.com/docs/en/hooks) for more details.

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

## Configuration

You can configure Agent Coder using:
1. **Command-line arguments** (highest priority)
2. **Environment variables** (prefix with `AGENT_CODER_`, e.g., `AGENT_CODER_MODEL=gpt-4o`)
3. **`.env` file** in the project root
4. **Settings files** (`.agent-coder/settings.json` or `.claude/settings.json`)

Example `.env`:
```
AGENT_CODER_MODEL=claude-3-5-sonnet-latest
AGENT_CODER_MODEL_PROVIDER=anthropic
AGENT_CODER_MODE=auto
ANTHROPIC_API_KEY=your_api_key_here
```

## Development

To run the tests:

```bash
uv run tests/test_agent.py
```

## License

[Apache 2.0](LICENSE)

