import base64
from base64 import b64decode

from flask import Flask
from flask import request

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello Frank!"


@app.route('/debug', methods=['GET', 'POST'])
def debug():
    if request.method == 'POST':
        print(request)
        print(request.data)
        print(extract_message())

    return 'ok'


def extract_message():
    data = request.json.get('message', {}).get('data', '')
    return b64decode(data).decode('utf-8')

class DebugServer:
    pass
