"""
Gmail Tool - Email integration
"""

import asyncio
from typing import Dict, Any, List, Optional
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class GmailTool:
    def __init__(self, config: Dict):
        self.config = config
        self.credentials = config.get('google', {}).get('credentials_file', 'credentials.json')
        self.service = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize Gmail API"""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            
            SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
            
            creds = None
            if os.path.exists('gmail_token.json'):
                creds = Credentials.from_authorized_user_file('gmail_token.json', SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                elif os.path.exists(self.credentials):
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                if creds:
                    with open('gmail_token.json', 'w') as token:
                        token.write(creds.to_json())
            
            if creds:
                self.service = build('gmail', 'v1', credentials=creds)
                self.initialized = True
                return True
        except ImportError:
            print("Gmail libraries not installed")
        except Exception as e:
            print(f"Gmail init error: {e}")
        
        return False
    
    async def send_email(self, to: str, subject: str, body: str, cc: List[str] = None) -> Dict:
        """Send an email"""
        if not self.initialized:
            return {"status": "offline", "message": "Gmail not connected"}
        
        try:
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = ', '.join(cc)
            
            message.attach(MIMEText(body, 'plain'))
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            sent_message = await asyncio.to_thread(
                self.service.users().messages().send(
                    userId='me',
                    body={'raw': raw_message}
                ).execute
            )
            
            return {"status": "sent", "message_id": sent_message['id']}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def get_recent_emails(self, limit: int = 10, query: str = None) -> List[Dict]:
        """Get recent emails"""
        if not self.initialized:
            return []
        
        try:
            params = {
                'userId': 'me',
                'maxResults': limit,
                'labelIds': ['INBOX']
            }
            
            if query:
                params['q'] = query
            
            results = await asyncio.to_thread(
                self.service.users().messages().list(**params).execute
            )
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages[:limit]:
                message = await asyncio.to_thread(
                    self.service.users().messages().get(userId='me', id=msg['id']).execute
                )
                
                headers = message.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                
                snippet = message.get('snippet', '')
                
                emails.append({
                    'id': msg['id'],
                    'subject': subject,
                    'from': sender,
                    'snippet': snippet,
                    'date': next((h['value'] for h in headers if h['name'] == 'Date'), '')
                })
            
            return emails
        except Exception as e:
            print(f"Get emails error: {e}")
            return []
    
    async def search_emails(self, query: str, limit: int = 10) -> List[Dict]:
        """Search emails"""
        return await self.get_recent_emails(limit, query)
    
    async def mark_as_read(self, message_id: str) -> Dict:
        """Mark email as read"""
        if not self.initialized:
            return {"status": "offline"}
        
        try:
            await asyncio.to_thread(
                self.service.users().messages().modify(
                    userId='me',
                    id=message_id,
                    body={'removeLabelIds': ['UNREAD']}
                ).execute
            )
            return {"status": "marked_read"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def reply_to_email(self, message_id: str, body: str) -> Dict:
        """Reply to an email"""
        if not self.initialized:
            return {"status": "offline"}
        
        try:
            original = await asyncio.to_thread(
                self.service.users().messages().get(userId='me', id=message_id).execute
            )
            
            headers = original.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            
            message = MIMEText(body)
            message['to'] = sender
            message['subject'] = f"Re: {subject}"
            message['In-Reply-To'] = message_id
            message['References'] = message_id
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            await asyncio.to_thread(
                self.service.users().messages().send(
                    userId='me',
                    body={'raw': raw_message, 'threadId': original['threadId']}
                ).execute
            )
            
            return {"status": "replied"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def shutdown(self):
        """Cleanup"""
        self.initialized = False
        self.service = None
