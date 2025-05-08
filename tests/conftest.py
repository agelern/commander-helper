import pytest
import os
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        'DISCORD_TOKEN': 'test_token',
        'OLLAMA_HOST': 'http://localhost:11434',
        'OLLAMA_MODEL': 'test-model'
    }):
        yield

@pytest.fixture(autouse=True)
def mock_discord():
    """Mock Discord.py for testing."""
    with patch('discord.ext.commands.Bot') as mock_bot:
        mock_bot.return_value = mock_bot
        yield mock_bot 