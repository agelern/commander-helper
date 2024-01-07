from flask import Flask, render_template, request
from lib.app import *
import json

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/get_card_names', methods=['GET'])
def get_card_names():
    card_names = fetch_card_names()
    return json.dumps(card_names)

@app.route('/', methods=['POST'])
def process_form():
    card_list = request.form.get('listOfNames')
    return output(poll_edhrec(get_commanders(db_connect(), card_list)))

if __name__ == '__main__':
    app.run(port=5000, host="0.0.0.0")
