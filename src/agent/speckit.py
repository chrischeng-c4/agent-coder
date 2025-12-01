import os
import shutil
import re

def install_speckit(project_root: str):
    """Install SpecKit resources to the project."""
    
    # Source paths
    resources_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "speckit")
    
    # Destination paths
    agent_coder_dir = os.path.join(project_root, ".agent-coder")
    speckit_dir = os.path.join(agent_coder_dir, "speckit")
    skills_dir = os.path.join(agent_coder_dir, "skills")
    
    # Create directories
    os.makedirs(speckit_dir, exist_ok=True)
    os.makedirs(skills_dir, exist_ok=True)
    
    # Copy resources
    if os.path.exists(resources_dir):
        # Copy everything first
        if os.path.exists(speckit_dir):
            shutil.rmtree(speckit_dir)
        shutil.copytree(resources_dir, speckit_dir)
        
        # Patch scripts
        scripts_dir = os.path.join(speckit_dir, "scripts")
        for filename in os.listdir(scripts_dir):
            if filename.endswith(".sh"):
                filepath = os.path.join(scripts_dir, filename)
                with open(filepath, "r") as f:
                    content = f.read()
                
                # Patch template path: .specify/templates -> .agent-coder/speckit/templates
                content = content.replace(".specify/templates", ".agent-coder/speckit/templates")
                
                with open(filepath, "w") as f:
                    f.write(content)
                
                # Make executable
                os.chmod(filepath, 0o755)

        # Patch commands and install as skills
        commands_dir = os.path.join(speckit_dir, "commands")
        for filename in os.listdir(commands_dir):
            if filename.endswith(".md"):
                filepath = os.path.join(commands_dir, filename)
                with open(filepath, "r") as f:
                    content = f.read()
                
                # Determine script names based on filename
                # e.g. plan.md -> setup-plan.sh
                base_name = os.path.splitext(filename)[0]
                
                # Special cases mapping if needed, but spec-kit seems consistent
                # plan -> setup-plan.sh
                # specify -> setup-specify.sh
                # tasks -> setup-tasks.sh
                # analyze -> setup-analyze.sh
                # check -> setup-check.sh (if exists)
                
                script_name = f"setup-{base_name}.sh"
                script_path = f".agent-coder/speckit/scripts/{script_name}"
                
                # Replace {SCRIPT}
                # Note: The original md might have arguments in the yaml block, 
                # but in the text it uses {SCRIPT}.
                # We'll replace {SCRIPT} with the full command.
                
                # Check if script exists
                if os.path.exists(os.path.join(scripts_dir, script_name)):
                    full_command = f"{script_path} --json"
                    content = content.replace("{SCRIPT}", full_command)
                
                # Replace {AGENT_SCRIPT}
                agent_script_path = ".agent-coder/speckit/scripts/update-agent-context.sh"
                content = content.replace("{AGENT_SCRIPT}", agent_script_path)
                
                # Update header to be a valid skill
                # SpecKit headers are:
                # ---
                # description: ...
                # ...
                # ---
                # We need to ensure 'name' is present or let the loader handle it.
                # Our loader handles filename as name.
                # But let's add 'name: speckit-<cmd>' to be explicit.
                
                if not re.search(r"^name:", content, re.MULTILINE):
                    content = content.replace("---", f"---\nname: speckit-{base_name}", 1)
                
                # Write to skills dir
                skill_path = os.path.join(skills_dir, f"speckit-{filename}")
                with open(skill_path, "w") as f:
                    f.write(content)

    return True
