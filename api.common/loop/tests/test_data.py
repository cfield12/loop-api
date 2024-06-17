import unittest
from unittest.mock import call, patch

from loop import data, exceptions
from loop.test_setup.common import setup_rds, unbind_rds
from loop.utils import UserObject, get_admin_user
from pony.orm import Database

TEST_DB_SECRET = {
    'user': 'admin',
    'password': 'test_password',
    'port': 3306,
    'host': 'rds-loop-test.test.eu-west-2.rds.amazonaws.com',
    'database': 'loop',
    'provider': 'mysql',
}


class LoopTestGetUserRatings(unittest.TestCase):
    """
    Test getting user ratings.
    """

    @classmethod
    def setUpClass(cls):
        setup_rds()

    @classmethod
    def tearDownClass(cls):
        unbind_rds()

    def test_get_admin_ratings(self):
        admin_user_ratings = data.get_user_ratings(get_admin_user())
        self.assertEqual(
            admin_user_ratings,
            [
                {
                    'food': 3,
                    'price': 4,
                    'vibe': 4,
                    'place_name': 'Home',
                    'address': '14 Lambert Street, London, N1 1JE',
                    'google_id': 'test_google_id_1',
                },
                {
                    'food': 5,
                    'price': 4,
                    'vibe': 5,
                    'place_name': "Baggins'",
                    'address': '15 Noel Road, London, N1 8HQ',
                    'google_id': 'test_google_id_2',
                },
            ],
        )

    def test_get_test_user_ratings(self):
        user_ratings = data.get_user_ratings(UserObject(id=2))
        self.assertEqual(
            user_ratings,
            [
                {
                    'food': 3,
                    'price': 4,
                    'vibe': 5,
                    'place_name': 'Home',
                    'address': '14 Lambert Street, London, N1 1JE',
                    'google_id': 'test_google_id_1',
                },
                {
                    'food': 5,
                    'price': 5,
                    'vibe': 5,
                    'place_name': 'JFs',
                    'address': '38 Huntingdon Street, London, N1 1BP',
                    'google_id': 'test_google_id_3',
                },
            ],
        )

    def test_get_user_ratings_error(self):
        user = 1
        self.assertRaises(TypeError, data.get_user_ratings, user)


class LoopTestUserFromCognito(unittest.TestCase):
    """
    Test user from cognito user name.
    """

    @classmethod
    def setUpClass(cls):
        setup_rds()

    @classmethod
    def tearDownClass(cls):
        unbind_rds()

    def test_get_user_from_cognito(self):
        cognito_user_name = 'test_cognito_user_name'
        user = data.get_user_from_cognito_username(cognito_user_name)
        assert isinstance(user, UserObject)
        self.assertEqual(user.id, 1)

    def test_get_user_from_cognito_error(self):
        cognito_user_name = 'unknown_test_cognito_user_name'
        self.assertRaises(
            exceptions.UnauthorizedError,
            data.get_user_from_cognito_username,
            cognito_user_name,
        )


class LoopTestInitDB(unittest.TestCase):
    """
    Test init db.
    """

    @patch('loop.secrets.get_db_dict')
    @patch.object(Database, 'generate_mapping')
    @patch.object(Database, 'bind')
    def test_init_db(
        self, mock_bind_db, mock_generate_mapping, mock_db_secret
    ):
        mock_db_secret.return_value = TEST_DB_SECRET
        data.init_write_db()

        self.assertEqual(
            mock_bind_db.call_args,
            call(
                user='admin',
                password='test_password',
                port=3306,
                host='rds-loop-test.test.eu-west-2.rds.amazonaws.com',
                database='loop',
                provider='mysql',
            ),
        )
        self.assertEqual(
            mock_generate_mapping.call_args,
            call(
                check_tables=False,
                create_tables=False,
            ),
        )

    @patch('loop.secrets.get_db_dict')
    @patch(
        'pony.orm.Database.bind', side_effect=Exception("Test init DB error.")
    )
    @patch('loop.data.sleep')
    def test_init_db_error(self, mock_sleep, mock_bind_db, mock_db_secret):
        mock_db_secret.return_value = TEST_DB_SECRET
        self.assertRaises(exceptions.DbInitFailedError, data.init_write_db)

    @patch('loop.secrets.get_db_dict')
    @patch(
        'pony.orm.Database.bind', side_effect=Exception("was already bound.")
    )
    def test_init_db_already_init_1(self, mock_bind_db, mock_db_secret):
        mock_db_secret.return_value = TEST_DB_SECRET
        data.init_write_db()
        self.assertEqual(data.DB_TYPE['write'], None)

    @patch('loop.secrets.get_db_dict')
    @patch(
        'pony.orm.Database.bind',
        side_effect=Exception("Mapping was already generated."),
    )
    def test_init_db_already_init_2(self, mock_bind_db, mock_db_secret):
        mock_db_secret.return_value = TEST_DB_SECRET
        data.init_write_db()
        self.assertEqual(data.DB_TYPE['write'], None)

    @patch.object(Database, 'disconnect')
    def test_disconnect_db_1(self, mock_disconnect_db):
        data.DB_TYPE['write'] = Database()
        data.disconnect_db()
        self.assertTrue(mock_disconnect_db.called)

    @patch(
        'pony.orm.Database.disconnect',
        side_effect=Exception("Disconnect error"),
    )
    def test_disconnect_db_2(self, mock_disconnect_db):
        data.DB_TYPE['write'] = Database()
        self.assertRaises(
            exceptions.DbDisconnectFailedError, data.disconnect_db
        )

    def test_disconnect_db_3(self):
        data.DB_TYPE['write'] = 'TEST_ERROR'
        self.assertRaises(
            exceptions.DbDisconnectFailedError, data.disconnect_db
        )


if __name__ == "__main__":
    unittest.main()
