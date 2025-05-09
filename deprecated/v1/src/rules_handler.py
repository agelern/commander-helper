import PyPDF2
from typing import List, Dict, Optional
import re
from pathlib import Path

class RulesHandler:
    def __init__(self, rules_pdf_path: str):
        """Initialize the rules handler with the path to the rules PDF."""
        self.rules_pdf_path = Path(rules_pdf_path)
        self.rules_text = self._load_rules()
        self.rules_sections = self._parse_sections()

    def _load_rules(self) -> str:
        """Load and extract text from the rules PDF."""
        if not self.rules_pdf_path.exists():
            raise FileNotFoundError(f"Rules PDF not found at {self.rules_pdf_path}")
        
        text = ""
        with open(self.rules_pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text

    def _parse_sections(self) -> Dict[str, str]:
        """Parse the rules text into sections based on rule numbers."""
        sections = {}
        # Look for patterns like "100.1" or "100.1a" at the start of lines
        section_pattern = r'^(\d+\.\d+[a-z]?)\s+(.+?)(?=\n\d+\.\d+[a-z]?\s+|\Z)'
        matches = re.finditer(section_pattern, self.rules_text, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            rule_number = match.group(1)
            content = match.group(2).strip()
            sections[rule_number] = content
        
        return sections

    def get_rule(self, rule_number: str) -> Optional[str]:
        """Get a specific rule by its number."""
        return self.rules_sections.get(rule_number)

    def search_rules(self, query: str) -> List[Dict[str, str]]:
        """Search through rules for relevant content."""
        results = []
        query = query.lower()
        
        for rule_number, content in self.rules_sections.items():
            if query in content.lower():
                results.append({
                    'rule_number': rule_number,
                    'content': content
                })
        
        return results

    def get_relevant_rules(self, card_text: str) -> List[Dict[str, str]]:
        """Get rules relevant to a specific card's text."""
        # Extract keywords and mechanics from card text
        keywords = self._extract_keywords(card_text)
        relevant_rules = []
        
        for keyword in keywords:
            rules = self.search_rules(keyword)
            relevant_rules.extend(rules)
        
        return relevant_rules

    def _extract_keywords(self, card_text: str) -> List[str]:
        """Extract potential keywords and mechanics from card text."""
        # Common Magic keywords and mechanics
        common_keywords = [
            'flying', 'first strike', 'double strike', 'haste', 'vigilance',
            'deathtouch', 'lifelink', 'menace', 'reach', 'trample',
            'hexproof', 'indestructible', 'protection', 'shroud',
            'flash', 'prowess', 'scry', 'surveil', 'investigate',
            'equip', 'enchant', 'sacrifice', 'exile', 'counter',
            'destroy', 'damage', 'life', 'mana', 'draw', 'discard'
        ]
        
        # Find keywords in card text
        found_keywords = []
        card_text_lower = card_text.lower()
        
        for keyword in common_keywords:
            if keyword in card_text_lower:
                found_keywords.append(keyword)
        
        return found_keywords 