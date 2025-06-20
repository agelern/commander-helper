import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.main import main
from src.bot.discord_bot import DiscordBot
from src.data.card_data import CardData
from src.commands.card_info import CardInfoCommand
from src.commands.commander_recommendation import CommanderRecommendationCommand


class TestIntegration:
    """Integration tests for the entire system."""
    
    @pytest.fixture
    def sample_card_data_file(self):
        """Create a temporary card data file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            card_data = {
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
                }
            }
            json.dump(card_data, f)
            return f.name
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for integration tests."""
        config = Mock()
        config.discord_token = "test_token"
        config.log_level = "INFO"
        config.max_command_timeout = 10.0
        config.card_data_path = "data"
        config.edhrec_themes_path = "reference/edhrec_themes"
        return config
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_card_data_loading_integration(self, sample_card_data_file, mock_config):
        """Test that card data loads correctly in the full system."""
        # Update config to use our test data file
        data_dir = Path(sample_card_data_file).parent
        mock_config.card_data_path = str(data_dir)
        
        # Create card data instance
        card_data = CardData(data_path=str(data_dir))
        card_data.load_data()
        
        # Verify data was loaded
        assert card_data.is_loaded is True
        assert len(card_data.cards) == 3
        assert 'sol ring' in card_data.cards
        assert 'lightning bolt' in card_data.cards
        assert 'atraxa, praetors voice' in card_data.cards
        
        # Verify card data structure
        sol_ring = card_data.cards['sol ring']
        assert sol_ring['name'] == 'Sol Ring'
        assert sol_ring['type_line'] == 'Artifact'
        assert sol_ring['color_identity'] == []
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_card_info_command_integration(self, sample_card_data_file, mock_config):
        """Test card info command with real card data."""
        # Load card data
        data_dir = Path(sample_card_data_file).parent
        card_data = CardData(data_path=str(data_dir))
        card_data.load_data()
        
        # Create command
        command = CardInfoCommand(card_data)
        
        # Test with exact match
        embeds, view, files = await command.execute("sol ring")
        
        assert len(embeds) == 1
        embed = embeds[0]
        assert embed.title == "Sol Ring"
        assert "Artifact" in embed.description
        assert view is None
        assert files == []
        
        # Test with case insensitive match
        embeds, view, files = await command.execute("SOL RING")
        
        assert len(embeds) == 1
        embed = embeds[0]
        assert embed.title == "Sol Ring"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_commander_recommendation_integration(self, sample_card_data_file, mock_config):
        """Test commander recommendation with real card data."""
        # Load card data
        data_dir = Path(sample_card_data_file).parent
        card_data = CardData(data_path=str(data_dir))
        card_data.load_data()
        
        # Create command
        command = CommanderRecommendationCommand(card_data)
        
        # Test with artifact cards
        embeds, view, files = await command.execute("sol ring")
        
        assert len(embeds) == 1
        embed = embeds[0]
        assert "Atraxa" in embed.title  # Should recommend Atraxa for artifacts
        assert view is not None  # Should have pagination view
        assert isinstance(view, type(command).__class__.__bases__[0].__bases__[0])  # CommanderRecommendationView
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_bot_initialization_integration(self, sample_card_data_file, mock_config):
        """Test that the bot initializes correctly with real components."""
        with patch('src.bot.discord_bot.Config', return_value=mock_config):
            with patch('src.bot.discord_bot.CardData') as mock_card_data_class:
                # Mock card data loading
                mock_card_data = Mock()
                mock_card_data.load_data = Mock()
                mock_card_data.is_loaded = True
                mock_card_data_class.return_value = mock_card_data
                
                # Create bot
                bot = DiscordBot(mock_config)
                
                # Verify bot was created correctly
                assert bot.config == mock_config
                assert bot.card_data == mock_card_data
                assert len(bot.commands) == 0  # Commands loaded in setup_hook
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_command_loading_integration(self, sample_card_data_file, mock_config):
        """Test that commands are loaded correctly."""
        with patch('src.bot.discord_bot.Config', return_value=mock_config):
            with patch('src.bot.discord_bot.CardData') as mock_card_data_class:
                # Mock card data
                mock_card_data = Mock()
                mock_card_data.load_data = Mock()
                mock_card_data.is_loaded = True
                mock_card_data_class.return_value = mock_card_data
                
                # Create bot
                bot = DiscordBot(mock_config)
                
                # Load commands
                bot._load_commands()
                
                # Verify commands were loaded
                assert len(bot.commands) == 2
                assert "card_info" in bot.commands
                assert "recommend_commander" in bot.commands
                
                # Verify command instances
                card_command = bot.commands["card_info"]
                assert isinstance(card_command, CardInfoCommand)
                assert card_command.card_data == mock_card_data
                
                commander_command = bot.commands["recommend_commander"]
                assert isinstance(commander_command, CommanderRecommendationCommand)
                assert commander_command.card_data == mock_card_data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_card_lookup(self, sample_card_data_file, mock_config):
        """Test end-to-end card lookup functionality."""
        # Load card data
        data_dir = Path(sample_card_data_file).parent
        card_data = CardData(data_path=str(data_dir))
        card_data.load_data()
        
        # Create command
        command = CardInfoCommand(card_data)
        
        # Test various card lookups
        test_cases = [
            ("sol ring", "Sol Ring", "Artifact"),
            ("lightning bolt", "Lightning Bolt", "Instant"),
            ("atraxa, praetors voice", "Atraxa, Praetors' Voice", "Legendary Creature"),
        ]
        
        for input_name, expected_name, expected_type in test_cases:
            embeds, view, files = await command.execute(input_name)
            
            assert len(embeds) == 1
            embed = embeds[0]
            assert embed.title == expected_name
            assert expected_type in embed.description
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_commander_recommendation(self, sample_card_data_file, mock_config):
        """Test end-to-end commander recommendation functionality."""
        # Load card data
        data_dir = Path(sample_card_data_file).parent
        card_data = CardData(data_path=str(data_dir))
        card_data.load_data()
        
        # Create command
        command = CommanderRecommendationCommand(card_data)
        
        # Test commander recommendations
        test_cases = [
            ("sol ring", "artifacts"),  # Should recommend artifact commanders
            ("lightning bolt", "burn"),  # Should recommend burn commanders
        ]
        
        for input_cards, expected_theme in test_cases:
            embeds, view, files = await command.execute(input_cards)
            
            assert len(embeds) == 1
            embed = embeds[0]
            assert "commander" in embed.title.lower() or "atraxa" in embed.title.lower()
            assert view is not None  # Should have pagination
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, sample_card_data_file, mock_config):
        """Test error handling in the full system."""
        # Load card data
        data_dir = Path(sample_card_data_file).parent
        card_data = CardData(data_path=str(data_dir))
        card_data.load_data()
        
        # Create command
        command = CardInfoCommand(card_data)
        
        # Test with non-existent card
        embeds, view, files = await command.execute("NonExistentCard123")
        
        assert len(embeds) == 1
        embed = embeds[0]
        assert embed.title == "Error"
        assert "not found" in embed.description.lower()
        assert embed.color.value == 0xFF0000  # Red color
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_command_validation_integration(self, sample_card_data_file, mock_config):
        """Test command validation in the full system."""
        # Load card data
        data_dir = Path(sample_card_data_file).parent
        card_data = CardData(data_path=str(data_dir))
        card_data.load_data()
        
        # Create commands
        card_command = CardInfoCommand(card_data)
        commander_command = CommanderRecommendationCommand(card_data)
        
        # Test validation
        assert card_command.validate_args("") is False
        assert card_command.validate_args("   ") is False
        assert card_command.validate_args("sol ring") is True
        
        assert commander_command.validate_args("") is False
        assert commander_command.validate_args("   ") is False
        assert commander_command.validate_args("sol ring") is True
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_logging_integration(self, sample_card_data_file, mock_config):
        """Test that logging works correctly in the full system."""
        # Load card data
        data_dir = Path(sample_card_data_file).parent
        card_data = CardData(data_path=str(data_dir))
        card_data.load_data()
        
        # Create command
        command = CardInfoCommand(card_data)
        
        # Test successful execution logging
        with patch.object(command.logger, 'info') as mock_info:
            await command.execute("sol ring")
            mock_info.assert_called()
            call_args = mock_info.call_args[0][0]
            assert "SUCCESS" in call_args
            assert "sol ring" in call_args
        
        # Test failed execution logging
        with patch.object(command.logger, 'error') as mock_error:
            await command.execute("NonExistentCard")
            mock_error.assert_called()
            call_args = mock_error.call_args[0][0]
            assert "FAILED" in call_args
            assert "NonExistentCard" in call_args
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_performance_integration(self, sample_card_data_file, mock_config):
        """Test performance characteristics of the system."""
        import time
        
        # Load card data
        data_dir = Path(sample_card_data_file).parent
        card_data = CardData(data_path=str(data_dir))
        card_data.load_data()
        
        # Create command
        command = CardInfoCommand(card_data)
        
        # Test response time
        start_time = time.time()
        embeds, view, files = await command.execute("sol ring")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 1.0  # Should respond within 1 second
        
        # Test with multiple lookups
        start_time = time.time()
        for _ in range(10):
            await command.execute("sol ring")
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time = total_time / 10
        assert avg_time < 0.1  # Average response time should be under 100ms 