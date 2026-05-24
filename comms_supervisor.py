"""
Comms Supervisor - Communication domain (Email, Telegram, Twitter)
"""

import asyncio
import json
from typing import Dict, Any, List

class CommsSupervisor:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger
        self.model = cod3x.model
        self.agents = {}
    
    async def initialize(self):
        """Initialize communication agents"""
        self.agents = {
            'email': self.cod3x.agents['email'],
            'telegram': self.cod3x.agents['telegram'],
            'twitter': self.cod3x.agents['twitter']
        }
    
    async def process(self, request: str, user_id: str, context: List) -> str:
        """Process communication request"""
        text_lower = request.lower()
        
        # Smart routing based on platform mentions
        if any(kw in text_lower for kw in ['email', 'gmail', 'mail']):
            response = await self.agents['email'].process(request, user_id)
        elif any(kw in text_lower for kw in ['telegram', 'tg', 'channel']):
            response = await self.agents['telegram'].process(request, user_id)
        elif any(kw in text_lower for kw in ['tweet', 'twitter', 'x.com']):
            response = await self.agents['twitter'].process(request, user_id)
        else:
            # Try all agents and return best match
            responses = []
            for agent_name, agent in self.agents.items():
                try:
                    resp = await agent.process(request, user_id)
                    responses.append(f"[{agent_name}] {resp}")
                except:
                    pass
            
            response = "I can help with communications. Would you like to use email, Telegram, or Twitter?"
        
        return response
