import pytest
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
from src.mtg_data import MTGDataHandler
import urllib.parse

@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp ClientSession for testing."""
    with patch('aiohttp.ClientSession') as mock:
        session = AsyncMock()
        mock.return_value.__aenter__.return_value = session
        yield session

@pytest.fixture
def mtg_handler(mock_aiohttp_session):
    return MTGDataHandler()

@pytest.fixture
def mock_scryfall_response():
    """Mock Scryfall API response."""
    return {
        'name': 'Test Commander',
        'mana_cost': '{2}{W}{U}',
        'colors': ['W', 'U'],
        'type_line': 'Legendary Creature — Angel',
        'oracle_text': 'Test ability',
        'legalities': {'commander': 'legal'},
        'prices': {'usd': '10.00'}
    }

@pytest.fixture
def mock_edhrec_response():
    """Mock EDHREC API response."""
    return {
        'rank': 100,
        'average_decks': 500,
        'potential_decks': 1000,
        'synergies': [
            {'name': 'Test Card 1', 'synergy_score': 0.8, 'inclusion_rate': 0.6},
            {'name': 'Test Card 2', 'synergy_score': 0.7, 'inclusion_rate': 0.5}
        ],
        'budget_cards': [
            {'name': 'Budget Card 1', 'price': 5.00, 'synergy': 0.6},
            {'name': 'Budget Card 2', 'price': 3.00, 'synergy': 0.5}
        ]
    }

@pytest.mark.asyncio
async def test_get_commander_info(mtg_handler, mock_aiohttp_session, mock_scryfall_response, mock_edhrec_response):
    """Test getting commander information from both Scryfall and EDHREC."""
    # Mock Scryfall response
    mock_scryfall_session = AsyncMock()
    mock_scryfall_session.get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_scryfall_response)
    mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_scryfall_session

    # Mock EDHREC response
    mock_edhrec_session = AsyncMock()
    mock_edhrec_session.get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_edhrec_response)
    mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_edhrec_session

    commander_info = await mtg_handler.get_commander_info('Test Commander')

    assert commander_info['name'] == 'Test Commander'
    assert commander_info['mana_cost'] == '{2}{W}{U}'
    assert commander_info['colors'] == ['W', 'U']
    assert commander_info['type'] == 'Legendary Creature — Angel'
    assert commander_info['text'] == 'Test ability'
    assert commander_info['edhrec_rank'] == 100
    assert commander_info['average_decks'] == 500
    assert commander_info['potential_decks'] == 1000

@pytest.mark.asyncio
async def test_get_commander_info_scryfall_error(mtg_handler, mock_aiohttp_session):
    """Test error handling when Scryfall API fails."""
    mock_aiohttp_session.get.side_effect = aiohttp.ClientError("Test error")

    with pytest.raises(aiohttp.ClientError) as exc_info:
        await mtg_handler.get_commander_info('Test Commander')
    
    assert str(exc_info.value) == "Test error"

@pytest.mark.asyncio
async def test_get_commander_info_edhrec_error(mtg_handler, mock_aiohttp_session, mock_scryfall_response):
    """Test error handling when EDHREC API fails."""
    # Mock successful Scryfall response
    mock_scryfall_session = AsyncMock()
    mock_scryfall_session.get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_scryfall_response)
    mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_scryfall_session

    # Mock EDHREC error
    mock_aiohttp_session.get.side_effect = [mock_scryfall_session, aiohttp.ClientError("Test error")]

    commander_info = await mtg_handler.get_commander_info('Test Commander')
    
    # Should still return Scryfall data even if EDHREC fails
    assert commander_info['name'] == 'Test Commander'
    assert commander_info['mana_cost'] == '{2}{W}{U}'
    assert 'edhrec_rank' not in commander_info

@pytest.mark.asyncio
async def test_find_synergies(mtg_handler, mock_aiohttp_session, mock_edhrec_response):
    """Test finding card synergies."""
    mock_session = AsyncMock()
    mock_session.get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_edhrec_response)
    mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_session

    synergies = await mtg_handler.find_synergies('Test Card')

    assert len(synergies) == 2
    assert synergies[0]['name'] == 'Test Card 1'
    assert synergies[0]['synergy_score'] == 0.8
    assert synergies[0]['inclusion_rate'] == 0.6

@pytest.mark.asyncio
async def test_get_budget_suggestions(mtg_handler, mock_aiohttp_session, mock_edhrec_response):
    """Test getting budget card suggestions."""
    mock_session = AsyncMock()
    mock_session.get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_edhrec_response)
    mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_session

    budget_cards = await mtg_handler.get_budget_suggestions('Test Commander', 100.0)

    assert len(budget_cards) == 2
    assert budget_cards[0]['name'] == 'Budget Card 1'
    assert budget_cards[0]['price'] == 5.00
    assert budget_cards[0]['synergy'] == 0.6

@pytest.mark.asyncio
async def test_format_name_for_edhrec(mtg_handler):
    """Test formatting card names for EDHREC URLs."""
    test_cases = [
        ('Atraxa, Praetors\' Voice', 'atraxa-praetors-voice'),
        ('Sol Ring', 'sol-ring'),
        ('Counterspell', 'counterspell'),
        ('Edgar Markov', 'edgar-markov')
    ]
    
    for input_name, expected in test_cases:
        formatted = mtg_handler._format_name_for_edhrec(input_name)
        assert formatted == expected

@pytest.mark.asyncio
async def test_http_session_management(mtg_handler, mock_aiohttp_session):
    """Test proper HTTP session management."""
    async with mtg_handler as handler:
        await handler.get_commander_info('Test Commander')
    
    mock_aiohttp_session.close.assert_called_once()

@pytest.mark.asyncio
async def test_rate_limiting(mtg_handler, mock_aiohttp_session, mock_scryfall_response):
    """Test rate limiting between API calls."""
    mock_session = AsyncMock()
    mock_session.get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_scryfall_response)
    mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_session

    # Make multiple requests in quick succession
    await mtg_handler.get_commander_info('Test Commander 1')
    await mtg_handler.get_commander_info('Test Commander 2')
    await mtg_handler.get_commander_info('Test Commander 3')

    # Verify that get was called the correct number of times
    assert mock_aiohttp_session.get.call_count == 3 

@pytest.mark.asyncio
async def test_malicious_input_handling(mtg_handler, mock_aiohttp_session):
    """Test handling of malicious input in card names."""
    malicious_inputs = [
        "'; DROP TABLE cards; --",
        "../../../etc/passwd",
        "<script>alert('xss')</script>",
        "Test Commander' OR '1'='1",
        "Test Commander; rm -rf /",
        "Test Commander && cat /etc/passwd"
    ]
    
    for malicious_input in malicious_inputs:
        # Should not raise any exceptions
        await mtg_handler.get_commander_info(malicious_input)
        
        # Verify the input was properly encoded in the URL
        call_args = mock_aiohttp_session.get.call_args[0][0]
        encoded_input = urllib.parse.quote(malicious_input)
        assert encoded_input in call_args

@pytest.mark.asyncio
async def test_rate_limiting_exhaustion(mtg_handler, mock_aiohttp_session, mock_scryfall_response):
    """Test rate limiting exhaustion and backoff behavior."""
    mock_session = AsyncMock()
    mock_session.get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_scryfall_response)
    mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_session

    # Simulate rapid requests
    for _ in range(100):  # Exceed normal rate limit
        await mtg_handler.get_commander_info('Test Commander')
    
    # Verify that requests were properly spaced
    call_times = [call[1]['timeout'] for call in mock_aiohttp_session.get.call_args_list]
    assert all(timeout >= 0.1 for timeout in call_times)  # Minimum delay between requests

@pytest.mark.asyncio
async def test_error_message_sanitization(mtg_handler, mock_aiohttp_session):
    """Test that error messages don't leak sensitive information."""
    # Simulate various error scenarios
    error_scenarios = [
        (aiohttp.ClientError("Internal server error: API key invalid"), "API request failed"),
        (aiohttp.ClientError("Database error: connection refused"), "API request failed"),
        (aiohttp.ClientError("Authentication failed: invalid credentials"), "API request failed")
    ]
    
    for error, expected_message in error_scenarios:
        mock_aiohttp_session.get.side_effect = error
        with pytest.raises(aiohttp.ClientError) as exc_info:
            await mtg_handler.get_commander_info('Test Commander')
        assert str(exc_info.value) == expected_message

@pytest.mark.asyncio
async def test_session_timeout(mtg_handler, mock_aiohttp_session):
    """Test session timeout handling."""
    mock_aiohttp_session.get.side_effect = aiohttp.ClientError("Timeout")
    
    async with mtg_handler as handler:
        with pytest.raises(aiohttp.ClientError):
            await handler.get_commander_info('Test Commander')
    
    # Verify session was properly closed
    mock_aiohttp_session.close.assert_called_once()

@pytest.mark.asyncio
async def test_url_injection_prevention(mtg_handler, mock_aiohttp_session):
    """Test prevention of URL injection attacks."""
    injection_attempts = [
        "Test Commander?api_key=123",
        "Test Commander&redirect=http://malicious.com",
        "Test Commander#<script>alert(1)</script>",
        "Test Commander/../../../etc/passwd"
    ]
    
    for attempt in injection_attempts:
        await mtg_handler.get_commander_info(attempt)
        call_args = mock_aiohttp_session.get.call_args[0][0]
        # Verify the URL is properly encoded and doesn't contain the raw injection
        assert attempt not in call_args
        assert urllib.parse.quote(attempt) in call_args

@pytest.mark.asyncio
async def test_concurrent_request_handling(mtg_handler, mock_aiohttp_session, mock_scryfall_response):
    """Test handling of concurrent requests to prevent race conditions."""
    import asyncio
    
    mock_session = AsyncMock()
    mock_session.get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_scryfall_response)
    mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_session
    
    # Simulate multiple concurrent requests
    async def make_request():
        return await mtg_handler.get_commander_info('Test Commander')
    
    # Make 10 concurrent requests
    tasks = [make_request() for _ in range(10)]
    results = await asyncio.gather(*tasks)
    
    # Verify all requests were handled properly
    assert len(results) == 10
    assert all(result['name'] == 'Test Commander' for result in results)
    
    # Verify rate limiting was maintained
    call_times = [call[1]['timeout'] for call in mock_aiohttp_session.get.call_args_list]
    assert all(timeout >= 0.1 for timeout in call_times)

@pytest.mark.asyncio
async def test_resource_cleanup(mtg_handler, mock_aiohttp_session):
    """Test proper cleanup of resources even when errors occur."""
    mock_aiohttp_session.get.side_effect = Exception("Test error")
    
    try:
        async with mtg_handler as handler:
            await handler.get_commander_info('Test Commander')
    except Exception:
        pass
    
    # Verify session was properly closed even after error
    mock_aiohttp_session.close.assert_called_once()
    
    # Verify no lingering connections
    assert not mock_aiohttp_session._closed 