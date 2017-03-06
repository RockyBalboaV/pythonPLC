from flask import Flask, jsonify
import json

app = Flask(__name__)


@app.route('/api/_get_config')
def get_config():
    t = {
        'a': 1,
        'b': 2,
        'c': [3, 4, 5]
    }
    return json.dumps(t)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
