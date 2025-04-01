from flask import Flask

app = Flask(__name__)

from app import extractor
@app.route('/')
def home():
    return "Smart Bill Bot is Alive! Send POST to /extract"
