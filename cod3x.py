#!/usr/bin/env python3
"""
Cod3x Main System - Central coordinator for all agents
Fixed: Handle missing google.generativeai gracefully
"""

import asyncio
import os
from typing import Dict, Any, Optional

# Handle Gemini import gracefully
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from nexus_supervisor import NexusSupervisor
from memory.buffer_memory import BufferMemory
from memory.vector_memory import VectorMemory
from memory.sqlite_memory import SQLiteMemory
from utils.logger import Logger

class Cod3xMain:
    def __init__(self, config: Dict, logger: Logger):
        self.config = config
        self.logger = logger
        self.nexus = None
        self.memory = {}
        self.agents = {}
        self.tools = {}
        
        # Initialize Gemini if available
        api_key = config.get('gemini_api_key') or os.getenv('GEMINI_API_KEY')
        if GEMINI_AVAILABLE and api_key:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                self.logger.info("✅ Gemini API connected")
            except Exception as e:
                self.logger.warning(f"Gemini init failed: {e}")
                self.model = None
        else:
            if not GEMINI_AVAILABLE:
                self.logger.warning("⚠️  google-generativeai not installed. Run: pip install google-generativeai")
            if not api_key:
                self.logger.warning("⚠️  No Gemini API key. Get free key at https://makersuite.google.com/app/apikey")
            self.model = None
    
    async def initialize(self):
        """Initialize all components"""
        print("🔧 Initializing Cod3x System...")
        
        print("  📦 Memory systems...")
        await self._init_memory()
        
        print("  🔧 Tools...")
        await self._init_tools()
        
        print("  🤖 Agents...")
        await self._init_agents()
        
        print("  🧠 Nexus Supervisor...")
        self.nexus = NexusSupervisor(self)
        await self.nexus.initialize()
        
        print("✅ System ready!")
    
    async def _init_memory(self):
        """Initialize memory systems"""
        self.memory['buffer'] = BufferMemory(self.config.get('memory', {}))
        self.memory['vector'] = VectorMemory(self.config.get('memory', {}))
        self.memory['sqlite'] = SQLiteMemory(self.config.get('memory', {}))
        
        await self.memory['buffer'].initialize()
        await self.memory['vector'].initialize()
        await self.memory['sqlite'].initialize()
    
    async def _init_tools(self):
        """Initialize all tools"""
        from tools.calendar_tool import CalendarTool
        from tools.gmail_tool import GmailTool
        from tools.sheets_tool import SheetsTool
        from tools.serpapi_tool import SerpAPITool
        from tools.drive_tool import DriveTool
        from tools.telegram_tool import TelegramTool
        from tools.notify_tool import NotifyTool
        from tools.execute_tool import ExecuteTool
        
        self.tools['calendar'] = CalendarTool(self.config)
        self.tools['gmail'] = GmailTool(self.config)
        self.tools['sheets'] = SheetsTool(self.config)
        self.tools['serpapi'] = SerpAPITool(self.config)
        self.tools['drive'] = DriveTool(self.config)
        self.tools['telegram'] = TelegramTool(self.config)
        self.tools['notify'] = NotifyTool(self.config)
        self.tools['execute'] = ExecuteTool(self.config)
        
        for name, tool in self.tools.items():
            try:
                await tool.initialize()
            except Exception as e:
                self.logger.warning(f"Tool {name} init skipped: {e}")
    
    async def _init_agents(self):
        """Initialize all specialized agents"""
        from agents.calendar_agent import CalendarAgent
        from agents.tasks_agent import TasksAgent
        from agents.docs_agent import DocsAgent
        from agents.contacts_agent import ContactsAgent
        from agents.email_agent import EmailAgent
        from agents.telegram_agent import TelegramAgent
        from agents.twitter_agent import TwitterAgent
        from agents.expenses_agent import ExpensesAgent
        from agents.travel_agent import TravelAgent
        from agents.meals_agent import MealsAgent
        from agents.search_agent import SearchAgent
        from agents.research_agent import ResearchAgent
        from agents.crypto_agent import CryptoAgent
        from agents.social_agent import SocialAgent
        from agents.image_agent import ImageAgent
        from agents.content_agent import ContentAgent
        
        self.agents = {
            'calendar': CalendarAgent(self),
            'tasks': TasksAgent(self),
            'docs': DocsAgent(self),
            'contacts': ContactsAgent(self),
            'email': EmailAgent(self),
            'telegram': TelegramAgent(self),
            'twitter': TwitterAgent(self),
            'expenses': ExpensesAgent(self),
            'travel': TravelAgent(self),
            'meals': MealsAgent(self),
            'search': SearchAgent(self),
            'research': ResearchAgent(self),
            'crypto': CryptoAgent(self),
            'social': SocialAgent(self),
            'image': ImageAgent(self),
            'content': ContentAgent(self)
        }
        
        for name, agent in self.agents.items():
            try:
                await agent.initialize()
            except Exception as e:
                self.logger.warning(f"Agent {name} init skipped: {e}")
    
    async def process_request(self, user_input: str, user_id: str = None) -> str:
        """Process user request through the nexus"""
        # Store in buffer memory
        await self.memory['buffer'].add(user_id, 'user', user_input)
        
        # Route through nexus
        response = await self.nexus.route(user_input, user_id)
        
        # Store response
        await self.memory['buffer'].add(user_id, 'assistant', response)
        
        return response
    
    async def shutdown(self):
        """Graceful shutdown"""
        for agent in self.agents.values():
            try:
                await agent.shutdown()
            except:
                pass
        for tool in self.tools.values():
            try:
                await tool.shutdown()
            except:
                pass
        for mem in self.memory.values():
            try:
                await mem.shutdown()
            except:
                pass
