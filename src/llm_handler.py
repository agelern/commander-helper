import ollama
from typing import Dict, List, Optional

class LLMHandler:
    def __init__(self, model_name: str = "mistral"):
        self.model = model_name
        self.system_prompt = """You are an expert Magic: The Gathering Commander deck brewer. 
        You have extensive knowledge of card synergies, meta strategies, and budget options.
        Provide detailed, accurate, and helpful responses about deck building and card interactions.
        Always consider the commander's color identity and strategy when making recommendations."""

    async def analyze_commander(self, commander_info: Dict) -> str:
        """Analyze a commander and provide brewing suggestions"""
        prompt = f"""Based on the following commander information, provide detailed deck brewing suggestions:
        
        Commander: {commander_info['name']}
        Mana Cost: {commander_info['mana_cost']}
        Colors: {', '.join(commander_info['colors'])}
        Type: {commander_info['type']}
        Text: {commander_info['text']}
        
        Please provide:
        1. Main strategy and win conditions
        2. Key card categories to include
        3. Potential synergies
        4. Common pitfalls to avoid
        """
        
        response = await ollama.generate(
            model=self.model,
            prompt=prompt,
            system=self.system_prompt
        )
        return response['response']

    async def find_synergies(self, card_name: str, card_text: str) -> str:
        """Find synergistic cards for a given card"""
        prompt = f"""Find cards that synergize well with {card_name}:
        
        Card Text: {card_text}
        
        Please provide:
        1. Direct synergies (cards that work well with this card's abilities)
        2. Indirect synergies (cards that support the same strategy)
        3. Potential combo pieces
        """
        
        response = await ollama.generate(
            model=self.model,
            prompt=prompt,
            system=self.system_prompt
        )
        return response['response']

    async def get_budget_suggestions(self, commander_info: Dict, budget: float) -> str:
        """Get budget-friendly deck suggestions"""
        prompt = f"""Create a budget deck list for {commander_info['name']} with a maximum budget of ${budget}:
        
        Commander: {commander_info['name']}
        Colors: {', '.join(commander_info['colors'])}
        
        Please provide:
        1. Budget-friendly alternatives to expensive staples
        2. Hidden gems and underrated cards
        3. Cost-effective mana base options
        4. Upgrade path for the future
        """
        
        response = await ollama.generate(
            model=self.model,
            prompt=prompt,
            system=self.system_prompt
        )
        return response['response']

    async def analyze_meta(self, commander_name: str) -> str:
        """Analyze the meta for a commander"""
        prompt = f"""Analyze the current meta for {commander_name}:
        
        Please provide:
        1. Current meta position and popularity
        2. Common matchups and how to handle them
        3. Meta-specific tech choices
        4. Recent trends and developments
        """
        
        response = await ollama.generate(
            model=self.model,
            prompt=prompt,
            system=self.system_prompt
        )
        return response['response'] 