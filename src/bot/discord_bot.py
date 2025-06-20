"""
Discord bot implementation for the Commander Helper Bot.
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import logging

from src.data.card_database import CardData
from src.commands.card_info import CardInfoCommand
from src.commands.commander_recommendation import CommanderRecommendationCommand
from src.data.card_data_manager import CardDataManager
from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CommanderBot(commands.Bot):
    """Discord bot for Commander format assistance."""
    
    def __init__(self, config: Config):
        """Initialize the bot with configuration."""
        intents = discord.Intents.default()
        intents.message_content = True
        
        # Initialize with a dummy command prefix since we're only using slash commands
        # The command_prefix is required by the parent class but not used
        super().__init__(command_prefix="!", intents=intents)
        
        self.config = config
        self.card_data = CardData()
        self.card_info = CardInfoCommand(self.card_data)
        self.commander_recommendation = CommanderRecommendationCommand(self.card_data)
        self.data_dir = Path(__file__).parent.parent.parent / 'reference'
        self.last_download_file = self.data_dir / "last_download.json"
        
        logger.info("CommanderBot initialized")
    
    async def _check_and_update_data(self) -> None:
        """Check if card data needs to be updated and download if necessary."""
        try:
            # Create data directory if it doesn't exist
            self.data_dir.mkdir(exist_ok=True)
            
            # Use CardDataManager to check and update data
            downloader = CardDataManager()
            await downloader.check_and_update()
            
        except Exception as e:
            logger.error(f"Failed to check and update card data: {e}")
            # Don't raise - bot can still function with existing data
    
    async def setup_hook(self) -> None:
        """Set up the bot's commands and sync them with Discord."""
        logger.info("Setting up bot commands...")
        
        # Check and update card data
        await self._check_and_update_data()
        
        # Register slash commands
        await self._register_commands()
        
        logger.info("Bot setup complete")
    
    async def _register_commands(self) -> None:
        """Register all slash commands."""
        logger.info("Registering slash commands...")
        
        # Register /card command
        @self.tree.command(
            name="card",
            description="Get detailed information about a specific card"
        )
        async def card(interaction: discord.Interaction, card_name: str):
            """Get information about a specific card."""
            await self._handle_card_command(interaction, card_name)
        
        # Register /revedh command
        @self.tree.command(
            name="revedh",
            description="Recommend commanders based on a custom card list"
        )
        async def recommend_commander(interaction: discord.Interaction, card_list: str):
            """Recommend commanders based on a custom card list."""
            await self._handle_recommendation_command(interaction, card_list)
        
        # Sync commands with Discord
        try:
            synced = await self.tree.sync()
            logger.info(f"Successfully synced {len(synced)} commands:")
            for cmd in synced:
                logger.info(f"- /{cmd.name}")
        except Exception as e:
            logger.error(f"Error syncing commands: {e}")
            raise
    
    async def _handle_card_command(self, interaction: discord.Interaction, card_name: str) -> None:
        """Handle the /card command."""
        try:
            await interaction.response.defer()
            
            embeds, view, files = await self.card_info.execute(card_name)
            
            if not embeds:
                await interaction.followup.send("No card found with that name.")
                return
            
            # Send first embed with view and files
            await interaction.followup.send(
                embed=embeds[0],
                view=view,
                files=files
            )
            
            # Send additional embeds
            for embed in embeds[1:]:
                await interaction.followup.send(embed=embed)
                
        except discord.errors.NotFound:
            # Interaction has expired, try to send a new message
            await self._handle_expired_interaction(interaction, card_name, "card")
        except Exception as e:
            logger.error(f"Error in card command: {e}")
            await self._handle_command_error(interaction, e)
    
    async def _handle_recommendation_command(self, interaction: discord.Interaction, card_list: str) -> None:
        """Handle the /revedh command."""
        try:
            await interaction.response.defer()
            
            embeds, view, files = await self.commander_recommendation.execute(card_list)
            
            if not embeds:
                await interaction.followup.send("No commanders found for the given input.")
                return
            
            # Send first embed with view and files
            await interaction.followup.send(
                embed=embeds[0],
                view=view,
                files=files
            )
            
            # Send additional embeds
            for embed in embeds[1:]:
                await interaction.followup.send(embed=embed)
                
        except discord.errors.NotFound:
            # Interaction has expired, try to send a new message
            await self._handle_expired_interaction(interaction, card_list, "revedh")
        except Exception as e:
            logger.error(f"Error in recommendation command: {e}")
            await self._handle_command_error(interaction, e)
    
    async def _handle_expired_interaction(
        self,
        interaction: discord.Interaction,
        args: str,
        command_type: str
    ) -> None:
        """Handle expired interactions by sending a new message."""
        try:
            if command_type == "card":
                embeds, view, files = await self.card_info.execute(args)
            elif command_type == "revedh":
                embeds, view, files = await self.commander_recommendation.execute(args)
            else:
                await interaction.channel.send("Command processing failed.")
                return
            
            if embeds:
                await interaction.channel.send(
                    embed=embeds[0],
                    view=view,
                    files=files
                )
                
                for embed in embeds[1:]:
                    await interaction.channel.send(embed=embed)
            else:
                await interaction.channel.send("No results found.")
                
        except Exception as e:
            logger.error(f"Error handling expired interaction: {e}")
            await interaction.channel.send(f"Error processing command: {str(e)}")
    
    async def _handle_command_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """Handle command errors gracefully."""
        error_message = f"An error occurred while processing your command: {str(error)}"
        
        try:
            await interaction.followup.send(error_message)
        except discord.errors.NotFound:
            # Interaction has expired, send to channel
            await interaction.channel.send(error_message)
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    async def on_ready(self) -> None:
        """Called when the bot is ready and connected to Discord."""
        logger.info(f"Logged in as {self.user.name} (ID: {self.user.id})")
        logger.info("Bot is ready!")
        
        # Generate invite link with correct permissions
        invite_link = discord.utils.oauth_url(
            self.user.id,
            permissions=discord.Permissions(
                send_messages=True,
                embed_links=True,
                attach_files=True,
                read_messages=True,
                read_message_history=True
            ),
            scopes=("bot", "applications.commands")
        )
        logger.info(f"Invite link: {invite_link}")
    
    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Handle command errors."""
        logger.error(f"Command error: {error}")
        
        if isinstance(error, commands.CommandNotFound):
            # Ignore command not found errors since we only use slash commands
            return
        
        # Send error message to channel
        await ctx.send(f"An error occurred: {str(error)}")
    
    async def start(self, token: str) -> None:
        """Start the bot with proper error handling."""
        try:
            await super().start(token)
        except discord.LoginFailure:
            logger.error("Invalid Discord token provided")
            raise
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise 