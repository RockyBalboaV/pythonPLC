# coding=utf-8
import unittest

from web_server import create_app, db


class TestURLs(unittest.TestCase):

    def setUp(self):
        app = create_app('app.config.TestConfig')
        self.client = app.test_client()

        # 不在应用目录中运行会造成flask-sqlalchemy不能正确初始化，需要重新赋予应用实例
        db.app = app

        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_index(self):
        """测试首页"""
        result = self.client.get('/')
        self.assertIs(result.status_code, 200)


if __name__ == '__main__':
    unittest.main()
