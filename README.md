# Commander Helper Discord Bot

A Discord bot for Magic: The Gathering Commander format assistance. Provides card information, commander recommendations, and more, using up-to-date card data and EDHREC statistics.

## Features
- Detailed card lookup with fuzzy matching
- Commander recommendations based on custom card lists
- Slash command support for Discord
- Automatic card data updates
- Robust logging and configuration

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
   - `DISCORD_TOKEN`: Your Discord bot token (required)
   - Optional: `COMMAND_PREFIX`, `MAX_COMMAND_TIMEOUT`, etc. (see `src/utils/config.py`)

## Running the Bot
```sh
python -m src.main
```

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

## License
MIT 