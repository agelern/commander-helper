# Test Suite Documentation

This directory contains a comprehensive test suite for the Commander Helper Discord Bot project.

## Test Structure

```
tests/
├── conftest.py                    # Pytest configuration and shared fixtures
├── test_utils.py                  # Tests for utility modules (config, logger)
├── test_data.py                   # Tests for data modules (card_data, card_data_downloader)
├── test_commands.py               # Tests for command modules (base, card_info, image_utils)
├── test_commander_recommendation.py # Tests for commander recommendation logic
├── test_card_data_downloader.py   # Tests for card data downloader
├── test_integration.py            # Integration tests for the entire system
└── README.md                      # This file
```

## Test Categories

### 1. Unit Tests
- **Location**: Individual test files
- **Purpose**: Test individual functions and classes in isolation
- **Coverage**: Core functionality, edge cases, error handling
- **Markers**: `@pytest.mark.unit`

### 2. Integration Tests
- **Location**: `test_integration.py`
- **Purpose**: Test how components work together
- **Coverage**: End-to-end workflows, system interactions
- **Markers**: `@pytest.mark.integration`

### 3. Performance Tests
- **Location**: Various test files
- **Purpose**: Test performance characteristics
- **Coverage**: Response times, memory usage, scalability
- **Markers**: `@pytest.mark.performance`

### 4. Async Tests
- **Location**: Various test files
- **Purpose**: Test asynchronous functionality
- **Coverage**: Discord bot interactions, async commands
- **Markers**: `@pytest.mark.asyncio`

## Running Tests

### Prerequisites
```bash
pip install -r requirements.txt
```

### Basic Test Execution
```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_utils.py

# Run specific test class
python -m pytest tests/test_utils.py::TestConfig

# Run specific test method
python -m pytest tests/test_utils.py::TestConfig::test_config_default_values
```

### Using the Test Runner Script
```bash
# Run all tests
python run_tests.py

# Run only unit tests
python run_tests.py --type unit

# Run only integration tests
python run_tests.py --type integration

# Run tests with coverage
python run_tests.py --type coverage

# Run performance tests
python run_tests.py --type performance

# Skip slow tests
python run_tests.py --fast

# Verbose output
python run_tests.py --verbose
```

### Coverage Reports
```bash
# Generate coverage report
python run_tests.py --type coverage

# Generate HTML coverage report
python run_tests.py --type coverage --output html

# Generate XML coverage report
python run_tests.py --type coverage --output xml
```

## Test Configuration

### pytest.ini
- Configures test discovery and execution
- Sets up coverage reporting
- Defines custom markers
- Configures warning filters

### conftest.py
- Provides shared fixtures for all tests
- Sets up test data and mocks
- Configures test environment

## Test Fixtures

### Common Fixtures
- `mock_config`: Mock configuration object
- `mock_logger`: Mock logger instance
- `mock_card_data`: Mock card data with sample cards
- `sample_card_data`: Sample card data dictionary
- `mock_discord_interaction`: Mock Discord interaction
- `mock_discord_context`: Mock Discord context

### Specialized Fixtures
- `sample_commander_data`: Commander-specific test data
- `sample_recommendations`: Commander recommendation test data
- `mock_image_stitcher`: Mock image processing utility
- `card_name_variations`: Various card name formats for testing
- `invalid_card_names`: Invalid card names for error testing

## Test Data

### Sample Card Data
The test suite includes comprehensive sample card data covering:
- Basic artifacts (Sol Ring)
- Instants (Lightning Bolt)
- Legendary creatures (Atraxa, Praetors' Voice)
- Non-commander cards
- Illegal commander cards
- Cards with special characters
- Cards with various attributes (power/toughness, flavor text, etc.)

### Mock External Services
- Discord API interactions
- Scryfall API calls
- EDHREC API requests
- Image processing operations

## Test Coverage

### Current Coverage Areas
- ✅ Configuration management
- ✅ Logging system
- ✅ Card data loading and retrieval
- ✅ Card data downloading from APIs
- ✅ Command validation and execution
- ✅ Discord bot interactions
- ✅ Commander recommendation logic
- ✅ Image processing utilities
- ✅ Error handling and edge cases
- ✅ Performance characteristics

### Coverage Goals
- **Line Coverage**: >80%
- **Branch Coverage**: >75%
- **Function Coverage**: >90%

## Writing New Tests

### Test Naming Conventions
- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<description>`

### Test Structure
```python
def test_functionality_description(self, fixture_name):
    """Test description explaining what is being tested."""
    # Arrange
    # Set up test data and conditions
    
    # Act
    # Execute the function being tested
    
    # Assert
    # Verify the expected results
```

### Async Test Structure
```python
@pytest.mark.asyncio
async def test_async_functionality(self, fixture_name):
    """Test description for async functionality."""
    # Arrange
    # Set up test data and conditions
    
    # Act
    result = await async_function()
    
    # Assert
    assert result == expected_value
```

### Using Markers
```python
@pytest.mark.unit
def test_unit_functionality(self):
    """Unit test for isolated functionality."""
    pass

@pytest.mark.integration
def test_integration_functionality(self):
    """Integration test for component interaction."""
    pass

@pytest.mark.performance
def test_performance_characteristics(self):
    """Performance test for timing and resource usage."""
    pass

@pytest.mark.slow
def test_slow_operation(self):
    """Test that takes a long time to execute."""
    pass
```

## Mocking Guidelines

### When to Mock
- External API calls (Discord, Scryfall, EDHREC)
- File system operations
- Network requests
- Time-dependent operations
- Complex dependencies

### Mocking Patterns
```python
# Mock external API
@patch('requests.get')
def test_api_call(self, mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "value"}
    mock_get.return_value = mock_response
    
    result = function_that_calls_api()
    assert result == expected_value

# Mock async operations
@patch.object(AsyncClass, 'async_method')
async def test_async_operation(self, mock_async):
    mock_async.return_value = "mocked_result"
    
    result = await async_function()
    assert result == "mocked_result"
```

## Error Testing

### Exception Testing
```python
def test_function_raises_exception(self):
    """Test that function raises expected exception."""
    with pytest.raises(ValueError, match="expected error message"):
        function_that_should_raise_error()

def test_function_handles_exception(self):
    """Test that function handles exceptions gracefully."""
    with patch('external_library.function', side_effect=Exception("error")):
        result = function_that_handles_errors()
        assert result == fallback_value
```

## Performance Testing

### Response Time Testing
```python
@pytest.mark.performance
async def test_response_time(self):
    """Test that operation completes within acceptable time."""
    import time
    
    start_time = time.time()
    result = await async_operation()
    end_time = time.time()
    
    response_time = end_time - start_time
    assert response_time < 1.0  # Should complete within 1 second
```

### Memory Usage Testing
```python
@pytest.mark.performance
def test_memory_usage(self):
    """Test memory usage characteristics."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Perform operation
    operation_that_uses_memory()
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    assert memory_increase < 10 * 1024 * 1024  # Less than 10MB increase
```

## Continuous Integration

### GitHub Actions
The test suite is designed to work with GitHub Actions for continuous integration:
- Runs on every push and pull request
- Tests multiple Python versions
- Generates coverage reports
- Fails if coverage drops below threshold

### Local Development
For local development, use:
```bash
# Run tests before committing
python run_tests.py --type coverage

# Run specific tests during development
python -m pytest tests/test_specific_module.py -v

# Run tests with debugging
python -m pytest tests/ -v --pdb
```

## Troubleshooting

### Common Issues

#### Import Errors
- Ensure you're running tests from the project root
- Check that all dependencies are installed
- Verify Python path includes the project directory

#### Async Test Failures
- Use `@pytest.mark.asyncio` for async tests
- Ensure proper async/await syntax
- Mock async operations correctly

#### Coverage Issues
- Check that new code is being tested
- Ensure test files are properly named
- Verify test discovery is working

#### Performance Test Failures
- Check system resources during testing
- Adjust timing thresholds if needed
- Consider running performance tests in isolation

### Debugging Tests
```bash
# Run with debugger
python -m pytest tests/ --pdb

# Run with print statements
python -m pytest tests/ -s

# Run with maximum verbosity
python -m pytest tests/ -vvv

# Run specific failing test
python -m pytest tests/test_file.py::test_method -v -s
```

## Contributing

When adding new features or fixing bugs:
1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Maintain or improve coverage
4. Update this documentation if needed
5. Run the full test suite before submitting

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Python unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html) 