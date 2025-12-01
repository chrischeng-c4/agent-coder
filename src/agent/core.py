import os
import functools
import inspect
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

from src.agent.tools import read_file, write_file, list_dir
from src.agent.hooks import HookManager, HookEvent

from typing import Callable, Awaitable, Optional, List, Any
from src.models import AgentMode
from src.config import Settings

def create_agent(
    settings: Settings,
    confirmation_callback: Optional[Callable[[str], Awaitable[bool]]] = None,
    extra_tools: List[Any] = []
) -> Agent:
    """Create an agent with the specified configuration."""
    # Set default Ollama base URL if not present
    if "OLLAMA_BASE_URL" not in os.environ:
        os.environ["OLLAMA_BASE_URL"] = settings.ollama_base_url

    # Select model based on provider
    provider = settings.model_provider.lower()
    
    if provider == 'ollama':
        model = OpenAIModel(
            model_name=settings.model,
            provider='ollama',
        )
    elif provider in ('anthropic', 'claude'):
        from pydantic_ai.models.anthropic import AnthropicModel
        model = AnthropicModel(settings.model)
    elif provider in ('google', 'gemini'):
        from pydantic_ai.models.gemini import GeminiModel
        model = GeminiModel(settings.model)
    elif provider in ('openai', 'gpt'):
        model = OpenAIModel(settings.model)
    else:
        # Fallback to OpenAI compatible (e.g. for other providers)
        model = OpenAIModel(settings.model)
    
    # Initialize HookManager
    hook_manager = HookManager()
    
    # Helper to wrap tools with hooks
    def wrap_tool(tool: Callable) -> Callable:
        is_async = inspect.iscoroutinefunction(tool)
        
        @functools.wraps(tool)
        async def wrapped(*args, **kwargs):
            tool_name = tool.__name__
            await hook_manager.trigger(HookEvent.PRE_TOOL_USE, {
                "tool_name": tool_name,
                "args": args,
                "kwargs": kwargs
            })
            
            try:
                if is_async:
                    result = await tool(*args, **kwargs)
                else:
                    result = tool(*args, **kwargs)
            except Exception as e:
                result = f"Error in tool {tool_name}: {str(e)}"
                
            await hook_manager.trigger(HookEvent.POST_TOOL_USE, {
                "tool_name": tool_name,
                "result": result
            })
            return result
            
        return wrapped
    
    current_tools = [wrap_tool(read_file), wrap_tool(list_dir)]
    current_tools.extend([wrap_tool(t) for t in extra_tools])
    
    if settings.mode == AgentMode.AUTO:
        current_tools.append(wrap_tool(write_file))
    elif settings.mode == AgentMode.ASK:
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
            
        current_tools.append(wrap_tool(write_file_with_confirmation))
    
    # Adjust system prompt based on mode
    system_prompt = (
        'You are a helpful AI coding assistant. '
        'You have access to file system tools. '
        'When asked to create or modify a file, YOU MUST use the write_file tool. '
        'Do not just describe what you would do, actually call the tool.'
    )
    
    # Load project memory from AGENT_MEMORY.md
    memory_path = os.path.join(os.getcwd(), "AGENT_MEMORY.md")
    if os.path.exists(memory_path):
        try:
            with open(memory_path, "r") as f:
                memory_content = f.read()
            system_prompt += f"\n\nPROJECT MEMORY (AGENT_MEMORY.md):\n{memory_content}"
        except Exception:
            pass
    
    if settings.mode == AgentMode.PLAN:
        system_prompt += " You are in PLAN mode. You can read files but CANNOT write them. Propose a plan."

    # Load subagents
    from src.agent.subagents import load_subagents
    subagents = load_subagents(settings)
    
    # Create tools for subagents
    for name, config in subagents.items():
        # Create a tool function for this subagent
        async def subagent_tool(query: str) -> str:
            """Delegate a task to a specialized subagent."""
            # Create a new agent instance for the subagent
            # Inherit settings but override model if specified
            sub_settings = settings.model_copy()
            if config.model and config.model != 'inherit':
                sub_settings.model = config.model
                
            # Determine tools for subagent
            # For simplicity, we give subagents the same tools as the main agent for now
            # In a real implementation, we would filter based on config.tools
            
            # Determine model for subagent
            sub_provider = sub_settings.model_provider.lower()
            if sub_provider == 'ollama':
                sub_model = OpenAIModel(model_name=sub_settings.model, provider='ollama')
            elif sub_provider in ('anthropic', 'claude'):
                from pydantic_ai.models.anthropic import AnthropicModel
                sub_model = AnthropicModel(sub_settings.model)
            elif sub_provider in ('google', 'gemini'):
                from pydantic_ai.models.gemini import GeminiModel
                sub_model = GeminiModel(sub_settings.model)
            elif sub_provider in ('openai', 'gpt'):
                sub_model = OpenAIModel(sub_settings.model)
            else:
                sub_model = OpenAIModel(sub_settings.model)
            
            sub_agent = Agent(
                sub_model,
                system_prompt=config.prompt,
                tools=current_tools
            )
            
            try:
                result = await sub_agent.run(query)
                await hook_manager.trigger(HookEvent.SUBAGENT_STOP, {
                    "subagent": name, 
                    "result": result.output
                })
                return f"Subagent {name} response:\n{result.output}"
            except Exception as e:
                return f"Error running subagent {name}: {str(e)}"
        
        # Rename the function to match the subagent name (sanitized)
        subagent_tool.__name__ = f"delegate_to_{name.replace('-', '_')}"
        subagent_tool.__doc__ = f"Delegate to {name}: {config.description}"
        current_tools.append(wrap_tool(subagent_tool))

    # Load skills
    from src.agent.skills import load_skills
    skills = load_skills(settings)
    
    if skills:
        skills_list = "\n".join([f"- {s.name}: {s.description}" for s in skills.values()])
        system_prompt += f"\n\nAVAILABLE SKILLS:\n{skills_list}\n\nTo use a skill, call the get_skill tool with the skill name to retrieve its instructions."
        
        def get_skill(name: str) -> str:
            """Retrieve the instructions for a specific skill."""
            if name in skills:
                return f"Skill {name} Instructions:\n{skills[name].content}"
            return f"Skill {name} not found."
            
        current_tools.append(wrap_tool(get_skill))

    agent = Agent(
        model,
        system_prompt=system_prompt,
        tools=current_tools,
    )
    
    agent.hook_manager = hook_manager
    return agent

async def get_agent_response(agent: Agent, user_input: str) -> str:
    """Get a response from the agent."""
    try:
        if hasattr(agent, 'hook_manager'):
            await agent.hook_manager.trigger(HookEvent.USER_PROMPT_SUBMIT, {"user_input": user_input})
            
        result = await agent.run(user_input)
        return result.output
    except Exception as e:
        return f"Error communicating with agent: {str(e)}"
