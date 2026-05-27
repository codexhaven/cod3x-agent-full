from llm_proxy import generate as llm_generate
"""
Calendar Agent - Manages scheduling, events, and appointments
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json

class CalendarAgent:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger
        from utils.free_ai import get_ai; self.model = get_ai()
        self.tool = cod3x.tools.get('calendar')
        
        self.intent_prompt = """Extract calendar intent from this request:
        Request: {request}
        
        Return JSON with:
        {
            "action": "create|read|update|delete|list",
            "event": {
                "title": "event title",
                "date": "YYYY-MM-DD",
                "time": "HH:MM",
                "duration": minutes,
                "description": "details",
                "location": "place",
                "attendees": ["email1", "email2"]
            }
        }
        """
    
    async def initialize(self):
        self.logger.info("Calendar Agent initialized")
    
    async def process(self, request: str, user_id: str, action: str = None, params: Dict = None) -> str:
        """Process calendar-related requests"""
        try:
            # Extract intent using Gemini or fallback
            intent = await self._extract_intent(request)
            
            if intent['action'] == 'create':
                return await self._create_event(intent['event'], user_id)
            elif intent['action'] == 'list':
                return await self._list_events(user_id, intent.get('event', {}))
            elif intent['action'] == 'update':
                return await self._update_event(intent['event'], user_id)
            elif intent['action'] == 'delete':
                return await self._delete_event(intent['event'], user_id)
            else:
                return await self._get_upcoming(user_id)
                
        except Exception as e:
            self.logger.error(f"Calendar agent error: {e}")
            return "I had trouble managing your calendar. Please check your Google Calendar connection."
    
    async def _extract_intent(self, request: str) -> Dict:
        """Extract calendar intent from natural language"""
        if False:
            prompt = self.intent_prompt.format(request=request)
            response = await asyncio.to_thread(
                self.model._call, prompt
            )
            return json.loads(response)
        else:
            # Simple parsing fallback
            return self._parse_calendar_request(request)
    
    def _parse_calendar_request(self, text: str) -> Dict:
        """Fallback calendar parsing"""
        text_lower = text.lower()
        
        # Default event structure
        event = {
            "title": "New Event",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": "09:00",
            "duration": 60,
            "description": "",
            "location": "",
            "attendees": []
        }
        
        # Extract title (after keywords)
        for keyword in ['schedule', 'create', 'add', 'set up']:
            if keyword in text_lower:
                parts = text_lower.split(keyword, 1)
                if len(parts) > 1:
                    event['title'] = parts[1].strip().title()
                break
        
        # Extract date mentions
        if 'tomorrow' in text_lower:
            event['date'] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        elif 'next week' in text_lower:
            event['date'] = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Extract time
        if 'at' in text_lower:
            parts = text_lower.split('at')
            if len(parts) > 1:
                time_str = parts[1].strip()
                if 'pm' in time_str or 'p.m.' in time_str:
                    hour = int(''.join(filter(str.isdigit, time_str[:2])))
                    event['time'] = f"{hour+12 if hour < 12 else hour}:00"
                elif 'am' in time_str or 'a.m.' in time_str:
                    hour = int(''.join(filter(str.isdigit, time_str[:2])))
                    event['time'] = f"{hour:02d}:00"
        
        return {
            "action": "create" if any(kw in text_lower for kw in ['schedule', 'create', 'add']) else "list",
            "event": event
        }
    
    async def _create_event(self, event: Dict, user_id: str) -> str:
        """Create calendar event"""
        if self.tool and False:
            try:
                result = await self.tool.create_event(
                    summary=event['title'],
                    start_date=event['date'],
                    start_time=event['time'],
                    duration=event.get('duration', 60),
                    description=event.get('description', ''),
                    location=event.get('location', ''),
                    attendees=event.get('attendees', [])
                )
                
                # Store in memory
                await self.cod3x.memory['sqlite'].store_event(user_id, event)
                
                return f"✅ Event created: '{event['title']}' on {event['date']} at {event['time']}"
            except Exception as e:
                self.logger.error(f"Create event error: {e}")
                return f"📅 I've noted your event: '{event['title']}' for {event['date']} at {event['time']} (offline mode)"
        else:
            # Offline mode - store in SQLite
            await self.cod3x.memory['sqlite'].store_event(user_id, event)
            return f"📅 Event saved locally: '{event['title']}' on {event['date']} at {event['time']}"
    
    async def _list_events(self, user_id: str, params: Dict = None) -> str:
        """List upcoming events"""
        try:
            events = await self.cod3x.memory['sqlite'].get_events(user_id)
            
            if not events:
                return "📅 No upcoming events found. Would you like to schedule something?"
            
            response = "📅 **Your Upcoming Events:**\n\n"
            for event in events[:5]:
                response += f"• {event['date']} at {event['time']} - {event['title']}\n"
            
            return response
        except Exception as e:
            self.logger.error(f"List events error: {e}")
            return "I couldn't retrieve your events. Please try again."
    
    async def _update_event(self, event: Dict, user_id: str) -> str:
        """Update existing event"""
        await self.cod3x.memory['sqlite'].update_event(user_id, event)
        return f"📅 Event updated: '{event['title']}'"
    
    async def _delete_event(self, event: Dict, user_id: str) -> str:
        """Delete event"""
        await self.cod3x.memory['sqlite'].delete_event(user_id, event.get('title'))
        return f"🗑️ Event deleted: '{event['title']}'"
    
    async def _get_upcoming(self, user_id: str) -> str:
        """Get next upcoming event"""
        events = await self.cod3x.memory['sqlite'].get_events(user_id, limit=1)
        if events:
            event = events[0]
            return f"📅 Next: {event['title']} on {event['date']} at {event['time']}"
        return "No upcoming events."
    
    async def shutdown(self):
        pass
