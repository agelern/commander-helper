# Commander Helper Discord Bot

A Discord bot for Magic: The Gathering Commander format assistance. Provides card information, commander recommendations, and more, using up-to-date card data and EDHREC statistics.

## Features
- Detailed card lookup with fuzzy matching
- Commander recommendations based on custom card lists
- Slash command support for Discord
- Automatic card data updates
- Robust logging and configuration

## Environment Variables
Set these in your environment or a `.env` file:
- `DISCORD_TOKEN` (required): Your Discord bot token
- `COMMAND_PREFIX` (default: `!`): Command prefix (not used for slash commands)
- `MAX_COMMAND_TIMEOUT` (default: `30`): Max command timeout in seconds
- `MAX_FILE_SIZE` (default: `26214400`): Max file size in bytes (25MB)
- `DATA_UPDATE_INTERVAL` (default: `86400`): Card data update interval in seconds (24h)
- `MAX_DOWNLOAD_RETRIES` (default: `3`): Max download retries for card data
- `MAX_COMMANDER_CACHE_SIZE` (default: `1000`): Max cache size for commander recommendations
- `MAX_SYNERGY_CALCULATION_TIME` (default: `8.0`): Max time (seconds) for synergy calculations

## Setup
1. **Clone the repository:**
   ```sh
   git clone <repo-url>
   cd commander-helper
   ```
2. **Create and activate a virtual environment:**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Set environment variables:**
   See above for required and optional variables.

## Running the Bot
```sh
python -m src.main
```

## Command Usage
- All commands are available as **slash commands** in Discord:
  - `/card <card name>`: Get detailed information about a specific card
  - `/revedh <card1, card2, ...[, "card, with, comma", ...], t:[theme]>`: Recommend commanders based on a custom card list and optional theme

## Running Tests
- **All tests:**
  ```sh
  python run_tests.py
  # or
  pytest
  ```
- **Unit tests only:**
  ```sh
  python run_tests.py --type unit
  ```
- **Integration tests only:**
  ```sh
  python run_tests.py --type integration
  ```
- **With coverage:**
  ```sh
  python run_tests.py --type coverage
  ```
- **Skip slow tests:**
  ```sh
  python run_tests.py --fast
  ```

## Coverage
- Coverage reports are generated in `htmlcov/` and as XML.
- Minimum coverage threshold: 80% (see `pytest.ini`).

## Project Structure
- `src/` - Bot source code
- `tests/` - Test suite
- `reference/` - Card data and theme files

## Contributing
Pull requests and issues are welcome!

To contribute:
- **Lint:** `make lint` or `flake8 src/ && mypy src/`
- **Format:** `make format` or `black src/`
- **Test:** `make test` or `pytest`
- **Dev setup:** `make dev-setup`

Please ensure all code passes linting and tests before submitting a PR.

## Note on Themes
- The list of supported EDHREC themes is now loaded from `reference/edhrec_themes/theme_slugs.json`.
- To add or remove supported themes, simply edit this JSON file—no code changes required.

## License
MIT 