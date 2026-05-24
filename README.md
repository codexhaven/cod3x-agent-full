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
