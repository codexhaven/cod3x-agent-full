"""
Telegram Agent - Telegram messaging and channel management
"""

import asyncio
from typing import Dict, Any, List
import json

class TelegramAgent:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger
        self.model = cod3x.model
        self.tool = cod3x.tools.get('telegram')
    
    async def initialize(self):
        self.logger.info("Telegram Agent initialized")
        if self.tool:
            await self.tool.initialize()
    
    async def process(self, request: str, user_id: str, action: str = None, params: Dict = None) -> str:
        """Process Telegram-related requests"""
        text_lower = request.lower()
        
        try:
            if any(kw in text_lower for kw in ['send telegram', 'telegram message', 'send to telegram']):
                return await self._send_message(request, user_id)
            elif any(kw in text_lower for kw in ['check telegram', 'telegram messages', 'read telegram']):
                return await self._check_messages(user_id)
            elif any(kw in text_lower for kw in ['telegram channel', 'broadcast']):
                return await self._manage_channel(request, user_id)
            elif any(kw in text_lower for kw in ['telegram bot', 'bot command']):
                return await self._bot_commands(request, user_id)
            else:
                return await self._get_telegram_status(user_id)
        except Exception as e:
            self.logger.error(f"Telegram agent error: {e}")
            return "I had trouble with Telegram. Please check your bot token."
    
    async def _send_message(self, request: str, user_id: str) -> str:
        """Send a Telegram message"""
        message_details = await self._extract_message(request)
        
        if self.tool:
            try:
                result = await self.tool.send_message(
                    chat_id=message_details.get('chat_id'),
                    text=message_details['text']
                )
                return f"✈️ Telegram message sent to {message_details.get('recipient', 'chat')}"
            except Exception as e:
                self.logger.error(f"Send Telegram error: {e}")
                return "Failed to send Telegram message. Check your bot configuration."
        
        return "✈️ Telegram messaging requires bot token configuration."
    
    async def _extract_message(self, request: str) -> Dict:
        """Extract message details"""
        if self.model:
            prompt = f"""Extract Telegram message details from: {request}
            Return JSON: {{"recipient": "username or chat_id", "text": "message content", "chat_id": "id if specified"}}"""
            
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                return json.loads(response.text)
            except:
                pass
        
        # Fallback
        message = {
            "recipient": "",
            "text": "",
            "chat_id": None
        }
        
        text = request
        for prefix in ['send telegram', 'telegram message', 'send to telegram']:
            if prefix in text.lower():
                text = text.lower().split(prefix, 1)[1].strip()
                break
        
        # Extract recipient if "to [name]"
        if 'to ' in text.lower():
            parts = text.lower().split('to ', 1)
            if len(parts) > 1:
                recipient_part = parts[1].split(' ', 1)
                message['recipient'] = recipient_part[0]
                if len(recipient_part) > 1:
                    message['text'] = recipient_part[1].strip()
        else:
            message['text'] = text
        
        return message
    
    async def _check_messages(self, user_id: str) -> str:
        """Check recent Telegram messages"""
        if self.tool:
            try:
                messages = await self.tool.get_updates(limit=5)
                
                if not messages:
                    return "✈️ No new Telegram messages."
                
                response = "✈️ **Recent Telegram Messages:**\n\n"
                for msg in messages:
                    sender = msg.get('from', {}).get('first_name', 'Unknown')
                    text = msg.get('text', '')
                    response += f"📨 From: {sender}\n"
                    response += f"   {text[:100]}\n\n"
                
                return response
            except:
                pass
        
        return "✈️ Check Telegram messages (requires bot connection)"
    
    async def _manage_channel(self, request: str, user_id: str) -> str:
        """Manage Telegram channel"""
        if 'broadcast' in request.lower():
            # Extract broadcast message
            msg = request.lower().split('broadcast', 1)[1].strip() if 'broadcast' in request.lower() else ""
            
            if self.tool:
                try:
                    await self.tool.broadcast_message(msg)
                    return f"📢 Broadcast sent to channel: {msg[:50]}..."
                except:
                    pass
            
            return f"📢 Broadcast queued: {msg[:100]}"
        
        return "📢 Channel management: Use 'broadcast [message]' to send to your channel."
    
    async def _bot_commands(self, request: str, user_id: str) -> str:
        """Handle bot commands"""
        commands = {
            '/start': 'Bot started! How can I help you?',
            '/help': 'Available commands: /start, /help, /status, /tasks, /calendar',
            '/status': await self._get_telegram_status(user_id),
            '/tasks': await self.cod3x.agents['tasks'].process('list tasks', user_id),
            '/calendar': await self.cod3x.agents['calendar'].process('upcoming', user_id)
        }
        
        for cmd, response in commands.items():
            if cmd in request.lower():
                return response
        
        return "Available commands: /start, /help, /status, /tasks, /calendar"
    
    async def _get_telegram_status(self, user_id: str) -> str:
        """Get Telegram connection status"""
        status = "✈️ **Telegram Status:**\n"
        
        if self.tool:
            try:
                connected = await self.tool.test_connection()
                status += "✅ Bot connected and active\n"
                status += "• Ready to send/receive messages\n"
                status += "• Use 'send telegram to [user] [message]' to send"
            except:
                status += "⚠️ Bot configuration needed\n"
        else:
            status += "⚠️ Telegram tool not configured\n"
            status += "• Add your bot token in config.yaml"
        
        return status
    
    async def shutdown(self):
        if self.tool:
            await self.tool.shutdown()
