"""Content Agent - Content creation and writing assistant"""
import asyncio
from typing import Dict, Any
from datetime import datetime

class ContentAgent:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger

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
                return await self._write_article(request, user_id)
        except Exception as e:
            self.logger.error(f"Content agent error: {e}")
            return "✍️ I had trouble creating content. Please try again."

    async def _write_article(self, request: str, user_id: str) -> str:
        """Write an article or blog post"""
        from llm_proxy import generate
        
        topic = self._extract_topic(request)
        content_type = self._extract_content_type(request)

        if not topic:
            return "✍️ What topic should I write about?"

        prompt = f"""Write a {content_type} about: {topic}

Include:
- Engaging headline
- Introduction hook
- 3-5 key points with subheadings
- Supporting details
- Conclusion with call-to-action

Tone: {self._extract_tone(request)}
Length: {self._extract_length(request)}"""

        try:
            result = generate(prompt)
            
            # Store content
            await self.cod3x.memory['sqlite'].store_content(user_id, {
                'topic': topic,
                'content': result,
                'type': content_type,
                'created_at': datetime.now().isoformat(),
                'status': 'draft'
            })

            return f"✍️ **{content_type.title()}: {topic.title()}**\n\n{result}"
        except Exception as e:
            return f"✍️ Error: {str(e)[:200]}"

    def _extract_topic(self, request: str) -> str:
        text = request.lower()
        for prefix in ['write about', 'article about', 'blog about', 'content about', 'write article about', 'write blog about']:
            if prefix in text:
                topic = text.split(prefix, 1)[1].strip()
                return topic
        return text

    def _extract_content_type(self, request: str) -> str:
        text = request.lower()
        if 'blog' in text: return 'blog post'
        elif 'social' in text: return 'social media post'
        elif 'email' in text: return 'email'
        elif 'script' in text: return 'script'
        return 'article'

    def _extract_tone(self, request: str) -> str:
        text = request.lower()
        tones = {
            'professional': ['professional', 'formal', 'business'],
            'casual': ['casual', 'friendly', 'conversational'],
            'humorous': ['funny', 'humorous', 'witty'],
            'inspirational': ['inspirational', 'motivational'],
            'educational': ['educational', 'informative', 'tutorial']
        }
        for tone, keywords in tones.items():
            if any(kw in text for kw in keywords):
                return tone
        return 'professional'

    def _extract_length(self, request: str) -> str:
        text = request.lower()
        if 'short' in text: return '300-500 words'
        elif 'long' in text or 'detailed' in text: return '1500-2000 words'
        elif 'medium' in text: return '800-1000 words'
        return '800-1200 words'

    async def _generate_headlines(self, request: str, user_id: str) -> str:
        from llm_proxy import generate
        topic = self._extract_topic(request)
        prompt = f"Generate 10 compelling, SEO-friendly headlines for: {topic}. Include how-to, listicle, question, and emotional headlines."
        try:
            result = generate(prompt)
            return f"📰 **Headlines for '{topic}'**\n\n{result}"
        except Exception as e:
            return f"📰 Error: {e}"

    async def _create_outline(self, request: str, user_id: str) -> str:
        from llm_proxy import generate
        topic = self._extract_topic(request)
        prompt = f"Create a detailed content outline for: {topic}. Include title, introduction, 3-5 main sections with subpoints, conclusion, and call-to-action."
        try:
            result = generate(prompt)
            return f"📋 **Outline: {topic}**\n\n{result}"
        except Exception as e:
            return f"📋 Error: {e}"

    async def _rewrite_content(self, request: str, user_id: str) -> str:
        from llm_proxy import generate
        text = request
        for prefix in ['rewrite', 'paraphrase', 'improve']:
            if prefix in text.lower():
                text = text.lower().split(prefix, 1)[1].strip()
                break
        prompt = f"Rewrite and improve this content for clarity and engagement:\n\n{text}"
        try:
            result = generate(prompt)
            return f"✏️ **Rewritten**\n\n{result}"
        except Exception as e:
            return f"✏️ Error: {e}"

    async def _generate_ideas(self, request: str, user_id: str) -> str:
        from llm_proxy import generate
        niche = self._extract_topic(request)
        prompt = f"Generate 10 unique content ideas for: {niche}. Include title, description, target audience, and format for each."
        try:
            result = generate(prompt)
            return f"💡 **Content Ideas: {niche}**\n\n{result}"
        except Exception as e:
            return f"💡 Error: {e}"

    async def shutdown(self):
        pass
