#!/usr/bin/env python3
"""
Commander Helper Bot - Main Entry Point

A Discord bot for Magic: The Gathering Commander format assistance.
Provides card information and commander recommendations.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent)
sys.path.append(src_path)

from dotenv import load_dotenv
from src.bot.discord_bot import CommanderBot
from src.data.card_data_manager import CardDataManager
from src.utils.config import Config
from src.utils.logger import setup_logging

def setup_environment() -> Config:
    """Set up the application environment and configuration."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Set up logging
    setup_logging()
    
    # Load configuration
    config = Config()
    
    return config

async def ensure_card_data(config: Config) -> None:
    """Ensure card data exists, download if needed."""
    data_file = Path(__file__).parent.parent / 'reference' / 'oracle_cards.json'
    
    if not data_file.exists():
        logging.info("Card data not found. Downloading...")
        try:
            downloader = CardDataManager()
            await downloader.download()
            logging.info("Card data download complete.")
        except Exception as e:
            logging.error(f"Failed to download card data: {e}")
            raise
    else:
        logging.info("Card data found, checking for updates...")
        try:
            downloader = CardDataManager()
            await downloader.check_and_update()
        except Exception as e:
            logging.warning(f"Failed to check for card data updates: {e}")

async def main() -> None:
    """Main entry point for the bot."""
    try:
        # Set up environment
        config = setup_environment()
        
        # Ensure card data exists
        await ensure_card_data(config)
        
        # Create and run the bot
        bot = CommanderBot(config)
        await bot.start(config.discord_token)
        
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 