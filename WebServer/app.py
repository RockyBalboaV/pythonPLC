from flask import Flask, jsonify, request,Response
import json
from flask_json import FlaskJSON, JsonError, json_response, as_json
from urllib.request import urlopen

app = Flask(__name__)
json = FlaskJSON(app)


@app.route('/config', methods=['GET', 'POST'])
def get_config():
    if request.method == 'POST':
        data = request.get_json(force=True)
        print(data)
        id = int(data['id'])
        print(type(data))
        value = int(data['value'])
        b = {'f': 5}
        return jsonify(b)
        #return json_response(plc=1, config=True, fuck_you=True, id=id+1)
    t = {'a': 1, 'b': 2, 'c': [3, 4, 5]}
    #return Response(json.dumps(t), mimetype='application/json')
    return jsonify(t)


@app.route('/status', methods=['get', 'post'])
def post_status():
    data = request.get_json(force=True)
    print(type(data))
    value = int(data['value'])
    return json_response(plc=1, config=True)
    #data = json.loads(data)
    #if data['id'] == 1:
    #    return {'id':2}


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
