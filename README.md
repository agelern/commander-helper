# MTG Commander Deck Brewer Bot

A Discord bot that helps users brew Magic: The Gathering Commander decks by providing suggestions, synergies, and meta analysis.

## Features

- Deck brewing suggestions for specific commanders
- Card synergy analysis
- Budget deck recommendations
- Meta analysis for commanders

## Setup

1. Clone this repository
2. Create a `.env` file in the root directory with your configuration:
   ```
   # Discord Bot Token
   DISCORD_TOKEN=your_discord_bot_token_here
   
   # Ollama Configuration
   OLLAMA_HOST=http://your_ollama_host:11434
   OLLAMA_MODEL=gemma3
   ```
   
   Note: If you're running Ollama locally, the default host is `http://localhost:11434`. If you're running it on a remote server, use the appropriate IP address or hostname.

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

## Security Notes

- Never commit your `.env` file to version control
- Keep your Ollama instance behind a firewall or VPN when exposing it to the internet
- Consider using HTTPS if exposing Ollama over the internet
- Use environment variables for all sensitive configuration 