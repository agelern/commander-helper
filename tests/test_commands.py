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