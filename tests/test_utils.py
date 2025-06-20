import os
import tempfile
import logging
import pytest
from src.utils import logger as logger_module
from src.utils.config import Config
from src.utils.card_utils import normalize_card_name, extract_theme_from_args, extract_card_names_from_args
from src.commands.image_utils import ImageStitcher
from unittest.mock import patch, AsyncMock

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

def test_normalize_card_name():
    assert normalize_card_name("Atraxa, Praetors' Voice") == "atraxa-praetors-voice"
    assert normalize_card_name("Najeela, the Blade-Blossom") == "najeela-the-blade-blossom"
    assert normalize_card_name("Yuriko, the Tiger's Shadow") == "yuriko-the-tigers-shadow"
    assert normalize_card_name("Card Name // Other Name") == "card-name"
    assert normalize_card_name("O'Kagachi, Vengeful Kami") == "okagachi-vengeful-kami"
    assert normalize_card_name("Tiger's Claw") == "tigers-claw"
    assert normalize_card_name("A-B-C's") == "a-b-cs"
    assert normalize_card_name('"Quoted Name"') == "quoted-name"

def test_extract_theme_from_args():
    assert extract_theme_from_args('Sol Ring, t:artifacts') == "artifacts"
    assert extract_theme_from_args('t:dragons, Sol Ring') == "dragons"
    assert extract_theme_from_args('"Sol Ring, the Great", t:ramp') == "ramp"
    assert extract_theme_from_args('Sol Ring, "Rampant Growth", t:landfall') == "landfall"
    assert extract_theme_from_args('Sol Ring, "Rampant Growth"') is None

def test_extract_card_names_from_args():
    assert extract_card_names_from_args('Sol Ring, t:artifacts') == ["Sol Ring"]
    assert extract_card_names_from_args('t:dragons, Sol Ring') == ["Sol Ring"]
    assert extract_card_names_from_args('"Sol Ring, the Great", t:ramp') == ["Sol Ring, the Great"]
    assert extract_card_names_from_args('Sol Ring, "Rampant Growth", t:landfall') == ["Sol Ring", "Rampant Growth"]
    assert extract_card_names_from_args('Sol Ring, "Rampant Growth"') == ["Sol Ring", "Rampant Growth"]

def test_image_stitcher_get_cache_path_deterministic():
    stitcher = ImageStitcher()
    urls = ["http://a.com/1.png", "http://b.com/2.png"]
    path1 = stitcher._get_cache_path(urls)
    path2 = stitcher._get_cache_path(urls)
    assert path1 == path2
    # Changing order should change path
    path3 = stitcher._get_cache_path(list(reversed(urls)))
    assert path1 != path3

def test_image_stitcher_stitch_partner_images_invalid_url_count():
    stitcher = ImageStitcher()
    # Too few URLs
    with pytest.raises(ValueError):
        import asyncio
        asyncio.run(stitcher.stitch_partner_images(["http://a.com/1.png"]))
    # Too many URLs
    with pytest.raises(ValueError):
        import asyncio
        asyncio.run(stitcher.stitch_partner_images(["a", "b", "c"]))

# Optionally, you could add a test for the happy path with mocked _download_image and file system, but this is sufficient for utility coverage. 