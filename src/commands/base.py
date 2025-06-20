"""
Base command class for the Commander Helper Bot.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any
import discord
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Command(ABC):
    """Base class for all bot commands."""
    
    def __init__(self):
        """Initialize the command."""
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the command name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Get the command description."""
        pass
    
    @property
    @abstractmethod
    def usage(self) -> str:
        """Get the command usage string."""
        pass
    
    @abstractmethod
    async def execute(self, args: str) -> Tuple[List[discord.Embed], Optional[discord.ui.View], Optional[List[discord.File]]]:
        """Execute the command.
        
        Args:
            args: The command arguments as a string.
            
        Returns:
            A tuple containing:
            - List of Discord embeds to send
            - Optional view to attach to the message
            - Optional list of files to attach
        """
        pass
    
    def validate_args(self, args: str) -> bool:
        """Validate command arguments.
        
        Args:
            args: The command arguments to validate.
            
        Returns:
            True if arguments are valid, False otherwise.
        """
        return bool(args and args.strip())
    
    def create_error_embed(self, error_message: str) -> discord.Embed:
        """Create a standardized error embed.
        
        Args:
            error_message: The error message to display.
            
        Returns:
            A Discord embed with the error message.
        """
        embed = discord.Embed(
            title="Error",
            description=error_message,
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Command: {self.name}")
        return embed
    
    def create_success_embed(self, title: str, description: str) -> discord.Embed:
        """Create a standardized success embed.
        
        Args:
            title: The embed title.
            description: The embed description.
            
        Returns:
            A Discord embed with the success message.
        """
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Command: {self.name}")
        return embed
    
    def log_command_execution(self, args: str, success: bool, error: Optional[str] = None) -> None:
        """Log command execution for monitoring and debugging.
        
        Args:
            args: The command arguments.
            success: Whether the command executed successfully.
            error: Error message if the command failed.
        """
        if success:
            self.logger.info(f"Command {self.name} executed successfully with args: {args[:100]}...")
        else:
            self.logger.error(f"Command {self.name} failed with args: {args[:100]}... Error: {error}") 