from typing import Dict, List, Optional
from collections import deque
import re

class ConversationHandler:
    def __init__(self, max_history: int = 3):
        """Initialize conversation handler."""
        self.max_history = max_history
        self.conversations = {}

    def _extract_card_name(self, text: str) -> Optional[str]:
        """Extract card name from text using regex patterns."""
        # Look for quoted card names first
        quoted = re.search(r'"([^"]+)"', text)
        if quoted:
            return quoted.group(1)
        
        # Look for card names in specific patterns
        patterns = [
            r'(?:with|for|called|build|using)\s+([A-Z][a-zA-Z\s,\']+)(?:\s|$)',
            r'(?:synergize with|meta like for)\s+([A-Z][a-zA-Z\s,\']+)(?:\s|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return None

    def _extract_budget(self, text: str) -> Optional[float]:
        """Extract budget amount from text."""
        # Look for dollar amounts
        match = re.search(r'\$(\d+(?:\.\d{2})?)', text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    def _get_conversation_history(self, channel_id: int) -> str:
        """Get formatted conversation history."""
        if channel_id not in self.conversations:
            return ""
        
        return "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in self.conversations[channel_id]
        ])

    def add_message(self, channel_id: int, role: str, content: str) -> None:
        """Add message to conversation history."""
        if channel_id not in self.conversations:
            self.conversations[channel_id] = []
        
        self.conversations[channel_id].append({
            'role': role,
            'content': content
        })
        
        # Trim history if needed
        if len(self.conversations[channel_id]) > self.max_history:
            self.conversations[channel_id] = self.conversations[channel_id][-self.max_history:]

    def process_message(self, text: str) -> Dict[str, Any]:
        """Process message and determine query type and parameters."""
        card_name = self._extract_card_name(text)
        budget = self._extract_budget(text)
        
        # Determine query type
        query_type = None
        if 'budget' in text.lower():
            query_type = 'budget'
        elif 'synergize' in text.lower() or 'synergy' in text.lower():
            query_type = 'synergy'
        elif 'meta' in text.lower():
            query_type = 'meta'
        else:
            query_type = 'brew'
        
        return {
            'type': query_type,
            'card_name': card_name,
            'budget': budget,
            'original_text': text
        }

    def clear_history(self, channel_id: int) -> None:
        """Clear conversation history for a channel."""
        self.conversations[channel_id] = [] 