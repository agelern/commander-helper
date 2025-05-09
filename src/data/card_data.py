import json
from pathlib import Path
from typing import Dict, List, Optional

class CardData:
    """Handles loading and querying MTG card data from local JSON file."""
    
    def __init__(self):
        """Initialize the card data handler."""
        # Get the absolute path to the reference directory
        self.base_path = Path(__file__).parent.parent.parent
        self.data_dir = self.base_path / 'reference'
        self.data_file = self.data_dir / 'oracle_cards.json'
        self.cards: Dict[str, dict] = {}
        self._load_cards()
    
    def _load_cards(self):
        """Load card data from JSON file."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle both list and dictionary formats
                if isinstance(data, dict):
                    # If it's a dictionary, use it directly
                    self.cards = {name.lower(): card for name, card in data.items()}
                elif isinstance(data, list):
                    # If it's a list, convert to dictionary
                    self.cards = {card['name'].lower(): card for card in data}
                else:
                    raise ValueError(f"Unexpected data format in {self.data_file}")
            print(f"Loaded {len(self.cards)} cards from {self.data_file}")
        except FileNotFoundError:
            print(f"Failed to load cards: Card data file not found at {self.data_file}")
            raise
        except json.JSONDecodeError:
            print(f"Failed to load cards: Invalid JSON in {self.data_file}")
            raise
        except Exception as e:
            print(f"Failed to load cards: {str(e)}")
            raise
    
    def get_card(self, name: str) -> Optional[dict]:
        """Get a card by its exact name."""
        return self.cards.get(name.lower())
    
    def search_cards(self, query: str, limit: int = 5) -> List[dict]:
        """Search for cards matching the query string."""
        query = query.lower()
        matches = []
        
        for card in self.cards.values():
            if query in card['name'].lower():
                matches.append(card)
                if len(matches) >= limit:
                    break
        
        return matches 