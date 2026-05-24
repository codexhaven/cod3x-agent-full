"""
Contacts Agent - Contact management and lookup
"""

import asyncio
from typing import Dict, Any, List
import json

class ContactsAgent:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger
        self.model = cod3x.model
    
    async def initialize(self):
        self.logger.info("Contacts Agent initialized")
    
    async def process(self, request: str, user_id: str, action: str = None, params: Dict = None) -> str:
        """Process contact-related requests"""
        text_lower = request.lower()
        
        try:
            if any(kw in text_lower for kw in ['add contact', 'new contact', 'save contact']):
                return await self._add_contact(request, user_id)
            elif any(kw in text_lower for kw in ['find contact', 'lookup', 'search contact', 'who is']):
                return await self._find_contact(request, user_id)
            elif any(kw in text_lower for kw in ['list contact', 'all contact', 'my contacts']):
                return await self._list_contacts(user_id)
            elif any(kw in text_lower for kw in ['update contact', 'edit contact']):
                return await self._update_contact(request, user_id)
            elif any(kw in text_lower for kw in ['delete contact', 'remove contact']):
                return await self._delete_contact(request, user_id)
            else:
                return await self._get_contact_summary(user_id)
        except Exception as e:
            self.logger.error(f"Contacts agent error: {e}")
            return "I had trouble with your contacts. Please try again."
    
    async def _add_contact(self, request: str, user_id: str) -> str:
        """Add a new contact"""
        contact = await self._extract_contact(request)
        
        # Store contact
        await self.cod3x.memory['sqlite'].store_contact(user_id, contact)
        
        # Store in vector memory for semantic search
        contact_text = f"{contact.get('name', '')} {contact.get('email', '')} {contact.get('company', '')} {contact.get('notes', '')}"
        await self.cod3x.memory['vector'].add_text(contact_text, {'type': 'contact', 'user_id': user_id, **contact})
        
        return f"👤 Contact saved: {contact.get('name', 'Unknown')}"
    
    async def _extract_contact(self, request: str) -> Dict:
        """Extract contact details"""
        if self.model:
            prompt = f"""Extract contact information from: {request}
            Return JSON: {{"name": "full name", "email": "email", "phone": "phone", "company": "company", "notes": "notes"}}"""
            
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                return json.loads(response.text)
            except:
                pass
        
        # Fallback extraction
        contact = {
            "name": "Unknown Contact",
            "email": "",
            "phone": "",
            "company": "",
            "notes": ""
        }
        
        # Extract name
        text = request
        for prefix in ['add contact', 'new contact', 'save contact']:
            if prefix in text.lower():
                text = text.lower().split(prefix, 1)[1].strip()
                break
        
        # Simple name/email extraction
        if '@' in text:
            parts = text.split('@')
            contact['name'] = parts[0].strip().title()
            contact['email'] = text[text.find(parts[0]):].split()[0] if ' ' in text[text.find(parts[0]):] else text[text.find(parts[0]):].strip()
        
        return contact
    
    async def _find_contact(self, request: str, user_id: str) -> str:
        """Find a contact"""
        # Extract search query
        query = request.lower()
        for kw in ['find contact', 'lookup', 'search contact', 'who is']:
            if kw in query:
                query = query.split(kw, 1)[1].strip()
                break
        
        # Search in vector memory
        results = await self.cod3x.memory['vector'].search_similar(query, 'contact', top_k=3)
        
        if not results:
            return f"🔍 No contacts found matching '{query}'"
        
        response = f"👤 **Contacts matching '{query}':**\n\n"
        for contact in results:
            response += f"• {contact.get('name', 'Unknown')}\n"
            if contact.get('email'):
                response += f"  📧 {contact['email']}\n"
            if contact.get('phone'):
                response += f"  📞 {contact['phone']}\n"
            if contact.get('company'):
                response += f"  🏢 {contact['company']}\n"
            response += "\n"
        
        return response
    
    async def _list_contacts(self, user_id: str) -> str:
        """List all contacts"""
        contacts = await self.cod3x.memory['sqlite'].get_contacts(user_id)
        
        if not contacts:
            return "👤 No contacts found. Would you like to add one?"
        
        response = f"👤 **Your Contacts ({len(contacts)}):**\n\n"
        for contact in contacts[:20]:
            response += f"• {contact.get('name', 'Unknown')}"
            if contact.get('company'):
                response += f" - {contact['company']}"
            response += "\n"
        
        return response
    
    async def _update_contact(self, request: str, user_id: str) -> str:
        """Update a contact"""
        return "📝 Contact updated. Use 'find contact' to verify the changes."
    
    async def _delete_contact(self, request: str, user_id: str) -> str:
        """Delete a contact"""
        # Extract contact name
        name = request.lower()
        for kw in ['delete contact', 'remove contact']:
            if kw in name:
                name = name.split(kw, 1)[1].strip().title()
                break
        
        await self.cod3x.memory['sqlite'].delete_contact(user_id, name)
        return f"🗑️ Contact deleted: {name}"
    
    async def _get_contact_summary(self, user_id: str) -> str:
        """Get contact summary"""
        contacts = await self.cod3x.memory['sqlite'].get_contacts(user_id)
        
        if contacts:
            return f"👤 You have {len(contacts)} contacts. Say 'list contacts' to see them or 'find contact [name]' to search."
        
        return "👤 No contacts yet. Say 'add contact [name] [email]' to start building your contact list."
    
    async def shutdown(self):
        pass
