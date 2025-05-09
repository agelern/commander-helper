import json
from pathlib import Path
from typing import Dict, List, Optional
import logging

class CardData:
    def __init__(self, ref_dir: str = "ref"):
        """Initialize the card data handler."""
        self.ref_dir = Path(ref_dir)
        self.oracle_cards_file = self.ref_dir / "oracle_cards.json"
        self.cards: Dict[str, Dict] = {}
        self.logger = self._setup_logger()
        self._load_cards()

    def _setup_logger(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger("CardData")
        logger.setLevel(logging.INFO)
        
        # Create console handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger

    def _load_cards(self) -> None:
        """Load card data from the JSON file."""
        try:
            if not self.oracle_cards_file.exists():
                self.logger.error("Card data file not found. Please run card_data_downloader.py first.")
                return

            with open(self.oracle_cards_file, 'r', encoding='utf-8') as f:
                cards = json.load(f)
                # Create a dictionary with card names as keys for faster lookup
                self.cards = {card['name']: card for card in cards}
                self.logger.info(f"Loaded {len(self.cards)} cards")
        except Exception as e:
            self.logger.error(f"Error loading card data: {str(e)}")

    def get_card(self, name: str) -> Optional[Dict]:
        """Get a card by name."""
        return self.cards.get(name)

    def search_cards(self, query: str) -> List[Dict]:
        """Search for cards matching the query."""
        query = query.lower()
        results = []
        
        for card in self.cards.values():
            # Search in name, type line, and oracle text
            if (query in card['name'].lower() or
                query in card['type_line'].lower() or
                query in card['oracle_text'].lower()):
                results.append(card)
        
        return results

    def get_commanders(self) -> List[Dict]:
        """Get all legendary creatures that can be commanders."""
        commanders = []
        for card in self.cards.values():
            if ('Legendary' in card['type_line'] and 
                'Creature' in card['type_line'] and
                card.get('edhrec_rank') is not None):
                commanders.append(card)
        return sorted(commanders, key=lambda x: x.get('edhrec_rank', float('inf')))

    def get_synergies(self, card_name: str) -> List[Dict]:
        """Find potential synergies for a card based on keywords and mechanics."""
        card = self.get_card(card_name)
        if not card:
            return []

        synergies = []
        card_text = card['oracle_text'].lower()
        
        # Extract keywords and mechanics from the card
        keywords = set(card.get('keywords', []))
        
        # Add mechanics based on card text
        mechanics = {
            'sacrifice': 'sacrifice',
            'exile': 'exile',
            'counter': 'counter',
            'draw': 'draw',
            'discard': 'discard',
            'graveyard': 'graveyard',
            'token': 'token',
            'counter': 'counter',
            'damage': 'damage',
            'life': 'life',
            'mana': 'mana'
        }
        
        found_mechanics = set()
        for mechanic, keyword in mechanics.items():
            if keyword in card_text:
                found_mechanics.add(mechanic)

        # Search for cards that share keywords or mechanics
        for other_card in self.cards.values():
            if other_card['name'] == card_name:
                continue

            other_text = other_card['oracle_text'].lower()
            other_keywords = set(other_card.get('keywords', []))
            
            # Check for shared keywords
            shared_keywords = keywords.intersection(other_keywords)
            
            # Check for shared mechanics
            shared_mechanics = set()
            for mechanic in found_mechanics:
                if mechanics[mechanic] in other_text:
                    shared_mechanics.add(mechanic)

            if shared_keywords or shared_mechanics:
                synergies.append({
                    'card': other_card,
                    'shared_keywords': list(shared_keywords),
                    'shared_mechanics': list(shared_mechanics)
                })

        return synergies 