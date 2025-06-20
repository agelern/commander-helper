"""
Card database/repository for the Commander Helper Bot.
Handles loading and querying MTG card data from local JSON file.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Set
from src.utils.logger import get_logger
from src.utils.card_utils import normalize_card_name

logger = get_logger(__name__)


class CardData:
    """Handles loading and querying MTG card data from local JSON file."""
    
    def __init__(self, data_file: Optional[Path] = None):
        """Initialize the card data handler.
        
        Args:
            data_file: Optional path to the card data file.
        """
        # Get the absolute path to the reference directory
        self.base_path = Path(__file__).parent.parent.parent
        self.data_dir = self.base_path / 'reference'
        
        if data_file:
            self.data_file = data_file
        else:
            self.data_file = self.data_dir / 'oracle_cards.json'
        
        self.cards: Dict[str, dict] = {}
        self._load_time: Optional[float] = None
        self._load_cards()
    
    def _load_cards(self) -> None:
        """Load card data from JSON file."""
        start_time = time.time()
        
        try:
            if not self.data_file.exists():
                raise FileNotFoundError(f"Card data file not found at {self.data_file}")
            
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Handle both list and dictionary formats
                if isinstance(data, dict):
                    self.cards = {name.lower(): card for name, card in data.items()}
                elif isinstance(data, list):
                    self.cards = {card['name'].lower(): card for card in data}
                else:
                    raise ValueError(f"Unexpected data format in {self.data_file}")
                
                # Add front-face aliases for double-sided cards
                self._add_card_aliases()
                
                self._load_time = time.time()
                load_duration = self._load_time - start_time
                
                logger.info(f"Loaded {len(self.cards)} cards from {self.data_file} in {load_duration:.2f}s")
                
        except FileNotFoundError as e:
            logger.error(f"Failed to load cards: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to load cards: Invalid JSON in {self.data_file}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load cards: {e}")
            raise
    
    def _add_card_aliases(self) -> None:
        """Add aliases for double-sided cards and other common variations."""
        aliases_to_add = {}
        for name, card in self.cards.items():
            # Use normalize_card_name for all aliases
            normalized = normalize_card_name(name)
            if normalized != name and normalized not in self.cards:
                aliases_to_add[normalized] = card
        self.cards.update(aliases_to_add)
        if aliases_to_add:
            logger.info(f"Added {len(aliases_to_add)} card aliases")
    
    def get_card(self, name: str, include_tokens: bool = True) -> Optional[dict]:
        """Get a card by name, optionally including or excluding tokens.
        
        Args:
            name: The card name to search for.
            include_tokens: Whether to include token cards in the search.
            
        Returns:
            The card data if found, None otherwise.
        """
        name_lower = normalize_card_name(name).lower().strip()
        
        # Direct lookup
        if name_lower in self.cards:
            card = self.cards[name_lower]
            if include_tokens or "token" not in card.get('type_line', '').lower():
                return card
        
        # Try exact match with original case
        for card in self.cards.values():
            if card['name'].lower() == name_lower:
                if include_tokens or "token" not in card.get('type_line', '').lower():
                    return card
        
        return None
    
    def search_cards(self, query: str, limit: int = 5, include_tokens: bool = True) -> List[dict]:
        """Search for cards matching the query string.
        
        Args:
            query: The search query.
            limit: Maximum number of results to return.
            include_tokens: Whether to include token cards in the search.
            
        Returns:
            List of matching cards.
        """
        query = normalize_card_name(query).lower().strip()
        matches = []
        
        for card in self.cards.values():
            # Skip tokens if not included
            if not include_tokens and "token" in card.get('type_line', '').lower():
                continue
            
            # Check if query matches card name
            if query in card['name'].lower():
                matches.append(card)
                if len(matches) >= limit:
                    break
        
        return matches
    
    def get_cards_by_type(self, card_type: str, limit: int = 50) -> List[dict]:
        """Get cards by type (e.g., 'Creature', 'Artifact', 'Legendary').
        
        Args:
            card_type: The card type to search for.
            limit: Maximum number of results to return.
            
        Returns:
            List of cards of the specified type.
        """
        card_type_lower = card_type.lower()
        matches = []
        
        for card in self.cards.values():
            type_line = card.get('type_line', '').lower()
            if card_type_lower in type_line:
                matches.append(card)
                if len(matches) >= limit:
                    break
        
        return matches
    
    def get_card_count(self) -> int:
        """Get the total number of cards loaded.
        
        Returns:
            Total number of cards.
        """
        return len(self.cards)
    
    def get_load_time(self) -> Optional[float]:
        """Get the time when the card data was last loaded.
        
        Returns:
            Timestamp of last load, or None if not loaded.
        """
        return self._load_time
    
    def reload(self) -> None:
        """Reload the card data from the file."""
        logger.info("Reloading card data...")
        self.cards.clear()
        self._load_cards()
    
    def get_all_themes(self) -> Set[str]:
        """Return a set of all unique EDHREC themes (from 'used_in' fields)."""
        themes = set()
        for card in self.cards.values():
            if 'used_in' in card:
                themes.update(card['used_in'])
        return themes
    
    def get_commander_legal_cards(self) -> list:
        """Return a list of all cards that are legal in commander."""
        return [card for card in self.cards.values() if card.get('legalities', {}).get('commander') == 'legal'] 