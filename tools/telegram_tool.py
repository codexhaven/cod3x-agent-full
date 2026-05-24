"""
Telegram Tool - Telegram Bot integration
"""

import asyncio
from typing import Dict, Any, List, Optional
import json
import os

class TelegramTool:
    def __init__(self, config: Dict):
        self.config = config
        self.bot_token = config.get('telegram', {}).get('bot_token') or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = config.get('telegram', {}).get('chat_id')
        self.initialized = bool(self.bot_token)
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    async def initialize(self):
        """Initialize Telegram bot"""
        if self.bot_token:
            try:
                # Test connection
                response = await self._make_request('getMe')
                if response.get('ok'):
                    bot_info = response.get('result', {})
                    print(f"Telegram bot connected: @{bot_info.get('username')}")
                    self.initialized = True
                    return True
            except Exception as e:
                print(f"Telegram init error: {e}")
        
        self.initialized = False
        return False
    
    async def _make_request(self, method: str, params: Dict = None) -> Dict:
        """Make Telegram API request"""
        try:
            import aiohttp
            
            url = f"{self.base_url}/{method}"
            
            async with aiohttp.ClientSession() as session:
                if params:
                    async with session.post(url, json=params) as response:
                        return await response.json()
                else:
                    async with session.get(url) as response:
                        return await response.json()
        except ImportError:
            print("aiohttp required for Telegram")
            return {"ok": False, "error": "aiohttp not installed"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    async def send_message(self, chat_id: str = None, text: str = "", parse_mode: str = "HTML") -> Dict:
        """Send a message"""
        if not self.initialized:
            return {"status": "offline"}
        
        target_chat = chat_id or self.chat_id
        if not target_chat:
            return {"status": "error", "message": "No chat ID specified"}
        
        return await self._make_request('sendMessage', {
            'chat_id': target_chat,
            'text': text,
            'parse_mode': parse_mode
        })
    
    async def broadcast_message(self, text: str) -> Dict:
        """Broadcast to channel (if configured)"""
        channel_id = self.config.get('telegram', {}).get('channel_id')
        if channel_id:
            return await self.send_message(channel_id, text)
        return {"status": "error", "message": "No channel configured"}
    
    async def get_updates(self, limit: int = 10, offset: int = None) -> List[Dict]:
        """Get recent updates"""
        if not self.initialized:
            return []
        
        params = {'limit': limit}
        if offset:
            params['offset'] = offset
        
        response = await self._make_request('getUpdates', params)
        
        if response.get('ok'):
            return response.get('result', [])
        
        return []
    
    async def send_photo(self, chat_id: str, photo_url: str, caption: str = "") -> Dict:
        """Send a photo"""
        if not self.initialized:
            return {"status": "offline"}
        
        return await self._make_request('sendPhoto', {
            'chat_id': chat_id,
            'photo': photo_url,
            'caption': caption
        })
    
    async def send_document(self, chat_id: str, document_url: str, caption: str = "") -> Dict:
        """Send a document"""
        if not self.initialized:
            return {"status": "offline"}
        
        return await self._make_request('sendDocument', {
            'chat_id': chat_id,
            'document': document_url,
            'caption': caption
        })
    
    async def set_webhook(self, webhook_url: str) -> Dict:
        """Set webhook for receiving updates"""
        return await self._make_request('setWebhook', {'url': webhook_url})
    
    async def test_connection(self) -> bool:
        """Test if bot is connected"""
        if not self.bot_token:
            return False
        
        response = await self._make_request('getMe')
        return response.get('ok', False)
    
    async def shutdown(self):
        """Cleanup"""
        self.initialized = False
