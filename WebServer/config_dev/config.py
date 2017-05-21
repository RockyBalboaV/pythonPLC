# database
SQLALCHEMY_DATABASE_URI = 'mysql://web:web@localhost:3306/pyplc'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# csrf secret key
SECRET_KEY = 'yakumo17s'

# flask-cache
CACHE_TYPE = 'redis'
CACHE_REDIS_HOST = 'localhost'
CACHE_REDIS_PORT = '6379'
# CACHE_REDIS_PASSWORD = 'password'
CACHE_REDIS_DB = 0

# flask-debugtoolbar
DEBUG_TB_INTERCEPT_REDIRECTS = False
DEBUG = True
