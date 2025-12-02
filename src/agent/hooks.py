import os
import json
import subprocess
import asyncio
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from enum import Enum

class HookEvent(str, Enum):
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    USER_PROMPT_SUBMIT = "UserPromptSubmit"
    SESSION_START = "SessionStart"
    SESSION_END = "SessionEnd"
    SUBAGENT_STOP = "SubagentStop"
    PRE_COMPACT = "PreCompact"
    # Add others as needed

class HookType(str, Enum):
    COMMAND = "command"

class HookAction(BaseModel):
    type: HookType
    command: str

class HookRule(BaseModel):
    matcher: Optional[str] = None # For tool name matching, etc.
    hooks: List[HookAction]

class HookConfig(BaseModel):
    hooks: Dict[HookEvent, List[HookRule]] = Field(default_factory=dict)

class HookManager:
    def __init__(self, config_path: Optional[str] = None):
        self.config = HookConfig()
        self.cwd = os.getcwd()
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)
        else:
            # Try default locations
            default_paths = [
                os.path.join(self.cwd, ".agent-coder", "hooks.json"),
                os.path.join(self.cwd, ".claude", "hooks.json")
            ]
            for path in default_paths:
                if os.path.exists(path):
                    self.load_config(path)
                    break

    def load_config(self, path: str):
        try:
            with open(path, "r") as f:
                data = json.load(f)
            self.config = HookConfig(**data)
            print(f"Loaded hooks from {path}")
        except Exception as e:
            print(f"Error loading hooks from {path}: {e}")

    async def trigger(self, event: HookEvent, context: Dict[str, Any]):
        if event not in self.config.hooks:
            return

        rules = self.config.hooks[event]
        for rule in rules:
            if self._matches(rule, context):
                await self._execute_hooks(rule.hooks, context)

    def _matches(self, rule: HookRule, context: Dict[str, Any]) -> bool:
        if not rule.matcher:
            return True
        
        # Simple matching logic
        # For PreToolUse/PostToolUse, matcher checks tool name
        if "tool_name" in context:
            return rule.matcher == context["tool_name"] or rule.matcher == "*"
            
        return True

    async def _execute_hooks(self, actions: List[HookAction], context: Dict[str, Any]):
        # Prepare input JSON for the hook
        hook_input = json.dumps({
            "cwd": self.cwd,
            **context
        })

        for action in actions:
            if action.type == HookType.COMMAND:
                try:
                    # Run the command
                    process = await asyncio.create_subprocess_shell(
                        action.command,
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate(input=hook_input.encode())
                    
                    if process.returncode != 0:
                        print(f"Hook command '{action.command}' failed with code {process.returncode}")
                        print(f"Stderr: {stderr.decode()}")
                    else:
                        # Check for JSON output if needed (for decision control)
                        # For now, just print stdout if it's not empty
                        if stdout:
                            print(f"Hook output: {stdout.decode()}")
                            
                except Exception as e:
                    print(f"Error executing hook '{action.command}': {e}")
