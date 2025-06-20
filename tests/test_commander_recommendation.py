import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Set

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.commands.commander_recommendation import CommanderRecommendationCommand, CommanderRecommendationView
from src.data.card_data import CardData


class TestCommanderRecommendationCommand:
    """Test suite for CommanderRecommendationCommand."""
    
    @pytest.fixture
    def mock_card_data(self):
        """Create mock card data for testing."""
        mock_data = Mock(spec=CardData)
        mock_data.cards = {
            'sol ring': {
                'name': 'Sol Ring',
                'type_line': 'Artifact',
                'oracle_text': '{T}: Add {C}{C}.',
                'color_identity': [],
                'legalities': {'commander': 'legal'},
                'mana_cost': '{1}',
                'rarity': 'common'
            },
            'lightning bolt': {
                'name': 'Lightning Bolt',
                'type_line': 'Instant',
                'oracle_text': 'Lightning Bolt deals 3 damage to any target.',
                'color_identity': ['R'],
                'legalities': {'commander': 'legal'},
                'mana_cost': '{R}',
                'rarity': 'common'
            },
            'counterspell': {
                'name': 'Counterspell',
                'type_line': 'Instant',
                'oracle_text': 'Counter target spell.',
                'color_identity': ['U', 'U'],
                'legalities': {'commander': 'legal'},
                'mana_cost': '{U}{U}',
                'rarity': 'common'
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
                }
            },
            'atraxa, praetors voice': {
                'name': 'Atraxa, Praetors\' Voice',
                'type_line': 'Legendary Creature — Angel Horror',
                'oracle_text': 'Flying, vigilance, deathtouch, lifelink\nAt the beginning of your end step, proliferate.',
                'color_identity': ['W', 'U', 'B', 'G'],
                'legalities': {'commander': 'legal'},
                'mana_cost': '{2}{W}{U}{B}{G}',
                'rarity': 'mythic',
                'edhrec_data': {
                    'potential_decks': 8000
                }
            },
            'goblin guide': {
                'name': 'Goblin Guide',
                'type_line': 'Legendary Creature — Goblin Scout',
                'oracle_text': 'Haste\nWhenever Goblin Guide attacks, defending player reveals the top card of their library. If it\'s a land card, that player puts it into their hand.',
                'color_identity': ['R'],
                'legalities': {'commander': 'legal'},
                'mana_cost': '{R}',
                'rarity': 'rare',
                'edhrec_data': {
                    'potential_decks': 100
                }
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
        
        def get_card(name, include_tokens=True):
            return mock_data.cards.get(name.lower())
        
        mock_data.get_card = get_card
        return mock_data
    
    @pytest.fixture
    def command(self, mock_card_data):
        """Create a CommanderRecommendationCommand instance for testing."""
        return CommanderRecommendationCommand(mock_card_data)
    
    def test_is_commander_legendary_creature(self, command):
        """Test that legendary creatures are identified as commanders."""
        card = {
            'type_line': 'Legendary Creature — Angel',
            'oracle_text': 'Some text',
            'legalities': {'commander': 'legal'}
        }
        assert command._is_commander(card) is True
    
    def test_is_commander_can_be_commander_text(self, command):
        """Test that cards with 'can be your commander' text are identified as commanders."""
        card = {
            'type_line': 'Enchantment',
            'oracle_text': 'This card can be your commander.',
            'legalities': {'commander': 'legal'}
        }
        assert command._is_commander(card) is True
    
    def test_is_commander_not_legendary(self, command):
        """Test that non-legendary creatures are not identified as commanders."""
        card = {
            'type_line': 'Creature — Human',
            'oracle_text': 'Some text',
            'legalities': {'commander': 'legal'}
        }
        assert command._is_commander(card) is False
    
    def test_is_commander_illegal(self, command):
        """Test that illegal cards are not identified as commanders."""
        card = {
            'type_line': 'Legendary Creature — Dragon',
            'oracle_text': 'Some text',
            'legalities': {'commander': 'banned'}
        }
        assert command._is_commander(card) is False
    
    def test_extract_color_identity(self, command):
        """Test color identity extraction."""
        card = {'color_identity': ['W', 'U', 'B']}
        result = command._extract_color_identity(card)
        assert result == {'W', 'U', 'B'}
    
    def test_extract_color_identity_empty(self, command):
        """Test color identity extraction from colorless card."""
        card = {'color_identity': []}
        result = command._extract_color_identity(card)
        assert result == set()
    
    def test_aggregate_color_identity(self, command):
        """Test color identity aggregation from multiple cards."""
        cards = [
            {'color_identity': ['W', 'U']},
            {'color_identity': ['U', 'B']},
            {'color_identity': ['R']}
        ]
        result = command._aggregate_color_identity(cards)
        assert result == {'W', 'U', 'B', 'R'}
    
    def test_commander_matches_colors(self, command):
        """Test that commander color matching works correctly."""
        commander = {'color_identity': ['W', 'U', 'B', 'G']}
        required_colors = {'W', 'U'}
        assert command._commander_matches_colors(commander, required_colors) is True
    
    def test_commander_matches_colors_exact_match(self, command):
        """Test that commander with exact color match works."""
        commander = {'color_identity': ['W', 'U']}
        required_colors = {'W', 'U'}
        assert command._commander_matches_colors(commander, required_colors) is True
    
    def test_commander_matches_colors_no_match(self, command):
        """Test that commander without required colors doesn't match."""
        commander = {'color_identity': ['W', 'U']}
        required_colors = {'R', 'G'}
        assert command._commander_matches_colors(commander, required_colors) is False
    
    def test_find_shared_keywords(self, command):
        """Test finding shared keywords between card texts."""
        # Use lowercase text since the method expects lowercase
        text1 = "flying, first strike, draw a card"
        text2 = "flying, haste, destroy target creature"
        result = command._find_shared_keywords(text1, text2)
        assert 'flying' in result
        assert 'first strike' not in result  # Only in text1
        assert 'haste' not in result  # Only in text2
    
    def test_find_shared_keywords_no_matches(self, command):
        """Test finding shared keywords when there are none."""
        text1 = "flying, first strike"
        text2 = "haste, trample"
        result = command._find_shared_keywords(text1, text2)
        assert result == set()
    
    def test_has_tribal_synergy(self, command):
        """Test tribal synergy detection."""
        commander = {'type_line': 'Legendary Creature — Goblin Warrior'}
        card = {'type_line': 'Creature — Goblin Scout'}
        assert command._has_tribal_synergy(commander, card) is True
    
    def test_has_tribal_synergy_no_match(self, command):
        """Test tribal synergy detection when no match."""
        commander = {'type_line': 'Legendary Creature — Human'}
        card = {'type_line': 'Creature — Goblin'}
        assert command._has_tribal_synergy(commander, card) is False
    
    def test_has_mana_synergy(self, command):
        """Test mana cost synergy detection."""
        commander = {'mana_cost': '{2}{W}{U}'}
        card = {'mana_cost': '{W}'}
        assert command._has_mana_synergy(commander, card) is True
    
    def test_has_mana_synergy_no_match(self, command):
        """Test mana cost synergy detection when no match."""
        commander = {'mana_cost': '{2}{W}{U}'}
        card = {'mana_cost': '{R}'}
        assert command._has_mana_synergy(commander, card) is False
    
    def test_has_theme_synergy(self, command):
        """Test theme synergy detection."""
        commander = {'oracle_text': 'Draw a card when this enters the battlefield.'}
        card = {'oracle_text': 'Draw two cards.'}
        assert command._has_theme_synergy(commander, card) is True
    
    def test_has_theme_synergy_no_match(self, command):
        """Test theme synergy detection when no match."""
        commander = {'oracle_text': 'Deal damage to target creature.'}
        card = {'oracle_text': 'Draw a card.'}
        assert command._has_theme_synergy(commander, card) is False
    
    def test_calculate_popularity_score_with_edhrec_data(self, command):
        """Test popularity score calculation with EDHREC data."""
        commander = {
            'edhrec_data': {
                'potential_decks': 1000
            }
        }
        score = command._calculate_popularity_score(commander)
        # log(1001) ≈ 6.91, normalized to ~75.0
        assert 70 <= score <= 80
    
    def test_calculate_popularity_score_high_popularity(self, command):
        """Test popularity score calculation for very popular commander."""
        commander = {
            'edhrec_data': {
                'potential_decks': 10000
            }
        }
        score = command._calculate_popularity_score(commander)
        # log(10001) ≈ 9.21, should be close to 100
        assert score >= 95
    
    def test_calculate_popularity_score_low_popularity(self, command):
        """Test popularity score calculation for unpopular commander."""
        commander = {
            'edhrec_data': {
                'potential_decks': 10
            }
        }
        score = command._calculate_popularity_score(commander)
        # log(11) ≈ 2.40, normalized to ~26.0
        assert 20 <= score <= 30
    
    def test_calculate_popularity_score_zero_decks(self, command):
        """Test popularity score calculation for commander with 0 potential decks."""
        commander = {
            'edhrec_data': {
                'potential_decks': 0
            }
        }
        score = command._calculate_popularity_score(commander)
        assert score == 0.0
    
    def test_calculate_popularity_score_no_edhrec_data(self, command):
        """Test popularity score calculation when no EDHREC data is available."""
        commander = {}
        score = command._calculate_popularity_score(commander)
        assert score == 50.0  # Fallback score
    
    def test_parse_card_list(self, command):
        """Test parsing comma-separated card list."""
        args = "Sol Ring, Lightning Bolt, Counterspell"
        result = command._parse_card_list(args)
        assert result == ['Sol Ring', 'Lightning Bolt', 'Counterspell']
    
    def test_parse_card_list_with_whitespace(self, command):
        """Test parsing card list with extra whitespace."""
        args = "  Sol Ring  ,  Lightning Bolt  ,  Counterspell  "
        result = command._parse_card_list(args)
        assert result == ['Sol Ring', 'Lightning Bolt', 'Counterspell']
    
    def test_parse_card_list_empty(self, command):
        """Test parsing empty card list."""
        args = ""
        result = command._parse_card_list(args)
        assert result == []
    
    def test_parse_weights_default(self, command):
        """Test parsing weights with default values."""
        args = "Sol Ring, Lightning Bolt"
        synergy, popularity = command._parse_weights(args)
        assert synergy == 0.7
        assert popularity == 0.3
    
    def test_parse_weights_custom(self, command):
        """Test parsing custom weights."""
        args = "Sol Ring, Lightning Bolt 0.8 0.2"
        synergy, popularity = command._parse_weights(args)
        assert synergy == 0.8
        assert popularity == 0.2
    
    def test_parse_weights_invalid(self, command):
        """Test parsing weights with invalid values (should use defaults)."""
        args = "Sol Ring, Lightning Bolt invalid 0.2"
        synergy, popularity = command._parse_weights(args)
        assert synergy == 0.7  # Default
        assert popularity == 0.3  # Default
    
    @pytest.mark.asyncio
    async def test_execute_no_args(self, command):
        """Test execute with no arguments."""
        embeds, view = await command.execute("")
        assert len(embeds) == 1
        assert "Usage:" in embeds[0].description
        assert view is None
    
    @pytest.mark.asyncio
    async def test_execute_invalid_cards(self, command):
        """Test execute with invalid card names."""
        embeds, view = await command.execute("Invalid Card 1, Invalid Card 2")
        assert len(embeds) == 1
        assert "No valid cards found" in embeds[0].description
        assert view is None
    
    @pytest.mark.asyncio
    async def test_execute_successful_recommendation(self, command):
        """Test successful commander recommendation."""
        embeds, view = await command.execute("Sol Ring, Lightning Bolt")
        assert len(embeds) == 1
        assert "Commander Recommendations" in embeds[0].title
        assert "Based on 2 cards" in embeds[0].description
        # Should find Atraxa as it can include all colors
        assert any("Atraxa" in field.name for field in embeds[0].fields)
    
    @pytest.mark.asyncio
    async def test_execute_no_matching_commanders(self, command):
        """Test when no commanders match the color requirements."""
        # Use cards that require colors not available in any commander
        embeds, view = await command.execute("Lightning Bolt, Counterspell")
        assert len(embeds) == 1
        assert "No Commanders Found" in embeds[0].title
        assert view is None
    
    def test_get_commander_cache(self, command):
        """Test commander cache creation."""
        cache = command._get_commander_cache()
        # Should include Atraxa and Jace but not "not a commander" or "illegal commander"
        assert 'atraxa, praetors voice' in cache
        assert 'jace, the mind sculptor' in cache
        assert 'not a commander' not in cache
        assert 'illegal commander' not in cache
    
    def test_calculate_synergy_score(self, command):
        """Test synergy score calculation."""
        commander = {
            'oracle_text': 'Flying, draw a card when this enters the battlefield.',
            'type_line': 'Legendary Creature — Angel'
        }
        cards = [
            {
                'oracle_text': 'Flying, destroy target creature.',
                'type_line': 'Creature — Angel'
            }
        ]
        score = command._calculate_synergy_score(commander, cards)
        assert 0 <= score <= 100
        assert score > 0  # Should have some synergy due to flying and angel type
    
    def test_calculate_synergy_score_no_cards(self, command):
        """Test synergy score calculation with no input cards."""
        commander = {'oracle_text': 'Some text', 'type_line': 'Legendary Creature'}
        score = command._calculate_synergy_score(commander, [])
        assert score == 0.0
    
    def test_extract_creature_types(self, command):
        """Test creature type extraction."""
        type_line = "Legendary Creature — Angel Warrior"
        result = command._extract_creature_types(type_line)
        assert result == {'Angel', 'Warrior'}
    
    def test_extract_creature_types_no_types(self, command):
        """Test creature type extraction when no types present."""
        type_line = "Legendary Creature"
        result = command._extract_creature_types(type_line)
        assert result == set()
    
    def test_extract_creature_types_non_creature(self, command):
        """Test creature type extraction from non-creature card."""
        type_line = "Instant"
        result = command._extract_creature_types(type_line)
        assert result == set()


class TestCommanderRecommendationView:
    """Test suite for CommanderRecommendationView."""
    
    @pytest.fixture
    def mock_recommendations(self):
        """Create mock recommendations for testing."""
        return [
            {
                'commander': {'name': 'Commander 1'},
                'color_identity': ['W', 'U'],
                'synergy_score': 85.0,
                'popularity_score': 70.0,
                'final_score': 80.0
            },
            {
                'commander': {'name': 'Commander 2'},
                'color_identity': ['B', 'R'],
                'synergy_score': 75.0,
                'popularity_score': 80.0,
                'final_score': 76.5
            }
        ]
    
    @pytest.fixture
    def mock_card_data(self):
        """Create mock card data for testing."""
        return Mock(spec=CardData)
    
    @pytest.fixture
    def view(self, mock_recommendations, mock_card_data):
        """Create a CommanderRecommendationView instance for testing."""
        return CommanderRecommendationView(mock_recommendations, mock_card_data)
    
    def test_view_initialization(self, view):
        """Test view initialization."""
        assert view.recommendations is not None
        assert view.current_page == 0
        assert view.items_per_page == 5
    
    def test_create_recommendations_embed(self, view):
        """Test embed creation."""
        embed = view._create_recommendations_embed()
        assert embed.title == "Commander Recommendations"
        assert "Showing 1-2 of 2 recommendations" in embed.description
        assert len(embed.fields) == 2
    
    def test_create_recommendations_embed_color_symbols(self, view):
        """Test that color symbols are properly displayed."""
        embed = view._create_recommendations_embed()
        # Check that the first field contains color identity information
        field = embed.fields[0]
        assert "⚪🔵" in field.value  # W and U colors
        assert "⚫🔴" in embed.fields[1].value  # B and R colors
    
    @pytest.mark.asyncio
    async def test_interaction_check_prev_button(self, view):
        """Test previous button interaction."""
        # Start on page 1
        view.current_page = 1
        
        mock_interaction = Mock()
        mock_interaction.data = {"custom_id": "prev"}
        mock_interaction.response.edit_message = Mock()
        
        result = await view.interaction_check(mock_interaction)
        
        assert result is True
        assert view.current_page == 0
        mock_interaction.response.edit_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_interaction_check_next_button(self, view):
        """Test next button interaction."""
        mock_interaction = Mock()
        mock_interaction.data = {"custom_id": "next"}
        mock_interaction.response.edit_message = Mock()
        
        result = await view.interaction_check(mock_interaction)
        
        assert result is True
        assert view.current_page == 1
        mock_interaction.response.edit_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_interaction_check_prev_button_at_first_page(self, view):
        """Test previous button when already on first page."""
        view.current_page = 0
        
        mock_interaction = Mock()
        mock_interaction.data = {"custom_id": "prev"}
        mock_interaction.response.edit_message = Mock()
        
        result = await view.interaction_check(mock_interaction)
        
        assert result is True
        assert view.current_page == 0  # Should not go below 0
        mock_interaction.response.edit_message.assert_called_once()


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def mock_card_data(self):
        """Create mock card data for edge case testing."""
        mock_data = Mock(spec=CardData)
        mock_data.cards = {}
        mock_data.get_card = Mock(return_value=None)
        return mock_data
    
    @pytest.fixture
    def command(self, mock_card_data):
        """Create a CommanderRecommendationCommand instance for edge case testing."""
        return CommanderRecommendationCommand(mock_card_data)
    
    @pytest.mark.asyncio
    async def test_execute_exception_handling(self, command):
        """Test that exceptions are properly handled."""
        # Mock the card data to raise an exception
        command.card_data.cards = None  # This will cause an AttributeError
        
        embeds, view = await command.execute("Sol Ring")
        assert len(embeds) == 1
        assert "Error" in embeds[0].title
        assert "error occurred" in embeds[0].description.lower()
    
    def test_parse_card_list_single_card(self, command):
        """Test parsing a single card."""
        args = "Sol Ring"
        result = command._parse_card_list(args)
        assert result == ['Sol Ring']
    
    def test_parse_card_list_empty_entries(self, command):
        """Test parsing card list with empty entries."""
        args = "Sol Ring,,Lightning Bolt,"
        result = command._parse_card_list(args)
        assert result == ['Sol Ring', 'Lightning Bolt']
    
    def test_parse_weights_insufficient_parts(self, command):
        """Test parsing weights with insufficient parts."""
        args = "Sol Ring 0.8"  # Only one weight
        synergy, popularity = command._parse_weights(args)
        assert synergy == 0.7  # Default
        assert popularity == 0.3  # Default
    
    def test_parse_weights_non_numeric(self, command):
        """Test parsing weights with non-numeric values."""
        args = "Sol Ring abc def"
        synergy, popularity = command._parse_weights(args)
        assert synergy == 0.7  # Default
        assert popularity == 0.3  # Default 