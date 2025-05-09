from typing import List
import discord
from discord.ui import Button, View
from src.commands.base import Command
from src.data.card_data import CardData
from fuzzywuzzy import process
import aiohttp
from datetime import datetime

class CardSuggestionView(View):
    def __init__(self, card_data, suggestions):
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
        card = self.card_data.cards[card_name]
        
        # Create and send the card info embed
        embed = await self.card_info._format_card_info(card)
        await interaction.response.edit_message(embed=embed, view=None)

class CardInfoCommand(Command):
    """Command to get detailed information about a specific card."""
    
    MIN_MATCH_SCORE = 80  # Minimum score for a single match
    HIGH_CONFIDENCE_THRESHOLD = 95  # Score above which we automatically use the match
    MAX_SUGGESTIONS = 5   # Maximum number of suggestions to show
    
    def __init__(self, card_data):
        self.card_data = card_data
        self.session = None
    
    async def _get_rulings(self, card: dict) -> List[dict]:
        """Fetch rulings for a card from Scryfall's API."""
        if not card.get('rulings_uri'):
            return []
            
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        try:
            async with self.session.get(card['rulings_uri']) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', [])
                return []
        except Exception as e:
            print(f"Error fetching rulings: {e}")
            return []
    
    def _format_ruling(self, ruling: dict) -> str:
        """Format a single ruling with its date."""
        date = datetime.fromisoformat(ruling['published_at'].replace('Z', '+00:00'))
        formatted_date = date.strftime('%B %d, %Y')
        return f"**{formatted_date}**: {ruling['comment']}"
    
    @property
    def name(self) -> str:
        return "card"
    
    @property
    def description(self) -> str:
        return "Get detailed information about a specific card"
    
    @property
    def usage(self) -> str:
        return "!card <card name>"
    
    async def execute(self, args: str) -> tuple[List[discord.Embed], discord.ui.View | None]:
        """Execute the card info command."""
        if not args:
            return [discord.Embed(description=self.usage)], None
            
        # Try exact match first
        card = self.card_data.get_card(args)
        
        # If no exact match, try fuzzy matching
        if not card:
            # Get all card names for fuzzy matching
            card_names = list(self.card_data.cards.keys())
            
            # Find the best matches
            matches = process.extract(args, card_names, limit=self.MAX_SUGGESTIONS)
            
            # Check if we have any good matches
            good_matches = [match for match in matches if match[1] >= self.MIN_MATCH_SCORE]
            
            if good_matches:
                # If we have a high confidence match, use it
                if good_matches[0][1] >= self.HIGH_CONFIDENCE_THRESHOLD:
                    card_name, score = good_matches[0]
                    card = self.card_data.cards[card_name]
                    return [await self._format_card_info(card)], None
                
                # If we have exactly one good match, use it
                if len(good_matches) == 1:
                    card_name, score = good_matches[0]
                    card = self.card_data.cards[card_name]
                    return [await self._format_card_info(card)], None
                
                # Otherwise, show suggestions
                suggestions = []
                for card_name, score in good_matches:
                    # Properly capitalize the card name
                    formatted_name = ' '.join(word.capitalize() for word in card_name.split())
                    suggestions.append(f"• {formatted_name} ({score}%)")
                
                embed = discord.Embed(
                    title="Card Not Found",
                    description=f"Did you mean one of these cards?\n\n" + "\n".join(suggestions)
                )
                
                # Create a view with buttons for each suggestion
                view = CardSuggestionView(self.card_data, good_matches)
                return [embed], view
            else:
                return [discord.Embed(description=f"Card not found: {args}")], None
        
        return [await self._format_card_info(card)], None
    
    async def _format_card_info(self, card: dict) -> discord.Embed:
        """Format card information into a Discord embed."""
        embed = discord.Embed(title=card['name'])
        
        # Add mana cost to title if available
        if 'mana_cost' in card:
            embed.title = f"{card['name']} {card['mana_cost']}"
        
        # Add type line
        if 'type_line' in card:
            embed.description = f"*{card['type_line']}*"
        
        # Add oracle text if available
        if 'oracle_text' in card:
            embed.add_field(name="Oracle Text", value=card['oracle_text'], inline=False)
        
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
        
        # Add EDHREC data if available
        # if 'edhrec_data' in card:
        #     edhrec = card['edhrec_data']
            
        #     # Format card name for EDHREC URL
        #     formatted_name = card['name'].lower().replace(' ', '-').replace(',', '').replace("'", '')
        #     edhrec_url = f"https://edhrec.com/cards/{formatted_name}"
            
        #     # Add EDHREC link
        #     embed.add_field(name="EDHREC", value=f"[View on EDHREC]({edhrec_url})", inline=True)
            
        #     # Add rank if available
        #     if edhrec.get('rank'):
        #         embed.add_field(name="EDHREC Rank", value=f"#{edhrec['rank']}", inline=True)
            
        #     # Add deck statistics if available
        #     if edhrec.get('average_decks') or edhrec.get('potential_decks'):
        #         deck_stats = []
        #         if edhrec.get('average_decks'):
        #             deck_stats.append(f"Average Decks: {edhrec['average_decks']}")
        #         if edhrec.get('potential_decks'):
        #             deck_stats.append(f"Potential Decks: {edhrec['potential_decks']}")
        #         if deck_stats:
        #             embed.add_field(name="Deck Statistics", value="\n".join(deck_stats), inline=True)
            
        #     # Add top synergies if available
        #     if edhrec.get('top_cards'):
        #         top_cards = []
        #         for card_data in edhrec['top_cards'][:5]:  # Show top 5 synergies
        #             synergy = card_data.get('synergy', 0)
        #             inclusion = card_data.get('inclusion_rate', 0)
        #             top_cards.append(f"• {card_data['name']} (Synergy: {synergy:.2f}, Inclusion: {inclusion:.1%})")
        #         if top_cards:
        #             embed.add_field(name="Top Synergies", value="\n".join(top_cards), inline=False)
        
        # Add rulings if available
        rulings = await self._get_rulings(card)
        if rulings:
            rulings_text = "\n\n".join(self._format_ruling(ruling) for ruling in rulings)
            if len(rulings_text) > 1024:
                # Construct the Scryfall URL for the card's rulings page
                formatted_name = card['name'].lower().replace(' ', '-').replace(',', '').replace("'", '')
                scryfall_url = f"https://scryfall.com/card/{card['set']}/{card['collector_number']}#{card['set']}-rulings"
                embed.add_field(name="Rulings", value=f"[View Rulings on Scryfall]({scryfall_url})", inline=False)
            else:
                embed.add_field(name="Rulings", value=rulings_text, inline=False)
        
        # Add image if available
        if 'image_uris' in card and 'normal' in card['image_uris']:
            embed.set_image(url=card['image_uris']['normal'])
        
        return embed 