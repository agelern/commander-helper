from dotenv import load_dotenv
import os
import psycopg2
import pandas as pd
from sqlalchemy import create_engine
import requests
from thefuzz import process

def render_db_connect():
    # Load environment variables
    load_dotenv()
    db_user = os.getenv('RENDER_USER')
    db_password = os.getenv('RENDER_PASSWORD')
    db_host = os.getenv('RENDER_HOST')
    db_name = os.getenv('RENDER_NAME')

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

def send_local_to_render(local_connection, render_connection, table_name):
    