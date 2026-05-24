#!/bin/bash
# Setup script for Cod3x Agent

echo "🚀 Setting up Cod3x Multi-Agent System..."
echo ""

# Create directory structure
echo "📁 Creating directories..."
mkdir -p agents tools memory interface utils

# Check Python version
echo "🐍 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python $python_version detected"

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Create config if not exists
if [ ! -f config.yaml ]; then
    echo "⚙️  Creating default config..."
    cp config.yaml.example config.yaml 2>/dev/null || true
fi

# Set up environment variables
echo ""
echo "🔑 API Key Setup:"
echo "   You'll need these API keys for full functionality:"
echo "   - Gemini API (free): https://makersuite.google.com/app/apikey"
echo "   - SerpAPI: https://serpapi.com/ (for web search)"
echo "   - Telegram Bot: https://t.me/BotFather (for Telegram interface)"
echo ""
echo "   Set them with:"
echo "   export GEMINI_API_KEY='your-key-here'"
echo "   export SERPAPI_API_KEY='your-key-here'"
echo "   export TELEGRAM_BOT_TOKEN='your-token-here'"

# Initialize database
echo ""
echo "🗄️  Initializing database..."
python3 -c "
from memory.sqlite_memory import SQLiteMemory
import asyncio
async def init():
    mem = SQLiteMemory({'sqlite_path': 'cod3x_memory.db'})
    await mem.initialize()
    await mem.shutdown()
asyncio.run(init())
print('   Database initialized')
" 2>/dev/null || echo "   Database will initialize on first run"

echo ""
echo "✅ Setup complete! Run with:"
echo "   python cod3x.py --mode cli"
echo "   python cod3x.py --mode telegram"
echo "   python cod3x.py --mode voice"
echo ""
