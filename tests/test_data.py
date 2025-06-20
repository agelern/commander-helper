import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
import requests
from io import BytesIO

from src.data.card_data import CardData
from src.data.card_data_downloader import CardDataDownloader


class TestCardData:
    """Test suite for CardData class."""
    
    def test_card_data_initialization(self):
        """Test that CardData initializes correctly."""
        card_data = CardData()
        assert card_data.cards == {}
        assert card_data.is_loaded is False
        assert card_data.data_path == "data"
    
    def test_card_data_custom_path(self):
        """Test that CardData initializes with custom data path."""
        card_data = CardData(data_path="/custom/path")
        assert card_data.data_path == "/custom/path"
    
    def test_load_data_success(self, sample_card_data):
        """Test that CardData loads data successfully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / "cards.json"
            
            # Create test data file
            with open(data_file, 'w') as f:
                json.dump(sample_card_data, f)
            
            card_data = CardData(data_path=str(temp_dir))
            card_data.load_data()
            
            assert card_data.is_loaded is True
            assert len(card_data.cards) == len(sample_card_data)
            for card_name, card_info in sample_card_data.items():
                assert card_name in card_data.cards
                assert card_data.cards[card_name]['name'] == card_info['name']
    
    def test_load_data_file_not_found(self):
        """Test that CardData handles missing data file gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            card_data = CardData(data_path=str(temp_dir))
            
            # Should not raise an exception
            card_data.load_data()
            
            assert card_data.is_loaded is False
            assert card_data.cards == {}
    
    def test_load_data_invalid_json(self):
        """Test that CardData handles invalid JSON gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / "cards.json"
            
            # Create invalid JSON file
            with open(data_file, 'w') as f:
                f.write("invalid json content")
            
            card_data = CardData(data_path=str(temp_dir))
            
            # Should not raise an exception
            card_data.load_data()
            
            assert card_data.is_loaded is False
            assert card_data.cards == {}
    
    def test_load_data_empty_file(self):
        """Test that CardData handles empty file gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / "cards.json"
            
            # Create empty file
            data_file.touch()
            
            card_data = CardData(data_path=str(temp_dir))
            card_data.load_data()
            
            assert card_data.is_loaded is False
            assert card_data.cards == {}
    
    def test_get_card_exact_match(self, sample_card_data):
        """Test that get_card finds exact matches."""
        card_data = CardData()
        card_data.cards = sample_card_data
        card_data.is_loaded = True
        
        card = card_data.get_card("sol ring")
        assert card is not None
        assert card['name'] == "Sol Ring"
    
    def test_get_card_case_insensitive(self, sample_card_data):
        """Test that get_card is case insensitive."""
        card_data = CardData()
        card_data.cards = sample_card_data
        card_data.is_loaded = True
        
        card = card_data.get_card("SOL RING")
        assert card is not None
        assert card['name'] == "Sol Ring"
    
    def test_get_card_not_found(self, sample_card_data):
        """Test that get_card returns None for non-existent cards."""
        card_data = CardData()
        card_data.cards = sample_card_data
        card_data.is_loaded = True
        
        card = card_data.get_card("non-existent card")
        assert card is None
    
    def test_get_card_empty_string(self, sample_card_data):
        """Test that get_card handles empty string input."""
        card_data = CardData()
        card_data.cards = sample_card_data
        card_data.is_loaded = True
        
        card = card_data.get_card("")
        assert card is None
    
    def test_get_card_none_input(self, sample_card_data):
        """Test that get_card handles None input."""
        card_data = CardData()
        card_data.cards = sample_card_data
        card_data.is_loaded = True
        
        card = card_data.get_card(None)
        assert card is None
    
    def test_get_card_with_tokens_false(self, sample_card_data):
        """Test that get_card respects include_tokens parameter."""
        card_data = CardData()
        card_data.cards = sample_card_data
        card_data.is_loaded = True
        
        # Add a token to the data
        card_data.cards['test token'] = {
            'name': 'Test Token',
            'type_line': 'Token Creature — Goblin',
            'oracle_text': 'This is a token.',
            'color_identity': ['R'],
            'legalities': {'commander': 'legal'},
            'mana_cost': '',
            'rarity': 'common'
        }
        
        # Should not find token when include_tokens=False
        card = card_data.get_card("test token", include_tokens=False)
        assert card is None
        
        # Should find token when include_tokens=True (default)
        card = card_data.get_card("test token", include_tokens=True)
        assert card is not None
        assert card['name'] == "Test Token"
    
    def test_get_card_special_characters(self, sample_card_data):
        """Test that get_card handles special characters in card names."""
        card_data = CardData()
        card_data.cards = sample_card_data
        card_data.is_loaded = True
        
        # Add a card with special characters
        special_card = {
            'name': 'Fire // Ice',
            'type_line': 'Instant',
            'oracle_text': 'Choose one —\n• Fire deals 2 damage to any target.\n• Ice taps target permanent.',
            'color_identity': ['U', 'R'],
            'legalities': {'commander': 'legal'},
            'mana_cost': '{U/R}',
            'rarity': 'common'
        }
        card_data.cards['fire // ice'] = special_card
        
        card = card_data.get_card("Fire // Ice")
        assert card is not None
        assert card['name'] == "Fire // Ice"
    
    def test_get_card_whitespace_handling(self, sample_card_data):
        """Test that get_card handles whitespace correctly."""
        card_data = CardData()
        card_data.cards = sample_card_data
        card_data.is_loaded = True
        
        # Test with extra whitespace
        card = card_data.get_card("  sol ring  ")
        assert card is not None
        assert card['name'] == "Sol Ring"
    
    def test_load_data_permission_error(self):
        """Test that CardData handles permission errors gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / "cards.json"
            
            # Create a file that can't be read
            data_file.touch()
            os.chmod(data_file, 0o000)  # No permissions
            
            card_data = CardData(data_path=str(temp_dir))
            
            # Should not raise an exception
            card_data.load_data()
            
            assert card_data.is_loaded is False
            assert card_data.cards == {}
            
            # Restore permissions for cleanup
            os.chmod(data_file, 0o644)


class TestCardDataDownloader:
    """Test suite for CardDataDownloader class."""
    
    def test_downloader_initialization(self):
        """Test that CardDataDownloader initializes correctly."""
        downloader = CardDataDownloader()
        assert downloader.base_url == "https://api.scryfall.com"
        assert downloader.edhrec_base_url == "https://www.edhrec.com"
    
    def test_format_name_for_edhrec_simple(self):
        """Test basic name formatting for EDHREC."""
        downloader = CardDataDownloader()
        
        test_cases = [
            ("Sol Ring", "sol-ring"),
            ("Lightning Bolt", "lightning-bolt"),
            ("Atraxa, Praetors' Voice", "atraxa-praetors-voice"),
            ("Jace, the Mind Sculptor", "jace-the-mind-sculptor"),
        ]
        
        for input_name, expected in test_cases:
            result = downloader._format_name_for_edhrec(input_name)
            assert result == expected
    
    def test_format_name_for_edhrec_special_characters(self):
        """Test name formatting with special characters."""
        downloader = CardDataDownloader()
        
        test_cases = [
            ("Fire // Ice", "fire-ice"),
            ("Æther Vial", "aether-vial"),
            ("Jötun Grunt", "jotun-grunt"),
            ("Façade", "facade"),
            ("Señor of the Wilds", "senor-of-the-wilds"),
        ]
        
        for input_name, expected in test_cases:
            result = downloader._format_name_for_edhrec(input_name)
            assert result == expected
    
    def test_format_name_for_edhrec_edge_cases(self):
        """Test name formatting with edge cases."""
        downloader = CardDataDownloader()
        
        test_cases = [
            ("", ""),
            ("   ", ""),
            ("A", "a"),
            ("  Sol Ring  ", "sol-ring"),
            ("Sol\tRing\n", "sol-ring"),
        ]
        
        for input_name, expected in test_cases:
            result = downloader._format_name_for_edhrec(input_name)
            assert result == expected
    
    def test_format_name_for_edhrec_invalid_input(self):
        """Test name formatting with invalid input types."""
        downloader = CardDataDownloader()
        
        invalid_inputs = [None, 123, ["Sol Ring"], {"name": "Sol Ring"}, b"Sol Ring"]
        
        for invalid_input in invalid_inputs:
            with pytest.raises(TypeError):
                downloader._format_name_for_edhrec(invalid_input)
    
    @patch('requests.get')
    def test_fetch_card_data_success(self, mock_get):
        """Test successful card data fetching."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'Sol Ring',
            'type_line': 'Artifact',
            'oracle_text': '{T}: Add {C}{C}.',
            'color_identity': [],
            'legalities': {'commander': 'legal'},
            'mana_cost': '{1}',
            'rarity': 'common'
        }
        mock_get.return_value = mock_response
        
        downloader = CardDataDownloader()
        result = downloader._fetch_card_data("Sol Ring")
        
        assert result is not None
        assert result['name'] == 'Sol Ring'
        assert result['type_line'] == 'Artifact'
        
        # Verify the API was called correctly
        mock_get.assert_called_once_with(
            "https://api.scryfall.com/cards/named",
            params={'exact': 'Sol Ring'}
        )
    
    @patch('requests.get')
    def test_fetch_card_data_not_found(self, mock_get):
        """Test card data fetching when card is not found."""
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        downloader = CardDataDownloader()
        result = downloader._fetch_card_data("NonExistentCard")
        
        assert result is None
    
    @patch('requests.get')
    def test_fetch_card_data_api_error(self, mock_get):
        """Test card data fetching when API returns an error."""
        # Mock 500 response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        downloader = CardDataDownloader()
        result = downloader._fetch_card_data("Sol Ring")
        
        assert result is None
    
    @patch('requests.get')
    def test_fetch_card_data_network_error(self, mock_get):
        """Test card data fetching when network error occurs."""
        # Mock network error
        mock_get.side_effect = requests.RequestException("Network error")
        
        downloader = CardDataDownloader()
        result = downloader._fetch_card_data("Sol Ring")
        
        assert result is None
    
    @patch('requests.get')
    def test_fetch_edhrec_data_success(self, mock_get):
        """Test successful EDHREC data fetching."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'potential_decks': 5000,
            'synergies': ['ramp', 'artifacts']
        }
        mock_get.return_value = mock_response
        
        downloader = CardDataDownloader()
        result = downloader._fetch_edhrec_data("Sol Ring")
        
        assert result is not None
        assert result['potential_decks'] == 5000
        assert 'synergies' in result
        
        # Verify the API was called correctly
        mock_get.assert_called_once_with(
            "https://www.edhrec.com/api/cards/sol-ring"
        )
    
    @patch('requests.get')
    def test_fetch_edhrec_data_not_found(self, mock_get):
        """Test EDHREC data fetching when card is not found."""
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        downloader = CardDataDownloader()
        result = downloader._fetch_edhrec_data("NonExistentCard")
        
        assert result is None
    
    @patch('requests.get')
    def test_fetch_edhrec_data_api_error(self, mock_get):
        """Test EDHREC data fetching when API returns an error."""
        # Mock 500 response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        downloader = CardDataDownloader()
        result = downloader._fetch_edhrec_data("Sol Ring")
        
        assert result is None
    
    @patch('requests.get')
    def test_fetch_edhrec_data_network_error(self, mock_get):
        """Test EDHREC data fetching when network error occurs."""
        # Mock network error
        mock_get.side_effect = requests.RequestException("Network error")
        
        downloader = CardDataDownloader()
        result = downloader._fetch_edhrec_data("Sol Ring")
        
        assert result is None
    
    @patch.object(CardDataDownloader, '_fetch_card_data')
    @patch.object(CardDataDownloader, '_fetch_edhrec_data')
    def test_download_card_data_success(self, mock_edhrec, mock_scryfall):
        """Test successful card data downloading."""
        # Mock Scryfall response
        mock_scryfall.return_value = {
            'name': 'Sol Ring',
            'type_line': 'Artifact',
            'oracle_text': '{T}: Add {C}{C}.',
            'color_identity': [],
            'legalities': {'commander': 'legal'},
            'mana_cost': '{1}',
            'rarity': 'common'
        }
        
        # Mock EDHREC response
        mock_edhrec.return_value = {
            'potential_decks': 5000,
            'synergies': ['ramp', 'artifacts']
        }
        
        downloader = CardDataDownloader()
        result = downloader.download_card_data("Sol Ring")
        
        assert result is not None
        assert result['name'] == 'Sol Ring'
        assert result['edhrec_data']['potential_decks'] == 5000
        
        mock_scryfall.assert_called_once_with("Sol Ring")
        mock_edhrec.assert_called_once_with("sol-ring")
    
    @patch.object(CardDataDownloader, '_fetch_card_data')
    @patch.object(CardDataDownloader, '_fetch_edhrec_data')
    def test_download_card_data_scryfall_failure(self, mock_edhrec, mock_scryfall):
        """Test card data downloading when Scryfall fails."""
        # Mock Scryfall failure
        mock_scryfall.return_value = None
        
        downloader = CardDataDownloader()
        result = downloader.download_card_data("NonExistentCard")
        
        assert result is None
        
        mock_scryfall.assert_called_once_with("NonExistentCard")
        mock_edhrec.assert_not_called()
    
    @patch.object(CardDataDownloader, '_fetch_card_data')
    @patch.object(CardDataDownloader, '_fetch_edhrec_data')
    def test_download_card_data_edhrec_failure(self, mock_edhrec, mock_scryfall):
        """Test card data downloading when EDHREC fails."""
        # Mock Scryfall success
        mock_scryfall.return_value = {
            'name': 'Sol Ring',
            'type_line': 'Artifact',
            'oracle_text': '{T}: Add {C}{C}.',
            'color_identity': [],
            'legalities': {'commander': 'legal'},
            'mana_cost': '{1}',
            'rarity': 'common'
        }
        
        # Mock EDHREC failure
        mock_edhrec.return_value = None
        
        downloader = CardDataDownloader()
        result = downloader.download_card_data("Sol Ring")
        
        assert result is not None
        assert result['name'] == 'Sol Ring'
        assert 'edhrec_data' not in result
        
        mock_scryfall.assert_called_once_with("Sol Ring")
        mock_edhrec.assert_called_once_with("sol-ring")
    
    def test_download_card_data_empty_input(self):
        """Test card data downloading with empty input."""
        downloader = CardDataDownloader()
        result = downloader.download_card_data("")
        assert result is None
    
    def test_download_card_data_none_input(self):
        """Test card data downloading with None input."""
        downloader = CardDataDownloader()
        result = downloader.download_card_data(None)
        assert result is None
    
    @patch.object(CardDataDownloader, 'download_card_data')
    def test_download_multiple_cards_success(self, mock_download):
        """Test downloading multiple cards successfully."""
        # Mock successful downloads
        mock_download.side_effect = [
            {'name': 'Sol Ring', 'type_line': 'Artifact'},
            {'name': 'Lightning Bolt', 'type_line': 'Instant'},
            {'name': 'Counterspell', 'type_line': 'Instant'}
        ]
        
        downloader = CardDataDownloader()
        card_names = ["Sol Ring", "Lightning Bolt", "Counterspell"]
        results = downloader.download_multiple_cards(card_names)
        
        assert len(results) == 3
        assert all(result is not None for result in results)
        assert mock_download.call_count == 3
    
    @patch.object(CardDataDownloader, 'download_card_data')
    def test_download_multiple_cards_partial_failure(self, mock_download):
        """Test downloading multiple cards with some failures."""
        # Mock mixed results
        mock_download.side_effect = [
            {'name': 'Sol Ring', 'type_line': 'Artifact'},
            None,  # Lightning Bolt fails
            {'name': 'Counterspell', 'type_line': 'Instant'}
        ]
        
        downloader = CardDataDownloader()
        card_names = ["Sol Ring", "Lightning Bolt", "Counterspell"]
        results = downloader.download_multiple_cards(card_names)
        
        assert len(results) == 3
        assert results[0] is not None
        assert results[1] is None
        assert results[2] is not None
        assert mock_download.call_count == 3
    
    def test_download_multiple_cards_empty_list(self):
        """Test downloading multiple cards with empty list."""
        downloader = CardDataDownloader()
        results = downloader.download_multiple_cards([])
        assert results == []
    
    def test_download_multiple_cards_none_list(self):
        """Test downloading multiple cards with None list."""
        downloader = CardDataDownloader()
        results = downloader.download_multiple_cards(None)
        assert results == []
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_card_data_success(self, mock_json_dump, mock_file):
        """Test successful card data saving."""
        card_data = {
            'sol ring': {'name': 'Sol Ring', 'type_line': 'Artifact'},
            'lightning bolt': {'name': 'Lightning Bolt', 'type_line': 'Instant'}
        }
        
        downloader = CardDataDownloader()
        downloader.save_card_data(card_data, "test_output.json")
        
        mock_file.assert_called_once_with("test_output.json", 'w', encoding='utf-8')
        mock_json_dump.assert_called_once_with(card_data, mock_file(), indent=2, ensure_ascii=False)
    
    @patch('builtins.open')
    def test_save_card_data_permission_error(self, mock_file):
        """Test card data saving with permission error."""
        mock_file.side_effect = PermissionError("Permission denied")
        
        card_data = {'sol ring': {'name': 'Sol Ring'}}
        downloader = CardDataDownloader()
        
        # Should not raise an exception
        downloader.save_card_data(card_data, "/root/test.json")
    
    def test_save_card_data_empty_data(self):
        """Test card data saving with empty data."""
        downloader = CardDataDownloader()
        
        # Should not raise an exception
        downloader.save_card_data({}, "test.json")
    
    def test_save_card_data_none_data(self):
        """Test card data saving with None data."""
        downloader = CardDataDownloader()
        
        # Should not raise an exception
        downloader.save_card_data(None, "test.json") 