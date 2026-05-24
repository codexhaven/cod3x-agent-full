"""
Social Agent - Social media content creation and scheduling
"""

import asyncio
from typing import Dict, Any, List
import json
from datetime import datetime, timedelta

class SocialAgent:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger
        self.model = cod3x.model
    
    async def initialize(self):
        self.logger.info("Social Agent initialized")
    
    async def process(self, request: str, user_id: str, action: str = None, params: Dict = None) -> str:
        """Process social media requests"""
        text_lower = request.lower()
        
        try:
            if any(kw in text_lower for kw in ['create post', 'social post', 'write post']):
                return await self._create_post(request, user_id)
            elif any(kw in text_lower for kw in ['schedule', 'plan post']):
                return await self._schedule_post(request, user_id)
            elif any(kw in text_lower for kw in ['hashtag', 'tag suggest']):
                return await self._suggest_hashtags(request, user_id)
            elif any(kw in text_lower for kw in ['caption', 'write caption']):
                return await self._create_caption(request, user_id)
            elif any(kw in text_lower for kw in ['social calendar', 'content calendar']):
                return await self._view_calendar(user_id)
            else:
                return await self._social_assistance(user_id)
        except Exception as e:
            self.logger.error(f"Social agent error: {e}")
            return "I had trouble with social media content. Please try again."
    
    async def _create_post(self, request: str, user_id: str) -> str:
        """Create social media post"""
        platform = await self._extract_platform(request)
        topic = await self._extract_topic(request)
        
        if not topic:
            return "📱 What topic would you like to post about?"
        
        # Generate platform-specific content
        if self.model:
            prompt = f"""Create an engaging {platform} post about: {topic}
            
            Platform guidelines:
            - Twitter/X: Max 280 chars, concise
            - LinkedIn: Professional tone, 100-200 words
            - Instagram: Visual-focused caption, emojis
            - Facebook: Conversational, 50-150 words
            
            Include:
            1. Hook/Headline
            2. Main content
            3. Call to action
            4. 3-5 relevant hashtags"""
            
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                
                # Store post
                await self.cod3x.memory['sqlite'].store_social_post(user_id, {
                    'platform': platform,
                    'content': response.text,
                    'topic': topic,
                    'status': 'draft',
                    'created_at': datetime.now().isoformat()
                })
                
                return f"📱 **{platform.title()} Post Created**\n\n{response.text}"
            except:
                pass
        
        return f"📱 {platform.title()} post draft for '{topic}'. I'll optimize it for engagement."
    
    async def _extract_platform(self, request: str) -> str:
        """Extract social platform"""
        text = request.lower()
        
        platforms = {
            'twitter': ['twitter', 'tweet', 'x.com'],
            'linkedin': ['linkedin', 'linked in'],
            'instagram': ['instagram', 'insta'],
            'facebook': ['facebook', 'fb']
        }
        
        for platform, keywords in platforms.items():
            if any(kw in text for kw in keywords):
                return platform
        
        return 'twitter'  # Default
    
    async def _extract_topic(self, request: str) -> str:
        """Extract post topic"""
        text = request.lower()
        
        for prefix in ['about', 'post about', 'create post', 'write about']:
            if prefix in text:
                topic = text.split(prefix, 1)[1].strip()
                return topic
        
        return text
    
    async def _schedule_post(self, request: str, user_id: str) -> str:
        """Schedule a social media post"""
        # Extract schedule time
        schedule_time = datetime.now() + timedelta(hours=1)  # Default: 1 hour
        
        text_lower = request.lower()
        
        if 'tomorrow' in text_lower:
            schedule_time = datetime.now() + timedelta(days=1)
        elif 'next week' in text_lower:
            schedule_time = datetime.now() + timedelta(days=7)
        
        # Get latest draft
        drafts = await self.cod3x.memory['sqlite'].get_social_posts(user_id, status='draft', limit=1)
        
        if drafts:
            draft = drafts[0]
            await self.cod3x.memory['sqlite'].schedule_post(user_id, {
                'post_id': draft.get('id'),
                'scheduled_time': schedule_time.isoformat(),
                'platform': draft.get('platform')
            })
            
            return f"📅 Post scheduled for {schedule_time.strftime('%Y-%m-%d %H:%M')} on {draft.get('platform', 'social media')}"
        
        return "📅 No drafts to schedule. Create a post first with 'create post'!"
    
    async def _suggest_hashtags(self, request: str, user_id: str) -> str:
        """Suggest hashtags for content"""
        topic = await self._extract_topic(request)
        
        if self.model:
            prompt = f"Suggest 10 relevant and trending hashtags for social media content about: {topic}. Mix popular and niche hashtags."
            
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                return f"#️⃣ **Hashtag Suggestions for '{topic}'**\n\n{response.text}"
            except:
                pass
        
        return f"#️⃣ Popular hashtags for {topic}: #content #socialmedia #trending #viral"
    
    async def _create_caption(self, request: str, user_id: str) -> str:
        """Create image/video caption"""
        context = await self._extract_topic(request)
        
        if self.model:
            prompt = f"Write 3 engaging social media captions for content about: {context}. Include emojis and call-to-actions."
            
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                return f"✍️ **Caption Options**\n\n{response.text}"
            except:
                pass
        
        return "✍️ I can create engaging captions. Tell me about your content!"
    
    async def _view_calendar(self, user_id: str) -> str:
        """View social media content calendar"""
        scheduled = await self.cod3x.memory['sqlite'].get_scheduled_posts(user_id)
        drafts = await self.cod3x.memory['sqlite'].get_social_posts(user_id, status='draft')
        
        response = "📅 **Social Media Calendar**\n\n"
        
        if scheduled:
            response += "**Scheduled Posts:**\n"
            for post in scheduled[:5]:
                time = post.get('scheduled_time', 'Unknown')
                platform = post.get('platform', 'social')
                response += f"• {platform.title()} - {time}\n"
        else:
            response += "No scheduled posts\n"
        
        if drafts:
            response += f"\n**Drafts:** {len(drafts)} posts\n"
        
        response += "\nUse 'create post' and 'schedule' to plan content!"
        
        return response
    
    async def _social_assistance(self, user_id: str) -> str:
        """Social media assistance overview"""
        return "📱 **Social Media Assistant**\n\n• 'create post for [platform]' - Write posts\n• 'schedule post' - Plan publishing\n• 'suggest hashtags' - Get trending tags\n• 'create caption' - Write captions\n• 'content calendar' - View schedule"
    
    async def shutdown(self):
        pass
