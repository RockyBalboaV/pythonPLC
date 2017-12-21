import pymysql
from contextlib import contextmanager

from param import HOSTNAME, DATABASE, USERNAME, PASSWORD


class ConnMySQL(object):
    def __init__(self):
        self.db = pymysql.connect(
            host=HOSTNAME,
            port=3306,
            user=USERNAME,
            passwd=PASSWORD,
            db=DATABASE,
            charset='utf8'
        )

    def __enter__(self):
        return self.db

    def __exit__(self, *args):
        self.db.close()


mysql_db = ConnMySQL().db
