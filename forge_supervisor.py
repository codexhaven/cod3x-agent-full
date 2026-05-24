"""
Forge Supervisor - Publishing domain (Social, Image, Content)
"""

import asyncio
import json
from typing import Dict, Any, List

class ForgeSupervisor:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger
        self.model = cod3x.model
        self.agents = {}
    
    async def initialize(self):
        """Initialize publishing agents"""
        self.agents = {
            'social': self.cod3x.agents['social'],
            'image': self.cod3x.agents['image'],
            'content': self.cod3x.agents['content']
        }
    
    async def process(self, request: str, user_id: str, context: List) -> str:
        """Process publishing request"""
        text_lower = request.lower()
        
        if any(kw in text_lower for kw in ['image', 'picture', 'photo', 'generate image', 'create image']):
            response = await self.agents['image'].process(request, user_id)
        elif any(kw in text_lower for kw in ['post', 'social', 'tweet', 'share', 'publish']):
            response = await self.agents['social'].process(request, user_id)
        elif any(kw in text_lower for kw in ['write', 'content', 'article', 'blog', 'create']):
            response = await self.agents['content'].process(request, user_id)
        else:
            response = "I can help with social posts, image generation, and content creation. What do you need?"
        
        return response
