import aiohttp
import asyncio
import json
from pathlib import Path
import logging
from typing import Dict, List, Optional
import time

class CardDataDownloader:
    def __init__(self, ref_dir: str = "ref"):
        """Initialize the card data downloader."""
        self.ref_dir = Path(ref_dir)
        self.ref_dir.mkdir(exist_ok=True)
        self.bulk_data_url = "https://api.scryfall.com/bulk-data"
        self.oracle_cards_file = self.ref_dir / "oracle_cards.json"
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger("CardDataDownloader")
        logger.setLevel(logging.INFO)
        
        # Create console handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger

    async def get_bulk_data_info(self, session: aiohttp.ClientSession) -> Optional[Dict]:
        """Get information about available bulk data files."""
        try:
            async with session.get(self.bulk_data_url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Find the Oracle Cards bulk data
                    for item in data.get('data', []):
                        if item.get('type') == 'oracle_cards':
                            return item
                else:
                    self.logger.error(f"Failed to get bulk data info: {response.status}")
        except Exception as e:
            self.logger.error(f"Error getting bulk data info: {str(e)}")
        return None

    async def download_bulk_data(self, session: aiohttp.ClientSession, download_url: str) -> Optional[List[Dict]]:
        """Download the bulk data file."""
        try:
            self.logger.info("Downloading bulk data...")
            async with session.get(download_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    self.logger.error(f"Failed to download bulk data: {response.status}")
        except Exception as e:
            self.logger.error(f"Error downloading bulk data: {str(e)}")
        return None

    def _format_name_for_edhrec(self, name: str) -> str:
        """Format card name for EDHREC URL."""
        specials = "àáâãäåèéêëìíîïòóôõöùúûüýÿñç "
        replacements = "aaaaaaeeeeiiiiooooouuuuyync-"
        removals = ",'.\""
        char_map = str.maketrans(specials, replacements, removals)

        formatted_name = (
            name.split('/')[0]
            .replace(' + ', ' ')
            .strip()
            .lower()
            .translate(char_map)
        )
        return formatted_name

    async def _get_edhrec_data(self, card_name: str) -> Optional[Dict]:
        """Get EDHREC data for a card."""
        try:
            formatted_name = self._format_name_for_edhrec(card_name)
            url = f"https://json.edhrec.com/pages/commanders/{formatted_name}.json"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'cardlist' in data:
                            return {
                                'rank': data.get('rank', 0),
                                'synergies': data.get('synergies', []),
                                'average_decks': data.get('average_decks', 0),
                                'potential_decks': data.get('potential_decks', 0),
                                'top_cards': [
                                    {
                                        'name': card['name'],
                                        'synergy': card.get('synergy', 0),
                                        'inclusion_rate': card.get('num_decks', 0) / card.get('potential_decks', 1) if card.get('potential_decks', 0) > 0 else 0
                                    }
                                    for card in data['cardlist'][:10]  # Get top 10 cards
                                ]
                            }
            return None
        except Exception as e:
            self.logger.error(f"Error fetching EDHREC data for {card_name}: {str(e)}")
            return None

    async def process_card_data(self, cards: List[Dict]) -> List[Dict]:
        """Process and filter card data to keep only relevant fields."""
        processed_cards = []
        
        for card in cards:
            # Skip cards that aren't legal in Commander
            if card.get('legalities', {}).get('commander') != 'legal':
                continue

            # Get EDHREC data for legendary creatures
            edhrec_data = None
            if 'Legendary' in card.get('type_line', '') and 'Creature' in card.get('type_line', ''):
                edhrec_data = await self._get_edhrec_data(card['name'])
                # Add delay to respect rate limits
                await asyncio.sleep(0.1)

            # Extract only the fields we need
            processed_card = {
                'name': card.get('name'),
                'mana_cost': card.get('mana_cost'),
                'colors': card.get('colors', []),
                'color_identity': card.get('color_identity', []),
                'type_line': card.get('type_line'),
                'oracle_text': card.get('oracle_text'),
                'power': card.get('power'),
                'toughness': card.get('toughness'),
                'loyalty': card.get('loyalty'),
                'keywords': card.get('keywords', []),
                'edhrec_rank': edhrec_data.get('rank', 0) if edhrec_data else 0,
                'edhrec_synergies': edhrec_data.get('synergies', []) if edhrec_data else [],
                'edhrec_average_decks': edhrec_data.get('average_decks', 0) if edhrec_data else 0,
                'edhrec_potential_decks': edhrec_data.get('potential_decks', 0) if edhrec_data else 0,
                'edhrec_top_cards': edhrec_data.get('top_cards', []) if edhrec_data else [],
                'prices': {
                    'usd': card.get('prices', {}).get('usd'),
                    'usd_foil': card.get('prices', {}).get('usd_foil'),
                    'eur': card.get('prices', {}).get('eur'),
                    'eur_foil': card.get('prices', {}).get('eur_foil')
                }
            }
            processed_cards.append(processed_card)
        
        return processed_cards

    def save_processed_data(self, cards: List[Dict]) -> None:
        """Save the processed card data to a JSON file."""
        try:
            with open(self.oracle_cards_file, 'w', encoding='utf-8') as f:
                json.dump(cards, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Saved {len(cards)} cards to {self.oracle_cards_file}")
        except Exception as e:
            self.logger.error(f"Error saving processed data: {str(e)}")

    async def update_card_data(self) -> None:
        """Main method to update the card data."""
        async with aiohttp.ClientSession() as session:
            # Get bulk data info
            bulk_info = await self.get_bulk_data_info(session)
            if not bulk_info:
                self.logger.error("Could not get bulk data info")
                return

            # Check if we need to update
            if self.oracle_cards_file.exists():
                file_mtime = self.oracle_cards_file.stat().st_mtime
                if file_mtime > time.time() - 86400:  # 24 hours
                    self.logger.info("Card data is up to date")
                    return

            # Download and process the data
            cards = await self.download_bulk_data(session, bulk_info['download_uri'])
            if cards:
                processed_cards = self.process_card_data(cards)
                self.save_processed_data(processed_cards)

async def main():
    """Main entry point."""
    downloader = CardDataDownloader()
    await downloader.update_card_data()

if __name__ == "__main__":
    asyncio.run(main()) 