from llm_proxy import generate as llm_generate
"""
Research Agent - Deep research and analysis
"""

import asyncio
from typing import Dict, Any, List
import json
from datetime import datetime

class ResearchAgent:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger
        from utils.free_ai import get_ai; self.model = get_ai()
        self.search_tool = cod3x.tools.get('serpapi')
    
    async def initialize(self):
        self.logger.info("Research Agent initialized")
    
    async def process(self, request: str, user_id: str, action: str = None, params: Dict = None) -> str:
        """Process research requests"""
        text_lower = request.lower()
        
        try:
            if any(kw in text_lower for kw in ['research', 'analyze', 'deep dive', 'investigate']):
                return await self._deep_research(request, user_id)
            elif any(kw in text_lower for kw in ['compare', 'versus', 'vs']):
                return await self._compare_analysis(request, user_id)
            elif any(kw in text_lower for kw in ['summary', 'summarize', 'brief']):
                return await self._create_summary(request, user_id)
            elif any(kw in text_lower for kw in ['trends', 'analysis', 'insights']):
                return await self._analyze_trends(request, user_id)
            elif any(kw in text_lower for kw in ['report', 'detailed']):
                return await self._generate_report(request, user_id)
            else:
                return await self._quick_research(request, user_id)
        except Exception as e:
            self.logger.error(f"Research agent error: {e}")
            return "I had trouble with your research request. Let me try a simpler approach."
    
    async def _deep_research(self, request: str, user_id: str) -> str:
        """Conduct deep research on a topic"""
        topic = await self._extract_topic(request)
        
        if not topic:
            return "🔬 What topic would you like me to research?"
        
        # Gather information from multiple sources
        sources = []
        
        # Web search
        if self.search_tool:
            try:
                search_results = await self.search_tool.search(topic)
                sources.append(("Web", search_results[:500]))
            except:
                pass
        
        # Gemini analysis
        if self.model:
            prompt = f"""Conduct thorough research on: {topic}
            
            Provide:
            1. Executive Summary
            2. Key Facts and Data
            3. Historical Context
            4. Current Developments
            5. Expert Opinions
            6. Future Outlook
            7. Key Takeaways
            
            Be comprehensive, balanced, and cite key sources."""
            
            try:
                analysis = await asyncio.to_thread(
                    self.model._call, prompt
                )
                sources.append(("AI Analysis", analysis.text))
            except:
                pass
        
        if sources:
            # Store research
            research_data = {
                'topic': topic,
                'sources': sources,
                'timestamp': datetime.now().isoformat()
            }
            await self.cod3x.memory['vector'].add_text(
                f"Research: {topic}",
                research_data
            )
            
            # Format response
            response = f"🔬 **Research: {topic}**\n\n"
            for source_type, content in sources:
                response += f"[{source_type}]\n{content[:800]}\n\n"
            
            return response
        
        return f"🔬 Researching '{topic}'... I'll compile information from available sources."
    
    async def _extract_topic(self, request: str) -> str:
        """Extract research topic"""
        text = request.lower()
        
        for prefix in ['research', 'analyze', 'deep dive into', 'investigate']:
            if prefix in text:
                topic = text.split(prefix, 1)[1].strip()
                return topic
        
        return text
    
    async def _compare_analysis(self, request: str, user_id: str) -> str:
        """Compare two or more items"""
        items = await self._extract_comparison_items(request)
        
        if self.model and len(items) >= 2:
            prompt = f"""Compare and contrast: {' vs '.join(items)}
            
            Analyze:
            1. Key Features
            2. Strengths and Weaknesses
            3. Use Cases
            4. Cost/Value
            5. Recommendations
            
            Provide a balanced comparison with specific details."""
            
            try:
                response = await asyncio.to_thread(
                    self.model._call, prompt
                )
                return f"⚖️ **Comparison: {' vs '.join(items)}**\n\n{response}"
            except:
                pass
        
        return f"⚖️ Comparing {' vs '.join(items)}. I'll analyze key differences and similarities."
    
    async def _extract_comparison_items(self, request: str) -> List[str]:
        """Extract items for comparison"""
        text = request.lower()
        items = []
        
        # Split by comparison keywords
        for separator in [' vs ', ' versus ', ' compared to ', ' or ']:
            if separator in text:
                parts = text.split(separator)
                items = [p.strip() for p in parts if p.strip()]
                break
        
        # Remove leading keywords
        items = [item for item in items if item not in ['compare', 'which is better']]
        
        return items[:4]  # Max 4 items to compare
    
    async def _create_summary(self, request: str, user_id: str) -> str:
        """Create a summary of content"""
        content = request.lower()
        for kw in ['summarize', 'summary of', 'brief on']:
            if kw in content:
                content = content.split(kw, 1)[1].strip()
                break
        
        if self.model:
            prompt = f"Summarize the following concisely, highlighting key points:\n\n{content}"
            
            try:
                response = await asyncio.to_thread(
                    self.model._call, prompt
                )
                return f"📝 **Summary:**\n\n{response}"
            except:
                pass
        
        return "📝 I can create summaries. Provide me with text or a topic to summarize."
    
    async def _analyze_trends(self, request: str, user_id: str) -> str:
        """Analyze trends"""
        topic = await self._extract_topic(request)
        
        if self.model:
            prompt = f"""Analyze current trends for: {topic}
            
            Include:
            • Market Trends
            • Consumer Behavior
            • Technology Impact
            • Future Predictions"""
            
            try:
                response = await asyncio.to_thread(
                    self.model._call, prompt
                )
                return f"📈 **Trend Analysis: {topic}**\n\n{response}"
            except:
                pass
        
        return f"📈 Analyzing trends for {topic}. I'll identify patterns and predictions."
    
    async def _generate_report(self, request: str, user_id: str) -> str:
        """Generate detailed report"""
        topic = await self._extract_topic(request)
        
        if self.model:
            prompt = f"""Generate a professional report on: {topic}
            
            Format:
            📊 Executive Summary
            📋 Background
            🔍 Analysis
            📈 Findings
            💡 Recommendations
            📎 References"""
            
            try:
                response = await asyncio.to_thread(
                    self.model._call, prompt
                )
                
                # Store report
                await self.cod3x.memory['sqlite'].store_document(user_id, {
                    'title': f"Report: {topic}",
                    'content': response,
                    'type': 'report'
                })
                
                return f"📊 **Report Generated: {topic}**\n\n{response[:1000]}...\n\n(Full report saved to documents)"
            except:
                pass
        
        return f"📊 Report generation for '{topic}'. I'll create a comprehensive analysis."
    
    async def _quick_research(self, request: str, user_id: str) -> str:
        """Quick research assistance"""
        return "🔬 **Research Assistant**\n\n• 'research [topic]' - Deep analysis\n• 'compare A vs B' - Side-by-side\n• 'summarize [text]' - Quick summary\n• 'trends [topic]' - Trend analysis\n• 'report on [topic]' - Full report"
    
    async def shutdown(self):
        pass
