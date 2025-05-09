import ollama
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Tuple
from config import OLLAMA_HOST, OLLAMA_MODEL
from card_data import CardData
from rules_handler import RulesHandler
from pathlib import Path

class LLMHandler:
    """Handles interactions with the LLM."""
    
    def __init__(self, card_data=None, rules_pdf_path="ref/MagicCompRules_21031101.pdf"):
        """Initialize the LLM handler.
        
        Args:
            card_data: Optional shared CardData instance
            rules_pdf_path: Path to the Magic rules PDF
        """
        self.model_name = OLLAMA_MODEL
        self.client = ollama.Client(host=OLLAMA_HOST)
        self.rules_handler = RulesHandler(rules_pdf_path)
        self.card_data = card_data if card_data else CardData()
        self.executor = ThreadPoolExecutor(max_workers=4)  # Limit concurrent requests
        self.max_message_length = 1900  # Discord's limit is 2000, leave some buffer

    def _chunk_message(self, message: str) -> List[str]:
        """Split a message into chunks that fit within Discord's message length limit."""
        if len(message) <= self.max_message_length:
            return [message]
        
        chunks = []
        current_chunk = ""
        
        # Split by newlines first to keep logical sections together
        sections = message.split('\n')
        
        for section in sections:
            # If a single section is too long, split it by sentences
            if len(section) > self.max_message_length:
                sentences = section.split('. ')
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 2 <= self.max_message_length:
                        current_chunk += sentence + '. '
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + '. '
            # If section fits in current chunk, add it
            elif len(current_chunk) + len(section) + 1 <= self.max_message_length:
                current_chunk += section + '\n'
            # If section doesn't fit, start new chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = section + '\n'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

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

    async def generate_response(self, user_input: str, conversation_history: List[Dict[str, str]]) -> List[str]:
        """Generate a natural response based on user input and conversation history."""
        # First check if the input matches a card name
        card = self.card_data.get_card(user_input)
        if card:
            # If it's a card, use the card data to generate a response
            prompt = f"""You are a data-driven MTG Commander assistant that ONLY provides information from the local card database and official Magic rules.
            DO NOT generate or hallucinate any MTG information.
            If you don't have specific data from the database or rules, say so.
            Format your responses as:
            <thought_process>Your reasoning about what data to use</thought_process>
            <response>Your actual response based ONLY on the provided data</response>

            Here is the card data for {card['name']}:
            - Name: {card['name']}
            - Mana Cost: {card['mana_cost']}
            - Colors: {', '.join(card['colors'])}
            - Type: {card['type_line']}
            - Text: {card['oracle_text']}
            - Keywords: {', '.join(card.get('keywords', []))}
            - EDHREC Rank: {card.get('edhrec_rank', 'N/A')}

            User: {user_input}
            Assistant:"""
        else:
            # If not a card, use the conversation prompt
            prompt = self._build_conversation_prompt(user_input, conversation_history)

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            self.executor,
            self._generate_in_thread,
            prompt
        )
        
        return self._chunk_message(response['response'])

    def _build_conversation_prompt(self, user_input: str, conversation_history: List[Dict[str, str]]) -> str:
        """Build a prompt that includes conversation history."""
        prompt = """You are a data-driven MTG Commander assistant that ONLY provides information from the local card database and official Magic rules.
        DO NOT generate or hallucinate any MTG information.
        If you don't have specific data from the database or rules, say so.
        Format your responses as:
        <thought_process>Your reasoning about what data to use</thought_process>
        <response>Your actual response based ONLY on the provided data</response>\n\n"""
        
        # Add conversation history
        for message in conversation_history[-5:]:  # Only include last 5 messages for context
            if isinstance(message, dict) and "role" in message and "content" in message:
                role = "User" if message["role"] == "user" else "Assistant"
                prompt += f"{role}: {message['content']}\n"
        
        # Add current user input
        prompt += f"User: {user_input}\nAssistant:"
        
        return prompt

    async def analyze_commander(self, commander_name: str) -> List[str]:
        """Analyze a commander and provide deck brewing suggestions."""
        # Get card data
        card = self.card_data.get_card(commander_name)
        if not card:
            return ["Card not found in database."]

        # Get relevant rules
        relevant_rules = self.rules_handler.get_relevant_rules(card['oracle_text'])
        
        # Get synergies
        synergies = self.card_data.get_synergies(commander_name)

        # Build rules context
        rules_context = ""
        if relevant_rules:
            rules_context = "\nRelevant Rules:\n" + "\n".join(
                f"- Rule {rule['rule_number']}: {rule['content']}"
                for rule in relevant_rules
            )

        # Build synergies context
        synergies_context = ""
        if synergies:
            synergies_context = "\nPotential Synergies:\n" + "\n".join(
                f"- {syn['card']['name']} (Keywords: {', '.join(syn['shared_keywords'])}, "
                f"Mechanics: {', '.join(syn['shared_mechanics'])})"
                for syn in synergies[:10]  # Limit to top 10 synergies
            )

        prompt = f"""Analyze {card['name']} using ONLY the following data:

Card Data:
- Name: {card['name']}
- Mana Cost: {card['mana_cost']}
- Colors: {', '.join(card['colors'])}
- Type: {card['type_line']}
- Text: {card['oracle_text']}
- Keywords: {', '.join(card.get('keywords', []))}
- EDHREC Rank: {card.get('edhrec_rank', 'N/A')}

{rules_context}

{synergies_context}

Format your response as:
<thought_process>Your reasoning about what data to use</thought_process>
<response>Your analysis based ONLY on the above data</response>"""

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            self.executor,
            self._generate_in_thread,
            prompt
        )
        
        return self._chunk_message(response['response'])

    async def find_synergies(self, card_name: str) -> List[str]:
        """Find synergistic cards for a given card."""
        # Get card data
        card = self.card_data.get_card(card_name)
        if not card:
            return ["Card not found in database."]

        # Get relevant rules
        relevant_rules = self.rules_handler.get_relevant_rules(card['oracle_text'])
        
        # Get synergies
        synergies = self.card_data.get_synergies(card_name)

        # Build rules context
        rules_context = ""
        if relevant_rules:
            rules_context = "\nRelevant Rules:\n" + "\n".join(
                f"- Rule {rule['rule_number']}: {rule['content']}"
                for rule in relevant_rules
            )

        # Build synergies context
        synergies_context = ""
        if synergies:
            synergies_context = "\nFound Synergies:\n" + "\n".join(
                f"- {syn['card']['name']} (Keywords: {', '.join(syn['shared_keywords'])}, "
                f"Mechanics: {', '.join(syn['shared_mechanics'])})"
                for syn in synergies[:10]  # Limit to top 10 synergies
            )

        prompt = f"""Find synergies for {card['name']} using ONLY the following data:

Card Data:
- Name: {card['name']}
- Mana Cost: {card['mana_cost']}
- Colors: {', '.join(card['colors'])}
- Type: {card['type_line']}
- Text: {card['oracle_text']}
- Keywords: {', '.join(card.get('keywords', []))}

{rules_context}

{synergies_context}

Format your response as:
<thought_process>Your reasoning about what data to use</thought_process>
<response>Your synergy analysis based ONLY on the above data</response>"""

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            self.executor,
            self._generate_in_thread,
            prompt
        )
        
        return self._chunk_message(response['response'])

    async def get_budget_suggestions(self, commander_name: str, budget: float) -> List[str]:
        """Get budget-friendly deck suggestions."""
        # Get card data
        card = self.card_data.get_card(commander_name)
        if not card:
            return ["Card not found in database."]

        # Get relevant rules
        relevant_rules = self.rules_handler.get_relevant_rules(card['oracle_text'])
        
        # Get synergies
        synergies = self.card_data.get_synergies(commander_name)

        # Filter synergies by price
        budget_synergies = [
            syn for syn in synergies
            if syn['card'].get('prices', {}).get('usd', float('inf')) <= budget
        ]

        # Build rules context
        rules_context = ""
        if relevant_rules:
            rules_context = "\nRelevant Rules:\n" + "\n".join(
                f"- Rule {rule['rule_number']}: {rule['content']}"
                for rule in relevant_rules
            )

        # Build budget synergies context
        budget_context = ""
        if budget_synergies:
            budget_context = "\nBudget-Friendly Synergies:\n" + "\n".join(
                f"- {syn['card']['name']} (${syn['card'].get('prices', {}).get('usd', 'N/A')})"
                for syn in budget_synergies[:10]  # Limit to top 10 budget synergies
            )

        prompt = f"""Provide budget suggestions for {card['name']} (${budget}) using ONLY the following data:

Card Data:
- Name: {card['name']}
- Mana Cost: {card['mana_cost']}
- Colors: {', '.join(card['colors'])}
- Type: {card['type_line']}
- Text: {card['oracle_text']}
- Keywords: {', '.join(card.get('keywords', []))}

{rules_context}

{budget_context}

Format your response as:
<thought_process>Your reasoning about what data to use</thought_process>
<response>Your budget suggestions based ONLY on the above data</response>"""

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            self.executor,
            self._generate_in_thread,
            prompt
        )
        
        return self._chunk_message(response['response'])

    async def analyze_meta(self, commander_name: str) -> List[str]:
        """Analyze the meta for a given commander."""
        # Get card data
        card = self.card_data.get_card(commander_name)
        if not card:
            return ["Card not found in database."]

        # Get relevant rules
        relevant_rules = self.rules_handler.get_relevant_rules(card['oracle_text'])
        
        # Get synergies
        synergies = self.card_data.get_synergies(commander_name)

        # Build rules context
        rules_context = ""
        if relevant_rules:
            rules_context = "\nRelevant Rules:\n" + "\n".join(
                f"- Rule {rule['rule_number']}: {rule['content']}"
                for rule in relevant_rules
            )

        # Build synergies context
        synergies_context = ""
        if synergies:
            synergies_context = "\nCommon Synergies:\n" + "\n".join(
                f"- {syn['card']['name']} (Keywords: {', '.join(syn['shared_keywords'])}, "
                f"Mechanics: {', '.join(syn['shared_mechanics'])})"
                for syn in synergies[:10]  # Limit to top 10 synergies
            )

        prompt = f"""Analyze the meta for {card['name']} using ONLY the following data:

Card Data:
- Name: {card['name']}
- Mana Cost: {card['mana_cost']}
- Colors: {', '.join(card['colors'])}
- Type: {card['type_line']}
- Text: {card['oracle_text']}
- Keywords: {', '.join(card.get('keywords', []))}
- EDHREC Rank: {card.get('edhrec_rank', 'N/A')}

{rules_context}

{synergies_context}

Format your response as:
<thought_process>Your reasoning about what data to use</thought_process>
<response>Your meta analysis based ONLY on the above data</response>"""

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            self.executor,
            self._generate_in_thread,
            prompt
        )
        
        return self._chunk_message(response['response']) 