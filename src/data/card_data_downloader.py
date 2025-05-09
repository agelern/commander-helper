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
    
    def _save_cards(self, cards: Dict[str, Dict]):
        """Save processed cards to JSON file."""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(cards, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(cards)} cards to {self.data_file}")
        except Exception as e:
            print(f"Error saving card data: {e}")
    
    async def download(self):
        """Download and process all card data."""
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