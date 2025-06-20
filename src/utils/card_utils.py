"""
Card-related utility functions for normalization, theme extraction, and more.
"""

import unicodedata
import re
from typing import Optional, List, Set, Dict

def normalize_card_name(name: str) -> str:
    """Normalize a card or combination name for consistent lookups and EDHREC API URLs."""
    # Use only the front face for double-faced/split cards
    name = name.split('//')[0].strip()
    # Lowercase, remove accents, replace spaces and special chars with '-', remove punctuation
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    name = name.lower()
    # Replace possessive apostrophes (e.g., tiger's -> tigers)
    name = re.sub(r"([a-z0-9])'s\b", r"\1s", name)
    # Remove remaining apostrophes
    name = re.sub(r"'", '', name)
    name = re.sub(r'[\s\"]+', '-', name)
    name = re.sub(r"[^a-z0-9\-]", '', name)
    name = re.sub(r'-+', '-', name)
    name = name.strip('-')
    return name

def extract_theme_from_args(args: str) -> Optional[str]:
    """Extract a theme from a command argument string (e.g., t:theme)."""
    # Split on commas not inside quotes
    parts = [p.strip() for p in re.findall(r'"[^"]+"|[^,]+', args) if p.strip()]
    for part in parts:
        if re.fullmatch(r't:[\w\- ]+', part, re.IGNORECASE):
            return part[2:].strip(' :').strip()
    return None

def extract_card_names_from_args(args: str) -> List[str]:
    """Extract card names from a command argument string, supporting quoted names with commas."""
    parts = [p.strip() for p in re.findall(r'"[^"]+"|[^,]+', args) if p.strip()]
    card_names = []
    for part in parts:
        if not re.fullmatch(r't:[\w\- ]+', part, re.IGNORECASE):
            # Remove quotes if present
            if part.startswith('"') and part.endswith('"'):
                card_names.append(part[1:-1])
            else:
                card_names.append(part)
    return card_names

def get_card_theme_set(card: dict) -> Set[str]:
    """Get the set of themes a card is used in, if available."""
    return set(card.get('used_in', []))
