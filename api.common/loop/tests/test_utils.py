import unittest
from unittest.mock import Mock, call, patch

from loop.utils import *


class TestUtils(unittest.TestCase):
    def test_get_admin_user(self):
        user = get_admin_user()
        self.assertEqual(
            user,
            UserObject(
                id=1,
                cognito_user_name='86125274-40a1-70ec-da28-f779360f7c07',
                groups=['loop_admin'],
            ),
        )

    def test_conditional_load_with_string(self):
        body = '{"body": "hello"}'
        response = conditional_load(body)
        self.assertEqual(response, {'body': 'hello'})

    def test_conditional_load_with_dict(self):
        body = {'body': 'hello'}
        response = conditional_load(body)
        self.assertEqual(response, body)

    def test_conditional_dump_with_string(self):
        body = '{"body": "hello"}'
        response = conditional_dump(body)
        self.assertEqual(response, body)

    def test_conditional_dump_with_dict(self):
        body = {'body': 'hello'}
        response = conditional_dump(body)
        self.assertEqual(response, '{"body": "hello"}')

    def test_sqs_batch(self):
        batch = list()
        event = {
            'Records': [
                {'body': '{"body": "hello"}'},
                {'body': '{"body": "bye"}'},
            ]
        }
        for message in sqs_batch(event):
            batch.append(message)
        self.assertEqual(batch, [{'body': 'hello'}, {'body': 'bye'}])


if __name__ == '__main__':
    unittest.main()
