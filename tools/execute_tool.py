"""
Execute Tool - Command execution and system operations
"""

import asyncio
import subprocess
import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

class ExecuteTool:
    def __init__(self, config: Dict):
        self.config = config
        self.allowed_commands = config.get('execute', {}).get('allowed_commands', [
            'ls', 'dir', 'pwd', 'echo', 'date', 'time',
            'cat', 'head', 'tail', 'grep', 'find',
            'python --version', 'pip list', 'node --version',
            'git status', 'git log', 'whoami', 'hostname'
        ])
        self.working_directory = config.get('execute', {}).get('working_directory', os.getcwd())
        self.initialized = True
        self.sandbox_mode = config.get('execute', {}).get('sandbox_mode', True)
    
    async def initialize(self):
        """Initialize execute tool"""
        os.makedirs(self.working_directory, exist_ok=True)
        self.initialized = True
    
    async def execute(self, command: str, timeout: int = 30, working_dir: str = None) -> Dict:
        """Execute a shell command"""
        if not self.initialized:
            return {"status": "error", "message": "Execute tool not initialized"}
        
        # Check if command is allowed
        if self.sandbox_mode and not self._is_allowed(command):
            return {
                "status": "blocked",
                "message": f"Command not in allowed list: {command}",
                "allowed_commands": self.allowed_commands
            }
        
        try:
            # Set working directory
            cwd = working_dir or self.working_directory
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "status": "timeout",
                    "command": command,
                    "message": f"Command timed out after {timeout} seconds"
                }
            
            stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ""
            
            return {
                "status": "success" if process.returncode == 0 else "error",
                "command": command,
                "returncode": process.returncode,
                "stdout": stdout_text[:2000],  # Limit output
                "stderr": stderr_text[:1000]
            }
        except Exception as e:
            return {"status": "error", "command": command, "message": str(e)}
    
    def _is_allowed(self, command: str) -> bool:
        """Check if command is in allowed list"""
        cmd_base = command.strip().split()[0] if command.strip() else ""
        
        for allowed in self.allowed_commands:
            if command.startswith(allowed) or cmd_base == allowed.split()[0]:
                return True
        
        return False
    
    async def execute_python(self, code: str, timeout: int = 10) -> Dict:
        """Execute Python code snippet"""
        try:
            # Create a temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                result = await self.execute(f"python {temp_file}", timeout=timeout)
                return result
            finally:
                os.unlink(temp_file)
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def read_file(self, filepath: str) -> Dict:
        """Read file contents"""
        try:
            # Ensure file is within working directory
            full_path = os.path.join(self.working_directory, filepath)
            
            if not os.path.exists(full_path):
                return {"status": "error", "message": "File not found"}
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "status": "success",
                "file": filepath,
                "content": content[:5000],  # Limit size
                "size": len(content)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def write_file(self, filepath: str, content: str) -> Dict:
        """Write content to file"""
        try:
            full_path = os.path.join(self.working_directory, filepath)
            
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {"status": "success", "file": filepath, "size": len(content)}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def list_directory(self, path: str = ".") -> Dict:
        """List directory contents"""
        try:
            full_path = os.path.join(self.working_directory, path)
            
            items = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                items.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0
                })
            
            return {"status": "success", "path": path, "items": items}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def get_system_info(self) -> Dict:
        """Get system information"""
        info = {
            "platform": os.name,
            "cwd": os.getcwd(),
            "home": os.path.expanduser("~"),
            "python_version": __import__('sys').version
        }
        
        try:
            import platform
            info["os"] = platform.system()
            info["os_version"] = platform.version()
            info["processor"] = platform.processor()
        except:
            pass
        
        return {"status": "success", "system_info": info}
    
    async def shutdown(self):
        """Cleanup"""
        self.initialized = False
