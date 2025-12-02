import os
import json
import subprocess
import threading
import time
from typing import Dict, Any, Optional, List

class JSONRPCClient:
    def __init__(self, command: List[str], cwd: str):
        self.command = command
        self.cwd = cwd
        self.process = None
        self.request_id = 0
        self.pending_requests: Dict[int, Any] = {}
        self.lock = threading.Lock()
        self.running = False
        
    def start(self):
        self.process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.cwd,
            bufsize=0
        )
        self.running = True
        self.reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.reader_thread.start()
        
    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()
            self.process = None

    def send_request(self, method: str, params: Any) -> Any:
        with self.lock:
            req_id = self.request_id
            self.request_id += 1
            
        request = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params
        }
        
        future = threading.Event()
        result_container = {}
        
        with self.lock:
            self.pending_requests[req_id] = (future, result_container)
            
        self._send(request)
        
        if not future.wait(timeout=10.0):
            with self.lock:
                del self.pending_requests[req_id]
            raise TimeoutError(f"LSP request {method} timed out")
            
        if "error" in result_container:
            raise Exception(f"LSP Error: {result_container['error']}")
            
        return result_container.get("result")

    def send_notification(self, method: str, params: Any):
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        self._send(request)

    def _send(self, data: Dict[str, Any]):
        content = json.dumps(data)
        header = f"Content-Length: {len(content)}\r\n\r\n"
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(header.encode('utf-8'))
                self.process.stdin.write(content.encode('utf-8'))
                self.process.stdin.flush()
            except BrokenPipeError:
                pass

    def _read_loop(self):
        while self.running and self.process:
            try:
                # Read header
                line = self.process.stdout.readline()
                if not line:
                    break
                
                line = line.decode('utf-8').strip()
                if not line.startswith("Content-Length:"):
                    continue
                    
                length = int(line.split(":")[1].strip())
                
                # Skip empty line
                self.process.stdout.readline()
                
                # Read body
                body = self.process.stdout.read(length)
                if not body:
                    break
                    
                message = json.loads(body.decode('utf-8'))
                
                if "id" in message and message["id"] is not None:
                    with self.lock:
                        if message["id"] in self.pending_requests:
                            future, container = self.pending_requests[message["id"]]
                            if "error" in message:
                                container["error"] = message["error"]
                            else:
                                container["result"] = message.get("result")
                            future.set()
                            del self.pending_requests[message["id"]]
                            
            except Exception as e:
                print(f"LSP Read Error: {e}")
                break

class LSPClient(JSONRPCClient):
    def __init__(self, command: List[str], root_uri: str):
        super().__init__(command, cwd=root_uri.replace("file://", ""))
        self.root_uri = root_uri
        self.capabilities = {}
        
    def initialize(self):
        self.start()
        params = {
            "processId": os.getpid(),
            "rootUri": self.root_uri,
            "capabilities": {
                "textDocument": {
                    "hover": {"dynamicRegistration": True},
                    "synchronization": {"dynamicRegistration": True, "didSave": True},
                    "completion": {"dynamicRegistration": True},
                    "definition": {"dynamicRegistration": True},
                    "references": {"dynamicRegistration": True}
                }
            }
        }
        result = self.send_request("initialize", params)
        self.capabilities = result.get("capabilities", {})
        self.send_notification("initialized", {})
        return result

    def did_open(self, file_path: str, content: str, language_id: str = "python"):
        uri = f"file://{file_path}"
        params = {
            "textDocument": {
                "uri": uri,
                "languageId": language_id,
                "version": 1,
                "text": content
            }
        }
        self.send_notification("textDocument/didOpen", params)

    def did_save(self, file_path: str):
        uri = f"file://{file_path}"
        params = {
            "textDocument": {
                "uri": uri
            }
        }
        self.send_notification("textDocument/didSave", params)

    def hover(self, file_path: str, line: int, character: int) -> str:
        uri = f"file://{file_path}"
        params = {
            "textDocument": {"uri": uri},
            "position": {"line": line - 1, "character": character}
        }
        result = self.send_request("textDocument/hover", params)
        if result and "contents" in result:
            contents = result["contents"]
            if isinstance(contents, dict) and "value" in contents:
                return contents["value"]
            elif isinstance(contents, list):
                return "\n".join([c if isinstance(c, str) else c.get("value", "") for c in contents])
            return str(contents)
        return "No hover info."

    def definition(self, file_path: str, line: int, character: int) -> str:
        uri = f"file://{file_path}"
        params = {
            "textDocument": {"uri": uri},
            "position": {"line": line - 1, "character": character}
        }
        result = self.send_request("textDocument/definition", params)
        return json.dumps(result, indent=2)

    def references(self, file_path: str, line: int, character: int) -> str:
        uri = f"file://{file_path}"
        params = {
            "textDocument": {"uri": uri},
            "position": {"line": line - 1, "character": character},
            "context": {"includeDeclaration": True}
        }
        result = self.send_request("textDocument/references", params)
        return json.dumps(result, indent=2)

    def rename(self, file_path: str, line: int, character: int, new_name: str) -> str:
        uri = f"file://{file_path}"
        params = {
            "textDocument": {"uri": uri},
            "position": {"line": line - 1, "character": character},
            "newName": new_name
        }
        result = self.send_request("textDocument/rename", params)
        return json.dumps(result, indent=2)
