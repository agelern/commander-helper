import json
import tempfile
import os
import pytest
from src.data.card_data import CardData

def minimal_card_data():
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
        }
    }

@pytest.fixture
def temp_card_data_file(tmp_path):
    data = minimal_card_data()
    file_path = tmp_path / 'cards.json'
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return file_path

def test_card_data_init_and_load(temp_card_data_file):
    card_data = CardData(data_file=temp_card_data_file)
    assert len(card_data.cards) > 0
    assert card_data.get_load_time() is not None
    assert 'sol ring' in card_data.cards
    assert card_data.cards['sol ring']['name'] == 'Sol Ring'

def test_card_data_get_card(temp_card_data_file):
    card_data = CardData(data_file=temp_card_data_file)
    card = card_data.get_card('Sol Ring')
    assert card is not None
    assert card['name'] == 'Sol Ring'
    # Should be case-insensitive
    card2 = card_data.get_card('sOl RiNg')
    assert card2 is not None
    assert card2['name'] == 'Sol Ring'
    # Should return None for unknown card
    assert card_data.get_card('Nonexistent Card') is None

def test_card_data_search_cards(temp_card_data_file):
    card_data = CardData(data_file=temp_card_data_file)
    results = card_data.search_cards('sol')
    assert isinstance(results, list)
    assert any(card['name'] == 'Sol Ring' for card in results)
    # Should be case-insensitive and partial match
    results2 = card_data.search_cards('SOL')
    assert any(card['name'] == 'Sol Ring' for card in results2)
    # Should return empty list for no match
    assert card_data.search_cards('Nonexistent') == []

def test_card_data_get_cards_by_type(temp_card_data_file):
    card_data = CardData(data_file=temp_card_data_file)
    results = card_data.get_cards_by_type('Artifact')
    assert isinstance(results, list)
    assert any(card['name'] == 'Sol Ring' for card in results)
    # Should return empty list for unknown type
    assert card_data.get_cards_by_type('Goblin') == []

def test_card_data_get_commander_legal_cards(temp_card_data_file):
    card_data = CardData(data_file=temp_card_data_file)
    results = card_data.get_commander_legal_cards()
    assert isinstance(results, list)
    assert any(card['name'] == 'Sol Ring' for card in results) 