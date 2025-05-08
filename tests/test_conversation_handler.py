import pytest
from src.conversation_handler import ConversationHandler

@pytest.fixture
def conversation_handler():
    return ConversationHandler(max_history=3)

def test_init(conversation_handler):
    """Test ConversationHandler initialization."""
    assert conversation_handler.max_history == 3
    assert conversation_handler.conversations == {}

def test_extract_card_name():
    """Test card name extraction from messages."""
    handler = ConversationHandler()
    
    # Test valid card names
    assert handler._extract_card_name('Tell me about "Sol Ring"') == "Sol Ring"
    assert handler._extract_card_name('What\'s the price of "Black Lotus"?') == "Black Lotus"
    assert handler._extract_card_name('Show me "Dark Ritual"') == "Dark Ritual"
    
    # Test invalid messages
    assert handler._extract_card_name("Hello there") is None
    assert handler._extract_card_name("") is None
    assert handler._extract_card_name(None) is None

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
    """Test message processing and intent detection."""
    # Test price query
    result = conversation_handler.process_message("What's the price of Sol Ring?")
    assert result["type"] == "brew"
    assert result["card_name"] is None
    assert result["budget"] is None
    assert result["original_text"] == "What's the price of Sol Ring?"
    
    # Test budget query
    result = conversation_handler.process_message("Show me budget cards for $50")
    assert result["type"] == "budget"
    assert result["card_name"] is None
    assert result["budget"] == 50.0
    assert result["original_text"] == "Show me budget cards for $50"
    
    # Test invalid message
    result = conversation_handler.process_message("Hello there")
    assert result["type"] == "brew"
    assert result["card_name"] is None
    assert result["budget"] is None
    assert result["original_text"] == "Hello there"

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