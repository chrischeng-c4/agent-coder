import os
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

from src.agent.tools import read_file, write_file, list_dir

def create_agent(model_name: str = 'gpt-oss:20b') -> Agent:
    """Create an agent with the specified model."""
    # Set default Ollama base URL if not present
    if "OLLAMA_BASE_URL" not in os.environ:
        os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434/v1"

    # Ollama is compatible with OpenAI API
    model = OpenAIModel(
        model_name=model_name,
        provider='ollama',
    )
    
    return Agent(
        model,
        system_prompt=(
            'You are a helpful AI coding assistant. '
            'You have access to file system tools: read_file, write_file, list_dir. '
            'When asked to create or modify a file, YOU MUST use the write_file tool. '
            'Do not just describe what you would do, actually call the tool.'
        ),
        tools=[read_file, write_file, list_dir],
    )

async def get_agent_response(agent: Agent, user_input: str) -> str:
    """Get a response from the agent."""
    try:
        result = await agent.run(user_input)
        return result.output
    except Exception as e:
        return f"Error communicating with agent: {str(e)}"
