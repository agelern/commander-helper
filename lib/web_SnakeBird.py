import time
import requests
import json
import aiohttp
import asyncio
from urllib.parse import quote
from itertools import combinations


def get_full_color_identity(cards):
    colors = set()
    for name, card in cards.items():
        for color in card['color_identity']:
            colors.add(color.upper())
    return colors
    
async def get_solo_commanders(session,colors):
    commanders = {}
    colors = ''.join(colors)
    query = f'id>={colors} is:commander'
    encoded_query = quote(query)
    url = f"https://api.scryfall.com/cards/search?q={encoded_query}"
    async with session.get(url) as response:
        if response.status != 200:
            raise Exception(f"Solo request failed with status code {response.status}")

        possible_commanders = await response.json()
        if 'data' not in possible_commanders:
            raise Exception("No 'data' key in the solo response")
        
        print(f"{len(possible_commanders['data'])} solo commanders found.")

        for commander in possible_commanders["data"]:
            commanders[commander["name"]] = {"data": commander, "score": 0}
        return commanders

async def get_partner_commanders(session, colors):
    commanders = {}
    query = ''
    for color in colors:
        query += f'is:commander o:"Partner" -o:"Partner with" id>={color} OR '
    encoded_query = quote(query[:-4])
    url = f"https://api.scryfall.com/cards/search?q={encoded_query}"
    async with session.get(url) as response:
        if response.status != 200:
            raise Exception(f"Partner request failed with status code {response.status}.")
        
        partners = await response.json()
        if 'data' not in partners:
            raise Exception("No data key in the partner response.")
        partners_data = partners['data']
        
        print(f"{len(partners_data)} partner commanders found.")

        partner_combos = combinations(partners_data, 2)
        matching_combos = [combo for combo in partner_combos if colors.issubset(set(combo[0]['color_identity'] + combo[1]['color_identity']))]
        for combo in matching_combos:
            first_partner = combo[0]
            second_partner = combo[1]
            names = sorted([first_partner["name"], second_partner["name"]])
            joined_name = ' + '.join(names)
            commanders[joined_name] = {"data": [first_partner, second_partner], "score": 0}
        return commanders
    

async def get_partner_with_commanders(session,colors):
    commanders = {}
    query = ''
    for color in colors:
        query += f'is:commander o:"Partner with" id>={color} OR '
    encoded_query = quote(query[:-4])
    url = f"https://api.scryfall.com/cards/search?q={encoded_query}"
    async with session.get(url) as response:
        if response.status != 200:
            raise Exception(f"'Partner with...' request failed with status code {response.status}")
        
        possible_commanders = await response.json()
        if 'data' not in possible_commanders:
            raise Exception("No 'data' key in the 'partner with...' response")
        possible_commander_data = possible_commanders["data"]

        print(f"{len(possible_commander_data)} pwith commanders found.")

        partner_data = {}
        for partner in possible_commander_data:
            partner_data[partner["name"]] = {
                "data": partner,
                "color_identity": partner["color_identity"],
            }

        for first_partner in possible_commander_data:
            for part in first_partner["all_parts"]:
                if part["object"] == "related_card" and part["name"] != first_partner["name"] and 'Legendary' in part["type_line"]:
                    second_partner_name = part["name"]
            if second_partner_name in partner_data:
                color_id = set(partner_data[first_partner["name"]]["color_identity"] + partner_data[second_partner_name]["color_identity"])
                if colors.issubset(color_id):
                    name_list = sorted([first_partner["name"], second_partner_name])
                    joined_name = ' + '.join(name_list)
                    commanders[joined_name] = {"data": [first_partner, partner_data[second_partner_name]["data"]], "score": 0}

        return commanders
    
async def get_doctor_who_commanders(session,colors):
    commanders = {}

    companion_query = ''
    for color in colors:
        companion_query += f'is:commander o:"Doctor\'s companion" id>={color} OR '
    encoded_companion_query = quote(companion_query[:-4])
    companion_url = f"https://api.scryfall.com/cards/search?q={encoded_companion_query}"

    doctor_query = ''
    for color in colors:
        doctor_query += f'is:commander t:"Time Lord Doctor" id>={color} OR '
    encoded_doctor_query = quote(doctor_query[:-4])
    doctor_url = f"https://api.scryfall.com/cards/search?q={encoded_doctor_query}"

    async with session.get(companion_url) as companions_response:
        if companions_response.status != 200:
            raise Exception(f"Companion request failed with status code {companions_response.status}")
        companions = await companions_response.json()

    async with session.get(doctor_url) as doctors_response:
        if doctors_response.status != 200:
            raise Exception(f"Doctor request failed with status code {doctors_response.status} colors: {colors} doctorurl: {doctor_url}")
        doctors = await doctors_response.json()

    if 'data' not in companions or 'data' not in doctors:
        raise Exception("No 'data' key in the 'doctor/companion' responses")
    
    doctor_data = doctors["data"]
    companion_data = companions["data"]

    print(f"{len(doctors['data'])} doctor commanders found.")

    for doctor in doctor_data:
        for companion in companion_data:
            combined_colors = set(doctor['color_identity'] + companion['color_identity'])
            if colors.issubset(combined_colors):
                joined_name = f'{doctor["name"]} + {companion["name"]}'
                commanders[joined_name] = {"data": [doctor, companion], "score": 0}

    return commanders

async def get_background_commanders(session,colors):
    commanders = {}

    creature_query = ''
    for color in colors:
        creature_query += f'is:commander o:"Choose a Background" id>={color} OR '
    encoded_creature_query = quote(creature_query[:-4])
    creature_url = f"https://api.scryfall.com/cards/search?q={encoded_creature_query}"

    background_query = ''
    for color in colors:
        background_query += f't:background id>={color} OR '
    encoded_background_query = quote(background_query[:-4])
    background_url = f"https://api.scryfall.com/cards/search?q={encoded_background_query}"

    async with session.get(creature_url) as creature_response:
        if creature_response.status != 200:
            raise Exception(f"Creature(background) request failed with status code {creature_response.status}")
        creatures = await creature_response.json()

    async with session.get(background_url) as background_response:
        if background_response.status != 200:
            raise Exception(f"Background request failed with status code {background_response.status}")
        backgrounds = await background_response.json()

    if 'data' not in creatures or 'data' not in backgrounds:
        raise Exception("No 'data' key in the 'creature/background' responses")
    
    print(f"{len(creatures['data'])} bg commanders found")

    creature_data = creatures["data"]
    background_data = backgrounds["data"]

    for creature in creature_data:
        creature_colors = set(creature["color_identity"])
        deficit = colors - creature_colors
        valid_backgrounds = filter(lambda bg: deficit.issubset(bg["color_identity"]), background_data)
        for background in valid_backgrounds:
            name_list = [creature['name'], background['name']]
            joined_name = ' + '.join(name_list)
            commanders[joined_name] = {"data": [creature, background], "score": 0}
    return commanders

async def get_friends_forever_commanders(session,colors):
    commanders = {}
    query = ''
    for color in colors:
        query += f'is:commander o:"Friends forever" id>={color} OR '
    encoded_query = quote(query[:-4])
    url = f"https://api.scryfall.com/cards/search?q={encoded_query}"
    async with session.get(url) as response:
        if response.status == 200:
            
            friends = await response.json()
            
            print(f"{len(friends['data'])} friends forever commanders found")

            friends_data = friends["data"]
            friend_combos = combinations(friends_data, 2)
            matching_combos = [combo for combo in friend_combos if colors.issubset(set(combo[0]['color_identity'] + combo[1]['color_identity']))]
            for combo in matching_combos:
                first_friend = combo[0]
                second_friend = combo[1]
                names = sorted([first_friend["name"], second_friend["name"]])
                joined_name = ' + '.join(names)
                commanders[joined_name] = {"data": [first_friend, second_friend], "score": 0}
        
        else:
            print(f"No color matches in Friends Forever")
    return commanders

def format_name_for_edhrec(name):
    specials = "àáâãäåèéêëìíîïòóôõöùúûüýÿñç "
    replacements = "aaaaaaeeeeiiiiooooouuuuyync-"
    removals = ",'.\""
    char_map = str.maketrans(specials, replacements, removals)

    formatted_name = (
        name.split('/')[0]
        .replace(' + ', ' ')
        .strip()
        .lower()
        .translate(char_map)
    )
    return formatted_name

async def get_score_from_edhrec(session, commander_name, formatted_name, cards): 
    match_base_value = 2
    card_is_commander_value = 2
    high_synergy_value = 1
    high_inclusion_value = 1

    total_score = 0

    url = f"https://json.edhrec.com/pages/commanders/{formatted_name}.json"

    try:
        async with session.get(url) as response:
            if response.status == 200:
                json_data = await response.json()
                if 'cardlist' in json_data:
                    edhrec_cards = {card['name']: card for card in json_data['cardlist']}

                    for card in cards:
                        if card["name"] == commander_name:
                            total_score += card_is_commander_value

                        edhrec_card = edhrec_cards.get(card["name"])
                        if edhrec_card:
                            total_score += match_base_value

                            if edhrec_card['synergy'] >= 0.3: 
                                total_score += high_synergy_value
                            if edhrec_card['num_decks'] / edhrec_card['potential_decks'] >= 0.4:
                                total_score += high_inclusion_value

    except Exception as e:
        print(f"An error occurred: {e}")

    return round(total_score/len(cards)*2.5)

async def get_score(session, commander, data):
    await asyncio.sleep(0.05)  # 50 ms delay to respect rate limit
    cards = [card for name,card in data.items()]
    score = await get_score_from_edhrec(session, commander, format_name_for_edhrec(commander), cards)
    return commander, score

async def score_commanders(data, commanders):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for commander in commanders:
            task = asyncio.create_task(get_score(session, commander, data))
            tasks.append(task)
        results = await asyncio.gather(*tasks)

    for commander, score in results:
        commanders[commander]["score"] = score
    
    return commanders

async def get_commanders(colors):
    async with aiohttp.ClientSession() as scryfall_session:
        tasks =[ 
            asyncio.create_task(get_solo_commanders(scryfall_session,colors)),
            asyncio.create_task(get_partner_commanders(scryfall_session,colors)),
            asyncio.create_task(get_partner_with_commanders(scryfall_session,colors)),
            asyncio.create_task(get_background_commanders(scryfall_session,colors)),
            asyncio.create_task(get_friends_forever_commanders(scryfall_session,colors)),
            asyncio.create_task(get_doctor_who_commanders(scryfall_session,colors))
        ]
        commanders = await asyncio.gather(*tasks)
    return commanders

def run(user_entries):

    colors = get_full_color_identity(user_entries)
    print(colors)

    commanders = {}
    commanders_list = asyncio.run(get_commanders(colors))

    for commander in commanders_list:
        commanders.update(commander)

    scored_commanders = asyncio.run(score_commanders(user_entries, commanders))

    return scored_commanders