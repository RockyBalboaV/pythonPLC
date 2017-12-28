import unittest

import requests

HOST = 'http://1.yakumo.applinzi.com/'


class TestInterface(unittest.TestCase):
    # @unittest.skip()
    def test_api_variable(self):
        path = 'api/variable'
        url = HOST + path

        res = requests.get(url)
        self.assertIs(res.status_code, 200)

        data = {'variable_name': 'test'}
        res = requests.put(url, json=data)
        self.assertIs(res.status_code, 200)

        data = {'variable_name': 'test'}
        res = requests.post(url, json=data)
        self.assertIs(res.status_code, 200)

        data = {'variable_name': 'test', 'id': res.json()['data'][0]['id'], 'note': 'test'}
        res = requests.put(url, json=data)
        self.assertIs(res.status_code, 201)

        data = {'variable_name': 'test'}
        res = requests.post(url, json=data)
        self.assertEqual(res.json()['data'][0]['note'], 'test')

        data = {'variable_name': 'test'}
        res = requests.delete(url, json=data)
        self.assertIs(res.status_code, 201)

    def test_api_value(self):
        path = 'api/value'
        url = HOST + path

        res = requests.get(HOST + 'api/variable')
        variable_num = len(res.json()['data'])

        data = {'all_variable_id': True, 'limit': 1}
        res = requests.get(url, params=data)
        self.assertIs(res.status_code, 200)
        self.assertEqual(len(res.json()['data']), variable_num)


        # data = {'variable_name': 'test'}
        # res = requests.put(url, json=data)
        # self.assertIs(res.status_code, 200)
        #
        # data = {'variable_name': 'test'}
        # res = requests.post(url, json=data)
        # self.assertIs(res.status_code, 200)
        #
        # data = {'variable_name': 'test', 'id': res.json()['data'][0]['id'], 'note': 'test'}
        # res = requests.put(url, json=data)
        # self.assertIs(res.status_code, 201)
        #
        # data = {'variable_name': 'test'}
        # res = requests.post(url, json=data)
        # self.assertEqual(res.json()['data'][0]['note'], 'test')
        #
        # data = {'variable_name': 'test'}
        # res = requests.delete(url, json=data)
        # self.assertIs(res.status_code, 201)


if __name__ == '__main__':
    unittest.main()
