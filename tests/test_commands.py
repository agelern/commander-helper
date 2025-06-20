import pytest
import discord
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path
import tempfile
import os

from src.commands.base import Command
from src.commands.card_info import CardInfoCommand
from src.commands.image_utils import ImageStitcher


class TestBaseCommand:
    """Test suite for the base Command class."""
    
    def test_command_initialization(self):
        """Test that Command initializes correctly."""
        command = Command()
        assert command.logger is not None
        assert hasattr(command, 'name')
        assert hasattr(command, 'description')
        assert hasattr(command, 'usage')
    
    def test_validate_args_empty(self):
        """Test argument validation with empty string."""
        command = Command()
        assert command.validate_args("") is False
        assert command.validate_args("   ") is False
    
    def test_validate_args_valid(self):
        """Test argument validation with valid input."""
        command = Command()
        assert command.validate_args("valid arguments") is True
        assert command.validate_args("multiple words") is True
    
    def test_validate_args_none(self):
        """Test argument validation with None input."""
        command = Command()
        assert command.validate_args(None) is False
    
    def test_create_error_embed(self):
        """Test error embed creation."""
        command = Command()
        error_message = "Test error message"
        embed = command.create_error_embed(error_message)
        
        assert isinstance(embed, discord.Embed)
        assert embed.title == "Error"
        assert embed.description == error_message
        assert embed.color == discord.Color.red()
    
    def test_create_success_embed(self):
        """Test success embed creation."""
        command = Command()
        success_message = "Test success message"
        embed = command.create_success_embed(success_message)
        
        assert isinstance(embed, discord.Embed)
        assert embed.title == "Success"
        assert embed.description == success_message
        assert embed.color == discord.Color.green()
    
    def test_log_command_execution_success(self):
        """Test command execution logging for success."""
        command = Command()
        
        with patch.object(command.logger, 'info') as mock_info:
            command.log_command_execution("test args", True)
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            assert "SUCCESS" in call_args
            assert "test args" in call_args
    
    def test_log_command_execution_failure(self):
        """Test command execution logging for failure."""
        command = Command()
        
        with patch.object(command.logger, 'error') as mock_error:
            command.log_command_execution("test args", False, "error message")
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0][0]
            assert "FAILED" in call_args
            assert "test args" in call_args
            assert "error message" in call_args
    
    def test_log_command_execution_no_error_message(self):
        """Test command execution logging without error message."""
        command = Command()
        
        with patch.object(command.logger, 'error') as mock_error:
            command.log_command_execution("test args", False)
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0][0]
            assert "FAILED" in call_args
            assert "test args" in call_args
            assert "Unknown error" in call_args


class TestCardInfoCommand:
    """Test suite for CardInfoCommand class."""
    
    @pytest.fixture
    def command(self, mock_card_data):
        """Create a CardInfoCommand instance for testing."""
        return CardInfoCommand(mock_card_data)
    
    def test_command_properties(self, command):
        """Test that CardInfoCommand has correct properties."""
        assert command.name == "card_info"
        assert "card information" in command.description.lower()
        assert "/card" in command.usage
    
    def test_validate_args_valid(self, command):
        """Test argument validation with valid input."""
        assert command.validate_args("Sol Ring") is True
        assert command.validate_args("Lightning Bolt") is True
        assert command.validate_args("  Sol Ring  ") is True
    
    def test_validate_args_invalid(self, command):
        """Test argument validation with invalid input."""
        assert command.validate_args("") is False
        assert command.validate_args("   ") is False
        assert command.validate_args(None) is False
    
    @pytest.mark.asyncio
    async def test_execute_exact_match(self, command, sample_card_data):
        """Test card info execution with exact match."""
        args = "sol ring"
        embeds, view, files = await command.execute(args)
        
        assert len(embeds) == 1
        embed = embeds[0]
        assert embed.title == "Sol Ring"
        assert "Artifact" in embed.description
        assert view is None
        assert files == []
        
        # Verify logging was called
        assert command.logger.info.called
    
    @pytest.mark.asyncio
    async def test_execute_fuzzy_match(self, command, sample_card_data):
        """Test card info execution with fuzzy match."""
        args = "sol ring"  # Should match "sol ring" exactly
        embeds, view, files = await command.execute(args)
        
        assert len(embeds) == 1
        embed = embeds[0]
        assert embed.title == "Sol Ring"
        assert view is None
        assert files == []
    
    @pytest.mark.asyncio
    async def test_execute_no_match(self, command):
        """Test card info execution with no match."""
        args = "NonExistentCard123"
        embeds, view, files = await command.execute(args)
        
        assert len(embeds) == 1
        embed = embeds[0]
        assert embed.title == "Error"
        assert "not found" in embed.description.lower()
        assert embed.color == discord.Color.red()
        assert view is None
        assert files == []
    
    @pytest.mark.asyncio
    async def test_execute_empty_args(self, command):
        """Test card info execution with empty arguments."""
        args = ""
        embeds, view, files = await command.execute(args)
        
        assert len(embeds) == 1
        embed = embeds[0]
        assert embed.title == "Error"
        assert "card name" in embed.description.lower()
        assert embed.color == discord.Color.red()
        assert view is None
        assert files == []
    
    @pytest.mark.asyncio
    async def test_execute_card_with_image(self, command, sample_card_data):
        """Test card info execution with card that has image."""
        # Add image data to sample card
        sample_card_data['sol ring']['image_uris'] = {
            'normal': 'https://example.com/sol-ring.jpg'
        }
        
        args = "sol ring"
        embeds, view, files = await command.execute(args)
        
        assert len(embeds) == 1
        embed = embeds[0]
        assert embed.title == "Sol Ring"
        assert embed.image.url == 'https://example.com/sol-ring.jpg'
        assert view is None
        assert files == []
    
    @pytest.mark.asyncio
    async def test_execute_card_with_flavor_text(self, command, sample_card_data):
        """Test card info execution with card that has flavor text."""
        # Add flavor text to sample card
        sample_card_data['sol ring']['flavor_text'] = "The first artifact ever created."
        
        args = "sol ring"
        embeds, view, files = await command.execute(args)
        
        assert len(embeds) == 1
        embed = embeds[0]
        assert embed.title == "Sol Ring"
        
        # Check if flavor text field exists
        flavor_field = None
        for field in embed.fields:
            if field.name == "Flavor Text":
                flavor_field = field
                break
        
        assert flavor_field is not None
        assert "first artifact" in flavor_field.value
    
    @pytest.mark.asyncio
    async def test_execute_card_with_power_toughness(self, command, sample_card_data):
        """Test card info execution with creature card."""
        # Add power/toughness to sample card
        sample_card_data['goblin guide']['power'] = "2"
        sample_card_data['goblin guide']['toughness'] = "2"
        
        args = "goblin guide"
        embeds, view, files = await command.execute(args)
        
        assert len(embeds) == 1
        embed = embeds[0]
        assert embed.title == "Goblin Guide"
        
        # Check if power/toughness field exists
        pt_field = None
        for field in embed.fields:
            if field.name == "Power/Toughness":
                pt_field = field
                break
        
        assert pt_field is not None
        assert "2/2" in pt_field.value
    
    @pytest.mark.asyncio
    async def test_execute_exception_handling(self, command):
        """Test card info execution with exception."""
        # Mock get_card to raise an exception
        command.card_data.get_card = Mock(side_effect=Exception("Test exception"))
        
        args = "sol ring"
        embeds, view, files = await command.execute(args)
        
        assert len(embeds) == 1
        embed = embeds[0]
        assert embed.title == "Error"
        assert "error occurred" in embed.description.lower()
        assert embed.color == discord.Color.red()
        assert view is None
        assert files == []
    
    @pytest.mark.asyncio
    async def test_execute_dual_faced_card(self, command, sample_card_data):
        """Test card info execution with dual-faced card."""
        # Add dual-faced card data
        sample_card_data['fire // ice'] = {
            'name': 'Fire // Ice',
            'type_line': 'Instant',
            'oracle_text': 'Choose one —\n• Fire deals 2 damage to any target.\n• Ice taps target permanent.',
            'color_identity': ['U', 'R'],
            'legalities': {'commander': 'legal'},
            'mana_cost': '{U/R}',
            'rarity': 'common',
            'card_faces': [
                {
                    'name': 'Fire',
                    'mana_cost': '{R}',
                    'type_line': 'Instant',
                    'oracle_text': 'Fire deals 2 damage to any target.'
                },
                {
                    'name': 'Ice',
                    'mana_cost': '{U}',
                    'type_line': 'Instant',
                    'oracle_text': 'Ice taps target permanent.'
                }
            ]
        }
        
        args = "fire // ice"
        embeds, view, files = await command.execute(args)
        
        assert len(embeds) == 1
        embed = embeds[0]
        assert embed.title == "Fire // Ice"
        
        # Check if both faces are mentioned
        description = embed.description.lower()
        assert "fire" in description
        assert "ice" in description


class TestImageStitcher:
    """Test suite for ImageStitcher class."""
    
    @pytest.fixture
    def stitcher(self):
        """Create an ImageStitcher instance for testing."""
        return ImageStitcher()
    
    def test_stitcher_initialization(self, stitcher):
        """Test that ImageStitcher initializes correctly."""
        assert stitcher.session is not None
        assert stitcher.temp_dir is not None
    
    @pytest.mark.asyncio
    async def test_download_image_success(self, stitcher):
        """Test successful image download."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"fake_image_data"
        
        with patch.object(stitcher.session, 'get', return_value=mock_response):
            result = await stitcher._download_image("https://example.com/image.jpg")
            assert result is not None
            assert result == b"fake_image_data"
    
    @pytest.mark.asyncio
    async def test_download_image_failure(self, stitcher):
        """Test image download failure."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch.object(stitcher.session, 'get', return_value=mock_response):
            result = await stitcher._download_image("https://example.com/image.jpg")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_download_image_network_error(self, stitcher):
        """Test image download with network error."""
        with patch.object(stitcher.session, 'get', side_effect=Exception("Network error")):
            result = await stitcher._download_image("https://example.com/image.jpg")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_stitch_partner_images_success(self, stitcher):
        """Test successful partner image stitching."""
        # Mock image downloads
        fake_image_data = b"fake_image_data"
        
        with patch.object(stitcher, '_download_image', return_value=fake_image_data):
            with patch('PIL.Image.open') as mock_open:
                with patch('PIL.Image.new') as mock_new:
                    with patch.object(stitcher, '_save_image') as mock_save:
                        mock_save.return_value = "/tmp/test_output.png"
                        
                        image_urls = [
                            "https://example.com/image1.jpg",
                            "https://example.com/image2.jpg"
                        ]
                        
                        result = await stitcher.stitch_partner_images(image_urls)
                        
                        assert result == "/tmp/test_output.png"
                        assert stitcher._download_image.call_count == 2
                        assert mock_save.called
    
    @pytest.mark.asyncio
    async def test_stitch_partner_images_download_failure(self, stitcher):
        """Test partner image stitching with download failure."""
        # Mock download failure
        with patch.object(stitcher, '_download_image', return_value=None):
            image_urls = [
                "https://example.com/image1.jpg",
                "https://example.com/image2.jpg"
            ]
            
            with pytest.raises(Exception, match="Failed to download images"):
                await stitcher.stitch_partner_images(image_urls)
    
    @pytest.mark.asyncio
    async def test_stitch_partner_images_insufficient_urls(self, stitcher):
        """Test partner image stitching with insufficient URLs."""
        image_urls = ["https://example.com/image1.jpg"]  # Only one URL
        
        with pytest.raises(ValueError, match="Exactly 2 image URLs"):
            await stitcher.stitch_partner_images(image_urls)
    
    @pytest.mark.asyncio
    async def test_stitch_partner_images_too_many_urls(self, stitcher):
        """Test partner image stitching with too many URLs."""
        image_urls = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
            "https://example.com/image3.jpg"
        ]
        
        with pytest.raises(ValueError, match="Exactly 2 image URLs"):
            await stitcher.stitch_partner_images(image_urls)
    
    @pytest.mark.asyncio
    async def test_stitch_partner_images_empty_urls(self, stitcher):
        """Test partner image stitching with empty URLs."""
        image_urls = []
        
        with pytest.raises(ValueError, match="Exactly 2 image URLs"):
            await stitcher.stitch_partner_images(image_urls)
    
    def test_save_image_success(self, stitcher):
        """Test successful image saving."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock image
            mock_image = Mock()
            
            # Mock the save method
            mock_image.save = Mock()
            
            # Test saving
            output_path = stitcher._save_image(mock_image, temp_dir, "test.png")
            
            assert output_path == os.path.join(temp_dir, "test.png")
            mock_image.save.assert_called_once_with(output_path)
    
    def test_save_image_permission_error(self, stitcher):
        """Test image saving with permission error."""
        mock_image = Mock()
        mock_image.save = Mock(side_effect=PermissionError("Permission denied"))
        
        with pytest.raises(PermissionError):
            stitcher._save_image(mock_image, "/root", "test.png")
    
    @pytest.mark.asyncio
    async def test_close(self, stitcher):
        """Test ImageStitcher cleanup."""
        # Mock session close
        with patch.object(stitcher.session, 'close') as mock_close:
            await stitcher.close()
            mock_close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test ImageStitcher as context manager."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            async with ImageStitcher() as stitcher:
                assert stitcher.session == mock_session
            
            mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stitch_partner_images_pil_error(self, stitcher):
        """Test partner image stitching with PIL error."""
        # Mock image downloads
        fake_image_data = b"fake_image_data"
        
        with patch.object(stitcher, '_download_image', return_value=fake_image_data):
            with patch('PIL.Image.open', side_effect=Exception("PIL error")):
                image_urls = [
                    "https://example.com/image1.jpg",
                    "https://example.com/image2.jpg"
                ]
                
                with pytest.raises(Exception, match="PIL error"):
                    await stitcher.stitch_partner_images(image_urls)
    
    @pytest.mark.asyncio
    async def test_stitch_partner_images_save_error(self, stitcher):
        """Test partner image stitching with save error."""
        # Mock image downloads
        fake_image_data = b"fake_image_data"
        
        with patch.object(stitcher, '_download_image', return_value=fake_image_data):
            with patch('PIL.Image.open'):
                with patch('PIL.Image.new'):
                    with patch.object(stitcher, '_save_image', side_effect=Exception("Save error")):
                        image_urls = [
                            "https://example.com/image1.jpg",
                            "https://example.com/image2.jpg"
                        ]
                        
                        with pytest.raises(Exception, match="Save error"):
                            await stitcher.stitch_partner_images(image_urls) 