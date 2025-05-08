import ollama
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional
from config import OLLAMA_HOST, OLLAMA_MODEL
from mtg_data import MTGDataHandler

class LLMHandler:
    def __init__(self, model_name: str = OLLAMA_MODEL):
        """Initialize the LLM handler with the specified model."""
        self.model_name = model_name
        self.system_prompt = """You are a professional Magic: The Gathering Commander deck brewer. 
        You provide clear, concise, and accurate advice about deck building and card interactions.
        Focus on practical recommendations and strategic insights.
        Consider color identity, mana curve, and win conditions in your analysis."""
        
        # Configure Ollama client
        self.client = ollama.Client(host=OLLAMA_HOST)
        self.mtg_handler = MTGDataHandler()
        self.executor = ThreadPoolExecutor(max_workers=4)  # Limit concurrent requests

    def _generate_in_thread(self, prompt: str) -> Dict:
        """Run the Ollama generate call in a separate thread."""
        return self.client.generate(
            model=self.model_name,
            prompt=prompt,
            options={
                "temperature": 0.5,
                "num_predict": 1000
            }
        )

    async def generate_response(self, user_input: str, conversation_history: List[Dict[str, str]]) -> str:
        """Generate a natural response based on user input and conversation history."""
        # Build the prompt with conversation history
        prompt = self._build_conversation_prompt(user_input, conversation_history)
        
        # Run the generate call in a separate thread
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            self.executor,
            self._generate_in_thread,
            prompt
        )
        
        return response['response']

    def _build_conversation_prompt(self, user_input: str, conversation_history: List[Dict[str, str]]) -> str:
        """Build a prompt that includes conversation history."""
        prompt = """You are a professional MTG Commander deck brewing assistant. Provide clear, direct advice based on EDHREC data and strategic analysis. Keep responses focused and practical.\n\n"""
        
        # Add conversation history
        for message in conversation_history[-5:]:  # Only include last 5 messages for context
            if isinstance(message, dict) and "role" in message and "content" in message:
                role = "User" if message["role"] == "user" else "Assistant"
                prompt += f"{role}: {message['content']}\n"
        
        # Add current user input
        prompt += f"User: {user_input}\nAssistant:"
        
        return prompt

    async def analyze_commander(self, commander_info: Dict) -> str:
        """Analyze a commander and provide deck brewing suggestions."""
        prompt = f"""Analyze the following commander and provide strategic deck building recommendations:

Commander Information:
Name: {commander_info['name']}
Mana Cost: {commander_info['mana_cost']}
Colors: {', '.join(commander_info['colors'])}
Type: {commander_info['type']}
Text: {commander_info['text']}
EDHREC Rank: {commander_info['edhrec_rank']}
Average Decks: {commander_info['average_decks']}
Potential Decks: {commander_info['potential_decks']}

Provide a structured analysis covering:
1. Primary strategy and win conditions
2. Key card categories and essential includes
3. Mana base composition
4. Common pitfalls and solutions
5. Strategic considerations

Keep the analysis clear and focused on practical deck building decisions."""

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            self.executor,
            self._generate_in_thread,
            prompt
        )
        
        return response['response']

    async def find_synergies(self, card_name: str, card_text: str) -> str:
        """Find synergistic cards for a given card."""
        prompt = f"""Analyze synergistic options for the following card:

Card: {card_name}
Text: {card_text}

Provide a structured analysis of:
1. Direct synergies and their strategic value
2. Supporting cards that enhance the strategy
3. Potential combo pieces and their requirements
4. Mana curve considerations and timing

Focus on practical card choices and their strategic applications."""

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            self.executor,
            self._generate_in_thread,
            prompt
        )
        
        return response['response']

    async def get_budget_suggestions(self, commander_info: Dict, budget: float) -> str:
        """Get budget-friendly deck suggestions."""
        prompt = f"""Provide budget deck building recommendations for:

Commander: {commander_info['name']}
Budget: ${budget}

Include:
1. Cost-effective alternatives to expensive staples
2. Efficient mana base options within budget
3. Strategic budget card choices
4. Clear upgrade path for future improvements

Focus on maximizing strategic value within budget constraints."""

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            self.executor,
            self._generate_in_thread,
            prompt
        )
        
        return response['response']

    async def analyze_meta(self, commander_name: str) -> str:
        """Analyze the meta for a given commander."""
        prompt = f"""Provide a meta analysis for {commander_name}:

Include:
1. Current competitive position and trends
2. Primary strategies and their effectiveness
3. Key matchups and strategic considerations
4. Meta-specific card choices and tech options

Focus on practical insights for competitive play."""

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            self.executor,
            self._generate_in_thread,
            prompt
        )
        
        return response['response'] 