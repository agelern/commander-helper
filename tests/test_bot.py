import pytest
import discord
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio

from src.bot.discord_bot import DiscordBot


class TestDiscordBot:
    """Test suite for DiscordBot class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = Mock()
        config.discord_token = "test_token"
        config.log_level = "INFO"
        config.max_command_timeout = 10.0
        return config
    
    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        logger = Mock()
        logger.info = Mock()
        logger.error = Mock()
        logger.warning = Mock()
        return logger
    
    @pytest.fixture
    def mock_card_data(self):
        """Create a mock card data instance."""
        card_data = Mock()
        card_data.load_data = Mock()
        card_data.is_loaded = True
        return card_data
    
    @pytest.fixture
    def bot(self, mock_config, mock_logger, mock_card_data):
        """Create a DiscordBot instance for testing."""
        with patch('src.bot.discord_bot.Logger', return_value=mock_logger):
            with patch('src.bot.discord_bot.CardData', return_value=mock_card_data):
                return DiscordBot(mock_config)
    
    def test_bot_initialization(self, bot, mock_config, mock_logger, mock_card_data):
        """Test that DiscordBot initializes correctly."""
        assert bot.config == mock_config
        assert bot.logger == mock_logger
        assert bot.card_data == mock_card_data
        assert bot.commands == {}
        assert bot.command_prefix == "!"  # Dummy prefix for compatibility
    
    def test_bot_intents(self, bot):
        """Test that DiscordBot has correct intents."""
        intents = bot.intents
        assert intents.message_content is True
        assert intents.guilds is True
    
    @pytest.mark.asyncio
    async def test_setup_hook_success(self, bot):
        """Test successful setup hook execution."""
        with patch.object(bot, '_load_commands') as mock_load:
            with patch.object(bot, '_sync_commands') as mock_sync:
                await bot.setup_hook()
                
                mock_load.assert_called_once()
                mock_sync.assert_called_once()
                bot.logger.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_setup_hook_load_commands_failure(self, bot):
        """Test setup hook with command loading failure."""
        with patch.object(bot, '_load_commands', side_effect=Exception("Load error")):
            with patch.object(bot, '_sync_commands') as mock_sync:
                await bot.setup_hook()
                
                mock_sync.assert_not_called()
                bot.logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_setup_hook_sync_commands_failure(self, bot):
        """Test setup hook with command sync failure."""
        with patch.object(bot, '_load_commands'):
            with patch.object(bot, '_sync_commands', side_effect=Exception("Sync error")):
                await bot.setup_hook()
                
                bot.logger.error.assert_called()
    
    def test_load_commands_success(self, bot):
        """Test successful command loading."""
        # Mock command classes
        mock_card_command = Mock()
        mock_card_command.return_value.name = "card_info"
        mock_card_command.return_value.description = "Get card information"
        
        mock_commander_command = Mock()
        mock_commander_command.return_value.name = "recommend_commander"
        mock_commander_command.return_value.description = "Recommend commanders"
        
        with patch('src.bot.discord_bot.CardInfoCommand', mock_card_command):
            with patch('src.bot.discord_bot.CommanderRecommendationCommand', mock_commander_command):
                bot._load_commands()
                
                assert len(bot.commands) == 2
                assert "card_info" in bot.commands
                assert "recommend_commander" in bot.commands
                bot.logger.info.assert_called()
    
    def test_load_commands_failure(self, bot):
        """Test command loading with failure."""
        with patch('src.bot.discord_bot.CardInfoCommand', side_effect=Exception("Import error")):
            bot._load_commands()
            
            bot.logger.error.assert_called()
            assert len(bot.commands) == 0
    
    @pytest.mark.asyncio
    async def test_sync_commands_success(self, bot):
        """Test successful command synchronization."""
        # Mock tree
        mock_tree = Mock()
        bot.tree = mock_tree
        
        with patch.object(mock_tree, 'sync') as mock_sync:
            await bot._sync_commands()
            
            mock_sync.assert_called_once()
            bot.logger.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_sync_commands_failure(self, bot):
        """Test command synchronization with failure."""
        # Mock tree
        mock_tree = Mock()
        mock_tree.sync.side_effect = Exception("Sync error")
        bot.tree = mock_tree
        
        await bot._sync_commands()
        
        bot.logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_on_ready_success(self, bot):
        """Test successful on_ready event."""
        await bot.on_ready()
        
        bot.logger.info.assert_called()
        # Check that the log message contains the bot's name
        call_args = bot.logger.info.call_args[0][0]
        assert "logged in as" in call_args.lower()
    
    @pytest.mark.asyncio
    async def test_on_ready_with_user(self, bot):
        """Test on_ready event with user information."""
        # Mock user
        mock_user = Mock()
        mock_user.name = "TestBot"
        mock_user.id = 123456789
        bot.user = mock_user
        
        await bot.on_ready()
        
        bot.logger.info.assert_called()
        call_args = bot.logger.info.call_args[0][0]
        assert "TestBot" in call_args
        assert "123456789" in call_args
    
    @pytest.mark.asyncio
    async def test_on_interaction_success(self, bot):
        """Test successful interaction handling."""
        # Mock interaction
        mock_interaction = Mock()
        mock_interaction.type = discord.InteractionType.application_command
        mock_interaction.data = {"name": "card_info"}
        mock_interaction.response = Mock()
        mock_interaction.response.send_message = AsyncMock()
        
        # Mock command
        mock_command = Mock()
        mock_command.execute = AsyncMock(return_value=([Mock()], None, []))
        bot.commands["card_info"] = mock_command
        
        await bot.on_interaction(mock_interaction)
        
        mock_command.execute.assert_called_once_with("")
        mock_interaction.response.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_on_interaction_non_command(self, bot):
        """Test interaction handling for non-command interactions."""
        # Mock interaction
        mock_interaction = Mock()
        mock_interaction.type = discord.InteractionType.ping  # Not a command
        
        await bot.on_interaction(mock_interaction)
        
        # Should not process non-command interactions
        assert not hasattr(mock_interaction, 'response')
    
    @pytest.mark.asyncio
    async def test_on_interaction_unknown_command(self, bot):
        """Test interaction handling for unknown commands."""
        # Mock interaction
        mock_interaction = Mock()
        mock_interaction.type = discord.InteractionType.application_command
        mock_interaction.data = {"name": "unknown_command"}
        mock_interaction.response = Mock()
        mock_interaction.response.send_message = AsyncMock()
        
        await bot.on_interaction(mock_interaction)
        
        # Should send error message
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args[0][0]
        assert "Unknown command" in call_args
    
    @pytest.mark.asyncio
    async def test_on_interaction_command_error(self, bot):
        """Test interaction handling with command error."""
        # Mock interaction
        mock_interaction = Mock()
        mock_interaction.type = discord.InteractionType.application_command
        mock_interaction.data = {"name": "card_info"}
        mock_interaction.response = Mock()
        mock_interaction.response.send_message = AsyncMock()
        
        # Mock command that raises an exception
        mock_command = Mock()
        mock_command.execute = AsyncMock(side_effect=Exception("Command error"))
        bot.commands["card_info"] = mock_command
        
        await bot.on_interaction(mock_interaction)
        
        # Should send error message
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args[0][0]
        assert "error occurred" in call_args.lower()
        bot.logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_on_interaction_with_args(self, bot):
        """Test interaction handling with command arguments."""
        # Mock interaction
        mock_interaction = Mock()
        mock_interaction.type = discord.InteractionType.application_command
        mock_interaction.data = {
            "name": "card_info",
            "options": [{"name": "card_name", "value": "Sol Ring"}]
        }
        mock_interaction.response = Mock()
        mock_interaction.response.send_message = AsyncMock()
        
        # Mock command
        mock_command = Mock()
        mock_command.execute = AsyncMock(return_value=([Mock()], None, []))
        bot.commands["card_info"] = mock_command
        
        await bot.on_interaction(mock_interaction)
        
        mock_command.execute.assert_called_once_with("Sol Ring")
    
    @pytest.mark.asyncio
    async def test_on_interaction_multiple_args(self, bot):
        """Test interaction handling with multiple command arguments."""
        # Mock interaction
        mock_interaction = Mock()
        mock_interaction.type = discord.InteractionType.application_command
        mock_interaction.data = {
            "name": "recommend_commander",
            "options": [
                {"name": "cards", "value": "Sol Ring, Lightning Bolt"}
            ]
        }
        mock_interaction.response = Mock()
        mock_interaction.response.send_message = AsyncMock()
        
        # Mock command
        mock_command = Mock()
        mock_command.execute = AsyncMock(return_value=([Mock()], None, []))
        bot.commands["recommend_commander"] = mock_command
        
        await bot.on_interaction(mock_interaction)
        
        mock_command.execute.assert_called_once_with("Sol Ring, Lightning Bolt")
    
    @pytest.mark.asyncio
    async def test_on_interaction_no_options(self, bot):
        """Test interaction handling with no options."""
        # Mock interaction
        mock_interaction = Mock()
        mock_interaction.type = discord.InteractionType.application_command
        mock_interaction.data = {"name": "card_info"}
        mock_interaction.response = Mock()
        mock_interaction.response.send_message = AsyncMock()
        
        # Mock command
        mock_command = Mock()
        mock_command.execute = AsyncMock(return_value=([Mock()], None, []))
        bot.commands["card_info"] = mock_command
        
        await bot.on_interaction(mock_interaction)
        
        mock_command.execute.assert_called_once_with("")
    
    @pytest.mark.asyncio
    async def test_on_interaction_with_view(self, bot):
        """Test interaction handling with view response."""
        # Mock interaction
        mock_interaction = Mock()
        mock_interaction.type = discord.InteractionType.application_command
        mock_interaction.data = {"name": "recommend_commander"}
        mock_interaction.response = Mock()
        mock_interaction.response.send_message = AsyncMock()
        
        # Mock view
        mock_view = Mock()
        
        # Mock command that returns a view
        mock_command = Mock()
        mock_command.execute = AsyncMock(return_value=([Mock()], mock_view, []))
        bot.commands["recommend_commander"] = mock_command
        
        await bot.on_interaction(mock_interaction)
        
        # Should send message with view
        mock_interaction.response.send_message.assert_called_once()
        call_kwargs = mock_interaction.response.send_message.call_args[1]
        assert call_kwargs.get('view') == mock_view
    
    @pytest.mark.asyncio
    async def test_on_interaction_with_files(self, bot):
        """Test interaction handling with file response."""
        # Mock interaction
        mock_interaction = Mock()
        mock_interaction.type = discord.InteractionType.application_command
        mock_interaction.data = {"name": "recommend_commander"}
        mock_interaction.response = Mock()
        mock_interaction.response.send_message = AsyncMock()
        
        # Mock file
        mock_file = Mock()
        
        # Mock command that returns files
        mock_command = Mock()
        mock_command.execute = AsyncMock(return_value=([Mock()], None, [mock_file]))
        bot.commands["recommend_commander"] = mock_command
        
        await bot.on_interaction(mock_interaction)
        
        # Should send message with files
        mock_interaction.response.send_message.assert_called_once()
        call_kwargs = mock_interaction.response.send_message.call_args[1]
        assert call_kwargs.get('files') == [mock_file]
    
    @pytest.mark.asyncio
    async def test_on_interaction_multiple_embeds(self, bot):
        """Test interaction handling with multiple embeds."""
        # Mock interaction
        mock_interaction = Mock()
        mock_interaction.type = discord.InteractionType.application_command
        mock_interaction.data = {"name": "card_info"}
        mock_interaction.response = Mock()
        mock_interaction.response.send_message = AsyncMock()
        
        # Mock multiple embeds
        mock_embed1 = Mock()
        mock_embed2 = Mock()
        
        # Mock command that returns multiple embeds
        mock_command = Mock()
        mock_command.execute = AsyncMock(return_value=([mock_embed1, mock_embed2], None, []))
        bot.commands["card_info"] = mock_command
        
        await bot.on_interaction(mock_interaction)
        
        # Should send message with multiple embeds
        mock_interaction.response.send_message.assert_called_once()
        call_kwargs = mock_interaction.response.send_message.call_args[1]
        assert call_kwargs.get('embeds') == [mock_embed1, mock_embed2]
    
    @pytest.mark.asyncio
    async def test_on_error(self, bot):
        """Test error event handling."""
        # Mock error
        mock_error = Exception("Test error")
        
        # Mock context
        mock_context = Mock()
        mock_context.command = Mock()
        mock_context.command.name = "test_command"
        
        await bot.on_error(mock_context, mock_error)
        
        bot.logger.error.assert_called()
        call_args = bot.logger.error.call_args[0][0]
        assert "test_command" in call_args
        assert "Test error" in call_args
    
    @pytest.mark.asyncio
    async def test_on_command_error(self, bot):
        """Test command error event handling."""
        # Mock error
        mock_error = Exception("Command error")
        
        # Mock context
        mock_context = Mock()
        mock_context.command = Mock()
        mock_context.command.name = "test_command"
        mock_context.send = AsyncMock()
        
        await bot.on_command_error(mock_context, mock_error)
        
        mock_context.send.assert_called_once()
        call_args = mock_context.send.call_args[0][0]
        assert "error occurred" in call_args.lower()
        bot.logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_run_success(self, bot):
        """Test successful bot startup."""
        with patch.object(bot, 'start') as mock_start:
            await bot.run()
            
            mock_start.assert_called_once_with("test_token")
    
    @pytest.mark.asyncio
    async def test_run_startup_error(self, bot):
        """Test bot startup with error."""
        with patch.object(bot, 'start', side_effect=Exception("Startup error")):
            with pytest.raises(Exception, match="Startup error"):
                await bot.run()
            
            bot.logger.error.assert_called()
    
    def test_get_invite_link(self, bot):
        """Test invite link generation."""
        # Mock application info
        mock_app_info = Mock()
        mock_app_info.id = 123456789
        
        with patch.object(bot, 'application_info', return_value=mock_app_info):
            invite_link = bot.get_invite_link()
            
            assert "123456789" in invite_link
            assert "applications.commands" in invite_link
            assert "bot" in invite_link 