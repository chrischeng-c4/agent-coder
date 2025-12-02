# Agent Coder Architecture

This document outlines the high-level architecture of Agent Coder, a TUI-based AI coding assistant.

## Core Components

### 1. Agent Core (`src/agent/core.py`)
The heart of the application. It orchestrates the AI model, tools, and memory.
- **Agent Creation**: Dynamically assembles an agent based on configuration (Model, Provider, Tools).
- **Tool Management**: Wraps and injects tools (File I/O, LSP, MCP, Skills) into the agent context.
- **Hook System**: Triggers events (Pre/Post Tool Use, Session Start/End) for extensibility.

### 2. TUI Layer (`src/tui/`)
Built with [Textual](https://textual.textualize.io/), providing a rich terminal interface.
- **`app.py`**: Main application loop, event handling, and UI layout.
- **`settings_screen.py`**: Modal dialog for runtime configuration.
- **Slash Commands**: Handles user commands like `/model`, `/lsp`, `/compact`.

### 3. Tool Systems

The agent's capabilities are modular and composed at runtime:

#### A. Core Tools (`src/agent/tools.py`)
Stateless, fundamental operations.
- `read_file`, `write_file`, `list_dir`

#### B. LSP Manager (`src/agent/lsp_manager.py`)
**Stateful** integration with Language Server Protocol.
- Manages a background process (e.g., `pylsp`, `pyright`).
- Exposes tools: `lsp_hover`, `lsp_definition`, `lsp_references`, `lsp_rename`.
- Syncs file changes to the LSP server via hooks.

#### C. MCP Manager (`src/agent/mcp_manager.py`)
Integration with [Model Context Protocol](https://modelcontextprotocol.io/).
- Connects to external MCP servers (stdio).
- Dynamically registers tools exposed by MCP servers.

#### D. Subagents (`src/agent/subagents.py`)
Specialized agents for specific tasks.
- Loaded from `.agent-coder/agents/*.md`.
- Each subagent has its own system prompt and configuration.
- Exposed as `delegate_to_<name>` tools to the main agent.

#### E. Skills (`src/agent/skills.py`)
Reusable prompt fragments / instructions.
- Loaded from `.agent-coder/skills/*.md`.
- Exposed via `get_skill` tool.

### 4. Configuration (`src/config.py`)
- Uses `pydantic-settings` for robust configuration management.
- Sources: CLI args > Environment Variables > `.env` file > Defaults.

## Data Flow

1. **User Input**: User types a query in the TUI.
2. **Command Handling**: TUI checks for slash commands (`/`).
3. **Agent Execution**:
   - Query is sent to `get_agent_response`.
   - Hooks trigger `UserPromptSubmit`.
   - Agent (Pydantic AI) processes the query.
4. **Tool Loop**:
   - Model requests a tool call.
   - `PreToolUse` hook fires.
   - Tool executes (File I/O, LSP query, etc.).
   - `PostToolUse` hook fires (LSP syncs file changes here).
   - Result returned to model.
5. **Response**: Final answer displayed in TUI.

## Directory Structure

```
src/
├── agent/          # Core agent logic
│   ├── core.py     # Agent factory and runner
│   ├── tools.py    # Stateless core tools
│   ├── lsp.py      # Low-level LSP client
│   ├── lsp_manager.py # Stateful LSP management
│   ├── mcp_manager.py # MCP integration
│   ├── hooks.py    # Event hooks system
│   ├── subagents.py # Subagent loader
│   └── skills.py   # Skill loader
├── tui/            # User Interface
│   ├── app.py      # Main TUI app
│   └── settings_screen.py
├── config.py       # Configuration models
└── models.py       # Shared data models
```
