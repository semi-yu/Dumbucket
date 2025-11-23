from flask import Flask, request

from src.connection import ping

app = Flask(__name__)

@app.route('/ping')
def pong():
    return ping()

@app.route('/store', methods=['POST'])
def store(): ...

@app.route('/fetch', methods=['GET'])
def fetch(): ...

if __name__ == "__main__":
    app.run()
