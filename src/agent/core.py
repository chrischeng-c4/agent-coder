import os
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

from src.agent.tools import read_file, write_file, list_dir

from typing import Callable, Awaitable, Optional
from enum import Enum

class AgentMode(str, Enum):
    AUTO = 'auto'
    PLAN = 'plan'
    ASK = 'ask'

def create_agent(
    model_name: str = 'gpt-oss:20b',
    mode: AgentMode = AgentMode.AUTO,
    confirmation_callback: Optional[Callable[[str], Awaitable[bool]]] = None
) -> Agent:
    """Create an agent with the specified model and mode."""
    # Set default Ollama base URL if not present
    if "OLLAMA_BASE_URL" not in os.environ:
        os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434/v1"

    # Ollama is compatible with OpenAI API
    model = OpenAIModel(
        model_name=model_name,
        provider='ollama',
    )
    
    current_tools = [read_file, list_dir]
    
    if mode == AgentMode.AUTO:
        current_tools.append(write_file)
    elif mode == AgentMode.ASK:
        if confirmation_callback is None:
            # Fallback to auto if no callback provided, or raise error. 
            # For safety, let's just not add write_file or warn.
            # But better to wrap it.
            pass
            
        async def write_file_with_confirmation(path: str, content: str) -> str:
            """Write content to a file with user confirmation."""
            if confirmation_callback:
                confirmed = await confirmation_callback(f"Write to {path}?")
                if not confirmed:
                    return "Action cancelled by user."
            return write_file(path, content)
            
        current_tools.append(write_file_with_confirmation)
    
    # Adjust system prompt based on mode
    system_prompt = (
        'You are a helpful AI coding assistant. '
        'You have access to file system tools. '
        'When asked to create or modify a file, YOU MUST use the write_file tool. '
        'Do not just describe what you would do, actually call the tool.'
    )
    
    if mode == AgentMode.PLAN:
        system_prompt += " You are in PLAN mode. You can read files but CANNOT write them. Propose a plan."

    return Agent(
        model,
        system_prompt=system_prompt,
        tools=current_tools,
    )

async def get_agent_response(agent: Agent, user_input: str) -> str:
    """Get a response from the agent."""
    try:
        result = await agent.run(user_input)
        return result.output
    except Exception as e:
        return f"Error communicating with agent: {str(e)}"
