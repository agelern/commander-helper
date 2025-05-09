import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from card_data import CardData
from llm_handler import LLMHandler
from conversation_handler import ConversationHandler

# Load environment variables
load_dotenv()

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Initialize shared instances
card_data = CardData()  # Single instance of CardData
llm_handler = LLMHandler(card_data=card_data)  # Pass the shared instance
conversation_handler = ConversationHandler()

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.event
async def on_message(message):
    # Don't respond to our own messages
    if message.author == bot.user:
        return

    # Process commands first
    await bot.process_commands(message)

    # If the message doesn't start with a command prefix, treat it as a conversation
    if not message.content.startswith('!'):
        await handle_conversation(message)

async def handle_conversation(message):
    """Handle natural language conversation."""
    # Send immediate acknowledgment
    await message.channel.send("Processing your request...")
    
    # Add user message to conversation history
    conversation_handler.add_message(message.channel.id, "user", message.content)
    
    # Process the message
    result = conversation_handler.process_message(message.content)
    
    if not result['type'] or not result['card_name']:
        # If we can't determine the type or card name, use the LLM to generate a response
        response_chunks = await llm_handler.generate_response(
            message.content,
            conversation_handler._get_conversation_history(message.channel.id)
        )
        for chunk in response_chunks:
            await message.channel.send(chunk)
            conversation_handler.add_message(message.channel.id, "assistant", chunk)
        return

    # Handle specific query types
    if result['type'] == 'brew':
        await handle_brew_query(message, result)
    elif result['type'] == 'synergy':
        await handle_synergy_query(message, result)
    elif result['type'] == 'budget':
        await handle_budget_query(message, result)
    elif result['type'] == 'meta':
        await handle_meta_query(message, result)

async def handle_brew_query(message, result):
    """Handle deck brewing queries."""
    card = card_data.get_card(result['card_name'])
    if not card:
        response = f"Sorry, I couldn't find information for {result['card_name']}. Please check the spelling and try again."
        await message.channel.send(response)
        conversation_handler.add_message(message.channel.id, "assistant", response)
        return
    
    suggestions = await llm_handler.analyze_commander(result['card_name'])
    for chunk in suggestions:
        await message.channel.send(chunk)
        conversation_handler.add_message(message.channel.id, "assistant", chunk)

async def handle_synergy_query(message, result):
    """Handle synergy queries."""
    card = card_data.get_card(result['card_name'])
    if not card:
        response = f"Sorry, I couldn't find information for {result['card_name']}. Please check the spelling and try again."
        await message.channel.send(response)
        conversation_handler.add_message(message.channel.id, "assistant", response)
        return
    
    synergies = await llm_handler.find_synergies(result['card_name'])
    for chunk in synergies:
        await message.channel.send(chunk)
        conversation_handler.add_message(message.channel.id, "assistant", chunk)

async def handle_budget_query(message, result):
    """Handle budget queries."""
    if not result['budget']:
        response = "Please specify a budget amount (e.g., $100)."
        await message.channel.send(response)
        conversation_handler.add_message(message.channel.id, "assistant", response)
        return
    
    card = card_data.get_card(result['card_name'])
    if not card:
        response = f"Sorry, I couldn't find information for {result['card_name']}. Please check the spelling and try again."
        await message.channel.send(response)
        conversation_handler.add_message(message.channel.id, "assistant", response)
        return
    
    suggestions = await llm_handler.get_budget_suggestions(result['card_name'], result['budget'])
    for chunk in suggestions:
        await message.channel.send(chunk)
        conversation_handler.add_message(message.channel.id, "assistant", chunk)

async def handle_meta_query(message, result):
    """Handle meta analysis queries."""
    card = card_data.get_card(result['card_name'])
    if not card:
        response = f"Sorry, I couldn't find information for {result['card_name']}. Please check the spelling and try again."
        await message.channel.send(response)
        conversation_handler.add_message(message.channel.id, "assistant", response)
        return
    
    analysis = await llm_handler.analyze_meta(result['card_name'])
    for chunk in analysis:
        await message.channel.send(chunk)
        conversation_handler.add_message(message.channel.id, "assistant", chunk)

@bot.command(name='help_brew')
async def help_brew(ctx):
    """Display help information about deck brewing commands"""
    help_text = """
    **Commander Deck Brewer Bot**

    You can interact with me in two ways:

    1. **Commands**:
    `!brew <commander>` - Get deck brewing suggestions
    `!synergy <card>` - Find synergistic cards
    `!budget <commander> <budget>` - Get budget deck suggestions
    `!meta <commander>` - Get meta analysis

    2. **Natural Language**:
    Just chat with me! Try phrases like:
    - "Help me build a deck with Atraxa"
    - "What cards synergize with Sol Ring?"
    - "Show me budget options for $100"
    - "What's the meta like for Edgar Markov?"

    Example: `!brew Atraxa, Praetors' Voice`
    """
    await ctx.send(help_text)

# Keep the existing command handlers for backward compatibility
@bot.command(name='brew')
async def brew_deck(ctx, *, commander_name):
    """Generate deck brewing suggestions for a commander"""
    await handle_brew_query(ctx.message, {'card_name': commander_name})

@bot.command(name='synergy')
async def find_synergy(ctx, *, card_name):
    """Find cards that synergize well with a specific card"""
    await handle_synergy_query(ctx.message, {'card_name': card_name})

@bot.command(name='budget')
async def budget_deck(ctx, commander_name: str, budget: float):
    """Get budget deck suggestions"""
    await handle_budget_query(ctx.message, {'card_name': commander_name, 'budget': budget})

@bot.command(name='meta')
async def meta_analysis(ctx, *, commander_name):
    """Get meta analysis for a commander"""
    await handle_meta_query(ctx.message, {'card_name': commander_name})

def main():
    """Run the bot."""
    bot.run(os.getenv('DISCORD_TOKEN'))

if __name__ == '__main__':
    main() 