import os
import json
import discord
from discord import app_commands
from discord.ext import commands
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from src.data.card_data import CardData
from src.commands.card_info import CardInfoCommand
from src.data.card_data_downloader import CardDataDownloader

class CommanderBot(commands.Bot):
    """Discord bot for Commander format assistance."""
    
    def __init__(self):
        """Initialize the bot with command prefix and intents."""
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.card_data = CardData()
        self.card_info = CardInfoCommand(self.card_data)
        self.data_dir = Path(__file__).parent.parent.parent / 'reference'
        self.last_download_file = self.data_dir / "last_download.json"
        
    async def _check_and_update_data(self):
        """Check if card data needs to be updated and download if necessary."""
        # Create data directory if it doesn't exist
        self.data_dir.mkdir(exist_ok=True)
        
        # Check if we need to download new data
        should_download = False
        
        if not self.last_download_file.exists():
            should_download = True
        else:
            try:
                with open(self.last_download_file, 'r') as f:
                    last_download = json.load(f)
                    last_date = datetime.fromisoformat(last_download['date'])
                    if datetime.now() - last_date > timedelta(days=30):
                        should_download = True
            except Exception as e:
                print(f"Error reading last download date: {e}")
                should_download = True
        
        if should_download:
            print("Downloading updated card data...")
            downloader = CardDataDownloader()
            await downloader.download()
            
            # Update last download date
            with open(self.last_download_file, 'w') as f:
                json.dump({'date': datetime.now().isoformat()}, f)
            print("Card data update complete!")
        
    async def setup_hook(self):
        """Set up the bot's commands and sync them with Discord."""
        print("Setting up bot commands...")
        
        # Check and update card data
        await self._check_and_update_data()
        
        # Register slash commands
        @self.tree.command(name="card", description="Get detailed information about a specific card")
        async def card(interaction: discord.Interaction, card_name: str):
            """Get information about a specific card."""
            await interaction.response.defer()
            embeds, view = await self.card_info.execute(card_name)
            for embed in embeds:
                if view:
                    await interaction.followup.send(embed=embed, view=view)
                else:
                    await interaction.followup.send(embed=embed)
        
        # Sync commands with Discord
        print("Syncing commands with Discord...")
        try:
            synced = await self.tree.sync()
            print(f"Successfully synced {len(synced)} commands:")
            for cmd in synced:
                print(f"- /{cmd.name}")
        except Exception as e:
            print(f"Error syncing commands: {e}")
    
    async def on_ready(self):
        """Called when the bot is ready and connected to Discord."""
        print(f"Logged in as {self.user.name} (ID: {self.user.id})")
        print("------")
        
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
        print(f"\nInvite link with correct permissions:\n{invite_link}\n")

def run_bot():
    """Run the Discord bot."""
    # Get Discord token from environment
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("No Discord token found in environment variables")
    
    # Create and run the bot
    bot = CommanderBot()
    bot.run(token) 