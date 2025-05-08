# MTG Commander Deck Brewer Bot

A Discord bot that helps users brew Magic: The Gathering Commander decks by providing suggestions, synergies, and meta analysis.

## Features

- Deck brewing suggestions for specific commanders
- Card synergy analysis
- Budget deck recommendations
- Meta analysis for commanders

## Setup

1. Clone this repository
2. Create a `.env` file in the root directory with your Discord bot token:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   ```
3. Build and run the Docker container:
   ```bash
   docker build -t commander-brewer .
   docker run commander-brewer
   ```

## Commands

- `!help_brew` - Display help information
- `!brew <commander>` - Get deck brewing suggestions
- `!synergy <card>` - Find synergistic cards
- `!budget <commander> <budget>` - Get budget deck suggestions
- `!meta <commander>` - Get meta analysis

## Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the bot locally:
   ```bash
   python src/bot.py
   ```

## Contributing

Feel free to submit issues and enhancement requests! 