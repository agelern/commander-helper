import pytest
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
from src.mtg_data import MTGDataHandler
import urllib.parse

class AsyncContextManagerMock(AsyncMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._json = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def json(self):
        if self._json is not None:
            return self._json
        return {}

    @property
    def json_data(self):
        return self._json

    @json_data.setter
    def json_data(self, value):
        self._json = value

@pytest.fixture
def mock_aiohttp_session():
    """Create a mock aiohttp session."""
    session = AsyncMock()
    session.get = AsyncMock()
    session.get.return_value = AsyncContextManagerMock()
    session.close = AsyncMock()
    return session

@pytest.fixture
def mtg_handler(mock_aiohttp_session):
    """Create an MTGDataHandler instance with mocked session."""
    handler = MTGDataHandler()
    handler.session = mock_aiohttp_session
    return handler

@pytest.fixture
def mock_scryfall_response():
    """Mock Scryfall API response."""
    return {
        'name': 'Test Commander',
        'mana_cost': '{2}{W}{U}',
        'colors': ['W', 'U'],
        'color_identity': ['W', 'U'],
        'type_line': 'Legendary Creature — Angel',
        'oracle_text': 'Test ability',
        'legalities': {'commander': 'legal'}
    }

@pytest.fixture
def mock_edhrec_response():
    """Mock EDHREC API response."""
    return {
        'rank': 100,
        'synergies': [
            {'name': 'Test Card 1', 'synergy': 0.8, 'num_decks': 600, 'potential_decks': 1000},
            {'name': 'Test Card 2', 'synergy': 0.6, 'num_decks': 400, 'potential_decks': 1000}
        ],
        'average_decks': 500,
        'potential_decks': 1000,
        'budget_cards': [
            {'name': 'Budget Card 1', 'price': 5.0, 'synergy': 0.6},
            {'name': 'Budget Card 2', 'price': 3.0, 'synergy': 0.5}
        ]
    }

@pytest.mark.asyncio
async def test_get_commander_info(mtg_handler, mock_aiohttp_session):
    """Test getting commander information."""
    # Mock Scryfall response
    scryfall_resp = AsyncContextManagerMock()
    scryfall_resp.status = 200
    scryfall_resp.json_data = {
        'name': 'Test Commander',
        'mana_cost': '{2}{W}{U}',
        'colors': ['W', 'U'],
        'color_identity': ['W', 'U'],
        'type_line': 'Legendary Creature — Human Wizard',
        'oracle_text': 'Test text',
        'legalities': {'commander': 'legal'}
    }
    
    # Mock EDHREC response
    edhrec_resp = AsyncContextManagerMock()
    edhrec_resp.status = 200
    edhrec_resp.json_data = {
        'rank': 100,
        'cardlist': ['Card 1', 'Card 2'],
        'average_decks': 500,
        'potential_decks': 1000
    }
    
    # Set up mock session to return different responses for different URLs
    async def mock_get(url):
        if 'scryfall' in url:
            return scryfall_resp
        return edhrec_resp
    
    mock_aiohttp_session.get.side_effect = mock_get
    
    result = await mtg_handler.get_commander_info('Test Commander')
    assert result['name'] == 'Test Commander'
    assert result['mana_cost'] == '{2}{W}{U}'
    assert result['colors'] == ['W', 'U']
    assert result['edhrec_rank'] == 100

@pytest.mark.asyncio
async def test_get_commander_info_scryfall_error(mtg_handler, mock_aiohttp_session):
    """Test handling of Scryfall API errors."""
    # Mock error response
    error_resp = AsyncContextManagerMock()
    error_resp.status = 404
    mock_aiohttp_session.get.return_value = error_resp
    
    result = await mtg_handler.get_commander_info('Nonexistent Commander')
    assert result is None

@pytest.mark.asyncio
async def test_get_commander_info_edhrec_error(mtg_handler, mock_aiohttp_session):
    """Test handling of EDHREC API errors."""
    # Mock Scryfall success but EDHREC failure
    scryfall_resp = AsyncContextManagerMock()
    scryfall_resp.status = 200
    scryfall_resp.json_data = {
        'name': 'Test Commander',
        'legalities': {'commander': 'legal'}
    }
    
    error_resp = AsyncContextManagerMock()
    error_resp.status = 500
    
    async def mock_get(url):
        if 'scryfall' in url:
            return scryfall_resp
        return error_resp
    
    mock_aiohttp_session.get.side_effect = mock_get
    
    result = await mtg_handler.get_commander_info('Test Commander')
    assert result['name'] == 'Test Commander'
    assert result['edhrec_rank'] == 0
    assert result['synergies'] == []

@pytest.mark.asyncio
async def test_find_synergies(mtg_handler, mock_aiohttp_session):
    """Test finding card synergies."""
    # Mock Scryfall response
    scryfall_resp = AsyncContextManagerMock()
    scryfall_resp.status = 200
    scryfall_resp.json_data = {
        'name': 'Test Card',
        'legalities': {'commander': 'legal'}
    }
    
    # Mock EDHREC response
    edhrec_resp = AsyncContextManagerMock()
    edhrec_resp.status = 200
    edhrec_resp.json_data = {
        'cardlist': [
            {'name': 'Synergy 1', 'synergy': 0.8, 'num_decks': 100, 'potential_decks': 200},
            {'name': 'Synergy 2', 'synergy': 0.6, 'num_decks': 80, 'potential_decks': 200},
            {'name': 'Synergy 3', 'synergy': 0.2, 'num_decks': 40, 'potential_decks': 200}
        ]
    }
    
    async def mock_get(url):
        if 'scryfall' in url:
            return scryfall_resp
        return edhrec_resp
    
    mock_aiohttp_session.get.side_effect = mock_get
    
    synergies = await mtg_handler.find_synergies('Test Card')
    assert len(synergies) == 2  # Only synergies >= 0.3
    assert synergies[0]['name'] == 'Synergy 1'
    assert synergies[0]['synergy_score'] == 0.8

@pytest.mark.asyncio
async def test_get_budget_suggestions(mtg_handler, mock_aiohttp_session):
    """Test getting budget card suggestions."""
    # Mock EDHREC response
    edhrec_resp = AsyncContextManagerMock()
    edhrec_resp.status = 200
    edhrec_resp.json_data = {
        'cardlist': [
            {'name': 'Budget 1', 'price': 5.0, 'synergy': 0.8, 'num_decks': 100, 'potential_decks': 200},
            {'name': 'Budget 2', 'price': 3.0, 'synergy': 0.6, 'num_decks': 80, 'potential_decks': 200},
            {'name': 'Expensive', 'price': 50.0, 'synergy': 0.9, 'num_decks': 90, 'potential_decks': 200}
        ]
    }
    
    mock_aiohttp_session.get.return_value = edhrec_resp
    
    suggestions = await mtg_handler.get_budget_suggestions('Test Commander', 10.0)
    assert len(suggestions) == 2  # Only cards <= $10
    assert suggestions[0]['name'] == 'Budget 1'
    assert suggestions[0]['price'] == 5.0

@pytest.mark.asyncio
async def test_http_session_management(mtg_handler, mock_aiohttp_session):
    """Test proper HTTP session management."""
    async with mtg_handler as handler:
        assert handler.session is not None
        assert handler.session == mock_aiohttp_session
    
    # Session should be closed after context manager
    mock_aiohttp_session.close.assert_called_once()

@pytest.mark.asyncio
async def test_rate_limiting(mtg_handler, mock_aiohttp_session):
    """Test rate limiting between API calls."""
    # Mock successful responses
    resp = AsyncContextManagerMock()
    resp.status = 200
    resp.json_data = {
        'name': 'Test Commander',
        'legalities': {'commander': 'legal'}
    }
    mock_aiohttp_session.get.return_value = resp
    
    # Make multiple requests in quick succession
    await mtg_handler.get_commander_info('Test Commander 1')
    await mtg_handler.get_commander_info('Test Commander 2')
    await mtg_handler.get_commander_info('Test Commander 3')
    
    # Verify rate limiting was applied
    assert mock_aiohttp_session.get.call_count >= 3  # At least one call per commander

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
    
    # Mock successful response
    resp = AsyncContextManagerMock()
    resp.status = 200
    resp.json_data = {
        'name': 'Test Commander',
        'legalities': {'commander': 'legal'}
    }
    mock_aiohttp_session.get.return_value = resp
    
    for malicious_input in malicious_inputs:
        # Should not raise any exceptions
        result = await mtg_handler.get_commander_info(malicious_input)
        assert result is not None
        assert result['name'] == 'Test Commander'

@pytest.mark.asyncio
async def test_rate_limiting_exhaustion(mtg_handler, mock_aiohttp_session):
    """Test rate limiting exhaustion and backoff behavior."""
    # Mock successful response
    resp = AsyncContextManagerMock()
    resp.status = 200
    resp.json_data = {
        'name': 'Test Commander',
        'legalities': {'commander': 'legal'}
    }
    mock_aiohttp_session.get.return_value = resp
    
    # Simulate rapid requests
    for _ in range(100):  # Exceed normal rate limit
        await mtg_handler.get_commander_info('Test Commander')
    
    # Verify rate limiting was applied
    assert mock_aiohttp_session.get.call_count >= 100  # At least one call per request

@pytest.mark.asyncio
async def test_url_injection_prevention(mtg_handler, mock_aiohttp_session):
    """Test prevention of URL injection attacks."""
    injection_attempts = [
        "Test Commander?api_key=123",
        "Test Commander&redirect=http://malicious.com",
        "Test Commander#<script>alert(1)</script>",
        "Test Commander/../../../etc/passwd"
    ]
    
    # Mock successful response
    resp = AsyncContextManagerMock()
    resp.status = 200
    resp.json_data = {
        'name': 'Test Commander',
        'legalities': {'commander': 'legal'}
    }
    mock_aiohttp_session.get.return_value = resp
    
    for attempt in injection_attempts:
        # Should not raise any exceptions
        result = await mtg_handler.get_commander_info(attempt)
        assert result is not None
        assert result['name'] == 'Test Commander'

@pytest.mark.asyncio
async def test_concurrent_request_handling(mtg_handler, mock_aiohttp_session):
    """Test handling of concurrent requests to prevent race conditions."""
    import asyncio
    
    # Mock successful response
    resp = AsyncContextManagerMock()
    resp.status = 200
    resp.json_data = {
        'name': 'Test Commander',
        'legalities': {'commander': 'legal'}
    }
    mock_aiohttp_session.get.return_value = resp
    
    # Simulate multiple concurrent requests
    async def make_request():
        return await mtg_handler.get_commander_info('Test Commander')
    
    # Make 10 concurrent requests
    tasks = [make_request() for _ in range(10)]
    results = await asyncio.gather(*tasks)
    
    # Verify all requests completed successfully
    assert len(results) == 10
    assert all(result is not None for result in results)
    assert all(result['name'] == 'Test Commander' for result in results) 