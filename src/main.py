import os
import sys
from pathlib import Path
import asyncio

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent)
sys.path.append(src_path)

from dotenv import load_dotenv
from src.bot.discord_bot import run_bot
from src.data.card_data_downloader import CardDataDownloader

def ensure_card_data():
    """Ensure card data exists, download if needed."""
    data_file = Path(__file__).parent.parent / 'reference' / 'oracle_cards.json'
    if not data_file.exists():
        print("Card data not found. Downloading...")
        downloader = CardDataDownloader()
        asyncio.run(downloader.download())
        print("Card data download complete.")

def main():
    """Main entry point for the bot."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Ensure card data exists
    ensure_card_data()
    
    # Run the bot
    run_bot()

if __name__ == "__main__":
    main() 