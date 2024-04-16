from flask import Flask, render_template
import json

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(port=5000, host="0.0.0.0")
