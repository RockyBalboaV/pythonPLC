from flask_mako import MakoTemplates
from flask_sqlalchemy import SQLAlchemy
from flask_hashing import Hashing

mako = MakoTemplates()
db = SQLAlchemy()
hashing = Hashing()