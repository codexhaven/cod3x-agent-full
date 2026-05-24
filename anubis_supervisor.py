"""
Anubis Supervisor - Lifestyle domain (Expenses, Travel, Meals)
"""

import asyncio
import json
from typing import Dict, Any, List

class AnubisSupervisor:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger
        self.model = cod3x.model
        self.agents = {}
    
    async def initialize(self):
        """Initialize lifestyle agents"""
        self.agents = {
            'expenses': self.cod3x.agents['expenses'],
            'travel': self.cod3x.agents['travel'],
            'meals': self.cod3x.agents['meals']
        }
    
    async def process(self, request: str, user_id: str, context: List) -> str:
        """Process lifestyle request"""
        text_lower = request.lower()
        
        if any(kw in text_lower for kw in ['expense', 'spend', 'money', 'cost', 'budget', 'price']):
            response = await self.agents['expenses'].process(request, user_id)
        elif any(kw in text_lower for kw in ['travel', 'trip', 'flight', 'hotel', 'visit', 'vacation']):
            response = await self.agents['travel'].process(request, user_id)
        elif any(kw in text_lower for kw in ['meal', 'food', 'recipe', 'cook', 'restaurant', 'eat']):
            response = await self.agents['meals'].process(request, user_id)
        else:
            response = "I can help with expenses, travel planning, and meals. What interests you?"
        
        return response
