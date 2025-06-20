# Commander Helper Bot

Disclaimer: Tests are broken as heck right now because I thought it would be neat to try vibe coding. Fixing soon.

A Discord bot for Magic: The Gathering Commander format assistance. Provides card information and commander recommendations based on custom card lists.

## Features

- **Card Information**: Get detailed information about any MTG card using `/card`
- **Commander Recommendations**: Get personalized commander suggestions based on your card list using `/revedh`
- **Smart Synergy Analysis**: Advanced algorithm that considers theme overlap, typal synergies, and popularity
- **Image Support**: Displays card images and stitched partner commander images
- **Performance Optimized**: Efficient caching and early termination to prevent timeouts

## Installation

### Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd commander-helper
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   DISCORD_TOKEN=your_discord_bot_token_here
   ```

5. **Run the bot**
   ```bash
   python src/main.py
   ```

## Usage

### Commands

#### `/card <card_name>`
Get detailed information about a specific card.

**Examples:**
- `/card Sol Ring`
- `/card Lightning Bolt`
- `/card Counterspell`

#### `/revedh <card_list>`
Recommend commanders based on a custom card list.

**Examples:**
- `/revedh Sol Ring, Lightning Bolt, Counterspell`
- `/revedh Wrath of God, Swords to Plowshares, Path to Exile`

### Features

- **Fuzzy Matching**: The bot can find cards even with slight typos
- **Theme Analysis**: Considers card themes and synergies for recommendations
- **Popularity Weighting**: Balances synergy with commander popularity
- **Color Identity**: Ensures recommended commanders can include all your cards
- **Interactive Views**: Navigate through multiple recommendations with buttons

## Configuration

The bot can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCORD_TOKEN` | Required | Your Discord bot token |
| `COMMAND_PREFIX` | `!` | Command prefix (legacy, not used) |
| `MAX_COMMAND_TIMEOUT` | `30` | Maximum command execution time in seconds |
| `MAX_FILE_SIZE` | `26214400` | Maximum file size in bytes (25MB) |
| `DATA_UPDATE_INTERVAL` | `86400` | Card data update interval in seconds |
| `MAX_DOWNLOAD_RETRIES` | `3` | Maximum download retry attempts |
| `MAX_COMMANDER_CACHE_SIZE` | `1000` | Maximum commander cache size |
| `MAX_SYNERGY_CALCULATION_TIME` | `8.0` | Maximum synergy calculation time in seconds |

## Project Structure

```
commander-helper/
├── src/
│   ├── bot/
│   │   └── discord_bot.py          # Discord bot implementation
│   ├── commands/
│   │   ├── base.py                 # Base command class
│   │   ├── card_info.py            # Card information command
│   │   ├── commander_recommendation.py  # Commander recommendation command
│   │   └── image_utils.py          # Image processing utilities
│   ├── data/
│   │   ├── card_data.py            # Card data management
│   │   └── card_data_downloader.py # Card data downloader
│   ├── utils/
│   │   ├── config.py               # Configuration management
│   │   └── logger.py               # Logging configuration
│   └── main.py                     # Application entry point
├── reference/
│   ├── oracle_cards.json           # MTG card data
│   ├── edhrec_themes/              # EDHREC theme data
│   └── rules.txt                   # MTG rules reference
├── tests/                          # Test files
├── cache/                          # Cache directory
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker configuration
└── README.md                       # This file
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/
flake8 src/
mypy src/
```

### Adding New Commands

1. Create a new command class in `src/commands/`
2. Inherit from `Command` base class
3. Implement required methods: `name`, `description`, `usage`, `execute`
4. Register the command in `src/bot/discord_bot.py`

Example:
```python
from src.commands.base import Command

class MyCommand(Command):
    @property
    def name(self) -> str:
        return "mycommand"
    
    @property
    def description(self) -> str:
        return "Description of my command"
    
    @property
    def usage(self) -> str:
        return "Usage instructions"
    
    async def execute(self, args: str):
        # Command implementation
        pass
```

## Performance Optimizations

- **Commander Cache**: Pre-computed commander data with partner combinations
- **Early Termination**: Stops processing when enough high-synergy commanders are found
- **Pre-filtering**: Quick checks before expensive synergy calculations
- **Time Limits**: Prevents Discord heartbeat timeouts
- **Memory Management**: Efficient data structures and cleanup

## Security

- Environment variable configuration
- Input validation and sanitization
- Error handling without exposing sensitive information
- File size limits and validation
- Secure Discord token handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the existing issues
2. Create a new issue with detailed information
3. Include error logs and reproduction steps

## Acknowledgments

- [Scryfall API](https://scryfall.com/docs/api) for card data
- [EDHREC](https://edhrec.com/) for theme data and popularity metrics
- Discord.py community for the excellent Discord API wrapper 