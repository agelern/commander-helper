from dotenv import load_dotenv
import os
import psycopg2
import pandas as pd
from sqlalchemy import create_engine
import requests
from thefuzz import process

# find partners on initial search << future fix

# initial get request should populate name database for fuzzy search

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
        item = input("Enter a card or press return to begin search: ")
        if item == '':
            break
        entries.append(item.strip())
    return entries

def fetch_card_names(connection): # for flask route
    query = "SELECT name FROM cards"
    df = pd.read_sql(query, connection)
    all_cards = df['name'].astype(str).values.tolist()
    return all_cards

def fuzzy_search_cleanup(connection, entries):
    #clean_entries is established globally because of a later use in the score() function
    query = f"SELECT name FROM cards"
    df = pd.read_sql(query, connection)
    all_cards = df['name'].astype(str).values.tolist()
    for entry in entries:
        better_entry = process.extractOne(entry, all_cards)
        if better_entry[1] > 80:
            clean_entries.append(better_entry[0].replace("'", "''"))
            print(f'Found {better_entry[0]} for "{entry}"')
        else:
            print(f'No results for "{entry}".')

def get_commanders(connection, clean_entries):
    if clean_entries is None:
        raise ValueError("Card list cannot be None.")
        
    clean_entries_str = "', '".join(clean_entries)

    query = f"SELECT DISTINCT name, coloridentity FROM cards WHERE name IN ('{clean_entries_str}');"
    result_df = pd.read_sql(query, connection)

    identities = [x.replace(',', '').replace(' ', '') for x in result_df['coloridentity'] if x is not None]
    identities_string = ''.join(identities)
    command_color = list(''.join(dict.fromkeys(identities_string)))
    
    print(f"\nSearching on {clean_entries}")
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

    formatted_name = creature_name.lower().replace('[^a-zA-Z0-9]', '').replace(' ', '-').replace(',', '').replace("'", '')
    score = 0
    url = f"https://json.edhrec.com/pages/commanders/{formatted_name}.json"
    response = requests.get(url)
    if response.status_code == 200:
        json_data = response.json()
        if 'cardlist' in json_data:
            scoring_cards = []
            for entered_card in clean_entries:
                if entered_card.replace("''", "'") == creature_name:
                    score += 4
                for edhrec_card in json_data['cardlist']:
                    if entered_card.replace("''", "'") == edhrec_card['name']:
                        score += 2
                        if edhrec_card['synergy'] >= 0.3:
                            score += 1
                        if edhrec_card['num_decks'] / edhrec_card['potential_decks'] >= 0.4:
                            score += 1
                        scoring_cards.append(entered_card)
            return round(score/len(clean_entries)*2.5), scoring_cards
        else:
            return 0, []
    else:
        return 0, []

def poll_edhrec(commander_df):

    print('Scoring cards...\n')
    commander_df['score'], commander_df['makesGoodUseOf'] = zip(*commander_df['name'].apply(score))
    commander_df['wholeness'] = commander_df['makesGoodUseOf'].apply(lambda x: len(x))

    commander_df = commander_df.sort_values(['wholeness', 'score', 'edhrecrank'], ascending=[False, False, True]).reset_index(drop=True)
    return commander_df

def online_output(commander_df):
    formatted_list = []
    for index, row in commander_df.head(10).iterrows():
        formatted_name = row['name'].lower().replace('[^a-zA-Z0-9]', '').replace(' ', '-').replace(',', '').replace("'", '')
        web_direct = f"edhrec.com/commanders/{formatted_name}"

        formatted_return = f"""{row['name']} || {row['coloridentity']} || Overall Score: {row['score']}/10
        Makes good use of: {row['makesGoodUseOf']}
        {web_direct}
        """

        formatted_list.append(formatted_return)
    return formatted_list

def output(commander_df):

    for index, row in commander_df.head(10).iterrows():
        formatted_name = row['name'].lower().replace('[^a-zA-Z0-9]', '').replace(' ', '-').replace(',', '').replace("'", '')
        web_direct = f"edhrec.com/commanders/{formatted_name}"

        print(f"""{row['name']} || {row['coloridentity']} || Overall Score: {row['score']}/10
        Makes good use of: {row['makesGoodUseOf']}
        {web_direct}
        """
        )

if __name__ == "__main__":
    entries = []
    clean_entries = []
    fuzzy_search_cleanup(db_connect(), user_input())
    output(poll_edhrec(get_commanders(db_connect(), clean_entries)))