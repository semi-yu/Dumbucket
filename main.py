from flask import Flask, request, make_response, jsonify, redirect, url_for, render_template
from dotenv import load_dotenv

from src.connection import ping
from src.file import save, load
from src.error_handle.error import FileNotFound, InternalError
from src.error_handle.formalizer import formatter


load_dotenv()
app = Flask(__name__)

@app.route('/')
def index():
    return redirect(url_for('store'))

@app.route('/ping')
def pong():
    return make_response(ping(), 200)

@app.route('/store', methods=['GET', 'POST'])
def store():
    if request.method == 'GET': return render_template('store.html')
    
    if "file" not in request.files:
        return jsonify(formatter(400,
                         "File to store is required",
                         "File field is empty",
                         "Attach the file to store (obiously)"))

    file_content = request.files['file']
    filename = request.files['file'].filename
    if not filename:
        return jsonify(formatter(400,
                         "File name is required",
                         "File name is not valid",
                         "Provide an valid file name"))

    save_result = save(filename, file_content)
    if not save_result: 
        return jsonify(formatter(500, "File could not be saved due to internal errors"))

    return jsonify({
        'code': 200,
        'message': 'OK', 
        'data': {
            'filename': filename,
            'uuid': save_result.uuid
        }
    })

@app.get('/fetch')
def fetch():
    filename = request.args.get("filename")
    if not filename: return render_template('fetch.html')

    """
    if not filename:
        return jsonify(formatter(400,
                         "The location of a file is required",
                         "The filename field is empty",
                         "Provide an valid file name"))    
    """

    try:
        load_result = load(filename)
    except FileNotFound:
        return jsonify(formatter(404,
                         "The file does not exists with the given URI",
                         "File is not existing on the bucket",
                         "Check your file name, or check if you have uploaded the file (obiously)"))  
    except InternalError as e:
        return jsonify(formatter(500, f"File could not be fetched due to internal errors: {e}"))  

    content = load_result.content
    content_type = load_result.content_type

    return make_response(f"{content}", 200, { "content-type": content_type })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
