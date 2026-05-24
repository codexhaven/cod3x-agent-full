"""
Configuration Management
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

class Config:
    def __init__(self, config_path: str = 'config.yaml'):
        self.config_path = config_path
        self.data = {}
        self._load_config()
        self._load_env_vars()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    self.data = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Error loading config: {e}")
                self.data = {}
        else:
            # Create default config
            self.data = self._get_default_config()
            self._save_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'gemini_api_key': os.getenv('GEMINI_API_KEY', ''),
            
            'logging': {
                'level': 'INFO',
                'file': 'cod3x.log',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            
            'memory': {
                'buffer_size': 100,
                'buffer_ttl': 60,
                'vector_storage_path': 'vector_memory.pkl',
                'sqlite_path': 'cod3x_memory.db',
                'use_gemini_embeddings': True
            },
            
            'google': {
                'credentials_file': 'credentials.json',
                'spreadsheet_id': None
            },
            
            'serpapi': {
                'api_key': os.getenv('SERPAPI_API_KEY', '')
            },
            
            'telegram': {
                'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
                'chat_id': os.getenv('TELEGRAM_CHAT_ID', ''),
                'channel_id': None,
                'allowed_users': []
            },
            
            'twitter': {
                'api_key': os.getenv('TWITTER_API_KEY', ''),
                'api_secret': os.getenv('TWITTER_API_SECRET', ''),
                'access_token': os.getenv('TWITTER_ACCESS_TOKEN', ''),
                'access_secret': os.getenv('TWITTER_ACCESS_SECRET', '')
            },
            
            'notifications': {
                'method': 'desktop',
                'sound': True
            },
            
            'voice': {
                'wake_word': 'hey cod3x',
                'language': 'en-US',
                'speaker_voice': 'default',
                'speaking_rate': 175,
                'volume': 1.0
            },
            
            'execute': {
                'sandbox_mode': True,
                'working_directory': os.getcwd(),
                'allowed_commands': [
                    'ls', 'pwd', 'echo', 'date',
                    'cat', 'head', 'tail', 'grep',
                    'python --version', 'pip list',
                    'git status', 'whoami'
                ]
            },
            
            'cli': {
                'history_size': 100
            }
        }
    
    def _load_env_vars(self):
        """Override config with environment variables"""
        env_mappings = {
            'GEMINI_API_KEY': ('gemini_api_key',),
            'SERPAPI_API_KEY': ('serpapi', 'api_key'),
            'TELEGRAM_BOT_TOKEN': ('telegram', 'bot_token'),
            'TELEGRAM_CHAT_ID': ('telegram', 'chat_id'),
            'TWITTER_API_KEY': ('twitter', 'api_key'),
            'TWITTER_API_SECRET': ('twitter', 'api_secret'),
        }
        
        for env_var, path in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                target = self.data
                for key in path[:-1]:
                    if key not in target:
                        target[key] = {}
                    target = target[key]
                target[path[-1]] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.data
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        target = self.data
        
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        
        target[keys[-1]] = value
    
    def update(self, updates: Dict):
        """Update multiple configuration values"""
        self.data.update(updates)
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.data, f, default_flow_style=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_all(self) -> Dict:
        """Get entire configuration"""
        return self.data.copy()
    
    def validate(self) -> Dict:
        """Validate configuration and return warnings"""
        warnings = []
        
        # Check required API keys
        if not self.get('gemini_api_key'):
            warnings.append("GEMINI_API_KEY not set. AI features will be limited.")
        
        if not self.get('serpapi.api_key'):
            warnings.append("SERPAPI_API_KEY not set. Web search will be limited.")
        
        if not self.get('telegram.bot_token'):
            warnings.append("TELEGRAM_BOT_TOKEN not set. Telegram bot won't work.")
        
        return {
            'valid': len([w for w in warnings if 'required' in w.lower()]) == 0,
            'warnings': warnings
        }
