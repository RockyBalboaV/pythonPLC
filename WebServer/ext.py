from flask_mako import MakoTemplates
from flask_sqlalchemy import SQLAlchemy
from flask_hashing import Hashing
from flask_restful import Api

mako = MakoTemplates()
db = SQLAlchemy()
hashing = Hashing()
api = Api()