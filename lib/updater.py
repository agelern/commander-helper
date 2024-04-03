import requests
import psycopg2

conn = psycopg2.connect(database="mtg", user="your_username", password="your_password", host="your_host", port="your_port")
cur = conn.cursor()

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'cards'")
columns = [row[0] for row in cur.fetchall()]

response = requests.get("https://api.scryfall.com/cards")

cards = response.json()["data"]
for card in cards:
    cur.execute("UPDATE cards SET column1 = %s, column2 = %s WHERE id = %s", (card["column1"], card["column2"], card["id"]))
    
    cur.execute("""
        INSERT INTO cards (id, column1, column2) 
        VALUES (%s, %s, %s) 
        ON CONFLICT (id) 
        DO NOTHING
    """, (card["id"], card["column1"], card["column2"]))

conn.commit()
cur.close()
conn.close()
