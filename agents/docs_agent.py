"""
Docs Agent - Document creation, management, and search
"""

import asyncio
from typing import Dict, Any, List
import json

class DocsAgent:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger
        self.model = cod3x.model
        self.tool = cod3x.tools.get('drive')
    
    async def initialize(self):
        self.logger.info("Docs Agent initialized")
    
    async def process(self, request: str, user_id: str, action: str = None, params: Dict = None) -> str:
        """Process document-related requests"""
        text_lower = request.lower()
        
        try:
            if any(kw in text_lower for kw in ['create doc', 'new document', 'write doc']):
                return await self._create_document(request, user_id)
            elif any(kw in text_lower for kw in ['find doc', 'search doc', 'where is']):
                return await self._search_documents(request, user_id)
            elif any(kw in text_lower for kw in ['list doc', 'my documents', 'all docs']):
                return await self._list_documents(user_id)
            elif any(kw in text_lower for kw in ['edit doc', 'update doc', 'modify']):
                return await self._edit_document(request, user_id)
            elif any(kw in text_lower for kw in ['summarize', 'summary', 'tldr']):
                return await self._summarize_document(request, user_id)
            else:
                return await self._get_recent_docs(user_id)
        except Exception as e:
            self.logger.error(f"Docs agent error: {e}")
            return "I had trouble with your document request. Please try again."
    
    async def _create_document(self, request: str, user_id: str) -> str:
        """Create a new document"""
        # Extract document details
        doc_details = await self._extract_doc_details(request)
        
        # Generate content if needed
        if self.model and not doc_details.get('content'):
            prompt = f"Write a {doc_details.get('type', 'document')} about: {doc_details.get('title', '')}\nTopic: {doc_details.get('topic', '')}"
            response = await asyncio.to_thread(
                self.model.generate_content, prompt
            )
            doc_details['content'] = response.text
        
        # Store document
        doc_id = await self.cod3x.memory['sqlite'].store_document(user_id, doc_details)
        
        # Try to create in Google Drive if available
        if self.tool:
            try:
                await self.tool.create_doc(doc_details['title'], doc_details.get('content', ''))
                return f"📄 Document created in Google Drive: '{doc_details['title']}'"
            except:
                pass
        
        return f"📄 Document saved: '{doc_details['title']}' (ID: {doc_id})"
    
    async def _extract_doc_details(self, request: str) -> Dict:
        """Extract document creation details"""
        if self.model:
            prompt = f"""Extract document details from: {request}
            Return JSON: {{"title": "doc title", "type": "document|spreadsheet|presentation", "topic": "main topic", "content": "generated content if specified"}}"""
            
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                return json.loads(response.text)
            except:
                pass
        
        # Fallback
        doc = {
            "title": "Untitled Document",
            "type": "document",
            "topic": "",
            "content": ""
        }
        
        for prefix in ['create doc', 'new document', 'write doc']:
            if prefix in request.lower():
                doc['title'] = request.lower().split(prefix, 1)[1].strip().title()
                break
        
        return doc
    
    async def _search_documents(self, request: str, user_id: str) -> str:
        """Search for documents"""
        # Extract search query
        query = request.lower()
        for kw in ['find doc', 'search doc', 'where is']:
            if kw in query:
                query = query.split(kw, 1)[1].strip()
                break
        
        # Search in memory
        docs = await self.cod3x.memory['vector'].search_similar(query, 'documents', top_k=5)
        
        if not docs:
            return f"🔍 No documents found matching '{query}'"
        
        response = f"🔍 **Documents matching '{query}':**\n\n"
        for doc in docs:
            response += f"📄 {doc['title']}\n"
            response += f"   Preview: {doc.get('content', '')[:100]}...\n\n"
        
        return response
    
    async def _list_documents(self, user_id: str) -> str:
        """List all documents"""
        docs = await self.cod3x.memory['sqlite'].get_documents(user_id)
        
        if not docs:
            return "📄 No documents found. Would you like to create one?"
        
        response = "📄 **Your Documents:**\n\n"
        for doc in docs[:10]:
            response += f"• {doc['title']} ({doc.get('type', 'doc')}) - {doc.get('created_at', 'Unknown date')}\n"
        
        return response
    
    async def _edit_document(self, request: str, user_id: str) -> str:
        """Edit an existing document"""
        return "📝 Document editing is available. Please specify the document name and changes you'd like to make."
    
    async def _summarize_document(self, request: str, user_id: str) -> str:
        """Summarize a document"""
        if self.model:
            # Extract document reference
            doc_ref = request.lower()
            for kw in ['summarize', 'summary']:
                if kw in doc_ref:
                    doc_ref = doc_ref.split(kw, 1)[1].strip()
                    break
            
            # Get document content
            docs = await self.cod3x.memory['vector'].search_similar(doc_ref, 'documents', top_k=1)
            
            if docs and docs[0].get('content'):
                prompt = f"Summarize this document in 3-5 bullet points:\n\n{docs[0]['content']}"
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                return f"📄 **Summary of '{docs[0]['title']}':**\n\n{response.text}"
        
        return "I couldn't summarize that document. Please make sure it exists and has content."
    
    async def _get_recent_docs(self, user_id: str) -> str:
        """Get recently accessed documents"""
        docs = await self.cod3x.memory['sqlite'].get_documents(user_id, limit=3)
        
        if docs:
            response = "📄 **Recent Documents:**\n\n"
            for doc in docs:
                response += f"• {doc['title']}\n"
            return response
        
        return "No recent documents."
    
    async def shutdown(self):
        pass
