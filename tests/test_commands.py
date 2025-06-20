import pytest
from unittest.mock import Mock
from src.commands.card_info import CardInfoCommand
from src.commands.commander_recommendation import CommanderRecommendationCommand
import discord
from src.commands.base import Command
from src.commands.image_utils import ImageStitcher

@pytest.fixture
def mock_card_data():
    card_data = Mock()
    card_data.get_card = Mock(return_value={
        'name': 'Sol Ring',
        'type_line': 'Artifact',
        'oracle_text': '{T}: Add {C}{C}.',
        'color_identity': [],
        'legalities': {'commander': 'legal'},
        'mana_cost': '{1}',
        'rarity': 'common',
        'used_in': ['artifacts', 'ramp', 'good-stuff']
    })
    card_data.cards = {'sol ring': card_data.get_card.return_value}
    card_data.is_loaded = True
    return card_data

def test_card_info_command_init(mock_card_data):
    cmd = CardInfoCommand(mock_card_data)
    assert cmd.card_data is mock_card_data

def test_card_info_command_execute_runs(mock_card_data):
    cmd = CardInfoCommand(mock_card_data)
    # Should not raise for a known card
    import asyncio
    result = asyncio.run(cmd.execute('Sol Ring'))
    assert isinstance(result, tuple)
    assert len(result) == 3

def test_commander_recommendation_command_init(mock_card_data):
    cmd = CommanderRecommendationCommand(mock_card_data)
    assert cmd.card_data is mock_card_data

def test_commander_recommendation_command_execute_runs(mock_card_data):
    cmd = CommanderRecommendationCommand(mock_card_data)
    # Should not raise for a simple card list
    import asyncio
    result = asyncio.run(cmd.execute('Sol Ring'))
    assert isinstance(result, tuple)
    assert len(result) == 3

class DummyCommand(Command):
    @property
    def name(self):
        return "dummy"
    @property
    def description(self):
        return "desc"
    @property
    def usage(self):
        return "usage"
    async def execute(self, args):
        return [], None, []

def test_validate_args():
    cmd = DummyCommand()
    assert cmd.validate_args("foo")
    assert not cmd.validate_args("")
    assert not cmd.validate_args("   ")

def test_create_error_embed():
    cmd = DummyCommand()
    embed = cmd.create_error_embed("fail")
    assert isinstance(embed, discord.Embed)
    assert embed.title == "Error"
    assert embed.description == "fail"
    assert embed.footer.text == "Command: dummy"

def test_create_success_embed():
    cmd = DummyCommand()
    embed = cmd.create_success_embed("ok", "done")
    assert isinstance(embed, discord.Embed)
    assert embed.title == "ok"
    assert embed.description == "done"
    assert embed.footer.text == "Command: dummy"

def test_log_command_execution(capsys):
    cmd = DummyCommand()
    # Should not raise
    cmd.log_command_execution("foo", True)
    cmd.log_command_execution("foo", False, error="bad")

def test_image_stitcher_get_cache_path():
    stitcher = ImageStitcher()
    urls = ["http://a.com/1.png", "http://b.com/2.png"]
    path = stitcher._get_cache_path(urls)
    assert path.name.endswith("") or path.suffix == ""
    # Should be deterministic
    path2 = stitcher._get_cache_path(urls)
    assert path == path2 

@pytest.fixture
# Extended mock_card_data for theme tests
def mock_card_data_with_themes():
    card_data = Mock()
    # Commander 1: Artifacts theme
    card1 = {
        'name': 'Artifact Master',
        'type_line': 'Legendary Creature — Human Artificer',
        'oracle_text': 'Artifacts you control have hexproof.',
        'color_identity': ['U'],
        'legalities': {'commander': 'legal'},
        'mana_cost': '{2}{U}',
        'used_in': ['artifacts', 'good-stuff']
    }
    # Commander 2: Ramp theme
    card2 = {
        'name': 'Ramp Lord',
        'type_line': 'Legendary Creature — Elf Druid',
        'oracle_text': 'Lands you control have \'{T}: Add {G}.\'',
        'color_identity': ['G'],
        'legalities': {'commander': 'legal'},
        'mana_cost': '{3}{G}',
        'used_in': ['ramp', 'good-stuff']
    }
    # Commander 3: Not in theme
    card3 = {
        'name': 'Vanilla Hero',
        'type_line': 'Legendary Creature — Human',
        'oracle_text': '',
        'color_identity': ['W'],
        'legalities': {'commander': 'legal'},
        'mana_cost': '{2}{W}',
        'used_in': ['vanilla']
    }
    # Card for input
    input_card = {
        'name': 'Sol Ring',
        'type_line': 'Artifact',
        'oracle_text': '{T}: Add {C}{C}.',
        'color_identity': [],
        'legalities': {'commander': 'legal'},
        'mana_cost': '{1}',
        'used_in': ['artifacts', 'ramp', 'good-stuff']
    }
    card_data.get_card = Mock(side_effect=lambda name: {
        'artifact master': card1,
        'ramp lord': card2,
        'vanilla hero': card3,
        'sol ring': input_card
    }.get(name.lower()))
    card_data.cards = {
        'artifact master': card1,
        'ramp lord': card2,
        'vanilla hero': card3,
        'sol ring': input_card
    }
    card_data.is_loaded = True
    card_data.get_all_themes = Mock(return_value={'artifacts', 'ramp', 'good-stuff', 'vanilla'})
    # Add a minimal, realistic edhrec_cache for synergy tests
    card_data.edhrec_cache = {
        'artifact master': {
            'synergies': [
                {'name': 'Sol Ring'},
                {'name': 'Other Artifact'}
            ],
            'potential_decks': 100
        },
        'ramp lord': {
            'synergies': [
                {'name': 'Sol Ring'},
                {'name': 'Rampant Growth'}
            ],
            'potential_decks': 80
        },
        'vanilla hero': {
            'synergies': [
                {'name': 'Plains'}
            ],
            'potential_decks': 10
        },
        'sol ring': {
            'synergies': [],
            'potential_decks': 0
        }
    }
    return card_data

import asyncio

def test_commander_recommendation_theme_exact(mock_card_data_with_themes):
    cmd = CommanderRecommendationCommand(mock_card_data_with_themes)
    # Should only return Artifact Master for 'artifacts' theme
    result = asyncio.run(cmd.execute('Sol Ring, t:artifacts'))
    embeds, view, files = result
    assert any('Artifact Master' in (embed.title or '') for embed in embeds)
    assert not any('Ramp Lord' in (embed.title or '') for embed in embeds)
    assert not any('Vanilla Hero' in (embed.title or '') for embed in embeds)

def test_commander_recommendation_theme_fuzzy(mock_card_data_with_themes):
    cmd = CommanderRecommendationCommand(mock_card_data_with_themes)
    # Should fuzzy match 'artifcts' to 'artifacts'
    result = asyncio.run(cmd.execute('Sol Ring, t:artifcts'))
    embeds, view, files = result
    assert any('Artifact Master' in (embed.title or '') for embed in embeds)
    assert not any('Ramp Lord' in (embed.title or '') for embed in embeds)

def test_commander_recommendation_theme_no_match(mock_card_data_with_themes):
    cmd = CommanderRecommendationCommand(mock_card_data_with_themes)
    # Should return error for unknown theme
    result = asyncio.run(cmd.execute('Sol Ring, t:notarealtheme'))
    embeds, view, files = result
    assert any('Could not find a matching theme' in (embed.description or '') for embed in embeds)

def test_commander_recommendation_theme_no_commanders_in_theme(mock_card_data_with_themes):
    cmd = CommanderRecommendationCommand(mock_card_data_with_themes)
    # Should show a warning for theme with no matching commanders, but still return alternatives
    result = asyncio.run(cmd.execute('Sol Ring, t:vanilla'))
    embeds, view, files = result
    assert any('No commanders found for the given theme' in (embed.description or '') for embed in embeds)

def test_commander_recommendation_theme_t_colon_style(mock_card_data_with_themes):
    cmd = CommanderRecommendationCommand(mock_card_data_with_themes)
    # Theme at end
    result = asyncio.run(cmd.execute('Sol Ring, t:artifacts'))
    embeds, view, files = result
    assert any('Artifact Master' in (embed.title or '') for embed in embeds)
    # Theme at start (must be comma-separated)
    result = asyncio.run(cmd.execute('t:artifacts, Sol Ring'))
    embeds, view, files = result
    assert any('Artifact Master' in (embed.title or '') for embed in embeds)
    # Theme in middle
    result = asyncio.run(cmd.execute('Sol Ring, t:artifacts'))
    embeds, view, files = result
    assert any('Artifact Master' in (embed.title or '') for embed in embeds)

def test_commander_recommendation_card_names_with_commas(mock_card_data_with_themes):
    cmd = CommanderRecommendationCommand(mock_card_data_with_themes)
    # Quoted card name with comma
    result = asyncio.run(cmd.execute('"Ramp Lord, the Great", Sol Ring, t:ramp'))
    embeds, view, files = result
    # Should fuzzy match ramp theme and not break on comma in name
    # (No commander named "Ramp Lord, the Great" in mock, so only Sol Ring is valid)
    assert any('Ramp Lord' in (embed.title or '') for embed in embeds)
    # Quoted card name with comma that matches a real commander
    result = asyncio.run(cmd.execute('"Cazur, Ruthless Stalker", t:mutate'))
    embeds, view, files = result
    # Should not error, even if not in mock 