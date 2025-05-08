from typing import Dict, List, Optional
from collections import deque
import re

class ConversationHandler:
    def __init__(self, max_history: int = 5):
        self.max_history = max_history
        self.conversations: Dict[int, deque] = {}  # channel_id -> conversation history
        
    def _extract_card_name(self, text: str) -> Optional[str]:
        """Extract card names from text using common patterns."""
        # Look for card names in quotes
        quoted = re.findall(r'"([^"]*)"', text)
        if quoted:
            return quoted[0]
            
        # Look for card names after common phrases
        patterns = [
            r"(?:commander|card|deck)\s+(?:called|named|is|about)\s+([A-Za-z0-9\s,']+)",
            r"(?:build|brew|make)\s+(?:a|an)\s+(?:deck|commander)\s+(?:with|using)\s+([A-Za-z0-9\s,']+)",
            r"(?:find|get)\s+(?:synergies|suggestions)\s+(?:for|with)\s+([A-Za-z0-9\s,']+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1).strip()
        
        return None

    def _extract_budget(self, text: str) -> Optional[float]:
        """Extract budget amount from text."""
        # Look for dollar amounts
        match = re.search(r'\$(\d+(?:\.\d{1,2})?)', text)
        if match:
            return float(match.group(1))
        return None

    def _get_conversation_history(self, channel_id: int) -> str:
        """Get formatted conversation history."""
        if channel_id not in self.conversations:
            return ""
            
        history = []
        for msg in self.conversations[channel_id]:
            history.append(f"{msg['role']}: {msg['content']}")
        return "\n".join(history)

    def add_message(self, channel_id: int, role: str, content: str):
        """Add a message to the conversation history."""
        if channel_id not in self.conversations:
            self.conversations[channel_id] = deque(maxlen=self.max_history)
            
        self.conversations[channel_id].append({
            'role': role,
            'content': content
        })

    def process_message(self, text: str) -> Dict:
        """Process a message and extract relevant information."""
        card_name = self._extract_card_name(text)
        budget = self._extract_budget(text)
        
        # Determine the type of query
        query_type = None
        if any(word in text.lower() for word in ['synergy', 'synergize', 'work with']):
            query_type = 'synergy'
        elif any(word in text.lower() for word in ['budget', 'cheap', 'affordable', 'cost']):
            query_type = 'budget'
        elif any(word in text.lower() for word in ['meta', 'popular', 'trend']):
            query_type = 'meta'
        elif any(word in text.lower() for word in ['build', 'brew', 'make', 'deck']):
            query_type = 'brew'
            
        return {
            'type': query_type,
            'card_name': card_name,
            'budget': budget,
            'original_text': text
        }

    def clear_history(self, channel_id: int):
        """Clear conversation history for a channel."""
        if channel_id in self.conversations:
            self.conversations[channel_id].clear() 