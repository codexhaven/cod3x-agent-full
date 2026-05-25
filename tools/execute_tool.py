
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Execute Tool - Command execution and system operations
"""

import asyncio
import subprocess
import os
import json
import tempfile
import platform
from typing import Dict, Any, List, Optional
from pathlib import Path

class ExecuteTool:
    """
    Tool for executing shell commands and performing system operations in a controlled environment.
    """
    def __init__(self, config: Dict):
        self.config = config
        self.allowed_commands = config.get('execute', {}).get('allowed_commands', [
            'ls', 'dir', 'pwd', 'echo', 'date', 'time',
            'cat', 'head', 'tail', 'grep', 'find',
            'python --version', 'pip list', 'node --version',
            'git status', 'git log', 'whoami', 'hostname'
        ])
        self.working_directory = config.get('execute', {}).get('working_directory', os.getcwd())
        self.initialized = False
        self.sandbox_mode = config.get('execute', {}).get('sandbox_mode', True)
    
    async def initialize(self):
        """Initialize execute tool and verify working directory exists."""
        try:
            os.makedirs(self.working_directory, exist_ok=True)
            self.initialized = True
        except Exception as e:
            self.initialized = False

    async def execute(self, command: str, timeout: int = 30, working_dir: str = None) -> Dict:
        """Execute a shell command with validation and timeout."""
        if not self.initialized:
            return {'status': 'error', 'message': 'Execute tool not initialized'}
        
        if not command or not isinstance(command, str):
            return {'status': 'error', 'message': 'Invalid command provided'}

        if self.sandbox_mode and not self._is_allowed(command):
            return {
                'status': 'blocked',
                'message': 'Command not in allowed list',
                'command': command
            }
        
        try:
            cwd = working_dir or self.working_directory
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=max(1, timeout)
            )
            
            return {
                'status': 'success' if result.returncode == 0 else 'error',
                'command': command,
                'returncode': result.returncode,
                'stdout': result.stdout[:2000],
                'stderr': result.stderr[:1000]
            }
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'command': command,
                'message': 'Command timed out'
            }
        except Exception as e:
            return {'status': 'error', 'command': command, 'message': str(e)}
    
    def _is_allowed(self, command: str) -> bool:
        """Check if command is in allowed list."""
        if not command:
            return False
        cmd_base = command.strip().split()[0]
        
        for allowed in self.allowed_commands:
            if command.startswith(allowed) or cmd_base == allowed.split()[0]:
                return True
        return False
    
    async def execute_python(self, code: str, timeout: int = 10) -> Dict:
        """Execute Python code snippet securely."""
        if not code:
            return {'status': 'error', 'message': 'Empty code block'}
            
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = await self.execute(f'python {temp_file}', timeout=timeout)
            return result
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
        finally:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
    
    async def read_file(self, filepath: str) -> Dict:
        """Read file contents safely."""
        if not filepath:
            return {'status': 'error', 'message': 'No filepath provided'}
            
        try:
            full_path = os.path.abspath(os.path.join(self.working_directory, filepath))
            
            if not full_path.startswith(os.path.abspath(self.working_directory)):
                return {'status': 'error', 'message': 'Access denied'}
                
            if not os.path.exists(full_path):
                return {'status': 'error', 'message': 'File not found'}
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                'status': 'success',
                'file': filepath,
                'content': content[:5000],
                'size': len(content)
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    async def write_file(self, filepath: str, content: str) -> Dict:
        """Write content to file securely."""
        if not filepath:
            return {'status': 'error', 'message': 'No filepath provided'}
            
        try:
            full_path = os.path.abspath(os.path.join(self.working_directory, filepath))
            
            if not full_path.startswith(os.path.abspath(self.working_directory)):
                return {'status': 'error', 'message': 'Access denied'}
            
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content or '')
            
            return {'status': 'success', 'file': filepath, 'size': len(content or '')}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    async def list_directory(self, path: str = '.') -> Dict:
        """List directory contents."""
        try:
            full_path = os.path.abspath(os.path.join(self.working_directory, path))
            
            if not full_path.startswith(os.path.abspath(self.working_directory)):
                return {'status': 'error', 'message': 'Access denied'}
                
            items = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                items.append({
                    'name': item,
                    'type': 'directory' if os.path.isdir(item_path) else 'file',
                    'size': os.path.getsize(item_path) if os.path.isfile(item_path) else 0
                })
            
            return {'status': 'success', 'path': path, 'items': items}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    async def get_system_info(self) -> Dict:
        """Get system information."""
        info = {
            'platform': os.name,
            'cwd': os.getcwd(),
            'home': os.path.expanduser('~'),
            'python_version': sys.version
        }
        
        try:
            info['os'] = platform.system()
            info['os_version'] = platform.version()
            info['processor'] = platform.processor()
        except Exception:
            pass
        
        return {'status': 'success', 'system_info': info}
    
    async def shutdown(self):
        """Cleanup tool state."""
        self.initialized = False