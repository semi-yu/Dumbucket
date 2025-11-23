from flask import Flask, request, make_response
from dotenv import load_dotenv

from src.connection import ping
from src.file import save, load

load_dotenv()

app = Flask(__name__)

@app.route('/ping')
def pong():
    return ping()

@app.post('/store')
def store():
    if "file" not in request.files: return make_response("File is required", 400)

    file_content = request.files['file']
    file_name = request.files['file'].filename

    if not file_name: return make_response("File name is required", 400)

    save_result = save(file_name, file_content)

    if not save_result: return make_response("File could not be saved due to internal errors", 500)

    return make_response("File saved", 200)

@app.get('/fetch')
def fetch():
    if "" not in request.args: return make_response("")

if __name__ == "__main__":
    app.run()
