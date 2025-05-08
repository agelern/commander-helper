import pytest
from src.conversation_handler import ConversationHandler

@pytest.fixture
def conversation_handler():
    return ConversationHandler(max_history=3)

def test_init(conversation_handler):
    """Test ConversationHandler initialization."""
    assert conversation_handler.max_history == 3
    assert conversation_handler.conversations == {}

def test_extract_card_name(conversation_handler):
    """Test card name extraction from various text patterns."""
    test_cases = [
        ('"Atraxa, Praetors\' Voice" is my commander', 'Atraxa, Praetors\' Voice'),
        ('I want to build a deck with Sol Ring', 'Sol Ring'),
        ('What cards synergize with Counterspell?', 'Counterspell'),
        ('Help me brew a commander called Edgar Markov', 'Edgar Markov'),
        ('No card name here', None)
    ]
    
    for text, expected in test_cases:
        result = conversation_handler._extract_card_name(text)
        if expected is None:
            assert result is None
        else:
            assert result.lower() == expected.lower()

def test_extract_budget(conversation_handler):
    """Test budget extraction from various text patterns."""
    test_cases = [
        ('I have a budget of $100', 100.0),
        ('Can you make it work with $50.50?', 50.50),
        ('Budget is $1000.00', 1000.0),
        ('No budget mentioned', None),
        ('Invalid budget $abc', None)
    ]
    
    for text, expected in test_cases:
        assert conversation_handler._extract_budget(text) == expected

def test_add_message(conversation_handler):
    """Test adding messages to conversation history."""
    channel_id = 123
    conversation_handler.add_message(channel_id, 'user', 'Test message')
    
    assert channel_id in conversation_handler.conversations
    assert len(conversation_handler.conversations[channel_id]) == 1
    assert conversation_handler.conversations[channel_id][0]['role'] == 'user'
    assert conversation_handler.conversations[channel_id][0]['content'] == 'Test message'

def test_max_history(conversation_handler):
    """Test that conversation history respects max_history limit."""
    channel_id = 123
    
    # Add more messages than max_history
    for i in range(5):
        conversation_handler.add_message(channel_id, 'user', f'Message {i}')
    
    assert len(conversation_handler.conversations[channel_id]) == 3
    assert conversation_handler.conversations[channel_id][-1]['content'] == 'Message 4'

def test_process_message(conversation_handler):
    """Test message processing and query type detection."""
    test_cases = [
        ('Help me build a deck with Atraxa', {
            'type': 'brew',
            'card_name': 'Atraxa',
            'budget': None,
            'original_text': 'Help me build a deck with Atraxa'
        }),
        ('What cards synergize with Sol Ring?', {
            'type': 'synergy',
            'card_name': 'Sol Ring',
            'budget': None,
            'original_text': 'What cards synergize with Sol Ring?'
        }),
        ('Budget options for $100', {
            'type': 'budget',
            'card_name': None,
            'budget': 100.0,
            'original_text': 'Budget options for $100'
        }),
        ('What\'s the meta like for Edgar Markov?', {
            'type': 'meta',
            'card_name': 'Edgar Markov',
            'budget': None,
            'original_text': 'What\'s the meta like for Edgar Markov?'
        })
    ]
    
    for text, expected in test_cases:
        result = conversation_handler.process_message(text)
        # Compare card names case-insensitively if they exist
        if expected['card_name'] is not None:
            assert result['card_name'] is not None
            assert result['card_name'].lower() == expected['card_name'].lower()
        else:
            assert result['card_name'] is None
        # Compare other fields exactly
        assert result['type'] == expected['type']
        assert result['budget'] == expected['budget']
        assert result['original_text'] == expected['original_text']

def test_clear_history(conversation_handler):
    """Test clearing conversation history."""
    channel_id = 123
    conversation_handler.add_message(channel_id, 'user', 'Test message')
    
    assert len(conversation_handler.conversations[channel_id]) == 1
    conversation_handler.clear_history(channel_id)
    assert len(conversation_handler.conversations[channel_id]) == 0

def test_get_conversation_history(conversation_handler):
    """Test getting formatted conversation history."""
    channel_id = 123
    conversation_handler.add_message(channel_id, 'user', 'User message')
    conversation_handler.add_message(channel_id, 'assistant', 'Assistant response')
    
    history = conversation_handler._get_conversation_history(channel_id)
    assert 'user: User message' in history
    assert 'assistant: Assistant response' in history 