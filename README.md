# 🤖 Cod3x Multi-Agent System

A complete multi-agent AI system with 40+ specialized agents for productivity, communication, lifestyle, insights, and publishing.

## 🚀 Quick Start

```bash
# Clone and setup
git clone (https://github.com/codexhaven/cod3x-agent-full.git)
cd cod3x-agent-full
bash setup.sh

# Set your Gemini API key (get free key at https://makersuite.google.com/app/apikey)
export GEMINI_API_KEY='your-key-here'

# Run in CLI mode
python cod3x.py --mode cli

# Run Telegram bot
export TELEGRAM_BOT_TOKEN='your-bot-token'
python cod3x.py --mode telegram

# Run voice interface
python cod3x.py --mode voice

### 🏗️ Architecture
Core System
Nexus Supervisor: Central routing intelligence

6 Domain Supervisors: Codex, Comms, Anubis, Oracle, Forge

16 Specialized Agents: Calendar to Content

8 Tools: Calendar, Gmail, Sheets, SerpAPI, Drive, Telegram, Notify, Execute

3 Memory Systems: Buffer, Vector, SQLite

4 Interfaces: CLI, Telegram, Voice, API

Agent Categories
Productivity (Codex)

Calendar Agent - Scheduling & events

Tasks Agent - To-do management

Docs Agent - Document creation

Contacts Agent - Contact management

Communication (Comms)

Email Agent - Gmail integration

Telegram Agent - Messaging

Twitter Agent - Social posting

Lifestyle (Anubis)

Expenses Agent - Budget tracking

Travel Agent - Trip planning

Meals Agent - Recipes & meal plans

Insights (Oracle)

Search Agent - Web search

Research Agent - Deep analysis

Crypto Agent - Price tracking

Publishing (Forge)

Social Agent - Content creation

Image Agent - Image generation prompts

Content Agent - Article writing

### 📋 Features
✅ Natural language understanding

✅ Multi-domain expertise

✅ Persistent memory across sessions

✅ Vector search for semantic queries

✅ Tool integrations (Calendar, Email, etc.)

✅ Multiple interfaces (CLI, Telegram, Voice)

✅ Free Gemini API integration

✅ Extensible architecture

✅ Offline fallback modes

### 🔧 Configuration
Edit config.yaml or use environment variables:
export GEMINI_API_KEY='your-key'
export SERPAPI_API_KEY='your-key'
export TELEGRAM_BOT_TOKEN='your-token'
export TELEGRAM_CHAT_ID='your-chat-id'
### 📚 Usage Examples
# CLI mode
python cod3x.py

You> Schedule a meeting tomorrow at 2pm
Cod3x> 📅 Event created: 'Meeting' for tomorrow at 14:00

You> Add task: Buy groceries
Cod3x> ✅ Task added: 'Buy Groceries' (Priority: medium)

You> Search for latest AI news
Cod3x> 🔍 Searching for latest AI news...
[Displays search results]

You> What's the price of Bitcoin?
Cod3x> 💎 Bitcoin Price: $42,500 USD

You> Write a tweet about AI
Cod3x> 🐦 Tweet drafted: "Excited about the future of AI!..."

# Telegram mode
python cod3x.py --mode telegram
# Then interact with your bot on Telegram

### 🗂️ File Structure
cod3x-agent-full/
├── cod3x.py                 # Main entry point
├── cod3x_main.py            # Core system
├── nexus_supervisor.py      # Central router
├── codex_supervisor.py      # Productivity domain
├── comms_supervisor.py      # Communication domain
├── anubis_supervisor.py     # Lifestyle domain
├── oracle_supervisor.py     # Insights domain
├── forge_supervisor.py      # Publishing domain
├── agents/                  # 16 specialized agents
│   ├── calendar_agent.py
│   ├── tasks_agent.py
│   ├── ... (14 more)
├── tools/                   # 8 tool integrations
│   ├── calendar_tool.py
│   ├── gmail_tool.py
│   └── ... (6 more)
├── memory/                  # Memory systems
│   ├── buffer_memory.py
│   ├── vector_memory.py
│   └── sqlite_memory.py
├── interface/               # User interfaces
│   ├── cli_chat.py
│   ├── telegram_bot.py
│   ├── voice_listener.py
│   └── voice_speaker.py
├── utils/                   # Utilities
│   ├── config.py
│   ├── logger.py
│   └── helpers.py
├── config.yaml              # Configuration
├── requirements.txt         # Dependencies
├── setup.sh                 # Setup script
└── README.md               # Documentation

### 🎯 Total Files: 40+
6 Core Supervisor files

16 Agent files

8 Tool files

3 Memory files

4 Interface files

3 Utility files

1 Main entry point

Plus config, requirements, and documentation

### 💡 Tips
Get a free Gemini API key at https://makersuite.google.com/app/apikey

For web search, get a SerpAPI key at https://serpapi.com/

For Telegram, create a bot with @BotFather

All features work in offline mode (limited functionality)

Use /help in CLI or Telegram for available commands

### 📄 License
MIT License - Free to use, modify, and distribute

**Complete!** 🎉 

The Cod3x Multi-Agent System is now fully built with all 40+ files. The system includes:

✅ **Core**: Main entry, Nexus router, 6 domain supervisors
✅ **16 Agents**: Full functionality for all domains  
✅ **8 Tools**: API integrations ready to configure
✅ **3 Memory Systems**: Buffer, Vector, SQLite with full schemas
✅ **4 Interfaces**: CLI, Telegram, Voice in/out
✅ **3 Utilities**: Config, Logger, Helpers
✅ **Documentation**: README, config, requirements, setup script

All agents use the **free Gemini API** with complete fallback modes when offline. The system is modular, extensible, and ready to deploy!

To get started:
```bash
cd ~/cod3x-agent-full
bash setup.sh
export GEMINI_API_KEY='your-free-key'
python cod3x.py --mode cli
