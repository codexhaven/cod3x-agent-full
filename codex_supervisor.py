"""
Codex Supervisor - Productivity domain (Calendar, Tasks, Docs, Contacts)
"""

import asyncio
import json
from typing import Dict, Any, List

class CodexSupervisor:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger
        self.model = cod3x.model
        self.agents = {}
        
        self.routing_prompt = """Route this productivity request to the best agent:
        
        Agents:
        - CALENDAR: Scheduling, appointments, meetings, events
        - TASKS: To-dos, task management, deadlines, projects
        - DOCS: Document creation, editing, search, management
        - CONTACTS: Contact management, lookup, relationship tracking
        
        User request: {request}
        
        Respond with JSON: {"agent": "AGENT_NAME", "action": "specific_action", "parameters": {}}
        """
    
    async def initialize(self):
        """Initialize productivity agents"""
        self.agents = {
            'calendar': self.cod3x.agents['calendar'],
            'tasks': self.cod3x.agents['tasks'],
            'docs': self.cod3x.agents['docs'],
            'contacts': self.cod3x.agents['contacts']
        }
    
    async def route_to_agent(self, request: str, context: List) -> Dict:
        """Determine which agent should handle the request"""
        try:
            if self.model:
                prompt = self.routing_prompt.format(request=request)
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                return json.loads(response.text)
            else:
                return self._keyword_route(request)
        except Exception as e:
            self.logger.error(f"Agent routing error: {e}")
            return self._keyword_route(request)
    
    def _keyword_route(self, text: str) -> Dict:
        """Fallback routing using keywords"""
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in ['calendar', 'schedule', 'meeting', 'event', 'appointment']):
            return {"agent": "calendar", "action": "manage_calendar", "parameters": {}}
        elif any(kw in text_lower for kw in ['task', 'todo', 'deadline', 'remind']):
            return {"agent": "tasks", "action": "manage_tasks", "parameters": {}}
        elif any(kw in text_lower for kw in ['document', 'doc', 'write', 'note']):
            return {"agent": "docs", "action": "manage_docs", "parameters": {}}
        elif any(kw in text_lower for kw in ['contact', 'person', 'phone', 'address']):
            return {"agent": "contacts", "action": "manage_contacts", "parameters": {}}
        else:
            return {"agent": "calendar", "action": "general", "parameters": {}}
    
    async def process(self, request: str, user_id: str, context: List) -> str:
        """Process productivity request"""
        routing = await self.route_to_agent(request, context)
        agent_name = routing['agent']
        
        self.logger.info(f"Codex routing to {agent_name} agent")
        
        if agent_name in self.agents:
            try:
                response = await self.agents[agent_name].process(
                    request, user_id, routing.get('action'), routing.get('parameters', {})
                )
                return response
            except Exception as e:
                self.logger.error(f"Agent {agent_name} error: {e}")
                return f"I had trouble with your {agent_name} request. Let me try a different approach."
        else:
            return "I can help with calendar, tasks, documents, and contacts. What would you like to do?"
