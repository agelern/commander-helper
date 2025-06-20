import os
import tempfile
import logging
import pytest
from src.utils import logger as logger_module
from src.utils.config import Config

def test_get_logger_returns_logger_instance():
    log = logger_module.get_logger("test_logger")
    assert isinstance(log, logging.Logger)
    assert log.name == "test_logger"

def test_setup_logging_creates_handlers(tmp_path):
    log_file = tmp_path / "test.log"
    logger_module.setup_logging(level=logging.DEBUG, log_file=log_file)
    root_logger = logging.getLogger()
    # Should have at least a console handler and a file handler
    handler_types = {type(h) for h in root_logger.handlers}
    assert logging.StreamHandler in handler_types
    assert logging.FileHandler in handler_types

def test_logger_emits_to_file(tmp_path):
    log_file = tmp_path / "test.log"
    logger_module.setup_logging(level=logging.INFO, log_file=log_file)
    log = logger_module.get_logger("emit_test")
    log.info("Hello, file logging!")
    log.error("Error message!")
    # Flush all handlers
    for handler in log.handlers:
        handler.flush()
    with open(log_file, "r") as f:
        contents = f.read()
    assert "Hello, file logging!" in contents
    assert "Error message!" in contents

def test_config_env(monkeypatch):
    monkeypatch.setenv("DISCORD_TOKEN", "abc123")
    monkeypatch.delenv("COMMAND_PREFIX", raising=False)
    config = Config()
    assert config.discord_token == "abc123"
    assert config.command_prefix == "!"
    assert config.max_command_timeout == 30
    assert config.max_file_size == 25 * 1024 * 1024
    assert config.data_update_interval == 24 * 60 * 60
    assert config.max_download_retries == 3
    assert config.max_commander_cache_size == 1000
    assert config.max_synergy_calculation_time == 8.0

def test_config_env_overrides(monkeypatch):
    monkeypatch.setenv("DISCORD_TOKEN", "abc123")
    monkeypatch.setenv("COMMAND_PREFIX", "$")
    monkeypatch.setenv("MAX_COMMAND_TIMEOUT", "99")
    monkeypatch.setenv("MAX_FILE_SIZE", "12345")
    monkeypatch.setenv("DATA_UPDATE_INTERVAL", "42")
    monkeypatch.setenv("MAX_DOWNLOAD_RETRIES", "7")
    monkeypatch.setenv("MAX_COMMANDER_CACHE_SIZE", "55")
    monkeypatch.setenv("MAX_SYNERGY_CALCULATION_TIME", "2.5")
    config = Config()
    assert config.command_prefix == "$"
    assert config.max_command_timeout == 99
    assert config.max_file_size == 12345
    assert config.data_update_interval == 42
    assert config.max_download_retries == 7
    assert config.max_commander_cache_size == 55
    assert config.max_synergy_calculation_time == 2.5

def test_config_validation(monkeypatch):
    monkeypatch.setenv("DISCORD_TOKEN", "abc123")
    config = Config()
    config.validate()  # Should not raise
    # Test invalid values
    config.max_command_timeout = 0
    with pytest.raises(ValueError):
        config.validate()
    config.max_command_timeout = 30
    config.max_file_size = 0
    with pytest.raises(ValueError):
        config.validate()
    config.max_file_size = 1
    config.data_update_interval = 0
    with pytest.raises(ValueError):
        config.validate()
    config.data_update_interval = 1
    config.max_download_retries = -1
    with pytest.raises(ValueError):
        config.validate()
    config.max_download_retries = 0
    config.max_commander_cache_size = 0
    with pytest.raises(ValueError):
        config.validate()
    config.max_commander_cache_size = 1
    config.max_synergy_calculation_time = 0
    with pytest.raises(ValueError):
        config.validate()

def test_config_missing_token(monkeypatch):
    monkeypatch.delenv("DISCORD_TOKEN", raising=False)
    with pytest.raises(ValueError):
        Config() 