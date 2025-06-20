import pytest
import os
import tempfile
import logging
from unittest.mock import patch, mock_open
from pathlib import Path

from src.utils.config import Config
from src.utils.logger import Logger


class TestConfig:
    """Test suite for Config class."""
    
    def test_config_default_values(self):
        """Test that Config has default values when no environment variables are set."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            assert config.discord_token == ""
            assert config.log_level == "INFO"
            assert config.max_command_timeout == 10.0
            assert config.card_data_path == "data"
            assert config.edhrec_themes_path == "reference/edhrec_themes"
    
    def test_config_from_environment(self):
        """Test that Config reads values from environment variables."""
        test_env = {
            "DISCORD_TOKEN": "test_token_123",
            "LOG_LEVEL": "DEBUG",
            "MAX_COMMAND_TIMEOUT": "15.5",
            "CARD_DATA_PATH": "/custom/data/path",
            "EDHREC_THEMES_PATH": "/custom/themes/path"
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            config = Config()
            assert config.discord_token == "test_token_123"
            assert config.log_level == "DEBUG"
            assert config.max_command_timeout == 15.5
            assert config.card_data_path == "/custom/data/path"
            assert config.edhrec_themes_path == "/custom/themes/path"
    
    def test_config_invalid_timeout(self):
        """Test that Config handles invalid timeout values gracefully."""
        with patch.dict(os.environ, {"MAX_COMMAND_TIMEOUT": "invalid"}, clear=True):
            config = Config()
            assert config.max_command_timeout == 10.0  # Default value
    
    def test_config_negative_timeout(self):
        """Test that Config handles negative timeout values."""
        with patch.dict(os.environ, {"MAX_COMMAND_TIMEOUT": "-5"}, clear=True):
            config = Config()
            assert config.max_command_timeout == 10.0  # Default value
    
    def test_config_zero_timeout(self):
        """Test that Config handles zero timeout values."""
        with patch.dict(os.environ, {"MAX_COMMAND_TIMEOUT": "0"}, clear=True):
            config = Config()
            assert config.max_command_timeout == 10.0  # Default value
    
    def test_config_very_large_timeout(self):
        """Test that Config handles very large timeout values."""
        with patch.dict(os.environ, {"MAX_COMMAND_TIMEOUT": "999999"}, clear=True):
            config = Config()
            assert config.max_command_timeout == 999999.0
    
    def test_config_float_timeout(self):
        """Test that Config handles float timeout values."""
        with patch.dict(os.environ, {"MAX_COMMAND_TIMEOUT": "7.5"}, clear=True):
            config = Config()
            assert config.max_command_timeout == 7.5
    
    def test_config_invalid_log_level(self):
        """Test that Config handles invalid log level values."""
        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID_LEVEL"}, clear=True):
            config = Config()
            assert config.log_level == "INFO"  # Default value
    
    def test_config_valid_log_levels(self):
        """Test that Config accepts valid log level values."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in valid_levels:
            with patch.dict(os.environ, {"LOG_LEVEL": level}, clear=True):
                config = Config()
                assert config.log_level == level
    
    def test_config_case_insensitive_log_level(self):
        """Test that Config handles case-insensitive log levels."""
        with patch.dict(os.environ, {"LOG_LEVEL": "debug"}, clear=True):
            config = Config()
            assert config.log_level == "DEBUG"
        
        with patch.dict(os.environ, {"LOG_LEVEL": "info"}, clear=True):
            config = Config()
            assert config.log_level == "INFO"
    
    def test_config_empty_strings(self):
        """Test that Config handles empty string environment variables."""
        with patch.dict(os.environ, {
            "DISCORD_TOKEN": "",
            "LOG_LEVEL": "",
            "MAX_COMMAND_TIMEOUT": "",
            "CARD_DATA_PATH": "",
            "EDHREC_THEMES_PATH": ""
        }, clear=True):
            config = Config()
            assert config.discord_token == ""
            assert config.log_level == "INFO"  # Default for invalid level
            assert config.max_command_timeout == 10.0  # Default for invalid timeout
            assert config.card_data_path == ""
            assert config.edhrec_themes_path == ""
    
    def test_config_whitespace_handling(self):
        """Test that Config handles whitespace in environment variables."""
        with patch.dict(os.environ, {
            "DISCORD_TOKEN": "  test_token  ",
            "LOG_LEVEL": "  DEBUG  ",
            "MAX_COMMAND_TIMEOUT": "  12.5  ",
            "CARD_DATA_PATH": "  /path/with/spaces  ",
            "EDHREC_THEMES_PATH": "  /themes/with/spaces  "
        }, clear=True):
            config = Config()
            assert config.discord_token == "  test_token  "  # Preserves whitespace
            assert config.log_level == "DEBUG"  # Strips whitespace for validation
            assert config.max_command_timeout == 12.5
            assert config.card_data_path == "  /path/with/spaces  "
            assert config.edhrec_themes_path == "  /themes/with/spaces  "


class TestLogger:
    """Test suite for Logger class."""
    
    def test_logger_initialization(self):
        """Test that Logger initializes correctly with default settings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = Logger("test_logger", log_file)
            
            assert logger.name == "test_logger"
            assert logger.log_file == log_file
            assert logger.level == logging.INFO
    
    def test_logger_custom_level(self):
        """Test that Logger initializes with custom log level."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = Logger("test_logger", log_file, level="DEBUG")
            
            assert logger.level == logging.DEBUG
    
    def test_logger_invalid_level(self):
        """Test that Logger handles invalid log levels gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = Logger("test_logger", log_file, level="INVALID")
            
            assert logger.level == logging.INFO  # Default level
    
    def test_logger_info_logging(self):
        """Test that Logger logs info messages correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = Logger("test_logger", log_file)
            
            test_message = "Test info message"
            logger.info(test_message)
            
            # Check that the log file was created and contains the message
            assert log_file.exists()
            with open(log_file, 'r') as f:
                log_content = f.read()
                assert test_message in log_content
                assert "INFO" in log_content
    
    def test_logger_warning_logging(self):
        """Test that Logger logs warning messages correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = Logger("test_logger", log_file)
            
            test_message = "Test warning message"
            logger.warning(test_message)
            
            assert log_file.exists()
            with open(log_file, 'r') as f:
                log_content = f.read()
                assert test_message in log_content
                assert "WARNING" in log_content
    
    def test_logger_error_logging(self):
        """Test that Logger logs error messages correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = Logger("test_logger", log_file)
            
            test_message = "Test error message"
            logger.error(test_message)
            
            assert log_file.exists()
            with open(log_file, 'r') as f:
                log_content = f.read()
                assert test_message in log_content
                assert "ERROR" in log_content
    
    def test_logger_debug_logging(self):
        """Test that Logger logs debug messages when level is set to DEBUG."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = Logger("test_logger", log_file, level="DEBUG")
            
            test_message = "Test debug message"
            logger.debug(test_message)
            
            assert log_file.exists()
            with open(log_file, 'r') as f:
                log_content = f.read()
                assert test_message in log_content
                assert "DEBUG" in log_content
    
    def test_logger_debug_not_logged_at_info_level(self):
        """Test that debug messages are not logged when level is INFO."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = Logger("test_logger", log_file, level="INFO")
            
            test_message = "Test debug message"
            logger.debug(test_message)
            
            # Debug message should not be logged at INFO level
            if log_file.exists():
                with open(log_file, 'r') as f:
                    log_content = f.read()
                    assert test_message not in log_content
    
    def test_logger_multiple_messages(self):
        """Test that Logger handles multiple messages correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = Logger("test_logger", log_file)
            
            messages = [
                "First message",
                "Second message",
                "Third message"
            ]
            
            for message in messages:
                logger.info(message)
            
            assert log_file.exists()
            with open(log_file, 'r') as f:
                log_content = f.read()
                for message in messages:
                    assert message in log_content
    
    def test_logger_timestamp_format(self):
        """Test that Logger includes timestamps in log messages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = Logger("test_logger", log_file)
            
            test_message = "Test message with timestamp"
            logger.info(test_message)
            
            assert log_file.exists()
            with open(log_file, 'r') as f:
                log_content = f.read()
                # Check for timestamp format (YYYY-MM-DD HH:MM:SS)
                import re
                timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
                assert re.search(timestamp_pattern, log_content)
    
    def test_logger_file_creation(self):
        """Test that Logger creates log file if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "new_log_file.log"
            
            # File should not exist initially
            assert not log_file.exists()
            
            logger = Logger("test_logger", log_file)
            logger.info("Test message")
            
            # File should be created after logging
            assert log_file.exists()
    
    def test_logger_directory_creation(self):
        """Test that Logger creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "logs"
            log_file = log_dir / "test.log"
            
            # Directory should not exist initially
            assert not log_dir.exists()
            
            logger = Logger("test_logger", log_file)
            logger.info("Test message")
            
            # Directory and file should be created
            assert log_dir.exists()
            assert log_file.exists()
    
    def test_logger_exception_handling(self):
        """Test that Logger handles exceptions gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = Logger("test_logger", log_file)
            
            # Test with None message
            logger.info(None)
            
            # Test with empty message
            logger.info("")
            
            # Test with very long message
            long_message = "x" * 10000
            logger.info(long_message)
            
            # All should work without raising exceptions
            assert log_file.exists()
    
    def test_logger_special_characters(self):
        """Test that Logger handles special characters in messages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = Logger("test_logger", log_file)
            
            special_message = "Test message with special chars: éñç@#$%^&*()_+-=[]{}|;':\",./<>?"
            logger.info(special_message)
            
            assert log_file.exists()
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
                assert special_message in log_content
    
    def test_logger_concurrent_access(self):
        """Test that Logger handles concurrent access safely."""
        import threading
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = Logger("test_logger", log_file)
            
            def log_messages(thread_id):
                for i in range(10):
                    logger.info(f"Thread {thread_id} message {i}")
                    time.sleep(0.01)
            
            # Create multiple threads
            threads = []
            for i in range(5):
                thread = threading.Thread(target=log_messages, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Check that all messages were logged
            assert log_file.exists()
            with open(log_file, 'r') as f:
                log_content = f.read()
                for i in range(5):
                    assert f"Thread {i} message" in log_content 