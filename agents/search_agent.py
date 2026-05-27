from llm_proxy import generate as llm_generate
"""
Search Agent - Web search and information retrieval
"""

import asyncio
from typing import Dict, Any, List
import json

class SearchAgent:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger
        from utils.free_ai import get_ai; self.model = get_ai()
        self.search_tool = cod3x.tools.get('serpapi')
    
    async def initialize(self):
        self.logger.info("Search Agent initialized")
    
    async def process(self, request: str, user_id: str, action: str = None, params: Dict = None) -> str:
        """Process search requests"""
        text_lower = request.lower()
        
        try:
            if any(kw in text_lower for kw in ['search for', 'google', 'find information', 'lookup']):
                return await self._web_search(request, user_id)
            elif any(kw in text_lower for kw in ['news', 'latest', 'current events']):
                return await self._search_news(request, user_id)
            elif any(kw in text_lower for kw in ['image search', 'find picture', 'show me']):
                return await self._image_search(request, user_id)
            elif any(kw in text_lower for kw in ['weather', 'temperature']):
                return await self._get_weather(request, user_id)
            elif any(kw in text_lower for kw in ['define', 'what is', 'meaning of']):
                return await self._get_definition(request, user_id)
            else:
                return await self._quick_search(request, user_id)
        except Exception as e:
            self.logger.error(f"Search agent error: {e}")
            return "I had trouble searching. Let me try using my knowledge base instead."
    
    async def _web_search(self, request: str, user_id: str) -> str:
        """Perform web search"""
        query = await self._extract_search_query(request)
        
        results = []
        
        # Try SerpAPI first
        if self.search_tool:
            try:
                search_results = await self.search_tool.search(query)
                results.append(search_results)
            except Exception as e:
                self.logger.warning(f"SerpAPI error: {e}")
        
        # Use Gemini as fallback
        if not results and self.model:
            prompt = f"""Act as a search engine and provide information about: {query}
            
            Include:
            1. Key facts and information
            2. Recent developments (if applicable)
            3. Related topics
            4. Sources (if known)
            
            Be comprehensive but concise."""
            
            try:
                response = await asyncio.to_thread(
                    self.model._call, prompt
                )
                results.append(response)
            except:
                pass
        
        if results:
            # Store in memory for context
            await self.cod3x.memory['vector'].add_text(
                query + " " + results[0],
                {'type': 'search', 'user_id': user_id, 'query': query}
            )
            
            return f"🔍 **Search Results: {query}**\n\n{results[0][:1000]}"
        
        return f"🔍 Searching for '{query}'... Please configure search API for web results."
    
    async def _extract_search_query(self, request: str) -> str:
        """Extract search query"""
        text = request.lower()
        
        for prefix in ['search for', 'google', 'find information about', 'lookup']:
            if prefix in text:
                query = text.split(prefix, 1)[1].strip()
                return query
        
        return text
    
    async def _search_news(self, request: str, user_id: str) -> str:
        """Search for news"""
        query = request.lower()
        for kw in ['news about', 'latest on']:
            if kw in query:
                query = query.split(kw, 1)[1].strip()
                break
        
        if self.model:
            prompt = f"What are the latest news and developments about {query}? Provide a summary of recent events."
            
            try:
                response = await asyncio.to_thread(
                    self.model._call, prompt
                )
                return f"📰 **News: {query}**\n\n{response}"
            except:
                pass
        
        return f"📰 Latest news about '{query}' (search API needed for real-time updates)"
    
    async def _image_search(self, request: str, user_id: str) -> str:
        """Search for images"""
        query = request.lower()
        for kw in ['image of', 'picture of', 'show me', 'find image']:
            if kw in query:
                query = query.split(kw, 1)[1].strip()
                break
        
        return f"🖼️ Image search for '{query}'. Use an image generation tool or search engine for visual results."
    
    async def _get_weather(self, request: str, user_id: str) -> str:
        """Get weather information"""
        location = "your location"
        text = request.lower()
        
        if 'in ' in text:
            parts = text.split('in ', 1)
            if len(parts) > 1:
                location = parts[1].strip()
        
        return f"🌤️ Weather for {location}:\n(Connect weather API for real-time data)\n• Check weather.com or your weather app"
    
    async def _get_definition(self, request: str, user_id: str) -> str:
        """Get definition of term"""
        term = request.lower()
        for kw in ['define', 'what is', 'meaning of']:
            if kw in term:
                term = term.split(kw, 1)[1].strip()
                break
        
        if self.model:
            prompt = f"Define '{term}' and provide examples, etymology, and related concepts."
            
            try:
                response = await asyncio.to_thread(
                    self.model._call, prompt
                )
                return f"📚 **Definition: {term}**\n\n{response}"
            except:
                pass
        
        return f"📚 '{term}' - Check a dictionary for the most accurate definition."
    
    async def _quick_search(self, request: str, user_id: str) -> str:
        """Quick general search"""
        if self.model:
            try:
                response = await asyncio.to_thread(
                    self.model._call, request
                )
                return f"💡 {response[:1000]}"
            except:
                pass
        
        return "🔍 I can search the web, news, and more. Just ask me to 'search for [topic]'!"
    
    async def shutdown(self):
        pass
