"""
Calendar Tool - Google Calendar integration
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import os

class CalendarTool:
    def __init__(self, config: Dict):
        self.config = config
        self.credentials = config.get('google', {}).get('credentials_file', 'credentials.json')
        self.service = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize Google Calendar API"""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            
            SCOPES = ['https://www.googleapis.com/auth/calendar']
            
            creds = None
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                elif os.path.exists(self.credentials):
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                if creds:
                    with open('token.json', 'w') as token:
                        token.write(creds.to_json())
            
            if creds:
                self.service = build('calendar', 'v3', credentials=creds)
                self.initialized = True
                return True
        except ImportError:
            print("Google Calendar libraries not installed")
        except Exception as e:
            print(f"Calendar init error: {e}")
        
        self.initialized = False
        return False
    
    async def create_event(self, summary: str, start_date: str, start_time: str = "09:00",
                          duration: int = 60, description: str = "", location: str = "",
                          attendees: List[str] = None) -> Dict:
        """Create a calendar event"""
        if not self.initialized:
            return {"status": "offline", "message": "Calendar not connected"}
        
        try:
            start_datetime = f"{start_date}T{start_time}:00"
            end_datetime = (datetime.fromisoformat(start_datetime) + timedelta(minutes=duration)).isoformat()
            
            event = {
                'summary': summary,
                'location': location,
                'description': description,
                'start': {
                    'dateTime': start_datetime,
                    'timeZone': 'America/Los_Angeles',
                },
                'end': {
                    'dateTime': end_datetime,
                    'timeZone': 'America/Los_Angeles',
                },
                'attendees': [{'email': email} for email in (attendees or [])],
                'reminders': {
                    'useDefault': True,
                },
            }
            
            event = await asyncio.to_thread(
                self.service.events().insert(calendarId='primary', body=event).execute
            )
            
            return {"status": "created", "event_id": event.get('id'), "link": event.get('htmlLink')}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def list_events(self, max_results: int = 10, time_min: str = None) -> List[Dict]:
        """List upcoming events"""
        if not self.initialized:
            return []
        
        try:
            if not time_min:
                time_min = datetime.utcnow().isoformat() + 'Z'
            
            events_result = await asyncio.to_thread(
                self.service.events().list(
                    calendarId='primary',
                    timeMin=time_min,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute
            )
            
            events = events_result.get('items', [])
            
            return [{
                'id': event['id'],
                'summary': event.get('summary', 'No title'),
                'start': event['start'].get('dateTime', event['start'].get('date')),
                'end': event['end'].get('dateTime', event['end'].get('date')),
                'location': event.get('location', ''),
                'description': event.get('description', '')[:100]
            } for event in events]
        except Exception as e:
            print(f"List events error: {e}")
            return []
    
    async def update_event(self, event_id: str, updates: Dict) -> Dict:
        """Update an event"""
        if not self.initialized:
            return {"status": "offline"}
        
        try:
            event = await asyncio.to_thread(
                self.service.events().get(calendarId='primary', eventId=event_id).execute
            )
            
            for key, value in updates.items():
                event[key] = value
            
            updated_event = await asyncio.to_thread(
                self.service.events().update(calendarId='primary', eventId=event_id, body=event).execute
            )
            
            return {"status": "updated", "event_id": updated_event.get('id')}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def delete_event(self, event_id: str) -> Dict:
        """Delete an event"""
        if not self.initialized:
            return {"status": "offline"}
        
        try:
            await asyncio.to_thread(
                self.service.events().delete(calendarId='primary', eventId=event_id).execute
            )
            return {"status": "deleted"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def get_free_busy(self, time_min: str, time_max: str) -> List[Dict]:
        """Get free/busy information"""
        if not self.initialized:
            return []
        
        try:
            body = {
                "timeMin": time_min,
                "timeMax": time_max,
                "items": [{"id": "primary"}]
            }
            
            eventsResult = await asyncio.to_thread(
                self.service.freebusy().query(body=body).execute
            )
            
            return eventsResult.get('calendars', {}).get('primary', {}).get('busy', [])
        except Exception as e:
            print(f"Free/busy error: {e}")
            return []
    
    async def shutdown(self):
        """Cleanup"""
        self.initialized = False
        self.service = None
