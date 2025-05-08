import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from mtg_data import MTGDataHandler
from llm_handler import LLMHandler

# Load environment variables
load_dotenv()

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
mtg_handler = MTGDataHandler()
llm_handler = LLMHandler()

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='help_brew')
async def help_brew(ctx):
    """Display help information about deck brewing commands"""
    help_text = """
    **Commander Deck Brewer Bot Commands**
    
    `!brew <commander>` - Get deck brewing suggestions for a specific commander
    `!synergy <card>` - Find cards that synergize well with a specific card
    `!budget <commander> <budget>` - Get budget deck suggestions
    `!meta <commander>` - Get meta analysis for a commander
    
    Example: `!brew Atraxa, Praetors' Voice`
    """
    await ctx.send(help_text)

@bot.command(name='brew')
async def brew_deck(ctx, *, commander_name):
    """Generate deck brewing suggestions for a commander"""
    await ctx.send(f"Analyzing {commander_name} for deck brewing suggestions...")
    
    # Get commander info
    commander_info = await mtg_handler.get_commander_info(commander_name)
    if not commander_info:
        await ctx.send(f"Sorry, I couldn't find information for {commander_name}. Please check the spelling and try again.")
        return
    
    # Get brewing suggestions from LLM
    suggestions = await llm_handler.analyze_commander(commander_info)
    
    # Split the response into chunks if it's too long
    chunks = [suggestions[i:i+1900] for i in range(0, len(suggestions), 1900)]
    for chunk in chunks:
        await ctx.send(chunk)

@bot.command(name='synergy')
async def find_synergy(ctx, *, card_name):
    """Find cards that synergize well with a specific card"""
    await ctx.send(f"Finding synergies for {card_name}...")
    
    # Get card info
    card_info = await mtg_handler.get_commander_info(card_name)  # Reusing the same method for now
    if not card_info:
        await ctx.send(f"Sorry, I couldn't find information for {card_name}. Please check the spelling and try again.")
        return
    
    # Get synergy suggestions from LLM
    synergies = await llm_handler.find_synergies(card_name, card_info['text'])
    
    # Split the response into chunks if it's too long
    chunks = [synergies[i:i+1900] for i in range(0, len(synergies), 1900)]
    for chunk in chunks:
        await ctx.send(chunk)

@bot.command(name='budget')
async def budget_deck(ctx, commander_name: str, budget: float):
    """Get budget deck suggestions"""
    await ctx.send(f"Creating budget deck suggestions for {commander_name} with a ${budget} budget...")
    
    # Get commander info
    commander_info = await mtg_handler.get_commander_info(commander_name)
    if not commander_info:
        await ctx.send(f"Sorry, I couldn't find information for {commander_name}. Please check the spelling and try again.")
        return
    
    # Get budget suggestions from LLM
    suggestions = await llm_handler.get_budget_suggestions(commander_info, budget)
    
    # Split the response into chunks if it's too long
    chunks = [suggestions[i:i+1900] for i in range(0, len(suggestions), 1900)]
    for chunk in chunks:
        await ctx.send(chunk)

@bot.command(name='meta')
async def meta_analysis(ctx, *, commander_name):
    """Get meta analysis for a commander"""
    await ctx.send(f"Analyzing meta for {commander_name}...")
    
    # Get meta analysis from LLM
    analysis = await llm_handler.analyze_meta(commander_name)
    
    # Split the response into chunks if it's too long
    chunks = [analysis[i:i+1900] for i in range(0, len(analysis), 1900)]
    for chunk in chunks:
        await ctx.send(chunk)

# Run the bot
bot.run(os.getenv('DISCORD_TOKEN')) 