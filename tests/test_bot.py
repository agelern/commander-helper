import pytest
from unittest.mock import Mock, patch
from src.bot.discord_bot import CommanderBot
from src.commands.card_info import CardInfoCommand
from src.commands.commander_recommendation import CommanderRecommendationCommand

@pytest.fixture
def mock_config():
    config = Mock()
    config.discord_token = "test_token"
    config.log_level = "INFO"
    config.max_command_timeout = 10.0
    return config

@pytest.fixture
def mock_card_data():
    card_data = Mock()
    card_data.load_data = Mock()
    card_data.is_loaded = True
    return card_data

@pytest.fixture
def bot(mock_config, mock_card_data):
    with patch('src.bot.discord_bot.CardData', return_value=mock_card_data):
        return CommanderBot(mock_config)

def test_bot_instantiation_sets_config_and_card_data(bot, mock_config, mock_card_data):
    assert bot.config == mock_config
    assert bot.card_data == mock_card_data

def test_bot_instantiation_sets_command_objects(bot):
    assert isinstance(bot.card_info, CardInfoCommand)
    assert isinstance(bot.commander_recommendation, CommanderRecommendationCommand)
    # Both should use the same card_data instance
    assert bot.card_info.card_data is bot.card_data
    assert bot.commander_recommendation.card_data is bot.card_data

def test_bot_intents_are_set(bot):
    intents = bot.intents
    assert intents.message_content is True
    # Should have default intents otherwise
    assert hasattr(intents, 'guilds')
    assert hasattr(intents, 'members')

def test_bot_command_prefix(bot):
    # Should be the dummy prefix
    assert bot.command_prefix == "!" 