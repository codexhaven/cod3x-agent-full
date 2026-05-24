"""
SerpAPI Tool - Web search integration
"""

import asyncio
from typing import Dict, Any, List, Optional
import json
import os

class SerpAPITool:
    def __init__(self, config: Dict):
        self.config = config
        self.api_key = config.get('serpapi', {}).get('api_key') or os.getenv('SERPAPI_API_KEY')
        self.initialized = bool(self.api_key)
        self.base_url = "https://serpapi.com/search"
    
    async def initialize(self):
        """Initialize SerpAPI"""
        try:
            import aiohttp
            self.session = aiohttp.ClientSession()
            self.initialized = True
        except ImportError:
            print("aiohttp not installed. Install with: pip install aiohttp")
            self.initialized = False
    
    async def search(self, query: str, engine: str = "google", num_results: int = 10) -> str:
        """Perform a web search"""
        if not self.initialized:
            return f"Search API not configured. Query: {query}"
        
        try:
            import aiohttp
            
            params = {
                'q': query,
                'api_key': self.api_key,
                'engine': engine,
                'num': num_results
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_search_results(data, query)
                    else:
                        return f"Search failed with status {response.status}"
        except Exception as e:
            print(f"Search error: {e}")
            return self._fallback_search(query)
    
    def _format_search_results(self, data: Dict, query: str) -> str:
        """Format search results"""
        results = []
        
        # Organic results
        if 'organic_results' in data:
            for i, result in enumerate(data['organic_results'][:5], 1):
                title = result.get('title', 'No title')
                link = result.get('link', '')
                snippet = result.get('snippet', '')[:200]
                results.append(f"{i}. {title}\n   {snippet}\n   {link}\n")
        
        # Knowledge graph
        if 'knowledge_graph' in data:
            kg = data['knowledge_graph']
            if kg.get('title'):
                results.insert(0, f"📌 {kg['title']}: {kg.get('description', '')[:200]}\n")
        
        # Answer box
        if 'answer_box' in data:
            ab = data['answer_box']
            if ab.get('answer'):
                results.insert(0, f"💡 Answer: {ab['answer'][:300]}\n")
        
        return "\n".join(results) if results else f"No results found for '{query}'"
    
    def _fallback_search(self, query: str) -> str:
        """Fallback when API is not available"""
        return f"🔍 Search for '{query}' - Configure SerpAPI key for web results"
    
    async def search_news(self, query: str) -> str:
        """Search news"""
        return await self.search(query, engine="google_news")
    
    async def search_images(self, query: str, num_images: int = 5) -> str:
        """Search images"""
        if not self.initialized:
            return "Image search requires API key"
        
        try:
            import aiohttp
            
            params = {
                'q': query,
                'api_key': self.api_key,
                'engine': 'google_images',
                'ijn': '0'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        images = data.get('images_results', [])[:num_images]
                        
                        results = [f"🖼️ Image results for '{query}':\n"]
                        for i, img in enumerate(images, 1):
                            results.append(f"{i}. {img.get('title', 'Image')}")
                            results.append(f"   {img.get('original', '')[:100]}\n")
                        
                        return "\n".join(results)
        except Exception as e:
            print(f"Image search error: {e}")
        
        return f"🖼️ Image search for '{query}'"
    
    async def search_videos(self, query: str) -> str:
        """Search videos"""
        return await self.search(query, engine="youtube")
    
    async def shutdown(self):
        """Cleanup"""
        if hasattr(self, 'session'):
            await self.session.close()
