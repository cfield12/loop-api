import unittest
from unittest.mock import Mock, call, patch

from loop.data import DB_TYPE
from loop.enums import DbType
from loop.exceptions import CreateUserValidationError
from loop.test_setup import setup_rds, unbind_rds
from pony.orm import Database

from . import UserCreator
from .test_data import test_event


class TestCreateUser(unittest.TestCase):
    def setUp(self):
        self.user_creator = UserCreator()

    def tearDown(self):
        self.user_creator = None

    def test_validate_create_user_event(self):
        event = test_event.copy()
        self.user_creator._validate_event(event)

    def test_validate_create_user_event_no_username(self):
        event = test_event.copy()
        event.pop('userName')
        self.assertRaises(
            CreateUserValidationError,
            self.user_creator._validate_event,
            event,
        )

    def test_validate_create_user_event_no_user_attributes(self):
        event = test_event.copy()
        event['request'].pop('userAttributes')
        self.assertRaises(
            CreateUserValidationError,
            self.user_creator._validate_event,
            event,
        )

    def test_validate_create_user_event_no_first_name(self):
        event = test_event.copy()
        event['request']['userAttributes'].pop('given_name')
        self.assertRaises(
            CreateUserValidationError,
            self.user_creator._validate_event,
            event,
        )

    def test_create_user(self):
        DB_TYPE[DbType.WRITE] = Mock()
        event = test_event.copy()
        self.user_creator.create_user(event)
        self.assertEqual(
            DB_TYPE[DbType.WRITE].mock_calls[0],
            call.User(
                cognito_user_name='26f29234-c0e1-704f-3b56-2eade7808df9',
                email='charlie.field98@gmail.com',
                first_name='Charlie',
                last_name='Field',
            ),
        )
        DB_TYPE[DbType.WRITE] = None


if __name__ == '__main__':
    unittest.main()
