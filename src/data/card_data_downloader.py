import json
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class CardDataDownloader:
    """Downloads and processes MTG card data from Scryfall."""
    
    SCRYFALL_BULK_API = "https://api.scryfall.com/bulk-data"
    ORACLE_CARDS = "oracle_cards"
    EDHREC_BASE_URL = "https://json.edhrec.com/pages/commanders"
    
    def __init__(self):
        """Initialize the downloader."""
        # Get the absolute path to the reference directory
        self.base_path = Path(__file__).parent.parent.parent
        self.data_dir = self.base_path / 'reference'
        self.data_dir.mkdir(exist_ok=True)
        self.data_file = self.data_dir / 'oracle_cards.json'
        self.last_download_file = self.data_dir / 'last_download.json'
    
    def _update_last_download(self):
        """Update the last download timestamp."""
        try:
            timestamp = datetime.now().isoformat()
            with open(self.last_download_file, 'w', encoding='utf-8') as f:
                json.dump({'last_download': timestamp}, f, indent=2)
            print(f"Updated last download timestamp to {timestamp}")
        except Exception as e:
            print(f"Error updating last download timestamp: {e}")
    
    async def _get_bulk_data_url(self) -> Optional[str]:
        """Get the download URL for oracle cards bulk data."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.SCRYFALL_BULK_API) as response:
                    if response.status == 200:
                        data = await response.json()
                        for item in data['data']:
                            if item['type'] == self.ORACLE_CARDS:
                                return item['download_uri']
            except Exception as e:
                print(f"Error getting bulk data URL: {e}")
        return None
    
    async def _download_cards(self, url: str) -> List[Dict]:
        """Download and process card data from Scryfall."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
            except Exception as e:
                print(f"Error downloading card data: {e}")
        return []
    
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

    async def _get_edhrec_data(self, session: aiohttp.ClientSession, card_name: str) -> Optional[Dict]:
        """Get EDHREC data for a card."""
        try:
            formatted_name = self._format_name_for_edhrec(card_name)
            url = f"{self.EDHREC_BASE_URL}/{formatted_name}.json"
            
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
            print(f"Error fetching EDHREC data for {card_name}: {e}")
            return None

    def _process_cards(self, cards: List[Dict]) -> Dict[str, Dict]:
        """Process downloaded cards into a name-indexed dictionary."""
        processed = {}
        for card in cards:
            # Skip art cards
            if card.get('layout') == 'art_series':
                continue
                
            # Use the first face for double-faced cards
            if 'card_faces' in card:
                card = card['card_faces'][0]
            
            # Store the card with its name as the key
            processed[card['name'].lower()] = card
        
        return processed

    def _is_commander(self, card: Dict) -> bool:
        """Check if a card can be a commander."""
        # Check if card is legal in commander
        if card.get('legalities', {}).get('commander') != 'legal':
            return False

        type_line = card.get('type_line', '').lower()
        oracle_text = card.get('oracle_text', '').lower()
        
        # Check for regular legendary creatures
        if 'legendary' in type_line and 'creature' in type_line:
            return True
            
        # Check for planeswalkers that can be commanders
        if 'legendary' in type_line and 'planeswalker' in type_line:
            if 'can be your commander' in oracle_text:
                return True
            
        # Check for partner commanders
        if 'legendary' in type_line and 'creature' in type_line:
            if 'partner' in oracle_text and 'partner with' not in oracle_text:
                return True
                
        # Check for "partner with" commanders
        if 'legendary' in type_line and 'creature' in type_line:
            if 'partner with' in oracle_text:
                return True
                
        # Check for background commanders
        if 'legendary' in type_line and 'creature' in type_line:
            if 'choose a background' in oracle_text:
                return True
                
        # Check for Friends Forever commanders
        if 'legendary' in type_line and 'creature' in type_line:
            if 'friends forever' in oracle_text:
                return True
                
        # Check for Doctor Who commanders
        if 'legendary' in type_line and 'creature' in type_line:
            if "doctor's companion" in oracle_text or 'time lord doctor' in type_line:
                return True
                
        return False

    def _get_commander_name(self, card: Dict) -> str:
        """Get the formatted commander name for EDHREC lookup."""
        name = card['name']
        
        # Handle "partner with" commanders
        if 'all_parts' in card:
            for part in card['all_parts']:
                if (part['object'] == 'related_card' and 
                    part['name'] != name and 
                    'Legendary' in part['type_line']):
                    return f"{name} + {part['name']}"
        
        # Handle other partner-type commanders
        oracle_text = card.get('oracle_text', '').lower()
        if any(keyword in oracle_text for keyword in ['partner', 'choose a background', 'friends forever', "doctor's companion"]):
            # For these types, we'll need to handle the partner lookup separately
            # as it requires finding the matching partner card
            return name
            
        return name

    async def _enrich_with_edhrec_data(self, cards: Dict[str, Dict]) -> Dict[str, Dict]:
        """Enrich card data with EDHREC information."""
        # Count total commanders first
        total_commanders = sum(1 for card in cards.values() if self._is_commander(card))
        processed = 0
        
        print(f"\nEnriching {total_commanders} commanders with EDHREC data...")
        
        async with aiohttp.ClientSession() as session:
            for name, card in cards.items():
                if self._is_commander(card):
                    commander_name = self._get_commander_name(card)
                    edhrec_data = await self._get_edhrec_data(session, commander_name)
                    if edhrec_data:
                        card['edhrec_data'] = edhrec_data
                    
                    processed += 1
                    percentage = (processed / total_commanders) * 100
                    print(f"\rProgress: {processed}/{total_commanders} commanders processed ({percentage:.1f}%)", end="")
                    
                    # Add delay to respect rate limits
                    await asyncio.sleep(0.1)
        
        print("\nEDHREC data enrichment complete!")
        return cards

    def _save_cards(self, cards: Dict[str, Dict]):
        """Save processed cards to JSON file."""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(cards, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(cards)} cards to {self.data_file}")
        except Exception as e:
            print(f"Error saving card data: {e}")
    
    def _should_update_data(self) -> bool:
        """Check if the data needs to be updated (older than 1 month)."""
        if not self.last_download_file.exists():
            return True
            
        try:
            with open(self.last_download_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                last_download = datetime.fromisoformat(data['last_download'])
                time_since_update = datetime.now() - last_download
                return time_since_update.days >= 30
        except Exception as e:
            print(f"Error checking last download time: {e}")
            return True

    async def download(self):
        """Download and process all card data."""
        if not self._should_update_data():
            print("Card data is up to date (less than 30 days old)")
            return
            
        print("Getting bulk data URL...")
        url = await self._get_bulk_data_url()
        if not url:
            print("Failed to get bulk data URL")
            return
        
        print("Downloading card data...")
        cards = await self._download_cards(url)
        if not cards:
            print("Failed to download card data")
            return
        
        print("Processing cards...")
        processed = self._process_cards(cards)
        
        processed = await self._enrich_with_edhrec_data(processed)
        
        print("Saving cards...")
        self._save_cards(processed)
        
        print("Updating last download timestamp...")
        self._update_last_download()
        
        print("Done!")

async def main():
    """Main entry point for the downloader."""
    downloader = CardDataDownloader()
    await downloader.download()

if __name__ == "__main__":
    asyncio.run(main()) 