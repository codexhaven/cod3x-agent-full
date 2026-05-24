"""
Oracle Supervisor - Insights domain (Search, Research, Crypto)
"""

import asyncio
import json
from typing import Dict, Any, List

class OracleSupervisor:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger
        self.model = cod3x.model
        self.agents = {}
    
    async def initialize(self):
        """Initialize insights agents"""
        self.agents = {
            'search': self.cod3x.agents['search'],
            'research': self.cod3x.agents['research'],
            'crypto': self.cod3x.agents['crypto']
        }
    
    async def process(self, request: str, user_id: str, context: List) -> str:
        """Process insights request"""
        text_lower = request.lower()
        
        if any(kw in text_lower for kw in ['crypto', 'bitcoin', 'eth', 'token', 'blockchain', 'nft']):
            response = await self.agents['crypto'].process(request, user_id)
        elif any(kw in text_lower for kw in ['research', 'analyze', 'deep dive', 'study', 'investigate']):
            response = await self.agents['research'].process(request, user_id)
        elif any(kw in text_lower for kw in ['search', 'find', 'google', 'lookup', 'what is']):
            response = await self.agents['search'].process(request, user_id)
        else:
            response = "I can search, research, and check crypto. What would you like to know?"
        
        return response
