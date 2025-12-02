import os
import shlex
from typing import List, Any, Callable
from src.config import Settings
from src.agent.lsp import LSPClient
from src.agent.hooks import HookEvent

class LSPManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client: Optional[LSPClient] = None
        self.tools: List[Any] = []
        
    def start(self):
        if not self.settings.lsp_enabled:
            return

        try:
            command = shlex.split(self.settings.lsp_command)
            root_uri = f"file://{os.getcwd()}"
            
            self.client = LSPClient(command, root_uri)
            self.client.initialize()
            print(f"LSP Server started: {self.settings.lsp_command}")
            
            # Register tools
            self.tools = [
                self.lsp_hover,
                self.lsp_definition,
                self.lsp_references
            ]
            
        except Exception as e:
            print(f"Failed to start LSP server: {e}")

    def stop(self):
        if self.client:
            self.client.stop()

    def lsp_hover(self, file_path: str, line: int, character: int) -> str:
        """Get hover information for a symbol at the specified position."""
        if not self.client: return "LSP not running."
        # Ensure file is open
        self._ensure_open(file_path)
        return self.client.hover(file_path, line, character)

    def lsp_definition(self, file_path: str, line: int, character: int) -> str:
        """Get definition location for a symbol."""
        if not self.client: return "LSP not running."
        self._ensure_open(file_path)
        return self.client.definition(file_path, line, character)

    def lsp_references(self, file_path: str, line: int, character: int) -> str:
        """Find references to a symbol."""
        if not self.client: return "LSP not running."
        self._ensure_open(file_path)
        return self.client.references(file_path, line, character)

    def _ensure_open(self, file_path: str):
        # In a real impl, we track open files. For now, we just send didOpen every time 
        # (inefficient but safe if server handles it, or we check if we sent it).
        # Better: Read file content and send didOpen.
        if not os.path.exists(file_path):
            return
            
        with open(file_path, "r") as f:
            content = f.read()
        
        # Determine language ID
        ext = os.path.splitext(file_path)[1]
        lang_id = "python"
        if ext == ".rs": lang_id = "rust"
        elif ext == ".js": lang_id = "javascript"
        elif ext == ".ts": lang_id = "typescript"
        elif ext == ".go": lang_id = "go"
        
        self.client.did_open(file_path, content, lang_id)

    async def on_post_tool_use(self, event_data: dict):
        """Hook to handle file changes."""
        if not self.client: return
        
        tool_name = event_data.get("tool_name")
        if tool_name == "write_file":
            args = event_data.get("args", [])
            kwargs = event_data.get("kwargs", {})
            
            # write_file(path, content)
            path = kwargs.get("path") or (args[0] if len(args) > 0 else None)
            
            if path:
                self.client.did_save(path)
