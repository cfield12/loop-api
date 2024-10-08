import unittest
from datetime import datetime
from unittest.mock import call, patch

from loop import data, exceptions
from loop.api_classes import Coordinates, PaginatedRatings, UpdateRating
from loop.data_classes import Location, Rating, RatingsPageResults, UserObject
from loop.enums import DbType
from loop.friends import get_user_friends
from loop.test_setup.common import setup_rds, unbind_rds
from loop.utils import get_admin_user
from pony.orm import Database

TEST_DB_SECRET = {
    'user': 'admin',
    'password': 'test_password',
    'port': 3306,
    'host': 'rds-loop-test.test.eu-west-2.rds.amazonaws.com',
    'database': 'loop',
    'provider': 'mysql',
}
TEST_COORDINATES = Coordinates(lat=1.0, lng=1.0)


class LoopTestGetRatings(unittest.TestCase):
    """
    Test getting user ratings and all ratings.
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
                    'id': 3,
                    'food': 3,
                    'price': 4,
                    'vibe': 4,
                    'message': 'Food was incredible.',
                    'place_name': 'Home',
                    'address': '14 Lambert Street, London, N1 1JE',
                    'google_id': 'test_google_id_1',
                },
                {
                    'id': 4,
                    'food': 5,
                    'price': 4,
                    'vibe': 5,
                    'message': 'Place had a great atmosphere.',
                    'place_name': "Baggins'",
                    'address': '15 Noel Road, London, N1 8HQ',
                    'google_id': 'test_google_id_2',
                },
            ],
        )

    def test_get_test_user_ratings(self):
        user_ratings = data.get_user_ratings(
            UserObject(
                id=2, cognito_user_name='86125274-40a1-70ec-da28-f779360f7c07'
            )
        )
        self.assertEqual(
            user_ratings,
            [
                {
                    'id': 1,
                    'food': 3,
                    'price': 4,
                    'vibe': 5,
                    'message': None,
                    'place_name': 'Home',
                    'address': '14 Lambert Street, London, N1 1JE',
                    'google_id': 'test_google_id_1',
                },
                {
                    'id': 2,
                    'food': 5,
                    'price': 5,
                    'vibe': 5,
                    'message': None,
                    'place_name': 'JFs',
                    'address': '38 Huntingdon Street, London, N1 1BP',
                    'google_id': 'test_google_id_3',
                },
            ],
        )

    def test_get_user_ratings_error(self):
        user = 1
        self.assertRaises(TypeError, data.get_user_ratings, user)

    def test_get_ratings_for_user(self):
        users = [1, 3, 4]
        ratings = data.get_ratings(users)
        expected_ratings = [
            {
                'id': 3,
                'first_name': 'Test',
                'last_name': 'User',
                'place_id': 'test_google_id_1',
                'latitude': 1.5,
                'longitude': -0.7,
                'food': 3,
                'price': 4,
                'vibe': 4,
                'message': 'Food was incredible.',
                'time_created': '2000-01-01 00:00:00',
            },
            {
                'id': 4,
                'first_name': 'Test',
                'last_name': 'User',
                'place_id': 'test_google_id_2',
                'latitude': 1.2,
                'longitude': -0.9,
                'food': 5,
                'price': 4,
                'vibe': 5,
                'message': 'Place had a great atmosphere.',
                'time_created': '2000-01-01 00:00:00',
            },
        ]
        self.assertEqual(ratings, expected_ratings)

    def test_get_ratings_place_specific(self):
        users = [1, 2, 3, 4]
        place_id = 'test_google_id_1'
        ratings = data.get_ratings(users, place_id=place_id)
        expected_ratings = [
            {
                'id': 3,
                'first_name': 'Test',
                'last_name': 'User',
                'place_id': 'test_google_id_1',
                'latitude': 1.5,
                'longitude': -0.7,
                'food': 3,
                'price': 4,
                'vibe': 4,
                'message': 'Food was incredible.',
                'time_created': '2000-01-01 00:00:00',
            },
            {
                'id': 1,
                'first_name': 'Admin',
                'last_name': 'User',
                'place_id': 'test_google_id_1',
                'latitude': 1.5,
                'longitude': -0.7,
                'food': 3,
                'price': 4,
                'vibe': 5,
                'message': None,
                'time_created': '2000-01-01 00:00:00',
            },
        ]
        self.assertEqual(ratings, expected_ratings)

    def test_get_ratings(self):
        ratings = data.get_ratings()
        expected_ratings = [
            {
                'id': 1,
                'first_name': 'Admin',
                'last_name': 'User',
                'place_id': 'test_google_id_1',
                'latitude': 1.5,
                'longitude': -0.7,
                'food': 3,
                'price': 4,
                'vibe': 5,
                'message': None,
                'time_created': '2000-01-01 00:00:00',
            },
            {
                'id': 2,
                'first_name': 'Admin',
                'last_name': 'User',
                'place_id': 'test_google_id_3',
                'latitude': 1.9,
                'longitude': -0.8,
                'food': 5,
                'price': 5,
                'vibe': 5,
                'message': None,
                'time_created': '2000-01-01 00:00:00',
            },
            {
                'id': 3,
                'first_name': 'Test',
                'last_name': 'User',
                'place_id': 'test_google_id_1',
                'latitude': 1.5,
                'longitude': -0.7,
                'food': 3,
                'price': 4,
                'vibe': 4,
                'message': 'Food was incredible.',
                'time_created': '2000-01-01 00:00:00',
            },
            {
                'id': 4,
                'first_name': 'Test',
                'last_name': 'User',
                'place_id': 'test_google_id_2',
                'latitude': 1.2,
                'longitude': -0.9,
                'food': 5,
                'price': 4,
                'vibe': 5,
                'message': 'Place had a great atmosphere.',
                'time_created': '2000-01-01 00:00:00',
            },
        ]
        self.assertEqual(ratings, expected_ratings)

    def test_get_ratings_paginated(self):
        paginate = PaginatedRatings(page_count=1)
        paginated_ratings = data.get_ratings_paginated(paginate)
        expected_ratings = RatingsPageResults(
            page_data=[
                {
                    'id': 1,
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'place_id': 'test_google_id_1',
                    'latitude': 1.5,
                    'longitude': -0.7,
                    'food': 3,
                    'price': 4,
                    'vibe': 5,
                    'message': None,
                    'time_created': '2000-01-01 00:00:00',
                },
                {
                    'id': 2,
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'place_id': 'test_google_id_3',
                    'latitude': 1.9,
                    'longitude': -0.8,
                    'food': 5,
                    'price': 5,
                    'vibe': 5,
                    'message': None,
                    'time_created': '2000-01-01 00:00:00',
                },
                {
                    'id': 3,
                    'first_name': 'Test',
                    'last_name': 'User',
                    'place_id': 'test_google_id_1',
                    'latitude': 1.5,
                    'longitude': -0.7,
                    'food': 3,
                    'price': 4,
                    'vibe': 4,
                    'message': 'Food was incredible.',
                    'time_created': '2000-01-01 00:00:00',
                },
                {
                    'id': 4,
                    'first_name': 'Test',
                    'last_name': 'User',
                    'place_id': 'test_google_id_2',
                    'latitude': 1.2,
                    'longitude': -0.9,
                    'food': 5,
                    'price': 4,
                    'vibe': 5,
                    'message': 'Place had a great atmosphere.',
                    'time_created': '2000-01-01 00:00:00',
                },
            ],
            total_pages=1,
        )
        self.assertEqual(paginated_ratings, expected_ratings)

    def test_get_ratings_paginated(self):
        paginate = PaginatedRatings(page_count=1, place_id='unknown place id')
        paginated_ratings = data.get_ratings_paginated(paginate)
        expected_ratings = RatingsPageResults(page_data=[], total_pages=0)
        self.assertEqual(paginated_ratings, expected_ratings)

    def test_get_ratings_paginated_page_error(self):
        paginate = PaginatedRatings(page_count=2)
        self.assertRaises(
            exceptions.BadRequestError, data.get_ratings_paginated, paginate
        )


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

    def test_get_admin_user_from_cognito(self):
        cognito_user_name = '86125274-40a1-70ec-da28-f779360f7c07'
        user = data.get_user_from_cognito_username(cognito_user_name)
        assert isinstance(user, UserObject)
        self.assertEqual(user.id, 2)
        self.assertIn('loop_admin', user.groups)

    def test_get_user_from_cognito_error(self):
        cognito_user_name = 'unknown_test_cognito_user_name'
        self.assertRaises(
            exceptions.BadRequestError,
            data.get_user_from_cognito_username,
            cognito_user_name,
        )

    def test_get_user_from_email(self):
        email = 'test_email'
        user = data.get_user_from_email(email)
        assert isinstance(user, UserObject)
        self.assertEqual(user.id, 1)

    def test_get_user_from_email_error(self):
        email = 'unknown_email'
        self.assertRaises(
            exceptions.BadRequestError,
            data.get_user_from_email,
            email,
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
        self.assertEqual(data.DB_TYPE[DbType.WRITE], None)

    @patch('loop.secrets.get_db_dict')
    @patch(
        'pony.orm.Database.bind',
        side_effect=Exception("Mapping was already generated."),
    )
    def test_init_db_already_init_2(self, mock_bind_db, mock_db_secret):
        mock_db_secret.return_value = TEST_DB_SECRET
        data.init_write_db()
        self.assertEqual(data.DB_TYPE[DbType.WRITE], None)

    @patch.object(Database, 'disconnect')
    def test_disconnect_db_1(self, mock_disconnect_db):
        data.DB_TYPE[DbType.WRITE] = Database()
        data.disconnect_db()
        self.assertTrue(mock_disconnect_db.called)

    @patch(
        'pony.orm.Database.disconnect',
        side_effect=Exception("Disconnect error"),
    )
    def test_disconnect_db_2(self, mock_disconnect_db):
        data.DB_TYPE[DbType.WRITE] = Database()
        self.assertRaises(
            exceptions.DbDisconnectFailedError, data.disconnect_db
        )


class TestCreateUserRatings(unittest.TestCase):
    """
    Create user ratings.
    """

    @classmethod
    def setUpClass(cls):
        setup_rds()

    @classmethod
    def tearDownClass(cls):
        unbind_rds()

    def test_create_rating(self):
        rating = Rating(location=4, user=1, price=3, food=4, vibe=5)
        data.create_rating(rating)
        admin_user_ratings = data.get_user_ratings(get_admin_user())
        self.assertEqual(
            admin_user_ratings,
            [
                {
                    'id': 3,
                    'food': 3,
                    'price': 4,
                    'vibe': 4,
                    'message': 'Food was incredible.',
                    'place_name': 'Home',
                    'address': '14 Lambert Street, London, N1 1JE',
                    'google_id': 'test_google_id_1',
                },
                {
                    'id': 4,
                    'food': 5,
                    'price': 4,
                    'vibe': 5,
                    'message': 'Place had a great atmosphere.',
                    'place_name': "Baggins'",
                    'address': '15 Noel Road, London, N1 8HQ',
                    'google_id': 'test_google_id_2',
                },
                {
                    'id': 5,
                    'food': 4,
                    'price': 3,
                    'vibe': 5,
                    'message': None,
                    'place_name': 'som saa',
                    'address': '43A Commercial Street, London',
                    'google_id': 'ChIJobyn_rQcdkgRE042NxgeR1k',
                },
            ],
        )

    def test_create_rating_type_error(self):
        rating = {'location': 4, 'user': 1, 'price': 3, 'food': 4, 'vibe': 5}
        self.assertRaises(TypeError, data.create_rating, rating)

    @data.DB_SESSION_RETRYABLE
    def test_get_rating_wrong_user_error(self):
        rating_id = 1
        self.assertRaises(
            exceptions.BadRequestError,
            data._get_rating,
            rating_id,
            get_admin_user(),
        )

    @data.DB_SESSION_RETRYABLE
    def test_get_rating(self):
        rating_id = 1
        rating = data._get_rating(
            rating_id, UserObject(id=2, cognito_user_name='user_name')
        )
        self.assertEqual(rating.id, 1)

    @data.DB_SESSION_RETRYABLE
    def test_get_rating_type_error_id(self):
        rating_id = '1'
        self.assertRaises(
            TypeError,
            data._get_rating,
            rating_id,
            UserObject(id=2, cognito_user_name='user_name'),
        )

    @data.DB_SESSION_RETRYABLE
    def test_get_rating_type_error_user(self):
        rating_id = 1
        self.assertRaises(
            TypeError,
            data._get_rating,
            rating_id,
            {'id': 2, 'cognito_user_name': 'user_name'},
        )

    @data.DB_SESSION_RETRYABLE
    def test_update_rating_message(self):
        user = UserObject(id=2, cognito_user_name='user_name')
        update_rating = UpdateRating(id=1, message='hello')
        data.update_rating(update_rating, user)
        rating = data._get_rating(
            1, UserObject(id=2, cognito_user_name='user_name')
        )
        self.assertEqual(rating.message, 'hello')
        self.assertNotEqual(rating.last_updated, datetime(2000, 1, 1))

    @data.DB_SESSION_RETRYABLE
    def test_update_ratings(self):
        user = UserObject(id=2, cognito_user_name='user_name')
        update_rating = UpdateRating(id=1, price=4, food=3, vibe=2)
        data.update_rating(update_rating, user)
        rating = data._get_rating(
            1, UserObject(id=2, cognito_user_name='user_name')
        )
        self.assertEqual(rating.price, 4)
        self.assertEqual(rating.food, 3)
        self.assertEqual(rating.vibe, 2)

    def test_update_rating_type_error(self):
        update_rating = {'message': 'hello'}
        self.assertRaises(TypeError, data.update_rating, update_rating)

    @data.DB_SESSION_RETRYABLE
    def test_delete_rating(self):
        rating_id = 2
        user = UserObject(id=2, cognito_user_name='user_name')
        data.delete_rating(rating_id, user)
        self.assertRaises(
            exceptions.BadRequestError, data._get_rating, rating_id, user
        )

    @patch('loop.data._get_rating')
    def test_delete_rating_works_with_str_int(self, mock_get_rating):
        rating_id = '2'
        user = UserObject(id=2, cognito_user_name='user_name')
        data.delete_rating(rating_id, user)
        self.assertEqual(mock_get_rating.mock_calls[1], call().delete())

    @patch('loop.data._get_rating')
    def test_delete_rating_type_error_1(self, mock_get_rating):
        rating_id = 'hello'
        user = UserObject(id=2, cognito_user_name='user_name')
        self.assertRaises(TypeError, data.delete_rating, rating_id, user)


class TestCreateLocation(unittest.TestCase):
    """
    Create Location.
    """

    @classmethod
    def setUpClass(cls):
        setup_rds()

    @classmethod
    def tearDownClass(cls):
        unbind_rds()

    def test_create_location(self):
        location = Location(
            google_id='X_TEST_GOOGLE_ID_X',
            address='55 Northberk Street, Sunderland',
            display_name='Greggs',
            coordinates=TEST_COORDINATES,
        )
        location_entry = data.create_location_entry(location)
        self.assertEqual(location_entry.id, 5)

    def test_create_location_type_error(self):
        location = {
            'google_id': 'X_TEST_GOOGLE_ID_X',
            'address': '55 Northberk Street, Sunderland',
            'display_name': 'Greggs',
        }
        self.assertRaises(TypeError, data.create_location_entry, location)

    def test_get_or_create_location_id(self):
        google_id = 'test_google_id_1'
        location_id = data.get_or_create_location_id(google_id)
        self.assertEqual(location_id, 1)

    @patch('loop.data.find_location')
    def test_get_or_create_location_id_type_error(self, mock_location):
        mock_location.return_value = Location(
            google_id='test_google_id_5',
            address='33 South Road, Liverpool',
            display_name='Dominoes',
            coordinates=TEST_COORDINATES,
        )
        google_id = 'test_google_id_5'
        location_id = data.get_or_create_location_id(google_id)
        self.assertEqual(location_id, 6)


class TestUpdateObject(unittest.TestCase):
    """
    Tests the updating of DB objects.
    """

    @classmethod
    def setUpClass(cls):
        setup_rds()

    @classmethod
    def tearDownClass(cls):
        unbind_rds()

    @data.DB_SESSION_RETRYABLE
    def test_updating_last_updated_time_error(self):
        pending_status = data.DB_TYPE[data.DbType.WRITE].Friend_status.get(
            description='Pending'
        )
        self.assertRaises(
            AttributeError,
            data.update_object_last_updated_time,
            pending_status,
        )


class TestDeleteUser(unittest.TestCase):
    """
    Tests the functions used when deleting a user and all their objects from
    RDS.
    """

    @classmethod
    def setUpClass(cls):
        setup_rds()

    @classmethod
    def tearDownClass(cls):
        unbind_rds()

    @data.DB_SESSION_RETRYABLE
    def test_delete_user_ratings(self):
        user = UserObject(id=2, cognito_user_name='user_name')
        ratings = data.get_user_ratings(user)
        assert len(ratings) == 2
        data.delete_user_ratings(user)
        ratings = data.get_user_ratings(user)
        assert len(ratings) == 0

    def test_delete_user_ratings_type_error(self):
        user = 'user_name'
        self.assertRaises(TypeError, data.get_user_ratings, user)

    @data.DB_SESSION_RETRYABLE
    def test_delete_friendships(self):
        user = UserObject(id=2, cognito_user_name='user_name')
        friendships = get_user_friends(user)
        assert len(friendships) == 1
        data.delete_user_friendships(user)
        friendships = get_user_friends(user)
        assert len(friendships) == 0

    def test_delete_friendships_type_error(self):
        user = 'user_name'
        self.assertRaises(TypeError, data.delete_user_friendships, user)

    @data.DB_SESSION_RETRYABLE
    def test_delete_user_entry(self):
        user_name = 'test_cognito_user_name'
        user = data.get_user_from_cognito_username(user_name)
        self.assertIsInstance(user, UserObject)
        data.delete_user_entry(user)
        self.assertRaises(
            exceptions.BadRequestError,
            data.get_user_from_cognito_username,
            user_name,
        )


if __name__ == "__main__":
    unittest.main()
