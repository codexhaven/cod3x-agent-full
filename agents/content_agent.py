"""
Content Agent - Content creation and writing assistant
"""

import asyncio
from typing import Dict, Any, List
import json
from datetime import datetime

class ContentAgent:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger
        self.model = cod3x.model
    
    async def initialize(self):
        self.logger.info("Content Agent initialized")
    
    async def process(self, request: str, user_id: str, action: str = None, params: Dict = None) -> str:
        """Process content creation requests"""
        text_lower = request.lower()
        
        try:
            if any(kw in text_lower for kw in ['write article', 'blog post', 'create content']):
                return await self._write_article(request, user_id)
            elif any(kw in text_lower for kw in ['headline', 'title', 'subject line']):
                return await self._generate_headlines(request, user_id)
            elif any(kw in text_lower for kw in ['outline', 'structure']):
                return await self._create_outline(request, user_id)
            elif any(kw in text_lower for kw in ['rewrite', 'paraphrase', 'improve']):
                return await self._rewrite_content(request, user_id)
            elif any(kw in text_lower for kw in ['content ideas', 'topic ideas', 'what to write']):
                return await self._generate_ideas(request, user_id)
            else:
                return await self._content_assistance(user_id)
        except Exception as e:
            self.logger.error(f"Content agent error: {e}")
            return "I had trouble creating content. Please try again."
    
    async def _write_article(self, request: str, user_id: str) -> str:
        """Write an article or blog post"""
        topic = await self._extract_topic(request)
        content_type = await self._extract_content_type(request)
        
        if not topic:
            return "✍️ What topic should I write about?"
        
        if self.model:
            prompt = f"""Write a {content_type} about: {topic}
            
            Include:
            - Engaging headline
            - Introduction hook
            - 3-5 key points with subheadings
            - Supporting details
            - Conclusion with call-to-action
            - SEO considerations
            
            Tone: {await self._extract_tone(request)}
            Length: {await self._extract_length(request)}"""
            
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                
                # Store content
                await self.cod3x.memory['sqlite'].store_content(user_id, {
                    'topic': topic,
                    'content': response.text,
                    'type': content_type,
                    'created_at': datetime.now().isoformat(),
                    'status': 'draft'
                })
                
                return f"✍️ **{content_type.title()} Created: {topic}**\n\n{response.text[:1500]}...\n\n(Full content saved to drafts)"
            except:
                pass
        
        return f"✍️ Creating {content_type} about '{topic}'. I'll structure it for maximum engagement."
    
    async def _extract_topic(self, request: str) -> str:
        """Extract content topic"""
        text = request.lower()
        
        for prefix in ['write about', 'article about', 'blog about', 'content about']:
            if prefix in text:
                topic = text.split(prefix, 1)[1].strip()
                return topic
        
        return text
    
    async def _extract_content_type(self, request: str) -> str:
        """Extract content type"""
        text = request.lower()
        
        if 'blog' in text:
            return 'blog post'
        elif 'article' in text:
            return 'article'
        elif 'social' in text:
            return 'social media post'
        elif 'email' in text:
            return 'email'
        elif 'script' in text:
            return 'script'
        elif 'newsletter' in text:
            return 'newsletter'
        
        return 'article'
    
    async def _extract_tone(self, request: str) -> str:
        """Extract desired tone"""
        text = request.lower()
        
        tones = {
            'professional': ['professional', 'formal', 'business'],
            'casual': ['casual', 'friendly', 'conversational'],
            'humorous': ['funny', 'humorous', 'witty', 'humor'],
            'inspirational': ['inspirational', 'motivational', 'inspiring'],
            'educational': ['educational', 'informative', 'tutorial']
        }
        
        for tone, keywords in tones.items():
            if any(kw in text for kw in keywords):
                return tone
        
        return 'professional'
    
    async def _extract_length(self, request: str) -> str:
        """Extract desired length"""
        text = request.lower()
        
        if 'short' in text:
            return '300-500 words'
        elif 'long' in text or 'detailed' in text:
            return '1500-2000 words'
        elif 'medium' in text:
            return '800-1000 words'
        
        return '800-1200 words'
    
    async def _generate_headlines(self, request: str, user_id: str) -> str:
        """Generate headlines"""
        topic = await self._extract_topic(request)
        
        if self.model:
            prompt = f"""Generate 10 compelling headlines for: {topic}
            
            Include different types:
            - How-to headlines
            - Listicle headlines
            - Question headlines
            - Emotional headlines
            - Urgency headlines
            
            Make them SEO-friendly and click-worthy."""
            
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                return f"📰 **Headline Options for '{topic}'**\n\n{response.text}"
            except:
                pass
        
        return f"📰 Headline generation for '{topic}'. I'll create attention-grabbing options."
    
    async def _create_outline(self, request: str, user_id: str) -> str:
        """Create content outline"""
        topic = await self._extract_topic(request)
        
        if self.model:
            prompt = f"""Create a detailed content outline for: {topic}
            
            Include:
            1. Title/Headline
            2. Introduction (hook + thesis)
            3. Main sections (3-5) with subpoints
            4. Supporting evidence/examples
            5. Conclusion
            6. Call-to-action
            
            Format as a structured outline."""
            
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                return f"📋 **Content Outline: {topic}**\n\n{response.text}"
            except:
                pass
        
        return f"📋 Outline for '{topic}'. I'll structure it for clarity and flow."
    
    async def _rewrite_content(self, request: str, user_id: str) -> str:
        """Rewrite or improve content"""
        content = await self._extract_content_to_rewrite(request)
        
        if self.model and content:
            prompt = f"""Rewrite the following content to improve clarity, engagement, and flow:
            
            Original: {content}
            
            Provide:
            1. Rewritten version
            2. Summary of changes made
            3. Improvement suggestions"""
            
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                return f"✏️ **Rewritten Content**\n\n{response.text}"
            except:
                pass
        
        return "✏️ I can rewrite and improve content. Share the text you want me to enhance!"
    
    async def _extract_content_to_rewrite(self, request: str) -> str:
        """Extract content for rewriting"""
        text = request
        
        for prefix in ['rewrite', 'paraphrase', 'improve']:
            if prefix in text.lower():
                content = text.lower().split(prefix, 1)[1].strip()
                return content
        
        return text
    
    async def _generate_ideas(self, request: str, user_id: str) -> str:
        """Generate content ideas"""
        niche = await self._extract_topic(request)
        
        if self.model:
            prompt = f"""Generate 10 unique content ideas for: {niche}
            
            For each idea, provide:
            - Title/Headline
            - Brief description
            - Target audience
            - Content format (article, video, infographic, etc.)
            - Estimated effort (easy/medium/hard)"""
            
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                return f"💡 **Content Ideas: {niche}**\n\n{response.text}"
            except:
                pass
        
        return f"💡 Content ideas for {niche}. I'll suggest trending and evergreen topics."
    
    async def _content_assistance(self, user_id: str) -> str:
        """Content assistance overview"""
        recent = await self.cod3x.memory['sqlite'].get_content(user_id, limit=3)
        
        response = "✍️ **Content Creation Assistant**\n\n"
        response += "• 'write article about [topic]' - Create content\n"
        response += "• 'headlines for [topic]' - Get title ideas\n"
        response += "• 'outline for [topic]' - Structure content\n"
        response += "• 'rewrite [text]' - Improve writing\n"
        response += "• 'content ideas for [niche]' - Topic generation\n"
        
        if recent:
            response += f"\n📄 Recent drafts: {len(recent)}"
        
        return response
    
    async def shutdown(self):
        pass
