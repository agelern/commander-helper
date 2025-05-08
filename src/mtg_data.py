import aiohttp
import asyncio
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote
import re

class MTGDataHandler:
    def __init__(self):
        self.scryfall_base_url = "https://api.scryfall.com"
        self.edhrec_base_url = "https://json.edhrec.com/pages/commanders"
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _format_name_for_edhrec(self, name: str) -> str:
        """Format card name for EDHREC URL."""
        specials = "àáâãäåèéêëìíîïòóôõöùúûüýÿñç "
        replacements = "aaaaaaeeeeiiiiooooouuuuyync-"
        removals = ",'.\""
        char_map = str.maketrans(specials, replacements, removals)

        return (
            name.split('/')[0]
            .replace(' + ', ' ')
            .strip()
            .lower()
            .translate(char_map)
        )

    async def get_commander_info(self, commander_name: str) -> Dict:
        """Get comprehensive information about a commander from both Scryfall and EDHREC."""
        # Get basic card info from Scryfall
        scryfall_data = await self._get_scryfall_data(commander_name)
        if not scryfall_data:
            return None

        # Get EDHREC data
        edhrec_data = await self._get_edhrec_data(commander_name)
        
        # Combine the data
        return {
            'name': scryfall_data['name'],
            'mana_cost': scryfall_data.get('mana_cost', ''),
            'colors': scryfall_data.get('colors', []),
            'color_identity': scryfall_data.get('color_identity', []),
            'type': scryfall_data.get('type_line', ''),
            'text': scryfall_data.get('oracle_text', ''),
            'edhrec_rank': edhrec_data.get('rank', 0) if edhrec_data else 0,
            'synergies': edhrec_data.get('synergies', []) if edhrec_data else [],
            'average_decks': edhrec_data.get('average_decks', 0) if edhrec_data else 0,
            'potential_decks': edhrec_data.get('potential_decks', 0) if edhrec_data else 0
        }

    async def _get_scryfall_data(self, card_name: str) -> Optional[Dict]:
        """Get card data from Scryfall API."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async with context manager.")

        url = f"{self.scryfall_base_url}/cards/named?fuzzy={quote(card_name)}"
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('legalities', {}).get('commander') == 'legal':
                        return data
                return None
        except Exception as e:
            print(f"Error fetching Scryfall data: {e}")
            return None

    async def _get_edhrec_data(self, commander_name: str) -> Optional[Dict]:
        """Get commander data from EDHREC API."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async with context manager.")

        formatted_name = self._format_name_for_edhrec(commander_name)
        url = f"{self.edhrec_base_url}/{formatted_name}.json"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'cardlist' in data:
                        return {
                            'rank': data.get('rank', 0),
                            'synergies': data.get('cardlist', []),
                            'average_decks': data.get('average_decks', 0),
                            'potential_decks': data.get('potential_decks', 0)
                        }
                return None
        except Exception as e:
            print(f"Error fetching EDHREC data: {e}")
            return None

    async def find_synergies(self, card_name: str) -> List[Dict]:
        """Find synergistic cards for a given card."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async with context manager.")

        # Get card data first
        card_data = await self._get_scryfall_data(card_name)
        if not card_data:
            return []

        # Get EDHREC data for synergies
        formatted_name = self._format_name_for_edhrec(card_name)
        url = f"{self.edhrec_base_url}/{formatted_name}.json"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'cardlist' in data:
                        return [
                            {
                                'name': card['name'],
                                'synergy_score': card.get('synergy', 0),
                                'inclusion_rate': card.get('num_decks', 0) / card.get('potential_decks', 1)
                            }
                            for card in data['cardlist']
                            if card.get('synergy', 0) >= 0.3  # Only include high synergy cards
                        ]
                return []
        except Exception as e:
            print(f"Error fetching synergies: {e}")
            return []

    async def get_budget_suggestions(self, commander_name: str, budget: float) -> List[Dict]:
        """Get budget-friendly card suggestions for a commander."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async with context manager.")

        # Get EDHREC data
        formatted_name = self._format_name_for_edhrec(commander_name)
        url = f"{self.edhrec_base_url}/{formatted_name}.json"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'cardlist' in data:
                        # Filter and sort cards by price and synergy
                        budget_cards = [
                            {
                                'name': card['name'],
                                'price': card.get('price', 0),
                                'synergy': card.get('synergy', 0),
                                'inclusion_rate': card.get('num_decks', 0) / card.get('potential_decks', 1)
                            }
                            for card in data['cardlist']
                            if card.get('price', 0) <= budget
                        ]
                        # Sort by synergy and inclusion rate
                        return sorted(
                            budget_cards,
                            key=lambda x: (x['synergy'], x['inclusion_rate']),
                            reverse=True
                        )
                return []
        except Exception as e:
            print(f"Error fetching budget suggestions: {e}")
            return [] 