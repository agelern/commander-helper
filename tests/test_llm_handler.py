import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.llm_handler import LLMHandler

@pytest.fixture
def mock_ollama():
    """Mock Ollama client for testing."""
    with patch('src.llm_handler.ollama') as mock:
        client = AsyncMock()
        client.generate = AsyncMock(return_value={'response': 'Test response'})
        mock.Client.return_value = client
        yield mock

@pytest.fixture
def llm_handler(mock_ollama):
    """Create an LLMHandler instance with mocked Ollama client."""
    handler = LLMHandler(model_name='test-model')
    handler.client = mock_ollama.Client.return_value
    return handler

@pytest.mark.asyncio
async def test_init(llm_handler, mock_ollama):
    """Test LLMHandler initialization."""
    assert llm_handler.model_name == 'test-model'
    mock_ollama.Client.assert_called_once()

@pytest.mark.asyncio
async def test_generate_response(llm_handler, mock_ollama):
    """Test generate_response method."""
    user_input = "Test input"
    conversation_history = [
        {'role': 'user', 'content': 'Previous message'},
        {'role': 'assistant', 'content': 'Previous response'}
    ]
    
    response = await llm_handler.generate_response(user_input, conversation_history)
    
    assert response == 'Test response'
    mock_ollama.Client.return_value.generate.assert_awaited_once()
    call_args = mock_ollama.Client.return_value.generate.call_args[1]
    assert call_args['model'] == 'test-model'
    assert call_args['temperature'] == 0.5
    assert 'Test input' in call_args['prompt']

@pytest.mark.asyncio
async def test_analyze_commander(llm_handler, mock_ollama):
    """Test analyze_commander method."""
    commander_info = {
        'name': 'Test Commander',
        'mana_cost': '{2}{W}{U}',
        'colors': ['W', 'U'],
        'type': 'Legendary Creature',
        'text': 'Test ability',
        'edhrec_rank': 100,
        'average_decks': 500,
        'potential_decks': 1000
    }
    
    response = await llm_handler.analyze_commander(commander_info)
    
    assert response == 'Test response'
    mock_ollama.Client.return_value.generate.assert_awaited_once()
    call_args = mock_ollama.Client.return_value.generate.call_args[1]
    assert call_args['model'] == 'test-model'
    assert 'Test Commander' in call_args['prompt']
    assert 'W, U' in call_args['prompt']

@pytest.mark.asyncio
async def test_find_synergies(llm_handler, mock_ollama):
    """Test find_synergies method."""
    card_name = "Test Card"
    card_text = "Test ability"
    
    response = await llm_handler.find_synergies(card_name, card_text)
    
    assert response == 'Test response'
    mock_ollama.Client.return_value.generate.assert_awaited_once()
    call_args = mock_ollama.Client.return_value.generate.call_args[1]
    assert call_args['model'] == 'test-model'
    assert 'Test Card' in call_args['prompt']
    assert 'Test ability' in call_args['prompt']

@pytest.mark.asyncio
async def test_get_budget_suggestions(llm_handler, mock_ollama):
    """Test get_budget_suggestions method."""
    commander_info = {
        'name': 'Test Commander',
        'mana_cost': '{2}{W}{U}',
        'colors': ['W', 'U'],
        'type': 'Legendary Creature',
        'text': 'Test ability'
    }
    budget = 100.0
    
    response = await llm_handler.get_budget_suggestions(commander_info, budget)
    
    assert response == 'Test response'
    mock_ollama.Client.return_value.generate.assert_awaited_once()
    call_args = mock_ollama.Client.return_value.generate.call_args[1]
    assert call_args['model'] == 'test-model'
    assert 'Test Commander' in call_args['prompt']
    assert '$100' in call_args['prompt']

@pytest.mark.asyncio
async def test_analyze_meta(llm_handler, mock_ollama):
    """Test analyze_meta method."""
    commander_name = "Test Commander"
    
    response = await llm_handler.analyze_meta(commander_name)
    
    assert response == 'Test response'
    mock_ollama.Client.return_value.generate.assert_awaited_once()
    call_args = mock_ollama.Client.return_value.generate.call_args[1]
    assert call_args['model'] == 'test-model'
    assert 'Test Commander' in call_args['prompt']

@pytest.mark.asyncio
async def test_error_handling(llm_handler, mock_ollama):
    """Test error handling in generate_response."""
    mock_ollama.Client.return_value.generate.side_effect = Exception("Test error")
    
    with pytest.raises(Exception) as exc_info:
        await llm_handler.generate_response("Test input", [])
    
    assert str(exc_info.value) == "Test error" 