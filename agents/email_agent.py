from llm_proxy import generate as llm_generate
"""
Email Agent - Email management and composition
"""

import asyncio
from typing import Dict, Any, List
import json

class EmailAgent:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger
        from utils.free_ai import get_ai; self.model = get_ai()
        self.tool = cod3x.tools.get('gmail')
    
    async def initialize(self):
        self.logger.info("Email Agent initialized")
    
    async def process(self, request: str, user_id: str, action: str = None, params: Dict = None) -> str:
        """Process email-related requests"""
        text_lower = request.lower()
        
        try:
            if any(kw in text_lower for kw in ['send email', 'compose', 'write email']):
                return await self._send_email(request, user_id)
            elif any(kw in text_lower for kw in ['check email', 'inbox', 'new emails', 'read email']):
                return await self._check_inbox(user_id)
            elif any(kw in text_lower for kw in ['reply', 'respond']):
                return await self._reply_email(request, user_id)
            elif any(kw in text_lower for kw in ['search email', 'find email']):
                return await self._search_emails(request, user_id)
            elif any(kw in text_lower for kw in ['draft', 'save draft']):
                return await self._save_draft(request, user_id)
            else:
                return await self._get_email_summary(user_id)
        except Exception as e:
            self.logger.error(f"Email agent error: {e}")
            return "I had trouble with your email. Please check your Gmail connection."
    
    async def _send_email(self, request: str, user_id: str) -> str:
        """Send an email"""
        email_details = await self._extract_email_details(request)
        
        if self.tool:
            try:
                result = await self.tool.send_email(
                    to=email_details['to'],
                    subject=email_details['subject'],
                    body=email_details['body']
                )
                return f"📧 Email sent to {email_details['to']}"
            except Exception as e:
                self.logger.error(f"Send email error: {e}")
        
        # Store as draft if can't send
        await self.cod3x.memory['sqlite'].store_draft(user_id, email_details)
        return f"📧 Email draft saved for {email_details['to']}"
    
    async def _extract_email_details(self, request: str) -> Dict:
        """Extract email details from request"""
        if self.model:
            prompt = f"""Extract email details from: {request}
            Return JSON: {{"to": "recipient@email.com", "subject": "email subject", "body": "email content"}}"""
            
            try:
                response = await asyncio.to_thread(
                    self.model._call, prompt
                )
                return json.loads(response)
            except:
                pass
        
        # Fallback extraction
        email = {
            "to": "",
            "subject": "No Subject",
            "body": ""
        }
        
        text = request
        # Extract recipient
        if 'to ' in text.lower():
            parts = text.lower().split('to ', 1)
            if len(parts) > 1:
                email['to'] = parts[1].split()[0].strip().rstrip(',')
        
        # Extract subject
        if 'about ' in text.lower():
            parts = text.lower().split('about ', 1)
            if len(parts) > 1:
                email['subject'] = parts[1].split('.')[0].strip().title()
        elif 'subject ' in text.lower():
            parts = text.lower().split('subject ', 1)
            if len(parts) > 1:
                email['subject'] = parts[1].split('.')[0].strip().title()
        
        # Body is everything after "saying" or "body"
        if 'saying ' in text.lower():
            parts = text.lower().split('saying ', 1)
            if len(parts) > 1:
                email['body'] = parts[1].strip()
        elif 'body ' in text.lower():
            parts = text.lower().split('body ', 1)
            if len(parts) > 1:
                email['body'] = parts[1].strip()
        
        return email
    
    async def _check_inbox(self, user_id: str) -> str:
        """Check email inbox"""
        if self.tool:
            try:
                emails = await self.tool.get_recent_emails(limit=5)
                
                if not emails:
                    return "📧 No new emails in your inbox."
                
                response = "📧 **Recent Emails:**\n\n"
                for email in emails:
                    response += f"📨 From: {email.get('from', 'Unknown')}\n"
                    response += f"   Subject: {email.get('subject', 'No subject')}\n"
                    response += f"   Preview: {email.get('snippet', '')[:100]}...\n\n"
                
                return response
            except Exception as e:
                self.logger.error(f"Check inbox error: {e}")
        
        return "📧 Email checking requires Gmail connection. Please configure your credentials."
    
    async def _reply_email(self, request: str, user_id: str) -> str:
        """Reply to an email"""
        return "📧 Reply drafted. Use 'send email' to confirm sending."
    
    async def _search_emails(self, request: str, user_id: str) -> str:
        """Search emails"""
        query = request.lower()
        for kw in ['search email', 'find email']:
            if kw in query:
                query = query.split(kw, 1)[1].strip()
                break
        
        if self.tool:
            try:
                results = await self.tool.search_emails(query)
                return f"📧 Found {len(results)} emails matching '{query}'"
            except:
                pass
        
        return f"🔍 Searching for emails about '{query}' (requires Gmail connection)"
    
    async def _save_draft(self, request: str, user_id: str) -> str:
        """Save email as draft"""
        draft = await self._extract_email_details(request)
        await self.cod3x.memory['sqlite'].store_draft(user_id, draft)
        return "📝 Draft saved. You can continue editing later."
    
    async def _get_email_summary(self, user_id: str) -> str:
        """Get email summary"""
        drafts = await self.cod3x.memory['sqlite'].get_drafts(user_id)
        
        summary = "📧 **Email Summary:**\n"
        summary += "• Say 'check inbox' to read emails\n"
        summary += "• Say 'send email to [person]' to compose\n"
        
        if drafts:
            summary += f"\n• {len(drafts)} drafts saved\n"
        
        return summary
    
    async def shutdown(self):
        pass
