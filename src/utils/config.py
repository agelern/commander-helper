"""
Configuration management for the Commander Helper Bot.
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration class for the bot."""
    
    # Discord configuration
    discord_token: str
    
    # Bot configuration
    command_prefix: str = "!"
    max_command_timeout: int = 30  # seconds
    max_file_size: int = 25 * 1024 * 1024  # 25MB
    
    # Card data configuration
    data_update_interval: int = 24 * 60 * 60  # 24 hours in seconds
    max_download_retries: int = 3
    
    # Performance configuration
    max_commander_cache_size: int = 1000
    max_synergy_calculation_time: float = 8.0  # seconds
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Required environment variables
        self.discord_token = self._get_required_env("DISCORD_TOKEN")
        
        # Optional environment variables with defaults
        self.command_prefix = os.getenv("COMMAND_PREFIX", "!")
        self.max_command_timeout = int(os.getenv("MAX_COMMAND_TIMEOUT", "30"))
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", str(25 * 1024 * 1024)))
        self.data_update_interval = int(os.getenv("DATA_UPDATE_INTERVAL", str(24 * 60 * 60)))
        self.max_download_retries = int(os.getenv("MAX_DOWNLOAD_RETRIES", "3"))
        self.max_commander_cache_size = int(os.getenv("MAX_COMMANDER_CACHE_SIZE", "1000"))
        self.max_synergy_calculation_time = float(os.getenv("MAX_SYNERGY_CALCULATION_TIME", "8.0"))
    
    def _get_required_env(self, key: str) -> str:
        """Get a required environment variable."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    def validate(self) -> None:
        """Validate configuration values."""
        if not self.discord_token:
            raise ValueError("Discord token is required")
        
        if self.max_command_timeout <= 0:
            raise ValueError("Max command timeout must be positive")
        
        if self.max_file_size <= 0:
            raise ValueError("Max file size must be positive")
        
        if self.data_update_interval <= 0:
            raise ValueError("Data update interval must be positive")
        
        if self.max_download_retries < 0:
            raise ValueError("Max download retries must be non-negative")
        
        if self.max_commander_cache_size <= 0:
            raise ValueError("Max commander cache size must be positive")
        
        if self.max_synergy_calculation_time <= 0:
            raise ValueError("Max synergy calculation time must be positive") 