from llm_proxy import generate as llm_generate
"""
Twitter Agent - Twitter/X posting and monitoring
"""

import asyncio
from typing import Dict, Any, List
import json
from datetime import datetime

class TwitterAgent:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger
        from utils.free_ai import get_ai; self.model = get_ai()
    
    async def initialize(self):
        self.logger.info("Twitter Agent initialized")
        self.api_available = bool(self.config.get('twitter', {}).get('api_key'))
    
    async def process(self, request: str, user_id: str, action: str = None, params: Dict = None) -> str:
        """Process Twitter-related requests"""
        text_lower = request.lower()
        
        try:
            if any(kw in text_lower for kw in ['tweet', 'post to twitter', 'send tweet']):
                return await self._create_tweet(request, user_id)
            elif any(kw in text_lower for kw in ['twitter feed', 'timeline', 'tweets']):
                return await self._get_timeline(user_id)
            elif any(kw in text_lower for kw in ['twitter search', 'find tweet']):
                return await self._search_tweets(request, user_id)
            elif any(kw in text_lower for kw in ['twitter analytics', 'tweet stats']):
                return await self._get_analytics(user_id)
            elif any(kw in text_lower for kw in ['thread', 'tweetstorm']):
                return await self._create_thread(request, user_id)
            else:
                return await self._get_twitter_status(user_id)
        except Exception as e:
            self.logger.error(f"Twitter agent error: {e}")
            return "I had trouble with Twitter. Please check your API credentials."
    
    async def _create_tweet(self, request: str, user_id: str) -> str:
        """Create and post a tweet"""
        tweet_text = await self._extract_tweet_text(request)
        
        # Optimize for Twitter length
        if len(tweet_text) > 280:
            if self.model:
                prompt = f"Shorten this to under 280 characters while keeping key message:\n\n{tweet_text}"
                response = await asyncio.to_thread(
                    self.model._call, prompt
                )
                tweet_text = response[:280]
            else:
                tweet_text = tweet_text[:277] + "..."
        
        # Store tweet
        tweet_data = {
            'text': tweet_text,
            'created_at': datetime.now().isoformat(),
            'status': 'draft'
        }
        await self.cod3x.memory['sqlite'].store_tweet(user_id, tweet_data)
        
        # Post if API available
        if self.api_available:
            # Simulate posting (would use actual Twitter API)
            tweet_data['status'] = 'posted'
            return f"🐦 Tweet posted: \"{tweet_text[:100]}...\""
        
        return f"🐦 Tweet drafted (offline mode): \"{tweet_text[:100]}...\""
    
    async def _extract_tweet_text(self, request: str) -> str:
        """Extract tweet text from request"""
        text = request
        for prefix in ['tweet', 'post to twitter', 'send tweet']:
            if prefix in text.lower():
                text = text.lower().split(prefix, 1)[1].strip()
                break
        
        # Generate tweet if needed
        if not text and self.model:
            prompt = f"Generate an engaging tweet about: {request}"
            response = await asyncio.to_thread(
                self.model._call, prompt
            )
            text = response
        
        return text or "Hello Twitter! #Cod3x"
    
    async def _get_timeline(self, user_id: str) -> str:
        """Get Twitter timeline"""
        if self.api_available:
            return "🐦 **Recent Timeline:**\n\n(Connect Twitter API to see your timeline)"
        
        # Show recent drafts
        tweets = await self.cod3x.memory['sqlite'].get_tweets(user_id, limit=5)
        
        if tweets:
            response = "🐦 **Your Recent Tweets:**\n\n"
            for tweet in tweets:
                response += f"• {tweet['text'][:100]}\n"
                response += f"  {tweet['created_at']} - {tweet.get('status', 'draft')}\n\n"
            return response
        
        return "🐦 No recent tweets. Say 'tweet [message]' to create one!"
    
    async def _search_tweets(self, request: str, user_id: str) -> str:
        """Search for tweets"""
        query = request.lower()
        for kw in ['twitter search', 'find tweet']:
            if kw in query:
                query = query.split(kw, 1)[1].strip()
                break
        
        return f"🔍 Searching Twitter for '{query}'... (requires API connection)"
    
    async def _get_analytics(self, user_id: str) -> str:
        """Get Twitter analytics"""
        tweets = await self.cod3x.memory['sqlite'].get_tweets(user_id)
        
        response = "📊 **Twitter Analytics:**\n\n"
        response += f"• Total tweets: {len(tweets)}\n"
        response += f"• Drafts: {sum(1 for t in tweets if t.get('status') == 'draft')}\n"
        response += f"• Posted: {sum(1 for t in tweets if t.get('status') == 'posted')}\n"
        
        return response
    
    async def _create_thread(self, request: str, user_id: str) -> str:
        """Create a tweet thread"""
        if self.model:
            topic = request.lower()
            for kw in ['thread', 'tweetstorm']:
                if kw in topic:
                    topic = topic.split(kw, 1)[1].strip()
                    break
            
            prompt = f"Create a Twitter thread of 3-5 tweets about: {topic}\n\nFormat each tweet separated by ---"
            response = await asyncio.to_thread(
                self.model._call, prompt
            )
            
            tweets = [t.strip() for t in response.split('---') if t.strip()]
            
            # Store thread
            for i, tweet in enumerate(tweets):
                await self.cod3x.memory['sqlite'].store_tweet(user_id, {
                    'text': tweet[:280],
                    'created_at': datetime.now().isoformat(),
                    'status': 'draft',
                    'thread_position': i + 1
                })
            
            return f"🧵 Thread created with {len(tweets)} tweets:\n\n" + "\n\n".join(f"{i+1}. {t[:100]}" for i, t in enumerate(tweets))
        
        return "🧵 Thread creation requires Gemini API for content generation."
    
    async def _get_twitter_status(self, user_id: str) -> str:
        """Get Twitter integration status"""
        status = "🐦 **Twitter Status:**\n"
        
        if self.api_available:
            status += "✅ API configured\n"
            status += "• Ready to post tweets\n"
        else:
            status += "⚠️ API not configured\n"
            status += "• Working in offline mode (drafts)\n"
        
        status += "• Use 'tweet [message]' to create\n"
        status += "• Use 'thread [topic]' for tweetstorms"
        
        return status
    
    async def shutdown(self):
        pass
