import time
import requests

entered_cards = []
colors = []
returned_commanders = {}

# Edit values below to change score weighting
match_base_value = 2
card_is_commander_value = 2
high_synergy_value = 1
high_inclusion_value = 1

debug = False


def get_user_input():
    user_entries = []
    while True:
        item = input("Enter a card or press return to begin search: ")
        if item == '':
            break
        user_entries.append(item.strip())
    return user_entries

def get_cards_from_scryfall(user_entries):
    for card_name in user_entries:
        response = requests.get(f"https://api.scryfall.com/cards/named?fuzzy={card_name}")
        json_card = response.json()
        try:
            if json_card["legalities"]["commander"] == "legal":
                color_id = json_card["color_identity"] #list of single letter strings i.e. ["B","G","R","U","W"]

                entered_cards.append(json_card)

                for color in color_id:
                    if color not in colors:
                        colors.append(color)

            time.sleep(0.05) # Respecting Scryfall's API query rate guidelines
        except KeyError:
            print(f"No card found for '{card_name}'")

def get_solo_commanders_from_scryfall(colors):

    # Solo Commanders
    identity = ','.join(colors)
    solo_url = f"https://api.scryfall.com/cards/search?q=id%3E%3D{identity}%20t%3Alegend%20t%3Acreature"
    response = scryfall_session.get(solo_url)
    if response.status_code != 200:
        raise Exception(f"Solo request failed with status code {response.status_code}")

    possible_commanders = response.json()
    if 'data' not in possible_commanders:
        raise Exception("No 'data' key in the solo response")

    for commander in possible_commanders["data"]:
        if commander["legalities"]["commander"] == 'legal':
            returned_commanders[commander["name"]] = {"data": commander, "score": 0}

def get_partner_commanders_from_scryfall(colors):
    identity = ','.join(colors)
    partners_url = f"https://api.scryfall.com/cards/search?q=id%3A{identity}%20t%3Alegend%20t%3Acreature%20o%3A%22Partner%22%20%2Do%3A%22Partner%20with%22"
    partner_response = scryfall_session.get(partners_url)
    if partner_response.status_code != 200:
        raise Exception(f"Partner request failed with status code {partner_response.status_code}")
    
    possible_partners = partner_response.json()
    if 'data' not in possible_partners:
        raise Exception("No 'data' key in the partner response")
    
    for first_partner in possible_partners["data"]:
        if first_partner["legalities"]["commander"] == 'legal':
            deficit = [color for color in colors if color not in first_partner["color_identity"]]
            for second_partner in possible_partners["data"]:
                if all(color in second_partner["color_identity"] for color in deficit) and second_partner["legalities"]["commander"] == 'legal':
                    name_list = [first_partner['name'], second_partner['name']]
                    joined_name = ' + '.join(sorted(name_list))
                    returned_commanders[joined_name] = {"data": [first_partner, second_partner], "score": 0}

def get_partner_with_commanders_from_scryfall(colors):
    identity = ','.join(colors)
    partner_with_url = f"https://api.scryfall.com/cards/search?q=id%3A{identity}%20t%3Alegend%20o%3A%22Partner%20with%20%22"
    partner_with_response = scryfall_session.get(partner_with_url)
    if partner_with_response.status_code != 200:
        raise Exception(f"'Partner with...' request failed with status code {partner_with_response.status_code}")
    
    possible_partner_withs = partner_with_response.json()
    if 'data' not in possible_partner_withs:
        raise Exception("No 'data' key in the 'partner with...' response")
    
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
                        returned_commanders[joined_name] = {"data": [first_partner, second_partner], "score": 0}

def get_doctor_who_commanders_from_scryfall(colors):
    identity = ','.join(colors)
    if 'B' not in colors:
        companion_url = f"https://api.scryfall.com/cards/search?q=id%3A{identity}%20t%3Acreature%20o%3A%22Doctor%27s%20companion%22"
        doctor_url = f"https://api.scryfall.com/cards/search?q=id%3A{identity}%20t%3Atime%20t%3Alord%20t%3Adoctor"

        companions_response = scryfall_session.get(companion_url)
        doctors_response = scryfall_session.get(doctor_url)
        if companions_response.status_code != 200:
            raise Exception(f"Companion request failed with status code {companions_response.status_code}")
        if doctors_response.status_code != 200:
            raise Exception(f"Doctor request failed with status code {doctors_response.status_code}")

        companions = companions_response.json()
        doctors = doctors_response.json()
        if 'data' not in companions or 'data' not in doctors:
            raise Exception("No 'data' key in the 'doctor/companion' responses")
        
        for doctor in doctors['data']:
            if doctor["legalities"]["commander"] == 'legal':
                deficit = [color for color in colors if color not in doctor["color_identity"]]
                for companion in companions["data"]:
                    if all(color in companion["color_identity"] for color in deficit) and companion["legalities"]["commander"] == 'legal':
                        name_list = [doctor['name'], companion['name']]
                        joined_name = ' + '.join(name_list)
                        returned_commanders[joined_name] = {"data": [doctor, companion], "score": 0}

def get_background_commanders_from_scryfall(colors):
    identity = ','.join(colors)
    creature_url = f"https://api.scryfall.com/cards/search?q=id%3A{identity}%20t%3Acreature%20t%3Alegend%20o%3A%22Choose%20a%20Background%22"
    background_url = f"https://api.scryfall.com/cards/search?q=id%3A{identity}%20t%3Aenchantment%20t%3Alegend%20t%3ABackground"

    creature_response = scryfall_session.get(creature_url)
    background_response = scryfall_session.get(background_url)
    if creature_response.status_code != 200:
        raise Exception(f"Creature(background) request failed with status code {creature_response.status_code}")
    if background_response.status_code != 200:
        raise Exception(f"Background request failed with status code {background_response.status_code}")

    creatures = creature_response.json()
    backgrounds = background_response.json()
    if 'data' not in creatures or 'data' not in backgrounds:
        raise Exception("No 'data' key in the 'creature/background' responses")
    
    for creature in creatures['data']:
        if creature["legalities"]["commander"] == 'legal':
            deficit = [color for color in colors if color not in creature["color_identity"]]
            for background in backgrounds["data"]:
                if all(color in background["color_identity"] for color in deficit) and background["legalities"]["commander"] == 'legal':
                    name_list = [creature['name'], background['name']]
                    joined_name = ' + '.join(name_list)
                    returned_commanders[joined_name] = {"data": [creature, background], "score": 0}

def get_friends_forever_commanders_from_scryfall(colors):
    identity = ','.join(colors)
    friends_url = f"https://api.scryfall.com/cards/search?q=id%3A{identity}%20t%3Alegend%20t%3Acreature%20o%3A%22Friends%20forever%22"
    friends_response = scryfall_session.get(friends_url)
    if friends_response.status_code == 200:
        
        friends = friends_response.json()
        
        for first_friend in friends["data"]:
            if first_friend["legalities"]["commander"] == 'legal':
                deficit = [color for color in colors if color not in first_friend["color_identity"]]
                for second_friend in friends["data"]:
                    if all(color in second_friend["color_identity"] for color in deficit) and second_friend["legalities"]["commander"] == 'legal':
                        name_list = [first_friend['name'], second_friend['name']]
                        joined_name = ' + '.join(sorted(name_list))
                        returned_commanders[joined_name] = {"data": [first_friend, second_friend], "score": 0}
    else:
        print(f"No color matches in Friends Forever")

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

def get_score_from_edhrec(commander_name, formatted_name): 

    score = 0
    url = f"https://json.edhrec.com/pages/commanders/{formatted_name}.json"

    response = edhrec_session.get(url)
    if response.status_code == 200:
        json_data = response.json()
        if 'cardlist' in json_data:
            scored_cards = []

            for card in entered_cards:
                if card["name"] == commander_name:
                    score += card_is_commander_value

                for edhrec_card in json_data['cardlist']:
                    if card["name"] == edhrec_card['name']:
                        score += match_base_value

                        if edhrec_card['synergy'] >= 0.3: 
                            score += high_synergy_value
                        if edhrec_card['num_decks'] / edhrec_card['potential_decks'] >= 0.4:
                            score += high_inclusion_value

                        scored_cards.append(card["name"])

            returned_commanders[commander_name]["score"] = round(score/len(entered_cards)*2.5)
            time.sleep(0.05)
        else:
            if debug:
                print(f"No data found for {formatted_name} in return from EDHREC")
    else:
        if debug:
            print(f"{formatted_name} not found at EDHREC.")

def output_top_ten(returned_commanders):
    print("\n--- Top Commanders ---\n")
    sorted_commanders = dict(sorted(returned_commanders.items(), key=lambda item: item[1]["score"], reverse=True))

    for i, (commander, datascore) in enumerate(sorted_commanders.items()):
        if i >= 10 or datascore['score'] == 0:
            break
        print(f"{i+1}.{commander}") 
        print(f"Score: {datascore['score']}/10\n")



if __name__ == "__main__":

    get_cards_from_scryfall(get_user_input())
    print(f"Cards Found: {', '.join([card['name'] for card in entered_cards])}")
    print(f"Colors: {''.join(colors)}")

    with requests.Session() as scryfall_session:
        print("Retrieving Solo Commanders...")
        get_solo_commanders_from_scryfall(colors)

        print("Retrieving Partner Commanders...")
        get_partner_commanders_from_scryfall(colors)

        print("Retrieving 'Partner With' Commanders...")
        get_partner_with_commanders_from_scryfall(colors)

        print("Retrieving Background Commanders...")
        get_background_commanders_from_scryfall(colors)

        print("Retrieving Worlds Beyond Commanders...")
        get_friends_forever_commanders_from_scryfall(colors)
        get_doctor_who_commanders_from_scryfall(colors)

    print(f"{len(returned_commanders)} possible commanders found.")

    if debug:
        for commander in returned_commanders:
            print(commander)

    print("Scoring commanders... (This may take a moment)")
    with requests.Session() as edhrec_session:
        for commander in returned_commanders:
            get_score_from_edhrec(commander, format_name_for_edhrec(commander))

    output_top_ten(returned_commanders)
