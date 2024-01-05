from dotenv import load_dotenv
import os
import psycopg2
import pandas as pd
from sqlalchemy import create_engine
import requests

def db_connect():
    # Load environment variables
    load_dotenv()
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')

    # Connect to local MTG database for faster initial retrieval
    conn = psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_password
    )
    engine = create_engine(f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}")
    connection = engine.connect()
    return connection

def user_input():
    # Enter list of cards to match to a commander
    while True:
        item = input("Enter a card (exact spelling) or 'done' to finish: ")
        if item.lower() == 'done':
            break
        items.append(item.strip())
    return items

def get_commanders(connection, items):
    # Retrieve the cards and report
    items_str = "', '".join(items)
    query = f"SELECT DISTINCT name, coloridentity FROM cards WHERE name IN ('{items_str}');"
    result_df = pd.read_sql(query, connection)
    if len(items) == len(result_df):
        print('All items found')
    else:
        valid_items = [item for item in result_df["name"]]
        invalid_items = [item for item in items if item not in valid_items]

        print(f'Items found: {valid_items}')
        print(f'Ignoring invalid items: {invalid_items}')

    identities = [x.replace(',', '').replace(' ', '') for x in result_df['coloridentity'] if x is not None]
    identities_string = ''.join(identities)
    command_color = list(''.join(dict.fromkeys(identities_string)))

    print(f'\nCommander Color Identity: {", ".join(sorted(command_color))}\n')

    # Some SQL hackery to grab multiple values
    color_conditions = 'AND ' + ' AND '.join([f"coloridentity LIKE '%%{color}%%'" for color in command_color])
    if color_conditions == 'AND ':
        color_conditions = ''

    query = f"""
        SELECT DISTINCT name, edhrecrank, coloridentity, type, text, uuid 
        FROM (
            SELECT *
            FROM cards
            WHERE id in (select min(id) from cards group by name)
        ) unique_names
        WHERE type LIKE '%%Legendary%%Creature%%' 
            {color_conditions}
            AND edhrecrank >= 0
        ORDER BY edhrecrank
        """

    commander_df = pd.read_sql(query, connection)
    print(f'{len(commander_df)} viable commanders found.')
    return commander_df

def score(creature_name):
    creature_name = creature_name.lower().replace('[^a-zA-Z0-9]', '').replace(' ', '-').replace(',', '').replace("'", '')
    score = 0
    url = f"https://json.edhrec.com/pages/commanders/{creature_name}.json"
    response = requests.get(url)
    if response.status_code == 200:
        json_data = response.json()
        if 'cardlist' in json_data:
            scoring_cards = []
            for entered_card in items:
                for edhrec_card in json_data['cardlist']:
                    if entered_card == edhrec_card['name']:
                        score += 1
                        if edhrec_card['synergy'] >= 0.3:
                            score += 1
                        if edhrec_card['num_decks'] / edhrec_card['potential_decks'] >= 0.4:
                            score += 1
                        scoring_cards.append(entered_card)
            return score, scoring_cards
        else:
            return 0, []
    else:
        return 0, []

def poll_edhrec(commander_df):
    # All the calculations happen here
    print('Scoring cards...')
    commander_df['score'], commander_df['makesGoodUseOf'] = zip(*commander_df['name'].apply(score))
    commander_df['wholeness'] = commander_df['makesGoodUseOf'].apply(lambda x: len(x))

    commander_df = commander_df.sort_values(['wholeness', 'score', 'edhrecrank'], ascending=[False, False, True]).reset_index(drop=True)
    top_10_df = commander_df[['score', 'name', 'coloridentity', 'wholeness',]].head(10)
    print(top_10_df)

items = []
user_input()
poll_edhrec(get_commanders(db_connect(), items))