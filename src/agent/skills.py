import os
import yaml
from typing import Dict, List, Optional
from pydantic import BaseModel
from src.config import Settings

class SkillConfig(BaseModel):
    name: str
    description: str
    allowed_tools: Optional[List[str]] = None
    content: str

def load_skills(settings: Settings) -> Dict[str, SkillConfig]:
    """Load skills from .claude/skills directory."""
    skills = {}
    
    # Check .claude/skills/
    skills_dir = os.path.join(os.getcwd(), ".claude", "skills")
    if not os.path.exists(skills_dir):
        return skills
        
    # Walk through the directory to find SKILL.md files
    # Skills can be single files or directories containing SKILL.md
    for root, dirs, files in os.walk(skills_dir):
        for filename in files:
            if filename == "SKILL.md" or (root == skills_dir and filename.endswith(".md")):
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, "r") as f:
                        content = f.read()
                        if content.startswith("---"):
                            parts = content.split("---", 2)
                            if len(parts) >= 3:
                                yaml_content = parts[1]
                                body = parts[2].strip()
                                
                                config_data = yaml.safe_load(yaml_content)
                                # If name is not in frontmatter, infer from filename or directory
                                if "name" not in config_data:
                                    if filename == "SKILL.md":
                                        config_data["name"] = os.path.basename(root)
                                    else:
                                        config_data["name"] = os.path.splitext(filename)[0]
                                
                                config_data["content"] = body
                                skill = SkillConfig(**config_data)
                                skills[skill.name] = skill
                except Exception as e:
                    print(f"Error loading skill {file_path}: {e}")
                
    return skills
