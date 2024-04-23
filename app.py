from flask import Flask, render_template, request, jsonify
import json
from web_snakebird import run
import aiohttp
import asyncio

app = Flask(__name__)
app.debug = True

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def submit():
    data = request.get_json()
    commanders = run(data)
    return jsonify(commanders)

if __name__ == '__main__':
    app.run(port=5000, host="0.0.0.0")
