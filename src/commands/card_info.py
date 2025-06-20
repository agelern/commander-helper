from typing import List, Tuple, Optional
import discord
from discord.ui import Button, View
from src.commands.base import Command
from src.data.card_data import CardData
from fuzzywuzzy import process
import aiohttp
from datetime import datetime
from .image_utils import ImageStitcher

class CardSuggestionView(View):
    def __init__(self, card_data: CardData, suggestions: List[Tuple[str, int]]):
        super().__init__(timeout=60)  # Buttons expire after 60 seconds
        self.card_data = card_data
        self.card_info = CardInfoCommand(card_data)  # Create an instance for formatting
        
        # Create a button for each suggestion
        for card_name, _ in suggestions:
            button = Button(
                label=card_name,
                style=discord.ButtonStyle.primary,
                custom_id=f"card_{card_name}"
            )
            button.callback = self.button_callback
            self.add_item(button)
    
    async def button_callback(self, interaction: discord.Interaction):
        # Get the card name from the button's custom_id
        card_name = interaction.data["custom_id"][5:]  # Remove "card_" prefix
        card = self.card_data.cards[card_name.lower()]
        
        # Create and send the card info embed
        embed, file = await self.card_info._format_card_info(card)
        if file:
            await interaction.response.edit_message(embed=embed, view=None, attachments=[file])
        else:
            await interaction.response.edit_message(embed=embed, view=None, attachments=[])

class CardInfoCommand(Command):
    """Command to get information about a specific MTG card."""
    
    MIN_MATCH_SCORE = 85
    HIGH_CONFIDENCE_THRESHOLD = 95
    MAX_SUGGESTIONS = 5
    
    def __init__(self, card_data: CardData):
        super().__init__()  # Call parent constructor
        self.card_data = card_data
        self.image_stitcher = ImageStitcher()
    
    @property
    def name(self) -> str:
        return "card"
    
    @property
    def description(self) -> str:
        return "Get detailed information about a specific card"
    
    @property
    def usage(self) -> str:
        return "/card <card name>"
    
    async def execute(self, args: str) -> Tuple[List[discord.Embed], Optional[discord.ui.View], Optional[List[discord.File]]]:
        """Execute the card info command."""
        try:
            # Validate arguments
            if not self.validate_args(args):
                embed = self.create_error_embed("No card name provided. Please provide a card name to search for.")
                self.log_command_execution(args, False, "No arguments provided")
                return [embed], None, []
            
            # Determine if we should include tokens based on the presence of "token" in args
            include_tokens = "token" in args.lower()
            
            # Try exact match first
            card = self.card_data.get_card(args, include_tokens)
            
            # If no exact match, try fuzzy matching
            if not card:
                # Get all card names for fuzzy matching
                card_names_list = list(self.card_data.cards.keys())
                
                # Find the best matches
                matches = process.extract(args, card_names_list, limit=self.MAX_SUGGESTIONS)
                
                # Check if we have any good matches
                good_matches = [match for match in matches if match[1] >= self.MIN_MATCH_SCORE]
                
                if not good_matches:
                    embed = self.create_error_embed(f"Could not find a card matching '{args}'")
                    self.log_command_execution(args, False, "No matches found")
                    return [embed], None, []
                
                # If we have multiple good matches, show suggestions
                if len(good_matches) > 1:
                    # Filter out aliases to avoid duplicate suggestions
                    unique_matches = []
                    seen_cards = set()
                    for match, score in good_matches:
                        card_obj = self.card_data.cards[match]
                        if card_obj['name'] not in seen_cards:
                            unique_matches.append((card_obj['name'], score))
                            seen_cards.add(card_obj['name'])

                    if len(unique_matches) > 1:
                        embed = discord.Embed(
                            title="Multiple Matches Found",
                            description="Please select the card you meant:",
                            color=discord.Color.blue()
                        )
                        view = CardSuggestionView(self.card_data, unique_matches)
                        self.log_command_execution(args, True)
                        return [embed], view, []

                    card = self.card_data.cards[unique_matches[0][0].lower()]
                else:
                    card = self.card_data.cards[good_matches[0][0]]

            # Format and return the card info
            embed, file = await self._format_card_info(card)
            self.log_command_execution(args, True)
            return [embed], None, [file] if file else []
            
        except Exception as e:
            self.logger.error(f"Error in card info command: {e}")
            embed = self.create_error_embed(f"An error occurred while processing your request: {str(e)}")
            self.log_command_execution(args, False, str(e))
            return [embed], None, []

    async def _format_card_info(self, card: dict) -> Tuple[discord.Embed, Optional[discord.File]]:
        """Format card information into a Discord embed."""
        embed = discord.Embed(title=card['name'])
        file = None
        
        # Add mana cost to title if available
        if 'mana_cost' in card:
            embed.title = f"{card['name']} {card['mana_cost']}"
        
        # Add type line
        if 'type_line' in card:
            embed.description = f"*{card['type_line']}*"
        
        # Handle dual-faced cards
        if 'card_faces' in card and len(card['card_faces']) == 2:
            faces = card['card_faces']
            details = ""
            face_images = []
            for face in faces:
                details += f"**{face.get('name', '')}**\n{face.get('mana_cost', '')}\n{face.get('type_line', '')}\n{face.get('oracle_text', '')}\n\n"
                if 'image_uris' in face and 'normal' in face['image_uris']:
                    face_images.append(face['image_uris']['normal'])
            
            embed.add_field(name="Card Faces", value=details, inline=False)
            
            if len(face_images) == 2:
                try:
                    stitched_path = await self.image_stitcher.stitch_partner_images(face_images)
                    filename = f"dualsided_{card['name'].replace(' ', '_')}.png"
                    file = discord.File(stitched_path, filename=filename)
                    embed.set_image(url=f"attachment://{filename}")
                except Exception as e:
                    print(f"Error stitching images for dual-faced card: {e}")
        else:
            # Single-faced card
            if 'oracle_text' in card:
                embed.add_field(name="Oracle Text", value=card['oracle_text'], inline=False)
            if 'image_uris' in card and 'normal' in card['image_uris']:
                embed.set_image(url=card['image_uris']['normal'])

        # Add power/toughness if available and meaningful
        if 'power' in card and 'toughness' in card and card['power'] is not None and card['toughness'] is not None:
            embed.add_field(name="Power/Toughness", value=f"{card['power']}/{card['toughness']}", inline=True)
        
        # Add set information if available
        set_info = []
        if 'set_name' in card:
            set_info.append(card['set_name'])
        if 'set' in card:
            set_info.append(f"({card['set'].upper()})")
        if set_info:
            embed.add_field(name="Set", value=' '.join(set_info), inline=True)
        
        # Add rarity if available
        if 'rarity' in card:
            embed.add_field(name="Rarity", value=card['rarity'].title(), inline=True)
        
        # Add rulings if available
        rulings = await self._get_rulings(card)
        if rulings:
            rulings_text = "\n\n".join(self._format_ruling(ruling) for ruling in rulings)
            if len(rulings_text) > 1024:
                # Construct the Scryfall URL for the card's rulings page
                scryfall_url = card.get('scryfall_uri', 'https://scryfall.com')
                embed.add_field(name="Rulings", value=f"[View Rulings on Scryfall]({scryfall_url})", inline=False)
            else:
                embed.add_field(name="Rulings", value=rulings_text, inline=False)
        
        return embed, file
        
    async def _get_rulings(self, card: dict) -> List[dict]:
        """Get rulings for a card from Scryfall."""
        if 'rulings_uri' in card:
            async with aiohttp.ClientSession() as session:
                async with session.get(card['rulings_uri']) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', [])
        return []
        
    def _format_ruling(self, ruling: dict) -> str:
        """Format a ruling into a string."""
        date = datetime.strptime(ruling['published_at'], '%Y-%m-%d').strftime('%b %d, %Y')
        return f"**({date})** {ruling['comment']}" 