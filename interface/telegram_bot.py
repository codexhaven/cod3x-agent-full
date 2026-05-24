"""
Telegram Bot Interface - Telegram-based interaction
"""

import asyncio
from typing import Dict, Any, Optional
import json
import os
from datetime import datetime

class TelegramInterface:
    def __init__(self, cod3x, config: Dict):
        self.cod3x = cod3x
        self.config = config
        self.logger = cod3x.logger
        self.bot_token = config.get('telegram', {}).get('bot_token') or os.getenv('TELEGRAM_BOT_TOKEN')
        self.allowed_users = config.get('telegram', {}).get('allowed_users', [])
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.running = False
        self.offset = 0
        
        # Command handlers
        self.commands = {
            '/start': self._cmd_start,
            '/help': self._cmd_help,
            '/status': self._cmd_status,
            '/tasks': self._cmd_tasks,
            '/calendar': self._cmd_calendar,
            '/search': self._cmd_search,
            '/clear': self._cmd_clear,
            '/stats': self._cmd_stats,
            '/agents': self._cmd_agents,
            '/tools': self._cmd_tools
        }
    
    async def initialize(self):
        """Initialize Telegram bot"""
        if not self.bot_token:
            self.logger.error("No Telegram bot token configured")
            return False
        
        try:
            # Test connection
            response = await self._make_request('getMe')
            if response.get('ok'):
                bot_info = response.get('result', {})
                self.logger.info(f"Telegram bot connected: @{bot_info.get('username')}")
                return True
            else:
                self.logger.error(f"Telegram bot connection failed: {response}")
                return False
        except Exception as e:
            self.logger.error(f"Telegram init error: {e}")
            return False
    
    async def run(self):
        """Run Telegram bot polling"""
        if not await self.initialize():
            self.logger.error("Failed to initialize Telegram bot")
            return
        
        self.running = True
        self.logger.info("🤖 Telegram bot started. Waiting for messages...")
        
        try:
            while self.running:
                try:
                    updates = await self._get_updates()
                    
                    for update in updates:
                        await self._process_update(update)
                    
                    await asyncio.sleep(1)  # Poll every second
                    
                except Exception as e:
                    self.logger.error(f"Polling error: {e}")
                    await asyncio.sleep(5)  # Wait longer on error
        
        except KeyboardInterrupt:
            self.logger.info("Telegram bot stopped")
        finally:
            self.running = False
    
    async def _get_updates(self) -> list:
        """Get pending updates"""
        try:
            import aiohttp
            
            params = {
                'offset': self.offset,
                'timeout': 30,
                'allowed_updates': ['message']
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/getUpdates", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('result', [])
        except Exception as e:
            self.logger.error(f"Get updates error: {e}")
        
        return []
    
    async def _process_update(self, update: Dict):
        """Process a single update"""
        try:
            message = update.get('message')
            if not message:
                return
            
            # Update offset
            self.offset = update.get('update_id', 0) + 1
            
            # Extract message details
            chat_id = message.get('chat', {}).get('id')
            user_id = str(message.get('from', {}).get('id', chat_id))
            username = message.get('from', {}).get('username', 'unknown')
            text = message.get('text', '')
            
            # Check user authorization
            if self.allowed_users and username not in self.allowed_users:
                await self._send_message(chat_id, "⛔ You are not authorized to use this bot.")
                return
            
            # Process command or message
            if text.startswith('/'):
                await self._handle_command(chat_id, user_id, text)
            else:
                await self._handle_message(chat_id, user_id, text, username)
                
        except Exception as e:
            self.logger.error(f"Process update error: {e}")
    
    async def _handle_command(self, chat_id: int, user_id: str, command: str):
        """Handle bot commands"""
        cmd_parts = command.split()
        cmd = cmd_parts[0].lower()
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []
        
        if cmd in self.commands:
            response = await self.commands[cmd](user_id, args)
        else:
            response = "Unknown command. Use /help to see available commands."
        
        await self._send_message(chat_id, response)
    
    async def _handle_message(self, chat_id: int, user_id: str, text: str, username: str):
        """Handle regular messages"""
        # Send typing indicator
        await self._send_chat_action(chat_id, 'typing')
        
        # Process through Cod3x
        try:
            response = await self.cod3x.process_request(text, user_id)
            
            # Split long messages
            if len(response) > 4000:
                chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
                for chunk in chunks:
                    await self._send_message(chat_id, chunk)
                    await asyncio.sleep(0.5)
            else:
                await self._send_message(chat_id, response)
                
        except Exception as e:
            self.logger.error(f"Message processing error: {e}")
            await self._send_message(chat_id, "Sorry, I encountered an error processing your request.")
    
    async def _send_message(self, chat_id: int, text: str, parse_mode: str = "HTML"):
        """Send a message"""
        try:
            import aiohttp
            
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/sendMessage", json=data) as response:
                    return await response.json()
        except Exception as e:
            self.logger.error(f"Send message error: {e}")
    
    async def _send_chat_action(self, chat_id: int, action: str = 'typing'):
        """Send chat action (typing indicator)"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/sendChatAction", 
                    json={'chat_id': chat_id, 'action': action}) as response:
                    pass
        except:
            pass
    
    async def _make_request(self, method: str, params: Dict = None) -> Dict:
        """Make generic Telegram API request"""
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
        except:
            return {"ok": False}
    
    # Command handlers
    async def _cmd_start(self, user_id: str, args: list) -> str:
        return """🚀 *Welcome to Cod3x Agent!*

I'm your multi-agent AI assistant. I can help with:
• 📅 Calendar & Tasks
• 📧 Email & Communications
• 💰 Expenses & Travel
• 🔍 Research & Search
• 🎨 Content & Social Media
• 💎 Crypto Tracking

Type /help for commands or just ask me anything!"""
    
    async def _cmd_help(self, user_id: str, args: list) -> str:
        return """📚 *Available Commands:*

/start - Welcome message
/help - This help menu
/status - System status
/tasks - View your tasks
/calendar - Upcoming events
/search [query] - Web search
/clear - Clear conversation
/stats - Memory statistics
/agents - List active agents
/tools - Available tools

*You can also just chat naturally!*"""
    
    async def _cmd_status(self, user_id: str, args: list) -> str:
        stats = await self.cod3x.memory['buffer'].get_stats()
        return f"""📊 *System Status*

✅ Nexus Supervisor: Active
✅ Agents: {len(self.cod3x.agents)} loaded
✅ Memory: {stats['active_users']} users, {stats['total_messages']} messages
✅ Tools: {len(self.cod3x.tools)} available

Type /agents for detailed agent list."""
    
    async def _cmd_tasks(self, user_id: str, args: list) -> str:
        response = await self.cod3x.agents['tasks'].process('list tasks', user_id)
        return response
    
    async def _cmd_calendar(self, user_id: str, args: list) -> str:
        response = await self.cod3x.agents['calendar'].process('upcoming events', user_id)
        return response
    
    async def _cmd_search(self, user_id: str, args: list) -> str:
        query = ' '.join(args) if args else 'latest news'
        response = await self.cod3x.agents['search'].process(f'search for {query}', user_id)
        return response
    
    async def _cmd_clear(self, user_id: str, args: list) -> str:
        await self.cod3x.memory['buffer'].clear(user_id)
        return "🧹 Conversation cleared. Starting fresh!"
    
    async def _cmd_stats(self, user_id: str, args: list) -> str:
        buffer_stats = await self.cod3x.memory['buffer'].get_stats()
        vector_stats = await self.cod3x.memory['vector'].get_stats()
        sqlite_stats = await self.cod3x.memory['sqlite'].get_stats()
        
        return f"""📈 *Memory Statistics*

*Buffer:* {buffer_stats['total_messages']} messages, {buffer_stats['active_users']} users
*Vector:* {vector_stats['total_documents']} documents
*SQLite:* {sqlite_stats['tables']} tables active"""
    
    async def _cmd_agents(self, user_id: str, args: list) -> str:
        agents_list = "\n".join([f"• {name.title()}" for name in self.cod3x.agents.keys()])
        return f"🤖 *Active Agents ({len(self.cod3x.agents)}):*\n\n{agents_list}"
    
    async def _cmd_tools(self, user_id: str, args: list) -> str:
        tools_list = "\n".join([f"• {name.title()}" for name in self.cod3x.tools.keys()])
        return f"🔧 *Available Tools ({len(self.cod3x.tools)}):*\n\n{tools_list}"
    
    async def shutdown(self):
        """Cleanup"""
        self.running = False
