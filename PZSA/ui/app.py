from flask import Flask, send_file
from flask_cors import CORS
from PZSA.services.streaming.stream import stream_blueprint

app = Flask(__name__)
CORS(app)

app.register_blueprint(stream_blueprint)

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_file('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)