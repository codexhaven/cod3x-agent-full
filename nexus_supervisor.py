"""
Nexus Supervisor - Central routing intelligence
Routes requests to appropriate domain supervisors
"""

import asyncio
import json
from typing import Dict, Any, Optional
import google.generativeai as genai

class NexusSupervisor:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger
        self.model = cod3x.model
        self.supervisors = {}
        
        # Domain classification prompt
        self.classification_prompt = """You are a routing intelligence. Classify the user's request into ONE category:
        
        Categories:
        - PRODUCTIVITY: Calendar, tasks, documents, contacts, scheduling
        - COMMUNICATION: Email, Telegram, Twitter, messaging
        - LIFESTYLE: Expenses, travel, meals, personal
        - INSIGHTS: Search, research, crypto, information gathering
        - PUBLISHING: Social media posts, image creation, content generation
        
        User request: {request}
        
        Respond with JSON: {"category": "CATEGORY_NAME", "confidence": 0.95, "reasoning": "brief explanation"}
        """
    
    async def initialize(self):
        """Initialize all domain supervisors"""
        from codex_supervisor import CodexSupervisor
        from comms_supervisor import CommsSupervisor
        from anubis_supervisor import AnubisSupervisor
        from oracle_supervisor import OracleSupervisor
        from forge_supervisor import ForgeSupervisor
        
        self.supervisors = {
            'PRODUCTIVITY': CodexSupervisor(self.cod3x),
            'COMMUNICATION': CommsSupervisor(self.cod3x),
            'LIFESTYLE': AnubisSupervisor(self.cod3x),
            'INSIGHTS': OracleSupervisor(self.cod3x),
            'PUBLISHING': ForgeSupervisor(self.cod3x)
        }
        
        for supervisor in self.supervisors.values():
            await supervisor.initialize()
    
    async def classify_request(self, user_input: str) -> Dict[str, Any]:
        """Classify the request to determine which supervisor handles it"""
        try:
            # Try Gemini classification
            if self.model:
                prompt = self.classification_prompt.format(request=user_input)
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                result = json.loads(response.text)
                self.logger.info(f"Classified as: {result['category']} (confidence: {result['confidence']})")
                return result
            else:
                # Fallback keyword matching
                return self._keyword_classify(user_input)
        except Exception as e:
            self.logger.error(f"Classification error: {e}")
            return self._keyword_classify(user_input)
    
    def _keyword_classify(self, text: str) -> Dict[str, Any]:
        """Fallback classification using keywords"""
        text_lower = text.lower()
        
        # Productivity keywords
        productivity_kw = ['calendar', 'schedule', 'task', 'todo', 'document', 'doc', 
                          'contact', 'meeting', 'appointment', 'reminder']
        
        # Communication keywords
        comms_kw = ['email', 'mail', 'telegram', 'tweet', 'twitter', 'message', 
                   'send', 'reply', 'inbox']
        
        # Lifestyle keywords
        lifestyle_kw = ['expense', 'spend', 'travel', 'trip', 'meal', 'food', 
                       'recipe', 'budget', 'fitness', 'health']
        
        # Insights keywords
        insights_kw = ['search', 'research', 'find', 'crypto', 'bitcoin', 
                      'stock', 'price', 'analyze', 'investigate']
        
        # Publishing keywords
        publishing_kw = ['post', 'publish', 'create', 'image', 'content', 
                        'social', 'design', 'write', 'generate']
        
        scores = {
            'PRODUCTIVITY': sum(1 for kw in productivity_kw if kw in text_lower),
            'COMMUNICATION': sum(1 for kw in comms_kw if kw in text_lower),
            'LIFESTYLE': sum(1 for kw in lifestyle_kw if kw in text_lower),
            'INSIGHTS': sum(1 for kw in insights_kw if kw in text_lower),
            'PUBLISHING': sum(1 for kw in publishing_kw if kw in text_lower)
        }
        
        best = max(scores, key=scores.get)
        confidence = 0.5 + (scores[best] * 0.1)
        
        return {
            'category': best,
            'confidence': min(confidence, 0.9),
            'reasoning': 'Keyword-based classification'
        }
    
    async def route(self, user_input: str, user_id: str = None) -> str:
        """Route request to appropriate supervisor"""
        # Get conversation context
        context = await self.cod3x.memory['buffer'].get_context(user_id)
        full_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context])
        
        # Classify with context
        classification = await self.classify_request(full_context + "\n" + user_input)
        category = classification['category']
        
        self.logger.info(f"Routing to {category} supervisor")
        
        # Route to appropriate supervisor
        if category in self.supervisors:
            try:
                response = await self.supervisors[category].process(user_input, user_id, context)
                return response
            except Exception as e:
                self.logger.error(f"Supervisor error: {e}")
                return f"I encountered an error processing your {category.lower()} request. Please try again."
        else:
            return "I'm not sure how to handle that request. Can you be more specific?"
