# coding=utf-8
import json, hmac, chardet, base64, os, random, simplejson

from flask import Flask, abort, request, jsonify, redirect, g, render_template
from ext import db, mako
from models import *

app = Flask(__name__, template_folder='templates')
app.config.from_object('config')

mako.init_app(app)
db.init_app(app)


def get_current_user():
    users = User.query.all()
    return random.choice(users)


@app.before_first_request
def setup():
    db.drop_all()
    db.create_all()
    fake_users = [
        User('xiaoming', '3'),
        User('wangzhe', '2'),
        User('admin', '1')
    ]
    db.session.add_all(fake_users)
    db.session.commit()


@app.before_request
def before_request():
    g.user = get_current_user()


@app.teardown_appcontext
def teardown(exc=None):
    if exc is None:
        db.session.commit()
    else:
        db.session.rollback()
    db.session.remove()
    g.user = None


@app.context_processor
def template_extras():
    return {'enumerate': enumerate, 'current_user': g.user}


@app.template_filter('capitalize')
def reverse_filter(s):
    return s.capitalize()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        rv = request.get_json(force=True)
        #print rv
        data = rv["data"]
        print data
        #data = base64.b64decode(data)
        #data_origin = eval(data_origin)
        #print data
        #data = data.encode('utf-8')
        print data
        #chardet.detect(data)
        #data ={"a": "1", "b": "2"}
        #chardet.detect(data)
        di = rv["digest"]
        print di
        h = hmac.new(b'poree')
        h.update(bytes(data))
        test = h.hexdigest()
        print test

        if di == test:
            data = base64.b64decode(data)
            print data
            #print type(data)
            #data = json.dumps(data)
            #data = json.loads(data)
            print data
            print type(data)
            #data = json.loads(data)
            data = json.loads(data.replace("'", '"'))
            print data
            print type(data)
            uploaded_data = YjPLCInfo.query.filter_by(id=data["id"]).first()
            su = False
            print '1'
            if uploaded_data:
                uploaded_data = YjPLCInfo.query.all()
                return render_template('index_post.html', uploaded_data=uploaded_data)
            else:
            #    while su:
            #        try:
                uploaded_data = YjPLCInfo(name=data["name"], id=data["id"], tenid=data["tenid"])
                #todo 当输入值的键不存在时,怎么使用默认值代替
            #            su = True
            #        except KeyError as a:
            #            data[a] = None
            #print uploaded_data.id
            #print data
            #upload_data = YjPLCInfo.upload(data)
            db.session.add(uploaded_data)
            db.session.commit()
            uploaded_data = YjPLCInfo.query.all()
            print "s"
            return render_template('index_post.html', uploaded_data=uploaded_data)
    users = User.query.all()
    return render_template('index.html', users=users)
        #data =

        #something = request.form.get('id')
        #id = request.get_json(force=True)
        #db.session.add()
        #db.session.commit()






if __name__ == '__main__':
    app.run(host='0.0.0.0', port=11000, debug=True)
