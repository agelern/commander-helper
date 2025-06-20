from typing import List, Dict, Tuple, Set, Optional
import discord
from discord.ui import Button, View
from src.commands.base import Command
from src.data.card_data import CardData
from fuzzywuzzy import process
import re
from collections import defaultdict
import math
from .image_utils import ImageStitcher
import time

class CommanderRecommendationView(View):
    def __init__(self, recommendations: List[Dict], card_data: CardData, card_list_display: str):
        super().__init__(timeout=300)
        self.recommendations = recommendations
        self.card_data = card_data
        self.current_page = 0
        self.card_list_display = card_list_display
        self.image_stitcher = ImageStitcher()
        if len(self.recommendations) > 1:
            self.add_item(Button(label="◀ Previous", custom_id="prev", style=discord.ButtonStyle.secondary))
            self.add_item(Button(label="Next ▶", custom_id="next", style=discord.ButtonStyle.secondary))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        count = len(self.recommendations)
        if interaction.data["custom_id"] == "prev":
            self.current_page = (self.current_page - 1 + count) % count
        elif interaction.data["custom_id"] == "next":
            self.current_page = (self.current_page + 1) % count
        
        embed, file = await self._create_recommendation_embed()
        
        if file:
            await interaction.response.edit_message(embed=embed, attachments=[file], view=self)
        else:
            # Clear attachments if the new embed doesn't have one
            await interaction.response.edit_message(embed=embed, attachments=[], view=self)
        return True

    async def _create_recommendation_embed(self) -> Tuple[discord.Embed, Optional[discord.File]]:
        rec = self.recommendations[self.current_page]
        commander = rec['commander']
        synergy_score = rec['synergy_score']
        popularity_score = rec['popularity_score']

        # Format EDHREC link
        if 'partner_names' in commander:
            formatted_name = '-'.join([n.lower().replace("'", "").replace(",", "").replace(" ", "-") for n in commander['partner_names']])
        else:
            formatted_name = commander['name'].lower().replace("'", "").replace(",", "").replace(" ", "-")
        edhrec_link = f"https://www.edhrec.com/commanders/{formatted_name}"
        commander_name = f"[{commander['name']}]({edhrec_link})"
        
        # Get card details
        mana_cost = commander.get('mana_cost', '')
        type_line = commander.get('type_line', '')
        oracle_text = commander.get('oracle_text', '')
        flavor_text = commander.get('flavor_text', '')
        power = commander.get('power', None)
        toughness = commander.get('toughness', None)
        pt = f"{power}/{toughness}" if power is not None and toughness is not None else None

        # Create embed
        embed = discord.Embed(
            title=f"#{self.current_page + 1} {commander_name}",
            description=f"Based on cards: {self.card_list_display}"
        )

        # Handle images
        file = None
        if 'partner_names' in commander:
            # Get partner cards and their image URLs
            partner_images = []
            details = ""
            for partner_name in commander['partner_names']:
                partner_card = self.card_data.get_card(partner_name)
                if partner_card:
                    if 'image_uris' in partner_card and 'normal' in partner_card['image_uris']:
                        partner_images.append(partner_card['image_uris']['normal'])
                    details += f"**{partner_card['name']}**\nMana Cost: {partner_card.get('mana_cost', '')}\nType: {partner_card.get('type_line', '')}\nOracle Text: {partner_card.get('oracle_text', '')}\n\n"
            
            # If we have both images, stitch them
            if len(partner_images) == 2:
                try:
                    stitched_path = await self.image_stitcher.stitch_partner_images(partner_images)
                    filename = f"partners_{self.current_page}.png"
                    file = discord.File(stitched_path, filename=filename)
                    embed.set_image(url=f"attachment://{filename}")
                except Exception as e:
                    print(f"Error stitching images for partners: {e}")
                    embed.add_field(name="Details", value=details, inline=False)
            else:
                embed.add_field(name="Details", value=details, inline=False)
        elif 'card_faces' in commander and len(commander['card_faces']) == 2:
            # Dual-sided commander
            face_images = []
            details = ""
            for face in commander['card_faces']:
                if 'image_uris' in face and 'normal' in face['image_uris']:
                    face_images.append(face['image_uris']['normal'])
                details += f"**{face.get('name', '')}**\n{face.get('mana_cost', '')}\n{face.get('type_line', '')}\n{face.get('oracle_text', '')}\n\n"

            if len(face_images) == 2:
                try:
                    stitched_path = await self.image_stitcher.stitch_partner_images(face_images)
                    filename = f"dualsided_{self.current_page}.png"
                    file = discord.File(stitched_path, filename=filename)
                    embed.set_image(url=f"attachment://{filename}")
                except Exception as e:
                    print(f"Error stitching images for dual-faced card: {e}")
                    embed.add_field(name="Card Faces", value=details, inline=False)
            else:
                embed.add_field(name="Card Faces", value=details, inline=False)
        else:
            # Single commander
            if 'image_uris' in commander and 'normal' in commander['image_uris']:
                embed.set_image(url=commander['image_uris']['normal'])
            else:
                details = f"Mana Cost: {mana_cost}\nType: {type_line}\nOracle Text: {oracle_text}\n"
                embed.add_field(name="Details", value=details, inline=False)

        if pt:
            embed.add_field(name="Power/Toughness", value=pt, inline=True)
        if flavor_text:
            embed.add_field(name="Flavor Text", value=flavor_text, inline=False)
        embed.add_field(
            name="Scores",
            value=f"**Synergy:** {synergy_score:.1f} | **Popularity:** {popularity_score:.1f}",
            inline=False
        )
        embed.set_footer(text=f"Commander {self.current_page + 1} of {len(self.recommendations)}")
        return embed, file

    async def on_timeout(self):
        """Clean up resources when the view times out."""
        await self.image_stitcher.close()

class CommanderRecommendationCommand(Command):
    """Command to recommend commanders based on a custom card list."""
    
    MIN_MATCH_SCORE = 80
    HIGH_CONFIDENCE_THRESHOLD = 95
    MAX_SUGGESTIONS = 5
    MAX_RECOMMENDATIONS = 10
    
    def __init__(self, card_data: CardData):
        super().__init__()  # Call parent constructor
        self.card_data = card_data
        self._commander_cache = None
        self._commander_data = None
    
    @property
    def name(self) -> str:
        return "recommend_commander"
    
    @property
    def description(self) -> str:
        return "Recommend commanders based on a custom card list"
    
    @property
    def usage(self) -> str:
        return "/revedh <card1, card2, card3, ...>"
    
    def _get_commander_cache(self) -> Dict[str, dict]:
        """Get cached commander data, loading if necessary. Includes all special commander pairings."""
        if self._commander_cache is None:
            self._commander_cache = {}
            partners = []
            partner_with_pairs = set()
            background_commanders = []
            backgrounds = []
            doctors = []
            companions = []
            friends_forever = []
            # First, add all single commanders and collect special types
            for card in self.card_data.cards.values():
                if self._is_commander(card):
                    self._commander_cache[card['name'].lower()] = card
                    oracle = card.get('oracle_text', '').lower()
                    type_line = card.get('type_line', '').lower()
                    # Partner With
                    partner_with_match = re.findall(r'partner with ([^\n\r]+)', oracle)
                    if partner_with_match:
                        for partner_name in partner_with_match:
                            partner_with_pairs.add(tuple(sorted([card['name'], partner_name.strip()])))
                    # Only add to generic partners if it is not a 'partner with' card
                    if card.get('legalities', {}).get('commander') == 'legal' and 'partner' in oracle and not partner_with_match:
                        partners.append(card)
                    # Backgrounds
                    if 'choose a background' in oracle:
                        background_commanders.append(card)
                    if 'background' in type_line:
                        backgrounds.append(card)
                    # Doctor/Companion
                    if "doctor's companion" in oracle:
                        companions.append(card)
                    if "time lord" in oracle:
                        doctors.append(card)
                    # Friends Forever
                    if 'friends forever' in oracle:
                        friends_forever.append(card)
            
            # Optimize partner combinations - only create pairs for popular partners to prevent explosion
            if len(partners) > 30:
                # Sort partners by popularity and only use top ones for combinations
                popular_partners = sorted(partners, key=lambda x: self._calculate_popularity_score(x), reverse=True)[:30]
                # Create combinations only for the most popular partners
                for i, a in enumerate(popular_partners):
                    for b in popular_partners[i+1:]:
                        if a['name'] == b['name']:
                            continue
                        pair_name = f"{a['name']} + {b['name']}"
                        color_identity = list(set(a.get('color_identity', [])) | set(b.get('color_identity', [])))
                        edhrec_data = None
                        image_uris = None
                        if 'edhrec_data' in a and a['edhrec_data'] and 'partner_data' in a['edhrec_data']:
                            edhrec_data = a['edhrec_data']['partner_data']
                            image_uris = edhrec_data.get('image_uris') if edhrec_data else None
                        elif 'edhrec_data' in b and b['edhrec_data'] and 'partner_data' in b['edhrec_data']:
                            edhrec_data = b['edhrec_data']['partner_data']
                            image_uris = edhrec_data.get('image_uris') if edhrec_data else None
                        pair_commander = {
                            'name': pair_name,
                            'color_identity': color_identity,
                            'type_line': 'Partner Pair',
                            'oracle_text': f"Partner: {a['name']} and {b['name']}",
                            'edhrec_data': edhrec_data,
                            'partner_names': [a['name'], b['name']],
                            'image_uris': image_uris,
                        }
                        self._commander_cache[pair_name.lower()] = pair_commander
            else:
                # If we have a reasonable number of partners, create all combinations
                for i, a in enumerate(partners):
                    for b in partners[i+1:]:
                        if a['name'] == b['name']:
                            continue
                        pair_name = f"{a['name']} + {b['name']}"
                        color_identity = list(set(a.get('color_identity', [])) | set(b.get('color_identity', [])))
                        edhrec_data = None
                        image_uris = None
                        if 'edhrec_data' in a and a['edhrec_data'] and 'partner_data' in a['edhrec_data']:
                            edhrec_data = a['edhrec_data']['partner_data']
                            image_uris = edhrec_data.get('image_uris') if edhrec_data else None
                        elif 'edhrec_data' in b and b['edhrec_data'] and 'partner_data' in b['edhrec_data']:
                            edhrec_data = b['edhrec_data']['partner_data']
                            image_uris = edhrec_data.get('image_uris') if edhrec_data else None
                        pair_commander = {
                            'name': pair_name,
                            'color_identity': color_identity,
                            'type_line': 'Partner Pair',
                            'oracle_text': f"Partner: {a['name']} and {b['name']}",
                            'edhrec_data': edhrec_data,
                            'partner_names': [a['name'], b['name']],
                            'image_uris': image_uris,
                        }
                        self._commander_cache[pair_name.lower()] = pair_commander
            
            # Partner With pairs (only valid pairs) - these are always created
            for a_name, b_name in partner_with_pairs:
                a = self.card_data.get_card(a_name)
                b = self.card_data.get_card(b_name)
                if not a or not b:
                    continue
                pair_name = f"{a['name']} + {b['name']}"
                color_identity = list(set(a.get('color_identity', [])) | set(b.get('color_identity', [])))
                edhrec_data = None
                image_uris = None
                if 'edhrec_data' in a and a['edhrec_data'] and 'partner_data' in a['edhrec_data']:
                    edhrec_data = a['edhrec_data']['partner_data']
                    image_uris = edhrec_data.get('image_uris') if edhrec_data else None
                elif 'edhrec_data' in b and b['edhrec_data'] and 'partner_data' in b['edhrec_data']:
                    edhrec_data = b['edhrec_data']['partner_data']
                    image_uris = edhrec_data.get('image_uris') if edhrec_data else None
                pair_commander = {
                    'name': pair_name,
                    'color_identity': color_identity,
                    'type_line': 'Partner With Pair',
                    'oracle_text': f"Partner With: {a['name']} and {b['name']}",
                    'edhrec_data': edhrec_data,
                    'partner_names': [a['name'], b['name']],
                    'image_uris': image_uris,
                }
                self._commander_cache[pair_name.lower()] = pair_commander
            
            # Background commander + background (limit combinations to prevent explosion)
            if len(background_commanders) <= 15 and len(backgrounds) <= 15:
                for commander in background_commanders:
                    for background in backgrounds:
                        pair_name = f"{commander['name']} + {background['name']}"
                        color_identity = list(set(commander.get('color_identity', [])) | set(background.get('color_identity', [])))
                        edhrec_data = None
                        image_uris = None
                        if 'edhrec_data' in commander and commander['edhrec_data'] and 'background_data' in commander['edhrec_data']:
                            edhrec_data = commander['edhrec_data']['background_data']
                            image_uris = edhrec_data.get('image_uris') if edhrec_data else None
                        pair_commander = {
                            'name': pair_name,
                            'color_identity': color_identity,
                            'type_line': 'Background Pair',
                            'oracle_text': f"Background: {commander['name']} + {background['name']}",
                            'edhrec_data': edhrec_data,
                            'partner_names': [commander['name'], background['name']],
                            'image_uris': image_uris,
                        }
                        self._commander_cache[pair_name.lower()] = pair_commander
            
            # Doctor + Companion (limit combinations)
            if len(doctors) <= 10 and len(companions) <= 10:
                for doctor in doctors:
                    for companion in companions:
                        pair_name = f"{doctor['name']} + {companion['name']}"
                        color_identity = list(set(doctor.get('color_identity', [])) | set(companion.get('color_identity', [])))
                        edhrec_data = None
                        image_uris = None
                        if 'edhrec_data' in doctor and doctor['edhrec_data'] and 'doctor_data' in doctor['edhrec_data']:
                            edhrec_data = doctor['edhrec_data']['doctor_data']
                            image_uris = edhrec_data.get('image_uris') if edhrec_data else None
                        pair_commander = {
                            'name': pair_name,
                            'color_identity': color_identity,
                            'type_line': 'Doctor Companion Pair',
                            'oracle_text': f"Doctor + Companion: {doctor['name']} + {companion['name']}",
                            'edhrec_data': edhrec_data,
                            'partner_names': [doctor['name'], companion['name']],
                            'image_uris': image_uris,
                        }
                        self._commander_cache[pair_name.lower()] = pair_commander
            
            # Friends Forever pairs (unordered) - limit combinations
            if len(friends_forever) <= 20:
                for i, a in enumerate(friends_forever):
                    for b in friends_forever[i+1:]:
                        if a['name'] == b['name']:
                            continue
                        pair_name = f"{a['name']} + {b['name']}"
                        color_identity = list(set(a.get('color_identity', [])) | set(b.get('color_identity', [])))
                        edhrec_data = None
                        image_uris = None
                        if 'edhrec_data' in a and a['edhrec_data'] and 'friends_data' in a['edhrec_data']:
                            edhrec_data = a['edhrec_data']['friends_data']
                            image_uris = edhrec_data.get('image_uris') if edhrec_data else None
                        elif 'edhrec_data' in b and b['edhrec_data'] and 'friends_data' in b['edhrec_data']:
                            edhrec_data = b['edhrec_data']['friends_data']
                            image_uris = edhrec_data.get('image_uris') if edhrec_data else None
                        pair_commander = {
                            'name': pair_name,
                            'color_identity': color_identity,
                            'type_line': 'Friends Forever Pair',
                            'oracle_text': f"Friends Forever: {a['name']} and {b['name']}",
                            'edhrec_data': edhrec_data,
                            'partner_names': [a['name'], b['name']],
                            'image_uris': image_uris,
                        }
                        self._commander_cache[pair_name.lower()] = pair_commander
        return self._commander_cache
    
    def _is_commander(self, card: dict) -> bool:
        """Check if a card can be a commander."""
        # Check if card is legal in commander
        if card.get('legalities', {}).get('commander') != 'legal':
            return False
        
        type_line = card.get('type_line', '').lower()
        oracle_text = card.get('oracle_text', '').lower()
        
        # Legendary creatures or cards with "can be your commander"
        return (("legendary" in type_line and "creature" in type_line) or 
                "can be your commander" in oracle_text)
    
    def _extract_color_identity(self, card: dict) -> Set[str]:
        """Extract color identity from a card."""
        color_identity = card.get('color_identity', [])
        return set(color_identity)
    
    def _aggregate_color_identity(self, cards: List[dict]) -> Set[str]:
        """Aggregate color identity from multiple cards."""
        combined_colors = set()
        for card in cards:
            combined_colors.update(self._extract_color_identity(card))
        return combined_colors
    
    def _commander_matches_colors(self, commander: dict, required_colors: Set[str]) -> bool:
        """Allow commanders whose color identity is a superset of the required colors (not just an exact match)."""
        commander_colors = self._extract_color_identity(commander)
        return required_colors.issubset(commander_colors)
    
    def _has_typal_synergy(self, commander: dict, card: dict) -> bool:
        """Check for typal synergies between commander and card."""
        commander_type = commander.get('type_line', '').lower()
        card_type = card.get('type_line', '').lower()
        # Extract creature types
        commander_creatures = self._extract_creature_types(commander_type)
        card_creatures = self._extract_creature_types(card_type)
        # Check for shared creature types
        shared_types = commander_creatures.intersection(card_creatures)
        return len(shared_types) > 0

    def _extract_creature_types(self, type_line: str) -> Set[str]:
        """Extract creature types from a type line."""
        # Find the part after "Creature —" or similar
        if '—' in type_line:
            creature_part = type_line.split('—')[1].strip()
            types = set(creature_part.split())
            return types
        return set()
    
    def _has_mana_synergy(self, commander: dict, card: dict) -> bool:
        """Check for mana cost synergies."""
        commander_cost = commander.get('mana_cost', '')
        card_cost = card.get('mana_cost', '')
        
        # Check for shared colors in mana costs
        commander_colors = set(re.findall(r'[WUBRG]', commander_cost))
        card_colors = set(re.findall(r'[WUBRG]', card_cost))
        
        return len(commander_colors.intersection(card_colors)) > 0
    
    def _calculate_theme_overlap_score(self, commander: dict, input_cards: List[dict]) -> float:
        """Calculate synergy score based on overlap of 'used_in' theme slugs between commander and input cards."""
        if not input_cards:
            return 0.0
        # Check for specific card types in input
        has_planeswalkers = False
        has_artifacts = False
        has_enchantments = False
        has_creatures = False
        for card in input_cards:
            if 'type_line' in card:
                type_line = card['type_line']
                if 'Planeswalker' in type_line:
                    has_planeswalkers = True
                if 'Artifact' in type_line:
                    has_artifacts = True
                if 'Enchantment' in type_line:
                    has_enchantments = True
                if 'Creature' in type_line:
                    has_creatures = True
        # Get the set of themes for the commander (union if partner pair)
        commander_themes = set()
        if 'partner_names' in commander:
            for partner_name in commander['partner_names']:
                partner_card = self.card_data.get_card(partner_name)
                if partner_card and 'used_in' in partner_card:
                    commander_themes.update(partner_card['used_in'])
        elif 'used_in' in commander:
            commander_themes = set(commander['used_in'])
        else:
            card = self.card_data.get_card(commander['name'])
            if card and 'used_in' in card:
                commander_themes = set(card['used_in'])
        # Get the set of all themes for the input cards
        input_themes = set()
        for card in input_cards:
            if 'used_in' in card:
                input_themes.update(card['used_in'])
        if not commander_themes or not input_themes:
            return 0.0
        overlap = commander_themes & input_themes
        # Calculate both coverage ratios
        input_coverage = len(overlap) / len(input_themes)  # How many input themes are matched
        commander_focus = len(overlap) / len(commander_themes)  # How focused the commander is on matching themes
        # Penalize commanders that appear in too many themes (jack-of-all-trades)
        theme_penalty = 1.0
        if len(commander_themes) > 20:
            # Reduce score for commanders with too many themes (only knock down by 5%)
            theme_penalty = 0.95
        # Weighted average favoring commander focus (60%) over input coverage (40%)
        base_score = 100.0 * (0.6 * commander_focus + 0.4 * input_coverage)
        # Apply theme penalty
        score = base_score * theme_penalty
        # Add type-based bonuses
        type_bonus = 1.0
        # Planeswalker bonus - strongest bonus since it's most specific
        if has_planeswalkers and 'planeswalkers' in commander_themes:
            type_bonus *= 1.5
        # Artifact bonus
        if has_artifacts and 'artifacts' in commander_themes:
            type_bonus *= 1.2
        # Enchantment bonus
        if has_enchantments and 'enchantments' in commander_themes:
            type_bonus *= 1.2
        # Creature bonus (smaller since it's very common)
        if has_creatures and 'creatures' in commander_themes:
            type_bonus *= 1.1
        return score * type_bonus

    def _calculate_synergy_score(self, commander: dict, input_cards: List[dict]) -> float:
        """Calculate synergy score between commander and input cards, dominated by theme overlap."""
        if not input_cards:
            return 0.0
        # For partner pairs, average the synergy score of each partner
        if 'partner_names' in commander:
            partner_scores = []
            for partner_name in commander['partner_names']:
                partner_card = self.card_data.get_card(partner_name)
                if partner_card:
                    partner_scores.append(self._calculate_synergy_score(partner_card, input_cards))
            if partner_scores:
                return sum(partner_scores) / len(partner_scores)
        # Theme overlap is the dominant factor
        theme_score = self._calculate_theme_overlap_score(commander, input_cards)
        # Optionally, add a small bonus for typal, mana, or keyword synergy
        typal_bonus = 0.0
        mana_bonus = 0.0
        keyword_bonus = 0.0
        for card in input_cards:
            if self._has_typal_synergy(commander, card):
                typal_bonus += 2.0
            if self._has_mana_synergy(commander, card):
                mana_bonus += 1.0
            # Robust keyword synergy: check for shared or related keywords (e.g., ninjutsu, commander ninjutsu, etc.)
            commander_keywords = self._extract_keywords(commander)
            card_keywords = self._extract_keywords(card)
            for c_kw in commander_keywords:
                for i_kw in card_keywords:
                    if c_kw in i_kw or i_kw in c_kw:
                        keyword_bonus += 2.0
                        break
        # Normalize bonuses
        bonus = min(typal_bonus + mana_bonus + keyword_bonus, 10.0)
        # Final synergy score: 90% theme overlap, 10% bonus
        return min(theme_score * 0.9 + bonus, 100.0)
    
    def _calculate_popularity_score(self, commander: dict) -> float:
        """Calculate popularity score for a commander (including pairs) using EDHREC data."""
        # If this is a virtual pair (partners, backgrounds, etc)
        if 'partner_names' in commander:
            # Use the pair's edhrec_data if available
            if 'edhrec_data' in commander and commander['edhrec_data']:
                edhrec_data = commander['edhrec_data']
                if 'potential_decks' in edhrec_data:
                    potential_decks = edhrec_data['potential_decks']
                    if potential_decks > 0:
                        return min(100.0, 20.0 + math.log10(potential_decks) * 20.0)
            # Otherwise, average the popularity scores of the individual partners
            partner_scores = []
            for partner_name in commander['partner_names']:
                partner_card = self.card_data.get_card(partner_name)
                if partner_card:
                    partner_scores.append(self._calculate_popularity_score(partner_card))
            if partner_scores:
                return sum(partner_scores) / len(partner_scores)
            # Fallback to 0
            return 0.0
        # Single commander logic
        if 'edhrec_rank' in commander and commander['edhrec_rank'] is not None:
            rank = commander['edhrec_rank']
            if rank <= 100:
                return 95.0 + (100 - rank) * 0.05
            elif rank <= 500:
                return 85.0 + (500 - rank) * 0.02
            elif rank <= 1000:
                return 75.0 + (1000 - rank) * 0.02
            elif rank <= 5000:
                return 50.0 + (5000 - rank) * 0.01
            else:
                return max(20.0, 50.0 - (rank - 5000) * 0.005)
        if 'edhrec_data' in commander and commander['edhrec_data']:
            edhrec_data = commander['edhrec_data']
            if 'potential_decks' in edhrec_data:
                potential_decks = edhrec_data['potential_decks']
                if potential_decks > 0:
                    return min(100.0, 20.0 + math.log10(potential_decks) * 20.0)
        return 0.0
    
    def _parse_card_list(self, args: str) -> List[str]:
        """Parse comma-separated card list from arguments."""
        # Split by comma and clean up whitespace
        cards = [card.strip() for card in args.split(',') if card.strip()]
        return cards
    
    def _parse_weights(self, args: str) -> Tuple[float, float]:
        """Parse synergy and popularity weights from arguments."""
        parts = args.split()
        
        # Default weights
        synergy_weight = 0.7
        popularity_weight = 0.3
        
        # Try to extract weights from the end of the arguments
        if len(parts) >= 2:
            try:
                synergy_weight = float(parts[-2])
                popularity_weight = float(parts[-1])
                # Remove weights from card list
                args = ' '.join(parts[:-2])
            except ValueError:
                pass
        
        return synergy_weight, popularity_weight
    
    def _find_synergistic_commanders(self, valid_cards: List[dict], combined_colors: Set[str], max_time_seconds: float = 8.0) -> List[dict]:
        start_time = time.time()
        commanders = self._get_commander_cache()
        # Remove all per-commander (e.g., Yuriko) special handling
        # Color filtering
        if not combined_colors:
            colorless_commanders = []
            colored_commanders = []
            for commander in commanders.values():
                commander_colors = self._extract_color_identity(commander)
                if not commander_colors:
                    colorless_commanders.append(commander)
                else:
                    colored_commanders.append(commander)
            candidates = colorless_commanders + colored_commanders[:100]
        else:
            candidates = [commander for commander in commanders.values() 
                         if self._commander_matches_colors(commander, combined_colors)]
        # Pre-filtering
        potential_candidates = []
        for commander in candidates:
            if self._quick_synergy_check(commander, valid_cards):
                potential_candidates.append(commander)
            elif self._calculate_popularity_score(commander) > 60:
                potential_candidates.append(commander)
            if len(potential_candidates) >= 200:
                break
        # Scoring
        scored_commanders = []
        processed_count = 0
        for commander in potential_candidates:
            if time.time() - start_time > max_time_seconds:
                break
            synergy_score = self._calculate_synergy_score(commander, valid_cards)
            popularity_score = self._calculate_popularity_score(commander)
            scored_commanders.append({
                'commander': commander,
                'synergy_score': synergy_score,
                'popularity_score': popularity_score
            })
            processed_count += 1
            high_synergy_count = sum(1 for sc in scored_commanders if sc['synergy_score'] > 50)
            if high_synergy_count >= 20:
                break
        # Final recommendations (after sorting and limiting)
        scored_commanders.sort(key=lambda x: (round(x['synergy_score'], 1), x['popularity_score']), reverse=True)
        # Filter out solo 'partner with' commanders
        filtered_commanders = []
        for rec in scored_commanders:
            commander = rec['commander']
            oracle = commander.get('oracle_text', '').lower()
            # If this is a solo commander with 'partner with', skip it
            if (
                'partner with' in oracle
                and 'partner_names' not in commander
            ):
                continue
            filtered_commanders.append(rec)
        return filtered_commanders
    
    async def execute(self, args: str) -> Tuple[List[discord.Embed], Optional[discord.ui.View], Optional[List[discord.File]]]:
        """Execute the commander recommendation command."""
        try:
            # Validate arguments
            if not self.validate_args(args):
                embed = self.create_error_embed("No card list provided. Please provide a comma-separated list of cards.")
                self.log_command_execution(args, False, "No arguments provided")
                return [embed], None, []
            
            # Parse card list
            card_names = self._parse_card_list(args)
            if not card_names:
                embed = self.create_error_embed("No valid card names provided. Please provide a comma-separated list of cards.")
                self.log_command_execution(args, False, "No valid card names")
                return [embed], None, []
            
            # Find valid cards
            valid_cards = []
            invalid_cards = []
            for card_name in card_names:
                card = self.card_data.get_card(card_name)
                if card:
                    valid_cards.append(card)
                else:
                    card_names_list = list(self.card_data.cards.keys())
                    matches = process.extract(card_name, card_names_list, limit=1)
                    if matches and matches[0][1] >= self.MIN_MATCH_SCORE:
                        best_match = matches[0][0]
                        card = self.card_data.cards[best_match]
                        valid_cards.append(card)
                    else:
                        invalid_cards.append(card_name)
            
            if not valid_cards:
                embed = self.create_error_embed("No valid cards found. Please check your card names and try again.")
                self.log_command_execution(args, False, "No valid cards found")
                return [embed], None, []
            
            if invalid_cards:
                warning_embed = discord.Embed(
                    title="Warning",
                    description=f"Could not find these cards: {', '.join(invalid_cards)}",
                    color=discord.Color.orange()
                )
                self.logger.warning(f"Invalid cards found: {invalid_cards}")
            
            # Find synergistic commanders
            combined_colors = self._aggregate_color_identity(valid_cards)
            recommendations = self._find_synergistic_commanders(valid_cards, combined_colors)
            
            if not recommendations:
                embed = self.create_error_embed("No commanders found for the given input.")
                self.log_command_execution(args, False, "No commanders found")
                return [embed], None, []
            
            # Sort and limit recommendations
            recommendations.sort(key=lambda x: (round(x['synergy_score'], 1), x['popularity_score']), reverse=True)
            top_recommendations = recommendations[:self.MAX_RECOMMENDATIONS]
            
            # Create display
            card_list_display = ', '.join([card['name'] for card in valid_cards])
            view = CommanderRecommendationView(top_recommendations, self.card_data, card_list_display)
            embed, file = await view._create_recommendation_embed()
            
            self.log_command_execution(args, True)
            return [embed], view, [file] if file else []
            
        except Exception as e:
            self.logger.error(f"Error in commander recommendation command: {e}")
            embed = self.create_error_embed(f"An error occurred while processing your request: {str(e)}")
            self.log_command_execution(args, False, str(e))
            return [embed], None, []

    def _quick_synergy_check(self, commander: dict, input_cards: List[dict]) -> bool:
        """Quick check to see if a commander might be synergistic with the input cards."""
        if not input_cards:
            return False
        # Check for artifact synergies
        has_artifacts = any('Artifact' in card.get('type_line', '') for card in input_cards)
        if has_artifacts:
            oracle_text = commander.get('oracle_text', '').lower()
            if any(keyword in oracle_text for keyword in ['artifact', 'equipment', 'vehicle', 'treasure', 'clue', 'food']):
                return True
        # Check for typal synergies
        for card in input_cards:
            if self._has_typal_synergy(commander, card):
                return True
        # Check for mana cost synergies
        for card in input_cards:
            if self._has_mana_synergy(commander, card):
                return True
        # Check for theme keywords in commander name or oracle text
        commander_text = (commander.get('name', '') + ' ' + commander.get('oracle_text', '')).lower()
        card_types = set()
        for card in input_cards:
            type_line = card.get('type_line', '').lower()
            if 'creature' in type_line:
                card_types.add('creature')
            if 'artifact' in type_line:
                card_types.add('artifact')
            if 'enchantment' in type_line:
                card_types.add('enchantment')
            if 'planeswalker' in type_line:
                card_types.add('planeswalker')
            if 'instant' in type_line or 'sorcery' in type_line:
                card_types.add('spell')
        # Check for relevant keywords
        if 'creature' in card_types and any(keyword in commander_text for keyword in ['creature', 'token', 'sacrifice']):
            return True
        if 'artifact' in card_types and any(keyword in commander_text for keyword in ['artifact', 'equipment', 'vehicle']):
            return True
        if 'enchantment' in card_types and any(keyword in commander_text for keyword in ['enchantment', 'aura']):
            return True
        if 'planeswalker' in card_types and 'planeswalker' in commander_text:
            return True
        if 'spell' in card_types and any(keyword in commander_text for keyword in ['instant', 'sorcery', 'cast', 'spell']):
            return True
        # Robust keyword synergy: check for shared or related keywords (e.g., ninjutsu, commander ninjutsu, etc.)
        commander_keywords = self._extract_keywords(commander)
        for card in input_cards:
            card_keywords = self._extract_keywords(card)
            for c_kw in commander_keywords:
                for i_kw in card_keywords:
                    if c_kw in i_kw or i_kw in c_kw:
                        return True
        return False

    def _extract_keywords(self, card: dict) -> Set[str]:
        """Extracts a set of normalized keywords from a card's oracle text."""
        keywords = set()
        oracle = card.get('oracle_text', '').lower()
        # Find all keyword abilities (e.g., ninjutsu, commander ninjutsu, etc.)
        # This regex matches words and phrases ending in 'ninjutsu', 'cascade', etc.
        matches = re.findall(r'([a-z\- ]*ninjutsu|cascade|modular|prowl|mutate|connive|foretell|suspend|cycling|exploit|evoke|proliferate|surveil|flashback|persist|undying|delve|affinity|improvise|outlast|embalm|eternalize|jump-start|escape|adventure)', oracle)
        for match in matches:
            keywords.add(match.strip())
        return keywords 