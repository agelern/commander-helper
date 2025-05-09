# Commander Helper Bot

A Discord bot that helps Magic: The Gathering Commander players by providing quick access to card information.

## Features

- `/card <card name>` - Get detailed information about any Magic: The Gathering card
  - Shows card name, mana cost, type line, oracle text, power/toughness, set information, and card image
  - Fuzzy matching for card names with suggestions when exact match isn't found
  - Interactive buttons to select from suggested cards

## Application Flow

1. **Bot Initialization**
   - The bot starts up and loads environment variables
   - Checks if card data needs to be updated (downloads if older than 30 days)
   - Registers slash commands with Discord

2. **Card Data Management**
   - Card data is downloaded from Scryfall's bulk data API
   - Data is processed and stored locally in JSON format
   - Updates automatically when data is older than 30 days

3. **Command Processing**
   - When a user uses the `/card` command:
     1. Bot searches for exact card name match
     2. If no exact match, uses fuzzy matching to find similar cards
     3. If high confidence match found (>95%), returns that card
     4. If multiple matches found, shows interactive buttons for selection
     5. Formats and displays card information in a Discord embed

## Setup

1. Create a `.env` file with your Discord bot token:
   ```
   DISCORD_TOKEN=your_token_here
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the bot:
   ```
   python src/main.py
   ```

## Project Structure

```
.
├── src/
│   ├── bot/
│   │   └── discord_bot.py      # Main bot implementation
│   ├── commands/
│   │   ├── base.py            # Base command class
│   │   └── card_info.py       # Card info command implementation
│   ├── data/
│   │   ├── card_data.py       # Card data management
│   │   └── card_data_downloader.py  # Scryfall data downloader
│   └── main.py                # Application entry point
├── reference/                 # Local card data storage
├── .env                       # Environment variables
└── requirements.txt           # Python dependencies
```

## Dependencies

- discord.py - Discord bot framework
- python-dotenv - Environment variable management
- aiohttp - Async HTTP client for API calls
- fuzzywuzzy - Fuzzy string matching for card names 