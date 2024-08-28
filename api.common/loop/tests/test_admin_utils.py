import unittest
from unittest.mock import Mock, call, patch

from loop.admin_utils import (
    _get_rating,
    delete_rating,
    delete_user,
    delete_user_from_rds,
)
from loop.api_classes import UserCredentials
from loop.data import DB_SESSION_RETRYABLE
from loop.data_classes import UserObject
from loop.exceptions import BadRequestError
from loop.test_setup import setup_rds, unbind_rds


class TestAdminUtils(unittest.TestCase):
    def setUp(self):
        setup_rds()

    def tearDown(self):
        unbind_rds()

    @DB_SESSION_RETRYABLE
    def test_delete_rating(self):
        rating_id = 1
        delete_rating(rating_id)
        self.assertRaises(BadRequestError, _get_rating, rating_id)

    @patch('loop.admin_utils.CognitoAuth')
    @patch('loop.admin_utils.SqsClient')
    def test_delete_user(self, mock_queue_client, mock_cognito):
        user_credentials = UserCredentials(email='some_email@hotmail.com')
        delete_user(user_credentials)
        self.assertEqual(
            mock_queue_client.mock_calls,
            [
                call('loop-sqs-delete_user-test'),
                call().send_message({'email': 'some_email@hotmail.com'}),
            ],
        )
        self.assertEqual(
            mock_cognito.mock_calls,
            [
                call(),
                call().admin_delete_user(
                    UserCredentials(email='some_email@hotmail.com')
                ),
            ],
        )

    def test_delete_user_type_error(self):
        user_credentials = 'some_email@hotmail.com'
        self.assertRaises(TypeError, delete_user, user_credentials)

    @patch('loop.admin_utils.delete_user_entry')
    @patch('loop.admin_utils.delete_user_friendships')
    @patch('loop.admin_utils.delete_user_ratings')
    @patch('loop.admin_utils.get_user_from_email')
    def test_delete_user_from_rds(
        self,
        mock_user,
        mock_delete_ratings,
        mock_delete_freindships,
        mock_delete_user,
    ):
        mock_user.return_value = UserObject(
            id=2, cognito_user_name='user_name'
        )
        user_credentials = UserCredentials(email='some_email@hotmail.com')
        delete_user_from_rds(user_credentials)
        self.assertTrue(mock_delete_ratings.called)
        self.assertTrue(mock_delete_freindships.called)
        self.assertTrue(mock_delete_user.called)

    def test_delete_user_from_rds_type_error(self):
        user_credentials = 'some_email@hotmail.com'
        self.assertRaises(TypeError, delete_user_from_rds, user_credentials)


if __name__ == '__main__':
    unittest.main()
