"""
Card data manager for the Commander Helper Bot.
Handles downloading, enrichment, and management of MTG card data.
"""
import json
import asyncio
import aiohttp
import unicodedata
import re
from pathlib import Path
from typing import Optional, TypedDict, Any
from datetime import datetime
import logging
import sys
import argparse
from src.utils.card_utils import normalize_card_name

logger = logging.getLogger(__name__)


class CardRequiredFields(TypedDict):
    """Required fields for a card."""

    name: str
    layout: str
    type_line: str
    oracle_text: str
    legalities: dict[str, str]


class Card(CardRequiredFields, total=False):
    # Core Scryfall fields
    card_faces: list[dict[str, Any]]
    # Only present on some cards to link related parts:
    all_parts: list[dict[str, Any]]
    # Populated by your enrichment step:
    edhrec_data: dict[str, Any]


class CardDataManager:
    """Downloads and processes MTG card data from Scryfall."""

    SCRYFALL_BULK_API = "https://api.scryfall.com/bulk-data"
    ORACLE_CARDS = "oracle_cards"
    EDHREC_BASE_URL = "https://json.edhrec.com/pages/commanders"
    AVERAGE_DECK_BASE_URL = "https://json.edhrec.com/pages/average-decks"
    BACKGROUND_COMMANDERS = []
    BACKGROUNDS = []
    PARTNERS = []
    DOCTORS_COMPANIONS = []
    DOCTORS_COMMANDERS = []
    FRIENDS_FOREVER = []
    # THEME_SLUGS removed; now loaded from JSON file

    def __init__(self):
        """Initialize the downloader."""
        # Get the absolute path to the reference directory
        self.base_path = Path(__file__).parent.parent.parent
        self.data_dir = self.base_path / 'reference'
        self.data_dir.mkdir(exist_ok=True)
        self.data_file = self.data_dir / 'oracle_cards.json'
        self.last_download_file = self.data_dir / 'last_download.json'
        # EDHREC cache file
        self.edhrec_cache_file = self.data_dir / 'edhrec_cache.json'
        if self.edhrec_cache_file.exists():
            try:
                with open(self.edhrec_cache_file, 'r', encoding='utf-8') as f:
                    self.edhrec_cache = json.load(f)
            except Exception as e:
                print(f"Error loading EDHREC cache: {e}")
                self.edhrec_cache = {}
        else:
            self.edhrec_cache = {}
        # Load theme slugs from JSON file
        theme_slugs_path = self.data_dir / 'edhrec_themes' / 'theme_slugs.json'
        try:
            with open(theme_slugs_path, 'r', encoding='utf-8') as f:
                self.theme_slugs = json.load(f)
        except Exception as e:
            print(f"Error loading theme slugs from {theme_slugs_path}: {e}")
            self.theme_slugs = []

    def _save_edhrec_cache(self):
        try:
            with open(self.edhrec_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.edhrec_cache, f, indent=2, ensure_ascii=False)
            print(f"Saved EDHREC cache to {self.edhrec_cache_file}")
        except Exception as e:
            print(f"Error saving EDHREC cache: {e}")

    async def _get_edhrec_data(
        self, session: aiohttp.ClientSession, card_name: str, force_update: bool = False
    ) -> Optional[dict[str, Any]]:
        """Get EDHREC data for a card, using persistent cache."""
        try:
            formatted_name = normalize_card_name(card_name)
            # Check cache first
            if not force_update and formatted_name in self.edhrec_cache:
                return self.edhrec_cache[formatted_name]
            url = f"{self.EDHREC_BASE_URL}/{formatted_name}.json"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Handle redirect
                    if "redirect" in data:
                        redirect_path = data["redirect"]
                        redirect_url = f"https://json.edhrec.com{redirect_path}.json"
                        async with session.get(redirect_url) as redirect_response:
                            if redirect_response.status == 200:
                                data = await redirect_response.json()
                            else:
                                print(f"Failed to follow redirect for {card_name}: {redirect_url}")
                                self.edhrec_cache[formatted_name] = None
                                return None
                    try:
                        data_dictionary = data["container"]["json_dict"]
                        if "cardlists" in data_dictionary and "card" in data_dictionary:
                            synergies = data_dictionary["cardlists"][1] if len(data_dictionary["cardlists"]) > 1 else data_dictionary["cardlists"][0] if data_dictionary["cardlists"] else []
                            potential_decks = data_dictionary["card"].get("potential_decks", 0)
                            result = {
                                "synergies": synergies,
                                "potential_decks": potential_decks,
                            }
                            # Update cache
                            self.edhrec_cache[formatted_name] = result
                            return result
                        elif "card" in data_dictionary:
                            # For partner pairs and some combos, only "card" is present
                            potential_decks = data_dictionary["card"].get("potential_decks", 0)
                            result = {
                                "synergies": [],
                                "potential_decks": potential_decks,
                            }
                            self.edhrec_cache[formatted_name] = result
                            return result
                        else:
                            print(f"EDHREC data for {card_name} missing expected keys. Skipping. (Keys: {list(data_dictionary.keys())})")
                    except Exception as e:
                        print(f"Error parsing EDHREC data for {card_name}: {e}. Full response: {data}")
            # Cache negative result to avoid repeated failed lookups
            self.edhrec_cache[formatted_name] = None
            return None
        except Exception as e:
            print(f"Error fetching EDHREC data for {card_name}: {e}")
            return None

    async def _enrich_with_edhrec_data(self, cards: dict[str, Card], force_update: bool = False) -> dict[str, Card]:
        """Enrich card data with EDHREC information, using persistent cache."""
        print("Categorizing commanders...")
        # Use sets to avoid duplicates
        self.PARTNERS = set()
        self.BACKGROUND_COMMANDERS = set()
        self.BACKGROUNDS = set()
        self.DOCTORS_COMPANIONS = set()
        self.DOCTORS_COMMANDERS = set()
        self.FRIENDS_FOREVER = set()
        for card in cards.values():
            if self._is_commander(card):
                self._get_commander_type(card)
        # Build the set of all unique commander possibilities
        commander_possibilities = set()
        # 1. All single commanders
        for card in cards.values():
            if self._is_commander(card):
                commander_possibilities.add(self._get_commander_name(card))
        # 2. All unique unordered pairs of partners
        partners = list(self.PARTNERS)
        for i, partner1 in enumerate(partners):
            for partner2 in partners[i+1:]:
                pair = f"{partner1}-{partner2}" if partner1 < partner2 else f"{partner2}-{partner1}"
                commander_possibilities.add(pair)
        # 3. All background commander + background combinations
        for commander in self.BACKGROUND_COMMANDERS:
            for background in self.BACKGROUNDS:
                commander_possibilities.add(f"{commander}-{background}")
        # 4. All doctor + companion combinations
        for doctor in self.DOCTORS_COMMANDERS:
            for companion in self.DOCTORS_COMPANIONS:
                commander_possibilities.add(f"{doctor}-{companion}")
        # 5. All unique unordered pairs of friends forever
        friends = list(self.FRIENDS_FOREVER)
        for i, friend1 in enumerate(friends):
            for friend2 in friends[i+1:]:
                pair = f"{friend1}-{friend2}" if friend1 < friend2 else f"{friend2}-{friend1}"
                commander_possibilities.add(pair)
        print(f"Total unique commander possibilities to fetch: {len(commander_possibilities)}")
        processed = 0
        total_fetches = len(commander_possibilities)
        async with aiohttp.ClientSession() as session:
            for name in commander_possibilities:
                formatted_name = normalize_card_name(name)
                if not force_update and formatted_name in self.edhrec_cache:
                    processed += 1
                    percentage = (processed / total_fetches) * 100
                    print(f"\rProgress: {processed}/{total_fetches} processed ({percentage:.1f}%)", end="")
                    continue
                edhrec_data = await self._get_edhrec_data(session, name, force_update=force_update)
                # Optionally, you could store the data in the relevant cards here
                processed += 1
                percentage = (processed / total_fetches) * 100
                print(f"\rProgress: {processed}/{total_fetches} processed ({percentage:.1f}%)", end="")
                await asyncio.sleep(0.001)
        print("\nEDHREC data enrichment complete!")
        self._save_edhrec_cache()
        return cards

    def _save_cards(self, cards: dict[str, Card]):
        """Save processed cards to JSON file."""
        # Remove non-commander-legal cards before saving
        cards = self._remove_non_commander_legal_cards(cards)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(cards, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(cards)} cards to {self.data_file}")

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

    async def download_bulk_data_if_needed(self, force=False):
        """Download and process all card data if needed or if forced."""
        if not force and not self._should_update_data():
            print("Bulk card data is up to date (less than 30 days old). Skipping bulk download.")
            return
        print("Getting bulk data URL...")
        url = await self._get_bulk_data_url()
        if not url:
            print("Failed to get bulk data URL")
            return
        print("Downloading card data...")
        cards: list[Card] = await self._download_cards(url)
        if not cards:
            print("Failed to download card data")
            return
        print("Processing cards...")
        processed = self._process_cards(cards)
        print("Saving cards...")
        self._save_cards(processed)
        print("Updating last download timestamp...")
        self._update_last_download()
        print("Bulk data update complete!")

    async def enrich_with_edhrec_data_if_needed(self, force_update=False):
        """Enrich cards with EDHREC data if needed."""
        if not self.data_file.exists():
            print("No card data found. Please download bulk data first.")
            return
        print("Loading processed cards from file...")
        with open(self.data_file, 'r', encoding='utf-8') as f:
            cards = json.load(f)
        # If cards is a list, convert to dict
        if isinstance(cards, list):
            cards = {card['name']: card for card in cards if 'name' in card}
        print("Checking EDHREC data cache and enriching as needed...")
        await self._enrich_with_edhrec_data(cards, force_update=force_update)
        print("EDHREC enrichment complete!")

    async def download(self, force_update=False):
        print("=== Commander Helper Card Data Downloader ===")
        print("[Step 1] Checking bulk card data...")
        await self.download_bulk_data_if_needed(force=force_update)
        print("[Step 2] Checking EDHREC data for commanders...")
        await self.enrich_with_edhrec_data_if_needed(force_update=force_update)
        print("[Step 3] Checking EDHREC theme data...")
        theme_updated = await self.download_edhrec_theme_pages(force=force_update)
        if theme_updated:
            print("[Step 4] Enriching cards with theme usage info...")
            self.enrich_cards_with_theme_usage()
        print("=== All data checks complete. ===")

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

    async def _download_cards(self, url: str) -> list[Card]:
        """Download the oracle cards JSON from the given URL."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data  # Scryfall oracle_cards bulk is a list of card dicts
                    else:
                        print(f"Failed to download cards: HTTP {response.status}")
            except Exception as e:
                print(f"Error downloading cards: {e}")
        return []

    def _process_cards(self, cards: list[Card]) -> dict[str, Card]:
        """Convert list of cards to a dict keyed by card name."""
        return {card['name']: card for card in cards if 'name' in card}

    def _is_commander(self, card: Card) -> bool:
        """Return True if the card is a legal commander."""
        # Check for legendary creature
        if "type_line" in card and "Legendary Creature" in card["type_line"]:
            return True
        # Check for special rules text
        if "oracle_text" in card and "can be your commander" in card["oracle_text"].lower():
            return True
        return False

    def _get_commander_type(self, card: Card) -> None:
        """Categorize the commander type and populate relevant lists."""
        # Partner
        if "oracle_text" in card and "partner with" in card["oracle_text"].lower():
            if card["name"] not in self.PARTNERS:
                self.PARTNERS.add(card["name"])
        elif "oracle_text" in card and "partner" in card["oracle_text"].lower():
            if card["name"] not in self.PARTNERS:
                self.PARTNERS.add(card["name"])
        # Background
        if "oracle_text" in card and "choose a background" in card["oracle_text"].lower():
            if card["name"] not in self.BACKGROUND_COMMANDERS:
                self.BACKGROUND_COMMANDERS.add(card["name"])
        if "type_line" in card and "background" in card["type_line"].lower():
            if card["name"] not in self.BACKGROUNDS:
                self.BACKGROUNDS.add(card["name"])
        # Doctor's companion (for Universes Beyond: Doctor Who)
        if "oracle_text" in card and "doctor's companion" in card["oracle_text"].lower():
            if card["name"] not in self.DOCTORS_COMPANIONS:
                self.DOCTORS_COMPANIONS.add(card["name"])
        if "oracle_text" in card and "time lord" in card["oracle_text"].lower():
            if card["name"] not in self.DOCTORS_COMMANDERS:
                self.DOCTORS_COMMANDERS.add(card["name"])
        # Friends forever
        if "oracle_text" in card and "friends forever" in card["oracle_text"].lower():
            if card["name"] not in self.FRIENDS_FOREVER:
                self.FRIENDS_FOREVER.add(card["name"])

    def _get_commander_name(self, card: Card) -> str:
        """Return the correct name for a commander card (handles double-faced, etc)."""
        # For double-faced or split cards, use only the front face name
        if "name" in card:
            return card["name"].split(" // ")[0]
        # Fallback
        return str(card)

    def _update_last_download(self) -> None:
        """Update the last_download.json file with the current timestamp."""
        try:
            with open(self.last_download_file, 'w', encoding='utf-8') as f:
                json.dump({"last_download": datetime.now().isoformat()}, f, indent=2)
            print(f"Updated last download timestamp at {self.last_download_file}")
        except Exception as e:
            print(f"Error updating last download timestamp: {e}")

    def _theme_data_dir(self):
        return self.base_path / 'reference' / 'edhrec_themes'

    def _theme_last_download_file(self):
        return self._theme_data_dir() / 'last_download.json'

    def _should_update_theme_data(self) -> bool:
        """Check if the theme data needs to be updated (older than 30 days or missing)."""
        last_file = self._theme_last_download_file()
        if not last_file.exists():
            return True
        try:
            with open(last_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                last_download = datetime.fromisoformat(data['last_download'])
                time_since_update = datetime.now() - last_download
                return time_since_update.days >= 30
        except Exception as e:
            print(f"Error checking last theme download time: {e}")
            return True

    def _update_last_theme_download(self) -> None:
        """Update the last_download.json file for theme data with the current timestamp."""
        last_file = self._theme_last_download_file()
        try:
            with open(last_file, 'w', encoding='utf-8') as f:
                json.dump({"last_download": datetime.now().isoformat()}, f, indent=2)
            print(f"Updated last theme download timestamp at {last_file}")
        except Exception as e:
            print(f"Error updating last theme download timestamp: {e}")

    async def download_edhrec_theme_pages(self, theme_slugs: list[str] = None, force: bool = False) -> bool:
        """Download all EDHREC theme JSON pages for the given slugs, if out of date or if forced. Returns True if updated."""
        if theme_slugs is None:
            theme_slugs = self.theme_slugs
        theme_dir = self._theme_data_dir()
        theme_dir.mkdir(parents=True, exist_ok=True)
        if not force and not self._should_update_theme_data():
            print("Theme data is up to date (less than 30 days old). Skipping theme download.")
            return False
        headers = {'User-Agent': 'CommanderHelperBot/1.0'}
        success, fail = 0, 0
        async with aiohttp.ClientSession(headers=headers) as session:
            for idx, slug in enumerate(theme_slugs, 1):
                url = f'https://json.edhrec.com/pages/tags/{slug}.json'
                out_path = theme_dir / f'{slug}.json'
                print(f"[Theme {idx}/{len(theme_slugs)}] Downloading {slug}...")
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            with open(out_path, 'w', encoding='utf-8') as f:
                                json.dump(data, f, indent=2, ensure_ascii=False)
                            print(f"Saved {slug}.json")
                            success += 1
                        else:
                            print(f"Failed to download {slug}: HTTP {response.status}")
                            fail += 1
                except Exception as e:
                    print(f"Error downloading {slug}: {e}")
                    fail += 1
                await asyncio.sleep(1)
        self._update_last_theme_download()
        print(f"All EDHREC theme pages downloaded. Success: {success}, Failed: {fail}")
        return True

    def enrich_cards_with_theme_usage(self):
        """Enrich each card in oracle_cards.json with a 'used_in' key listing all theme slugs referencing it."""
        import glob
        theme_dir = self._theme_data_dir()
        theme_files = [f for f in theme_dir.glob('*.json') if f.name != 'last_download.json']
        # Build mapping: card name (case-insensitive) -> set of theme slugs
        card_to_themes = {}
        for theme_file in theme_files:
            slug = theme_file.stem
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                cardlists = data.get('container', {}).get('json_dict', {}).get('cardlists', [])
                for cardlist in cardlists:
                    for cardview in cardlist.get('cardviews', []):
                        # Some cardviews are commanders with 'names' (partner pairs), some are single cards
                        if 'names' in cardview:
                            for name in cardview['names']:
                                card_to_themes.setdefault(name.lower(), set()).add(slug)
                        elif 'name' in cardview:
                            card_to_themes.setdefault(cardview['name'].lower(), set()).add(slug)
            except Exception as e:
                print(f"Error processing {theme_file}: {e}")
        # Load oracle_cards.json
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                cards = json.load(f)
            # Handle both dict and list formats
            if isinstance(cards, dict):
                card_items = cards.items()
            elif isinstance(cards, list):
                card_items = ((card['name'], card) for card in cards if 'name' in card)
            else:
                print("Unexpected format in oracle_cards.json")
                return
            enriched = 0
            for name, card in card_items:
                used_in = card_to_themes.get(name.lower(), set())
                if used_in:
                    card['used_in'] = sorted(used_in)
                    enriched += 1
            # Save back in the same format
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(cards, f, indent=2, ensure_ascii=False)
            print(f"Enriched {enriched} cards in oracle_cards.json with 'used_in' theme info.")
        except Exception as e:
            print(f"Error enriching oracle_cards.json: {e}")

    async def check_and_update(self) -> None:
        """Check if data needs to be updated and download if necessary."""
        try:
            if self._should_update_data():
                logger.info("Card data is outdated, downloading updates...")
                await self.download()
            else:
                logger.info("Card data is up to date")
        except Exception as e:
            logger.error(f"Error checking/updating card data: {e}")
            raise

    def _remove_non_commander_legal_cards(self, cards: dict[str, Card]) -> dict[str, Card]:
        """Remove any cards that are not legal in commander format."""
        filtered = {k: v for k, v in cards.items() if v.get('legalities', {}).get('commander') == 'legal'}
        removed = len(cards) - len(filtered)
        if removed > 0:
            print(f"Removed {removed} non-commander-legal cards from card data.")
        return filtered

async def main():
    """Main entry point for the downloader."""
    parser = argparse.ArgumentParser(description="Commander Helper Card Data Downloader")
    parser.add_argument('--bulk', action='store_true', help='Download and process Scryfall bulk card data')
    parser.add_argument('--edhrec', action='store_true', help='Download and enrich with EDHREC commander data')
    parser.add_argument('--themes', action='store_true', help='Download and enrich with EDHREC theme data')
    parser.add_argument('--force', action='store_true', help='Force update all data')
    args = parser.parse_args()

    downloader = CardDataManager()
    print("=== Commander Helper Card Data Downloader ===")
    if not (args.bulk or args.edhrec or args.themes):
        # Default: do everything
        args.bulk = args.edhrec = args.themes = True

    if args.bulk:
        print("[Step 1] Checking bulk card data...")
        await downloader.download_bulk_data_if_needed(force=args.force)
    if args.edhrec:
        print("[Step 2] Checking EDHREC data for commanders...")
        await downloader.enrich_with_edhrec_data_if_needed(force_update=args.force)
    if args.themes:
        print("[Step 3] Checking EDHREC theme data...")
        theme_updated = await downloader.download_edhrec_theme_pages(force=args.force)
        if theme_updated:
            print("[Step 4] Enriching cards with theme usage info...")
            downloader.enrich_cards_with_theme_usage()
    print("=== All data checks complete. ===")

if __name__ == "__main__":
    asyncio.run(main())
