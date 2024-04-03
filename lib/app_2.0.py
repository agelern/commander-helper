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
def get_commanders_from_scryfall(colors):

    # Solo Commanders
    identity = ','.join(colors)
    solo_url = f"https://api.scryfall.com/cards/search?q=id%3E%3D{identity}%20t%3Alegend%20t%3Acreature"
    response = requests.get(solo_url)
    if response.status_code != 200:
        raise Exception(f"Request failed with status code {response.status_code}")

    possible_commanders = response.json()
    if 'data' not in possible_commanders:
        raise Exception("No 'data' key in the response")

    for commander in possible_commanders["data"]:
        if commander["legalities"]["commander"] == 'legal':
            returned_commanders[commander["name"]] = {"data": commander, "score": 0}

    # Partnered Commanders
    partners_url = f"https://api.scryfall.com/cards/search?q=id%3C%3D{identity}%20t%3Alegend%20t%3Acreature%20o%3A%22Partner%22%20%2Do%3A%22Partner%20with%22"
    response = requests.get(partners_url)
    if response.status_code != 200:
        raise Exception(f"Request failed with status code {response.status_code}")
    
    possible_partners = response.json()
    if 'data' not in possible_partners:
        raise Exception("No 'data' key in the response")
    
    for first_partner in possible_partners["data"]: # this is technically running each duo twice. fix soon.
        if first_partner["legalities"]["commander"] == 'legal':
            deficit = [color for color in colors if color not in first_partner["color_identity"]]
            for second_partner in possible_partners["data"]:
                if second_partner["color_identity"] == deficit and second_partner["legalities"]["commander"] == 'legal':
                    name_list = [first_partner['name'], second_partner['name']]
                    joined_name = ' + '.join(sorted(name_list))
                    returned_commanders[joined_name] = {"data": [first_partner, second_partner], "score": 0}

    # "Partner with..." Commanders
    partner_with_url = f"https://api.scryfall.com/cards/search?q=id%3A{identity}%20t%3Alegend%20o%3A%22Partner%20with%20%22"
    response = requests.get(partner_with_url)
    if response.status_code != 200:
        raise Exception(f"Request failed with status code {response.status_code}")
    
    possible_partner_withs = response.json()
    if 'data' not in possible_partner_withs:
        raise Exception("No 'data' key in the response")
    
    for first_partner in possible_partner_withs["data"]:
        # print(f"+++ assessing {first_partner['name']} +++")
        if first_partner["legalities"]["commander"] == 'legal':
            # print(f"First partner is legal. Assembling pair for {first_partner['name']}")
            color_id = first_partner["color_identity"]

            for part in first_partner["all_parts"]:
                if part["object"] == "related_card" and part["name"] != first_partner["name"] and 'Legendary Creature' in part["type_line"]:
                    second_partner_name = part["name"]
                    # print(f"Partner found: {second_partner_name}")
            # print("--- beginning second partner info dig ---")
            for second_partner in possible_partner_withs["data"]:
                if second_partner["name"] == second_partner_name and second_partner["legalities"]["commander"] == 'legal':
                    # print(f"{first_partner['name']}'s partner is {second_partner['name']}")
                    for color in second_partner["color_identity"]:
                        if color not in color_id:
                            color_id.append(color)
                    # print(f"The pair's colors are {color_id} Adequate?{all(color in color_id for color in colors)}")
                    if all(color in color_id for color in colors):
                        name_list = [first_partner["name"], second_partner["name"]]
                        joined_name = ' + '.join(sorted(name_list))
                        returned_commanders[joined_name] = {"data": [first_partner, second_partner], "score": 0}


        
def format_name_for_edhrec(name):
    specials = "àáâãäåèéêëìíîïòóôõöùúûüýÿñç "
    replacements = "aaaaaaeeeeiiiiooooouuuuyync-"
    removals = ",'."
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
    print(f"Scoring {commander_name}...")
    score = 0
    url = f"https://json.edhrec.com/pages/commanders/{formatted_name}.json"

    response = requests.get(url)
    if response.status_code != 200:
        print(f"{formatted_name} not found at EDHREC endpoint.")
        return

    json_data = response.json()

    scored_cards = []

    for card in entered_cards:
        if card["name"] == commander_name:
            score += card_is_commander_value
        try:
            for edhrec_card in json_data['cardlist']:
                if card["name"] == edhrec_card['name']:
                    score += match_base_value
                    if edhrec_card['synergy'] >= 0.3: 
                        score += high_synergy_value
                    if edhrec_card['num_decks'] / edhrec_card['potential_decks'] >= 0.4:
                        score += high_inclusion_value
                    scored_cards.append(card["name"])
        except KeyError:
            print(f"No data found for {commander_name}. Skipping for subsequent cards.")
            del returned_commanders[commander_name]
            break
    print("...done.")

    returned_commanders[commander_name]["score"] = round(score/len(entered_cards)*2.5)
    time.sleep(0.05)

def output_top_ten(returned_commanders):
    print("--- Top Commanders ---")
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

    get_commanders_from_scryfall(colors)
    print(f"{len(returned_commanders)} possible commanders found.")
    for commander in returned_commanders:
        print(commander)

    for commander in returned_commanders:
        get_score_from_edhrec(commander, format_name_for_edhrec(commander))

    output_top_ten(returned_commanders)
