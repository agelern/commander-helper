import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent)
sys.path.append(src_path)

from dotenv import load_dotenv
from src.bot.discord_bot import run_bot

def main():
    """Main entry point for the bot."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Run the bot
    run_bot()

if __name__ == "__main__":
    main() 