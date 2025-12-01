from enum import Enum
from pydantic import BaseModel, Field

class AgentMode(str, Enum):
    AUTO = 'auto'
    PLAN = 'plan'
    ASK = 'ask'

class AgentConfig(BaseModel):
    model_name: str = Field(default="gpt-oss:20b", description="Name of the Ollama model")
    mode: AgentMode = Field(default=AgentMode.AUTO, description="Operation mode of the agent")
    ollama_base_url: str = Field(default="http://localhost:11434/v1", description="Base URL for Ollama API")
