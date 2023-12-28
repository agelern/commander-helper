from dotenv import load_dotenv
import os
import psycopg2
import pandas as pd
from sqlalchemy import create_engine
import requests

# Load environment variables
load_dotenv()
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')

# Connect to my MTG database
conn = psycopg2.connect(
    host=db_host,
    database=db_name,
    user=db_user,
    password=db_password
)

# With the env variables loaded we can insert them into the engine connection string.
engine = create_engine(f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}")
connection = engine.connect()

# Enter list of cards to match to a commander
items = input("Enter a comma-separated list of cards (exact spelling): ").split(',')
items = [item.strip() for item in items]
print(f'Items Entered: {items}')

# Create a comma-separated string of items
items_str = "', '".join(items)

query = f"SELECT DISTINCT coloridentity FROM cards WHERE name IN ('{items_str}');"
result_df = pd.read_sql(query, connection)

identities = [x.replace(',', '').replace(' ', '') for x in result_df['coloridentity'] if x is not None]
identities_string = ''.join(identities)
command_color = list(''.join(dict.fromkeys(identities_string)))

print(f'\nCommander Color Identity: {command_color}\n')

color_conditions = ' AND '.join([f"coloridentity LIKE '%%{color}%%'" for color in command_color])

query = f"""
    SELECT DISTINCT name, edhrecrank, coloridentity, type, text, uuid 
    FROM (
        SELECT *
        FROM cards
        WHERE id in (select min(id) from cards group by name)
    ) unique_names
    WHERE type LIKE '%%Legendary%%Creature%%' 
        AND {color_conditions}
        AND edhrecrank >= 0
    ORDER BY edhrecrank
    LIMIT 100
    """

# Execute the query and store the results in a dataframe
commander_df = pd.read_sql(query, connection)
print('Viable commanders found.')


def score(creature_name):
    creature_name = creature_name.lower().replace('[^a-zA-Z0-9]', '').replace(' ', '-').replace(',', '').replace("'", '')
    score = 0
    url = f"https://json.edhrec.com/pages/commanders/{creature_name}.json"
    response = requests.get(url)
    if response.status_code == 200:
        json_data = response.json()
        scoring_cards = []  # List to store entered cards that increased the score
        for entered_card in items:
            for edhrec_card in json_data['cardlist']:
                if entered_card == edhrec_card['name']:
                    score += 1
                    if edhrec_card['synergy'] >= 0.3:
                        score += 1
                    if edhrec_card['num_decks'] / edhrec_card['potential_decks'] >= 0.4:
                        score += 1
                    scoring_cards.append(entered_card)  # Add entered card to the list
        return score, scoring_cards
    else:
        return 0, []


print('Scoring cards...')
commander_df['score'], commander_df['makesGoodUseOf'] = zip(*commander_df['name'].apply(score))

commander_df = commander_df.sort_values(['score', 'edhrecrank'], ascending=[False, True]).reset_index(drop=True)
top_10_df = commander_df[['score', 'edhrecrank', 'name', 'type', 'coloridentity', 'makesGoodUseOf']].head(10)
print(top_10_df)
