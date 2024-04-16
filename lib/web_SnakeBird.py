import time
import requests

entries = []
colors = []

def add_user_entry_to_list(entry):
    response = requests.get(f"https://api.scryfall.com/cards/named?fuzzy={entry}")
    json_card = response.json()
    try:
        if json_card["legalities"]["commander"] == "legal":
            color_id = json_card["color_identity"] #list of single letter strings i.e. ["B","G","R","U","W"]

            entries.append(json_card)

            for color in color_id:
                if color not in colors:
                    colors.append(color)

        time.sleep(0.05) # Respecting Scryfall's API query rate guidelines
    except KeyError:
        print(f"No card found for '{entry}'")