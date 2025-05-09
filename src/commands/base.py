from abc import ABC, abstractmethod
from typing import List
import discord

class Command(ABC):
    """Base class for all bot commands."""
    
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
    async def execute(self, args: str) -> tuple[List[discord.Embed], discord.ui.View | None]:
        """Execute the command.
        
        Args:
            args: The command arguments as a string.
            
        Returns:
            A tuple containing:
            - List of Discord embeds to send
            - Optional view to attach to the message
        """
        pass 