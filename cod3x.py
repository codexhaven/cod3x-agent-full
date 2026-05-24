#!/usr/bin/env python3
"""
Cod3x-Agent: Complete Multi-Agent System
Main entry point for the entire system
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from cod3x_main import Cod3xMain
from utils.config import Config
from utils.logger import setup_logger

async def main():
    parser = argparse.ArgumentParser(description='Cod3x Multi-Agent System')
    parser.add_argument('--mode', choices=['telegram', 'cli', 'voice'], 
                       default='cli', help='Interface mode')
    parser.add_argument('--config', default='config.yaml', 
                       help='Configuration file path')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Setup
    config = Config(args.config)
    logger = setup_logger(config.get('logging', {}), args.debug)
    
    logger.info("🚀 Initializing Cod3x-Agent System...")
    
    try:
        # Initialize main system
        cod3x = Cod3xMain(config, logger)
        await cod3x.initialize()
        
        logger.info("✅ Cod3x-Agent System initialized successfully")
        
        # Launch interface
        if args.mode == 'telegram':
            from interface.telegram_bot import TelegramInterface
            interface = TelegramInterface(cod3x, config)
        elif args.mode == 'voice':
            from interface.voice_listener import VoiceInterface
            interface = VoiceInterface(cod3x, config)
        else:
            from interface.cli_chat import CLIInterface
            interface = CLIInterface(cod3x, config)
        
        await interface.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down Cod3x-Agent...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise
    finally:
        await cod3x.shutdown()
        logger.info("👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())
