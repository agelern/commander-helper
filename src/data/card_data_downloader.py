import json
import asyncio
import aiohttp
import unicodedata
from pathlib import Path
from typing import Optional, TypedDict, Any
from datetime import datetime


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


class CardDataDownloader:
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

    async def _download_cards(self, url: str) -> list[Card]:
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
        nkfd = unicodedata.normalize('NFKD', name)

        # Handle one special case, the Æ and æ ligature which should be replaced with ae
        if 'æ' in nkfd or 'Æ' in nkfd:
            nkfd = nkfd.replace("æ", "ae").replace("Æ", "ae")

        return (
            nkfd.encode("ascii", "ignore")
            .decode("utf-8")
            .replace(" ", "-")
            .replace(",", "")
            .replace("'", "")
            .lower()
        )

    async def _get_edhrec_data(
        self, session: aiohttp.ClientSession, card_name: str
    ) -> Optional[dict[str, Any]]:
        """Get EDHREC data for a card."""
        try:
            formatted_name = self._format_name_for_edhrec(card_name)
            url = f"{self.EDHREC_BASE_URL}/{formatted_name}.json"

            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    data_dictionary = data["container"]["json_dict"]
                    if data_dictionary["cardlists"]:
                        return {
                            "synergies": data_dictionary["cardlists"][1],
                            "potential_decks": data_dictionary["card"].get(
                                "potential_decks", 0
                            ),
                        }
            return None
        except Exception as e:
            print(f"Error fetching EDHREC data for {card_name}: {e}")
            return None

    def _process_cards(self, cards: list[Card]) -> dict[str, Card]:
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

    def _is_commander(self, card: Card) -> bool:
        """Check if a card can be a commander."""
        # Check if card is legal in commander
        if card.get('legalities', {}).get('commander') != 'legal':
            return False

        type_line = card.get('type_line', '').lower()
        oracle_text = card.get('oracle_text', '').lower()

        # Handles legendary creatures and any card with the special text:
        # "This card can be your commander"
        if ("legendary" in type_line and "creature" in type_line) or (
            "can be your commander" in oracle_text
        ):
            return True

        return False

    def _get_commander_type(self, card: Card) -> None:
        """Check if a commander is a vanilla commander, a partner commander, a partner with commander, a background commander, a doctor's companion commander, or a friends forever commander."""

        oracle = card.get("oracle_text", "").lower()
        type_line = card.get("type_line", "").lower()

        match oracle:
            case _ if "background" in type_line:
                self.BACKGROUNDS.append(card["name"])
            case _ if "time lord doctor" in type_line:
                self.DOCTORS_COMMANDERS.append(card["name"])
            case _ if "partner" in oracle:
                self.PARTNERS.append(card["name"])
            case _ if "choose a background" in oracle:
                self.BACKGROUND_COMMANDERS.append(card["name"])
            case _ if "doctor's companion" in oracle:
                self.DOCTORS_COMPANIONS.append(card["name"])
            case _ if "friends forever" in oracle:
                self.FRIENDS_FOREVER.append(card["name"])
            case _:
                return None

    def _handle_partner_with_commander(self, card: Card) -> dict[str, str]:
        """Handle commanders that partner with another card."""
        # Full name of the commander will be the name of the card + the name of the partner
        oracle_text = card.get("oracle_text", "").lower()
        return {"name": (oracle_text.split("partner with")[1].split(".")[0].strip())}

    def _handle_background_commander(self, card: Card) -> dict[str, str | list[str]]:
        """Handle commanders that have a background."""
        # Since the background is multiple cards, we are returning a Dictionary with the name of a Commander + a list of all the backgrounds, which are cards with the type "background"
        return {"name": card["name"], "backgrounds": list(self.BACKGROUNDS)}

    def _handle_doctor_companion_commander(
        self, card: Card
    ) -> dict[str, str | list[str]]:
        """Handle commanders that are a doctor's companion."""
        # Since the doctor's companion is multiple cards, we are returning a Dictionary with the name of a Commander + a list of all the doctor's companions, which are cards with the type "doctor's companion"
        return {
            "name": card["name"],
            "doctor_companions": list(self.DOCTORS_COMPANIONS),
        }

    def _handle_friends_forever_commander(
        self, card: Card
    ) -> dict[str, str | list[str]]:
        """Handle commanders that are a friends forever."""
        # Since the friends forever is multiple cards, we are returning a Dictionary with the name of a Commander + a list of all the friends forever, which are cards with the type "friends forever"
        return {
            "name": card["name"],
            "friends_forever": [
                friend for friend in self.FRIENDS_FOREVER if friend != card["name"]
            ],
        }

    def _handle_partner_commander(self, card: Card) -> dict[str, str | list[str]]:
        """Handle commanders that are a partner."""
        # Since the partner is multiple cards, we are returning a Dictionary with the name of a Commander + a list of all the partners, which are cards with the type "partner"
        return {
            "name": card["name"],
            "partners": [
                partner for partner in self.PARTNERS if partner != card["name"]
            ],
        }

    def _get_commander_name(self, card: Card) -> str:
        """Get the formatted commander name for EDHREC lookup."""
        name = card['name']

        # Handle "partner with" commanders
        if 'all_parts' in card:
            for part in card['all_parts']:
                if (part['object'] == 'related_card' and
                    part['name'] != name and
                    'Legendary' in part['type_line']):
                    return f"{name}-{part['name']}"

        # Handle other partner-type commanders
        oracle_text = card.get('oracle_text', '').lower()
        if any(keyword in oracle_text for keyword in ['partner', 'choose a background', 'friends forever', "doctor's companion"]):
            # For these types, we'll need to handle the partner lookup separately
            # as it requires finding the matching partner card
            return name

        return name

    async def _enrich_with_edhrec_data(self, cards: dict[str, Card]) -> dict[str, Card]:
        """Enrich card data with EDHREC information."""
        # Count total commanders first
        total_commanders = sum(bool(self._is_commander(card))
                           for card in cards.values())
        processed = 0

        print(f"\nEnriching {total_commanders} commanders with EDHREC data...")

        async with aiohttp.ClientSession() as session:
            for card in cards.values():
                if self._is_commander(card):
                    commander_name = self._get_commander_name(card)
                    edhrec_data = await self._get_edhrec_data(session, commander_name)
                    if edhrec_data:
                        card['edhrec_data'] = edhrec_data
                    else:
                        print(f"Failed to fetch EDHREC data for {commander_name}")

                    processed += 1
                    percentage = (processed / total_commanders) * 100
                    print(f"\rProgress: {processed}/{total_commanders} commanders processed ({percentage:.1f}%)", end="")

                    # Add delay to respect rate limits
                    await asyncio.sleep(0.001)

        print("\nEDHREC data enrichment complete!")
        return cards

    def _save_cards(self, cards: dict[str, Card]):
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
        cards: list[Card] = await self._download_cards(url)
        if not cards:
            print("Failed to download card data")
            return

        print("Processing cards...")
        processed = self._process_cards(cards)

        processed: dict[str, Card] = await self._enrich_with_edhrec_data(processed)

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
