import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from src.config import Settings

class MCPServerConfig(BaseModel):
    command: str
    args: List[str] = []
    env: Dict[str, str] = {}

class MCPManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.servers: Dict[str, MCPServerConfig] = {}
        self.sessions: Dict[str, ClientSession] = {}
        self.tools: List[Any] = []
        self._exit_stack = None

    def load_config(self):
        """Load MCP configuration from .mcp.json or .agent-coder/mcp.json."""
        config_paths = [
            os.path.join(os.getcwd(), ".mcp.json"),
            os.path.join(os.getcwd(), ".agent-coder", "mcp.json"),
            os.path.join(os.getcwd(), ".claude", "mcp.json"),
        ]
        
        for path in config_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        data = json.load(f)
                        # Support both direct object and "mcpServers" key
                        servers_data = data.get("mcpServers", data)
                        for name, config in servers_data.items():
                            # Only support stdio for now
                            if config.get("type") == "stdio" or "command" in config:
                                self.servers[name] = MCPServerConfig(
                                    command=config["command"],
                                    args=config.get("args", []),
                                    env=config.get("env", {})
                                )
                except Exception as e:
                    print(f"Error loading MCP config from {path}: {e}")

    async def connect_all(self):
        """Connect to all configured MCP servers."""
        from contextlib import AsyncExitStack
        self._exit_stack = AsyncExitStack()
        
        for name, config in self.servers.items():
            try:
                # Merge env with current environment
                env = os.environ.copy()
                env.update(config.env)
                
                server_params = StdioServerParameters(
                    command=config.command,
                    args=config.args,
                    env=env
                )
                
                # Start the stdio client
                read, write = await self._exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
                
                # Create the session
                session = await self._exit_stack.enter_async_context(
                    ClientSession(read, write)
                )
                
                await session.initialize()
                self.sessions[name] = session
                
                # List tools
                result = await session.list_tools()
                for tool in result.tools:
                    # Wrap the tool for the agent
                    await self._register_tool(name, session, tool)
                    
            except Exception as e:
                print(f"Failed to connect to MCP server {name}: {e}")

    async def _register_tool(self, server_name: str, session: ClientSession, tool_info: Any):
        """Register an MCP tool as a callable for the agent."""
        
        async def mcp_tool_wrapper(**kwargs):
            """Dynamic wrapper for MCP tool."""
            try:
                result = await session.call_tool(tool_info.name, arguments=kwargs)
                # Format result
                output = []
                for content in result.content:
                    if content.type == "text":
                        output.append(content.text)
                    elif content.type == "image":
                        output.append(f"[Image: {content.mimeType}]")
                    elif content.type == "resource":
                        output.append(f"[Resource: {content.uri}]")
                return "\n".join(output)
            except Exception as e:
                return f"Error calling tool {tool_info.name}: {str(e)}"

        # Set metadata
        tool_name = f"{server_name}_{tool_info.name}"
        mcp_tool_wrapper.__name__ = tool_name
        mcp_tool_wrapper.__doc__ = f"{tool_info.description}\nParameters: {tool_info.inputSchema}"
        
        self.tools.append(mcp_tool_wrapper)

    async def cleanup(self):
        """Close all connections."""
        if self._exit_stack:
            await self._exit_stack.aclose()
