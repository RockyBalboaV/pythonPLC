from flask import Flask, jsonify, request,Response
import json
from flask_json import FlaskJSON, JsonError, json_response, as_json

app = Flask(__name__)


@app.route('/config')
def get_config():
    t = {'a': 1, 'b': 2, 'c': [3, 4, 5]}
    return Response(json.dumps(t), mimetype='application/json')
    # return jsonify(t)


@app.route('/status', methods=['post'])
def post_status():
    data = request.get_data()


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
