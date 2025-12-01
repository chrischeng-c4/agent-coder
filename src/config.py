import os
from typing import List, Dict, Optional, Any
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from src.models import AgentMode

class Settings(BaseSettings):
    """
    Application settings using pydantic-settings.
    Reads from environment variables (prefix AGENT_CODER_) and optional .env file.
    """
    model_config = SettingsConfigDict(
        env_prefix='AGENT_CODER_',
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # Core Agent Settings
    model: str = Field(default="gpt-oss:20b", description="Name of the Ollama model to use")
    mode: AgentMode = Field(default=AgentMode.AUTO, description="Default operation mode")
    ollama_base_url: str = Field(default="http://localhost:11434/v1", description="Base URL for Ollama API")
    
    # Context & Performance
    max_context_size: int = Field(default=8192, description="Maximum context size for the model")
    temperature: float = Field(default=0.7, description="Model temperature")

    # Permissions & Security
    # Simple list of tools that are always allowed without confirmation (in Auto mode)
    # In Ask mode, everything requires confirmation.
    allow_tools: List[str] = Field(default=["read_file", "list_dir"], description="Tools allowed without explicit confirmation in restricted modes (future use)")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    def save_to_json(self, path: str = "settings.json"):
        """Save current settings to a JSON file."""
        with open(path, "w") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def load_from_json(cls, path: str = "settings.json") -> "Settings":
        """Load settings from a JSON file, overriding defaults."""
        if os.path.exists(path):
            with open(path, "r") as f:
                import json
                data = json.load(f)
            return cls(**data)
        return cls()

# Global settings instance
settings = Settings()
