import os
import yaml
from typing import Dict, List, Optional
from pydantic import BaseModel
from src.config import Settings

class SubAgentConfig(BaseModel):
    name: str
    description: str
    prompt: str
    tools: List[str] = []
    model: Optional[str] = None
    permission_mode: str = "default"

def load_subagents(settings: Settings) -> Dict[str, SubAgentConfig]:
    """Load subagents from .claude/agents directory."""
    agents = {}
    
    # Check .claude/agents/
    agents_dir = os.path.join(os.getcwd(), ".claude", "agents")
    if not os.path.exists(agents_dir):
        return agents
        
    for filename in os.listdir(agents_dir):
        if filename.endswith(".yaml") or filename.endswith(".yml"):
            try:
                with open(os.path.join(agents_dir, filename), "r") as f:
                    # Parse frontmatter-like YAML
                    # The format described is:
                    # ---
                    # name: ...
                    # ---
                    # System prompt
                    
                    content = f.read()
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            yaml_content = parts[1]
                            system_prompt = parts[2].strip()
                            
                            config_data = yaml.safe_load(yaml_content)
                            config_data["prompt"] = system_prompt
                            
                            agent_config = SubAgentConfig(**config_data)
                            agents[agent_config.name] = agent_config
            except Exception as e:
                print(f"Error loading subagent {filename}: {e}")
                
    return agents
