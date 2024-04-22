import time
import requests
import json
import aiohttp
import asyncio


def get_full_color_identity(cards):
    colors = set()
    for name, card in cards.items():
        for color in card['color_identity']:
            colors.add(color.upper())
    return ''.join(colors)
    
async def get_solo_commanders_from_scryfall(scryfall_session,colors):
    commanders = {}
    solo_url = f"https://api.scryfall.com/cards/search?q=id%3E%3D{colors}%20t%3Alegend%20t%3Acreature"
    async with scryfall_session.get(solo_url) as response:
        if response.status != 200:
            raise Exception(f"Solo request failed with status code {response.status}")

        possible_commanders = await response.json()
        if 'data' not in possible_commanders:
            raise Exception("No 'data' key in the solo response")
        
        print(f"{len(possible_commanders['data'])} solo commanders found")

        for commander in possible_commanders["data"]:
            if commander["legalities"]["commander"] == 'legal':
                commanders[commander["name"]] = {"data": commander, "score": 0}
        return commanders

async def get_partner_commanders_from_scryfall(scryfall_session,colors):
    commanders = {}
    partners_url = f"https://api.scryfall.com/cards/search?q=id%3A{colors}%20t%3Alegend%20t%3Acreature%20o%3A%22Partner%22%20%2Do%3A%22Partner%20with%22"
    async with scryfall_session.get(partners_url) as partner_response:
        if partner_response.status != 200:
            raise Exception(f"Partner request failed with status code {partner_response.status}")
        
        possible_partners = await partner_response.json()
        if 'data' not in possible_partners:
            raise Exception("No 'data' key in the partner response")
        
        print(f"{len(possible_partners['data'])} partner commanders found")

        for first_partner in possible_partners["data"]:
            if first_partner["legalities"]["commander"] == 'legal':
                deficit = [color for color in colors if color not in first_partner["color_identity"]]
                for second_partner in possible_partners["data"]:
                    if all(color in second_partner["color_identity"] for color in deficit) and second_partner["legalities"]["commander"] == 'legal':
                        name_list = [first_partner['name'], second_partner['name']]
                        joined_name = ' + '.join(sorted(name_list))
                        commanders[joined_name] = {"data": [first_partner, second_partner], "score": 0}
        return commanders
async def get_partner_with_commanders_from_scryfall(scryfall_session,colors):
    commanders = {}
    partner_with_url = f"https://api.scryfall.com/cards/search?q=id%3A{colors}%20t%3Alegend%20o%3A%22Partner%20with%20%22"
    async with scryfall_session.get(partner_with_url) as partner_with_response:
        if partner_with_response.status != 200:
            raise Exception(f"'Partner with...' request failed with status code {partner_with_response.status}")
        
        possible_partner_withs = await partner_with_response.json()
        if 'data' not in possible_partner_withs:
            raise Exception("No 'data' key in the 'partner with...' response")
        
        print(f"{len(possible_partner_withs['data'])} pwith commanders found")

        for first_partner in possible_partner_withs["data"]:
            if first_partner["legalities"]["commander"] == 'legal':
                color_id = first_partner["color_identity"]

                for part in first_partner["all_parts"]:
                    if part["object"] == "related_card" and part["name"] != first_partner["name"] and 'Legendary Creature' in part["type_line"]:
                        second_partner_name = part["name"]

                for second_partner in possible_partner_withs["data"]:
                    if second_partner["name"] == second_partner_name and second_partner["legalities"]["commander"] == 'legal':
                        for color in second_partner["color_identity"]:
                            if color not in color_id:
                                color_id.append(color)

                        if all(color in color_id for color in colors):
                            name_list = [first_partner["name"], second_partner["name"]]
                            joined_name = ' + '.join(sorted(name_list))
                            commanders[joined_name] = {"data": [first_partner, second_partner], "score": 0}
        return commanders

async def get_doctor_who_commanders_from_scryfall(scryfall_session,colors):
    commanders = {}
    companion_url = f"https://api.scryfall.com/cards/search?q=id%3A{colors}%20t%3Acreature%20o%3A%22Doctor%27s%20companion%22"
    doctor_url = f"https://api.scryfall.com/cards/search?q=id%3A{colors}%20t%3Atime%20t%3Alord%20t%3Adoctor"

    async with scryfall_session.get(companion_url) as companions_response:
        if companions_response.status != 200:
            raise Exception(f"Companion request failed with status code {companions_response.status}")
        companions = await companions_response.json()
    async with scryfall_session.get(doctor_url) as doctors_response:
        if doctors_response.status != 200:
            raise Exception(f"Doctor request failed with status code {doctors_response.status}")
        doctors = await doctors_response.json()

    if 'data' not in companions or 'data' not in doctors:
        raise Exception("No 'data' key in the 'doctor/companion' responses")
    
    print(f"{len(doctors['data'])} doctor commanders found")

    for doctor in doctors['data']:
        if doctor["legalities"]["commander"] == 'legal':
            deficit = [color for color in colors if color not in doctor["color_identity"]]
            for companion in companions["data"]:
                if all(color in companion["color_identity"] for color in deficit) and companion["legalities"]["commander"] == 'legal':
                    name_list = [doctor['name'], companion['name']]
                    joined_name = ' + '.join(name_list)
                    commanders[joined_name] = {"data": [doctor, companion], "score": 0}
    return commanders

async def get_background_commanders_from_scryfall(scryfall_session,colors):
    commanders = {}
    creature_url = f"https://api.scryfall.com/cards/search?q=id%3A{colors}%20t%3Acreature%20t%3Alegend%20o%3A%22Choose%20a%20Background%22"
    background_url = f"https://api.scryfall.com/cards/search?q=id%3A{colors}%20t%3Aenchantment%20t%3Alegend%20t%3ABackground"

    async with scryfall_session.get(creature_url) as creature_response:
        if creature_response.status != 200:
            raise Exception(f"Creature(background) request failed with status code {creature_response.status}")
        creatures = await creature_response.json()
    async with scryfall_session.get(background_url) as background_response:
        if background_response.status != 200:
            raise Exception(f"Background request failed with status code {background_response.status}")
        backgrounds = await background_response.json()

    if 'data' not in creatures or 'data' not in backgrounds:
        raise Exception("No 'data' key in the 'creature/background' responses")
    
    print(f"{len(creatures['data'])} bg commanders found")

    for creature in creatures['data']:
        if creature["legalities"]["commander"] == 'legal':
            deficit = [color for color in colors if color not in creature["color_identity"]]
            for background in backgrounds["data"]:
                if all(color in background["color_identity"] for color in deficit) and background["legalities"]["commander"] == 'legal':
                    name_list = [creature['name'], background['name']]
                    joined_name = ' + '.join(name_list)
                    commanders[joined_name] = {"data": [creature, background], "score": 0}
    return commanders

async def get_friends_forever_commanders_from_scryfall(scryfall_session,colors):
    commanders = {}
    friends_url = f"https://api.scryfall.com/cards/search?q=id%3A{colors}%20t%3Alegend%20t%3Acreature%20o%3A%22Friends%20forever%22"
    async with scryfall_session.get(friends_url) as friends_response:
        if friends_response.status == 200:
            
            friends = await friends_response.json()
            
            print(f"{len(friends['data'])} friends forever commanders found")

            for first_friend in friends["data"]:
                if first_friend["legalities"]["commander"] == 'legal':
                    deficit = [color for color in colors if color not in first_friend["color_identity"]]
                    for second_friend in friends["data"]:
                        if all(color in second_friend["color_identity"] for color in deficit) and second_friend["legalities"]["commander"] == 'legal':
                            name_list = [first_friend['name'], second_friend['name']]
                            joined_name = ' + '.join(sorted(name_list))
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
    print(f"get_score output: {commander, score}")
    return commander, score

async def main(data, commanders):
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
            asyncio.create_task(get_solo_commanders_from_scryfall(scryfall_session,colors)),
            asyncio.create_task(get_partner_commanders_from_scryfall(scryfall_session,colors)),
            asyncio.create_task(get_partner_with_commanders_from_scryfall(scryfall_session,colors)),
            asyncio.create_task(get_background_commanders_from_scryfall(scryfall_session,colors)),
            asyncio.create_task(get_friends_forever_commanders_from_scryfall(scryfall_session,colors)),
            asyncio.create_task(get_doctor_who_commanders_from_scryfall(scryfall_session,colors))
        ]
        total_commanders = await asyncio.gather(*tasks)
    return total_commanders

def run(data):

    colors = get_full_color_identity(data)
    print(colors)

    commanders = {}
    total_commanders = asyncio.run(get_commanders(colors))

    for commander in total_commanders:
        commanders.update(commander)
    # print(commanders)
    scored_commanders = asyncio.run(main(data, commanders))
    # print(scored_commanders)
    return scored_commanders

if __name__ == "__main__":
    run(data)