import pytest
from unittest.mock import Mock, patch, AsyncMock
import discord
from src.bot import bot, handle_conversation, handle_brew_query, handle_synergy_query, handle_budget_query, handle_meta_query

@pytest.fixture
def mock_message():
    message = Mock(spec=discord.Message)
    message.author = Mock()
    message.author.bot = False
    message.channel = Mock()
    message.channel.id = 123
    message.content = "Test message"
    return message

@pytest.fixture
def mock_ctx():
    ctx = Mock()
    ctx.message = Mock(spec=discord.Message)
    ctx.message.channel = Mock()
    ctx.message.channel.id = 123
    return ctx

@pytest.fixture
def mock_mtg_handler():
    with patch('src.bot.mtg_handler') as mock:
        mock.get_commander_info = AsyncMock()
        mock.get_commander_info.return_value = {
            'name': 'Test Commander',
            'mana_cost': '{2}{W}{U}',
            'colors': ['W', 'U'],
            'type': 'Legendary Creature',
            'text': 'Test ability',
            'edhrec_rank': 100,
            'average_decks': 500,
            'potential_decks': 1000
        }
        yield mock

@pytest.fixture
def mock_llm_handler():
    with patch('src.bot.llm_handler') as mock:
        mock.analyze_commander = AsyncMock(return_value='Test analysis')
        mock.find_synergies = AsyncMock(return_value='Test synergies')
        mock.get_budget_suggestions = AsyncMock(return_value='Test budget suggestions')
        mock.analyze_meta = AsyncMock(return_value='Test meta analysis')
        mock.generate_response = AsyncMock(return_value='Test response')
        yield mock

@pytest.fixture
def mock_conversation_handler():
    with patch('src.bot.conversation_handler') as mock:
        mock.add_message = Mock()
        mock.process_message = Mock()
        mock.process_message.return_value = {
            'type': 'brew',
            'card_name': 'Test Commander',
            'budget': None,
            'original_text': 'Test message'
        }
        yield mock

@pytest.mark.asyncio
async def test_handle_conversation_brew(mock_message, mock_mtg_handler, mock_llm_handler, mock_conversation_handler):
    """Test handling a brew query in conversation."""
    mock_conversation_handler.process_message.return_value = {
        'type': 'brew',
        'card_name': 'Test Commander',
        'budget': None,
        'original_text': 'Test message'
    }
    
    await handle_conversation(mock_message)
    
    mock_mtg_handler.get_commander_info.assert_called_once_with('Test Commander')
    mock_llm_handler.analyze_commander.assert_called_once()
    mock_message.channel.send.assert_called()

@pytest.mark.asyncio
async def test_handle_conversation_synergy(mock_message, mock_mtg_handler, mock_llm_handler, mock_conversation_handler):
    """Test handling a synergy query in conversation."""
    mock_conversation_handler.process_message.return_value = {
        'type': 'synergy',
        'card_name': 'Test Card',
        'budget': None,
        'original_text': 'Test message'
    }
    
    await handle_conversation(mock_message)
    
    mock_mtg_handler.get_commander_info.assert_called_once_with('Test Card')
    mock_llm_handler.find_synergies.assert_called_once()
    mock_message.channel.send.assert_called()

@pytest.mark.asyncio
async def test_handle_conversation_budget(mock_message, mock_mtg_handler, mock_llm_handler, mock_conversation_handler):
    """Test handling a budget query in conversation."""
    mock_conversation_handler.process_message.return_value = {
        'type': 'budget',
        'card_name': 'Test Commander',
        'budget': 100.0,
        'original_text': 'Test message'
    }
    
    await handle_conversation(mock_message)
    
    mock_mtg_handler.get_commander_info.assert_called_once_with('Test Commander')
    mock_llm_handler.get_budget_suggestions.assert_called_once()
    mock_message.channel.send.assert_called()

@pytest.mark.asyncio
async def test_handle_conversation_meta(mock_message, mock_mtg_handler, mock_llm_handler, mock_conversation_handler):
    """Test handling a meta query in conversation."""
    mock_conversation_handler.process_message.return_value = {
        'type': 'meta',
        'card_name': 'Test Commander',
        'budget': None,
        'original_text': 'Test message'
    }
    
    await handle_conversation(mock_message)
    
    mock_llm_handler.analyze_meta.assert_called_once_with('Test Commander')
    mock_message.channel.send.assert_called()

@pytest.mark.asyncio
async def test_handle_conversation_general(mock_message, mock_llm_handler, mock_conversation_handler):
    """Test handling a general conversation message."""
    mock_conversation_handler.process_message.return_value = {
        'type': None,
        'card_name': None,
        'budget': None,
        'original_text': 'Test message'
    }
    
    await handle_conversation(mock_message)
    
    mock_llm_handler.generate_response.assert_called_once()
    mock_message.channel.send.assert_called()

@pytest.mark.asyncio
async def test_handle_brew_query(mock_message, mock_mtg_handler, mock_llm_handler, mock_conversation_handler):
    """Test handle_brew_query function."""
    result = {
        'card_name': 'Test Commander',
        'budget': None
    }
    
    await handle_brew_query(mock_message, result)
    
    mock_mtg_handler.get_commander_info.assert_called_once_with('Test Commander')
    mock_llm_handler.analyze_commander.assert_called_once()
    mock_message.channel.send.assert_called()

@pytest.mark.asyncio
async def test_handle_synergy_query(mock_message, mock_mtg_handler, mock_llm_handler, mock_conversation_handler):
    """Test handle_synergy_query function."""
    result = {
        'card_name': 'Test Card',
        'budget': None
    }
    
    await handle_synergy_query(mock_message, result)
    
    mock_mtg_handler.get_commander_info.assert_called_once_with('Test Card')
    mock_llm_handler.find_synergies.assert_called_once()
    mock_message.channel.send.assert_called()

@pytest.mark.asyncio
async def test_handle_budget_query(mock_message, mock_mtg_handler, mock_llm_handler, mock_conversation_handler):
    """Test handle_budget_query function."""
    result = {
        'card_name': 'Test Commander',
        'budget': 100.0
    }
    
    await handle_budget_query(mock_message, result)
    
    mock_mtg_handler.get_commander_info.assert_called_once_with('Test Commander')
    mock_llm_handler.get_budget_suggestions.assert_called_once()
    mock_message.channel.send.assert_called()

@pytest.mark.asyncio
async def test_handle_meta_query(mock_message, mock_llm_handler, mock_conversation_handler):
    """Test handle_meta_query function."""
    result = {
        'card_name': 'Test Commander',
        'budget': None
    }
    
    await handle_meta_query(mock_message, result)
    
    mock_llm_handler.analyze_meta.assert_called_once_with('Test Commander')
    mock_message.channel.send.assert_called()

@pytest.mark.asyncio
async def test_command_brew(mock_ctx, mock_mtg_handler, mock_llm_handler):
    """Test !brew command."""
    from src.bot import brew_deck
    
    await brew_deck(mock_ctx, commander_name='Test Commander')
    
    mock_mtg_handler.get_commander_info.assert_called_once_with('Test Commander')
    mock_llm_handler.analyze_commander.assert_called_once()
    mock_ctx.message.channel.send.assert_called()

@pytest.mark.asyncio
async def test_command_synergy(mock_ctx, mock_mtg_handler, mock_llm_handler):
    """Test !synergy command."""
    from src.bot import find_synergy
    
    await find_synergy(mock_ctx, card_name='Test Card')
    
    mock_mtg_handler.get_commander_info.assert_called_once_with('Test Card')
    mock_llm_handler.find_synergies.assert_called_once()
    mock_ctx.message.channel.send.assert_called()

@pytest.mark.asyncio
async def test_command_budget(mock_ctx, mock_mtg_handler, mock_llm_handler):
    """Test !budget command."""
    from src.bot import budget_deck
    
    await budget_deck(mock_ctx, commander_name='Test Commander', budget=100.0)
    
    mock_mtg_handler.get_commander_info.assert_called_once_with('Test Commander')
    mock_llm_handler.get_budget_suggestions.assert_called_once()
    mock_ctx.message.channel.send.assert_called()

@pytest.mark.asyncio
async def test_command_meta(mock_ctx, mock_llm_handler):
    """Test !meta command."""
    from src.bot import meta_analysis
    
    await meta_analysis(mock_ctx, commander_name='Test Commander')
    
    mock_llm_handler.analyze_meta.assert_called_once_with('Test Commander')
    mock_ctx.message.channel.send.assert_called()

@pytest.mark.asyncio
async def test_command_help(mock_ctx):
    """Test !help_brew command."""
    from src.bot import help_brew
    
    await help_brew(mock_ctx)
    
    mock_ctx.send.assert_called_once()
    help_text = mock_ctx.send.call_args[0][0]
    assert 'Commands' in help_text
    assert 'Natural Language' in help_text 