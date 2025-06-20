import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import discord
import asyncio
from typing import Dict, List, Any

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.card_data import CardData
from src.utils.config import Config
from src.utils.logger import Logger


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = Mock(spec=Config)
    config.discord_token = "test_token"
    config.log_level = "INFO"
    config.max_command_timeout = 10.0
    config.card_data_path = "test_data"
    config.edhrec_themes_path = "test_themes"
    return config


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = Mock(spec=Logger)
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def sample_card_data():
    """Create sample card data for testing."""
    return {
        'sol ring': {
            'name': 'Sol Ring',
            'type_line': 'Artifact',
            'oracle_text': '{T}: Add {C}{C}.',
            'color_identity': [],
            'legalities': {'commander': 'legal'},
            'mana_cost': '{1}',
            'rarity': 'common',
            'used_in': ['artifacts', 'ramp', 'good-stuff']
        },
        'lightning bolt': {
            'name': 'Lightning Bolt',
            'type_line': 'Instant',
            'oracle_text': 'Lightning Bolt deals 3 damage to any target.',
            'color_identity': ['R'],
            'legalities': {'commander': 'legal'},
            'mana_cost': '{R}',
            'rarity': 'common',
            'used_in': ['burn', 'spellslinger', 'aggro']
        },
        'atraxa, praetors voice': {
            'name': 'Atraxa, Praetors\' Voice',
            'type_line': 'Legendary Creature — Angel Horror',
            'oracle_text': 'Flying, vigilance, deathtouch, lifelink\nAt the beginning of your end step, proliferate.',
            'color_identity': ['W', 'U', 'B', 'G'],
            'legalities': {'commander': 'legal'},
            'mana_cost': '{2}{W}{U}{B}{G}',
            'rarity': 'mythic',
            'edhrec_rank': 5,
            'edhrec_data': {
                'potential_decks': 8000
            },
            'used_in': ['counters', 'proliferate', 'good-stuff']
        },
        'goblin guide': {
            'name': 'Goblin Guide',
            'type_line': 'Creature — Goblin Scout',
            'oracle_text': 'Haste\nWhenever Goblin Guide attacks, defending player reveals the top card of their library. If it\'s a land card, that player puts it into their hand.',
            'color_identity': ['R'],
            'legalities': {'commander': 'legal'},
            'mana_cost': '{R}',
            'rarity': 'rare',
            'edhrec_data': {
                'potential_decks': 100
            },
            'used_in': ['goblins', 'aggro', 'hatebears']
        },
        'not a commander': {
            'name': 'Not a Commander',
            'type_line': 'Creature — Human',
            'oracle_text': 'This is not a legendary creature.',
            'color_identity': ['W'],
            'legalities': {'commander': 'legal'},
            'mana_cost': '{W}',
            'rarity': 'common'
        },
        'illegal commander': {
            'name': 'Illegal Commander',
            'type_line': 'Legendary Creature — Dragon',
            'oracle_text': 'This is banned in commander.',
            'color_identity': ['R'],
            'legalities': {'commander': 'banned'},
            'mana_cost': '{R}',
            'rarity': 'rare'
        }
    }


@pytest.fixture
def mock_card_data(sample_card_data):
    """Create a mock CardData instance for testing."""
    mock_data = Mock(spec=CardData)
    mock_data.cards = sample_card_data
    
    def get_card(name, include_tokens=True):
        return sample_card_data.get(name.lower())
    
    mock_data.get_card = get_card
    mock_data.load_data = Mock()
    mock_data.is_loaded = True
    return mock_data


@pytest.fixture
def mock_discord_interaction():
    """Create a mock Discord interaction for testing."""
    interaction = Mock(spec=discord.Interaction)
    interaction.response = Mock()
    interaction.response.send_message = Mock()
    interaction.response.edit_message = Mock()
    interaction.followup = Mock()
    interaction.followup.send = Mock()
    interaction.data = {"custom_id": "test"}
    interaction.user = Mock()
    interaction.user.display_name = "TestUser"
    interaction.channel = Mock()
    interaction.channel.name = "test-channel"
    return interaction


@pytest.fixture
def mock_discord_context():
    """Create a mock Discord context for testing."""
    context = Mock()
    context.send = Mock()
    context.author = Mock()
    context.author.display_name = "TestUser"
    context.channel = Mock()
    context.channel.name = "test-channel"
    context.guild = Mock()
    context.guild.name = "TestGuild"
    return context


@pytest.fixture
def sample_commander_data():
    """Create sample commander data for testing."""
    return {
        'atraxa, praetors voice': {
            'name': 'Atraxa, Praetors\' Voice',
            'type_line': 'Legendary Creature — Angel Horror',
            'oracle_text': 'Flying, vigilance, deathtouch, lifelink\nAt the beginning of your end step, proliferate.',
            'color_identity': ['W', 'U', 'B', 'G'],
            'legalities': {'commander': 'legal'},
            'mana_cost': '{2}{W}{U}{B}{G}',
            'rarity': 'mythic',
            'edhrec_rank': 5,
            'edhrec_data': {
                'potential_decks': 8000
            },
            'used_in': ['counters', 'proliferate', 'good-stuff'],
            'image_uris': {
                'normal': 'https://example.com/atraxa.jpg'
            }
        },
        'jace, the mind sculptor': {
            'name': 'Jace, the Mind Sculptor',
            'type_line': 'Legendary Planeswalker — Jace',
            'oracle_text': '+2: Look at the top card of target player\'s library. You may put that card on the bottom of that player\'s library.',
            'color_identity': ['U'],
            'legalities': {'commander': 'legal'},
            'mana_cost': '{2}{U}{U}',
            'rarity': 'mythic',
            'edhrec_data': {
                'potential_decks': 5000
            },
            'used_in': ['planeswalkers', 'control', 'card-draw'],
            'image_uris': {
                'normal': 'https://example.com/jace.jpg'
            }
        }
    }


@pytest.fixture
def sample_recommendations(sample_commander_data):
    """Create sample commander recommendations for testing."""
    return [
        {
            'commander': sample_commander_data['atraxa, praetors voice'],
            'synergy_score': 85.5,
            'popularity_score': 92.3
        },
        {
            'commander': sample_commander_data['jace, the mind sculptor'],
            'synergy_score': 72.1,
            'popularity_score': 88.7
        }
    ]


@pytest.fixture
def mock_image_stitcher():
    """Create a mock ImageStitcher for testing."""
    stitcher = Mock()
    stitcher.stitch_partner_images = Mock()
    stitcher.close = Mock()
    return stitcher


# Test data for parametrized tests
@pytest.fixture
def card_name_variations():
    """Provide various card name formats for testing."""
    return [
        ("Sol Ring", "sol ring"),
        ("Lightning Bolt", "lightning bolt"),
        ("Atraxa, Praetors' Voice", "atraxa, praetors voice"),
        ("Jace, the Mind Sculptor", "jace, the mind sculptor"),
        ("Fire // Ice", "fire // ice"),
        ("Æther Vial", "æther vial"),
        ("", ""),
        ("   ", ""),
    ]


@pytest.fixture
def invalid_card_names():
    """Provide invalid card names for testing."""
    return [
        "NonExistentCard123",
        "Invalid Card Name!!!",
        "Card With Special @#$% Characters",
        "VeryLongCardNameThatDoesNotExistInAnyMagicTheGatheringSetEverPrinted",
    ]


@pytest.fixture
def color_identity_test_cases():
    """Provide test cases for color identity matching."""
    return [
        # (commander_colors, required_colors, expected_match)
        (['W', 'U', 'B', 'G'], ['W', 'U'], True),
        (['W', 'U'], ['W', 'U'], True),
        (['W', 'U'], ['R', 'G'], False),
        ([], ['W'], False),
        (['W', 'U', 'B'], [], True),
        (['R'], ['R'], True),
    ]


@pytest.fixture
def synergy_test_cases():
    """Provide test cases for synergy calculation."""
    return [
        # (commander_themes, card_themes, expected_score_range)
        (['artifacts', 'ramp'], ['artifacts'], (50, 100)),
        (['goblins', 'aggro'], ['goblins'], (50, 100)),
        (['control'], ['burn'], (0, 30)),
        ([], ['artifacts'], (0, 10)),
        (['artifacts'], [], (0, 10)),
    ] 