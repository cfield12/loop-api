import importlib
import json
import unittest
from unittest.mock import patch

from chalice.test import Client
from loop import data
from loop.constants import RDS_WRITE
from loop.test_setup.common import setup_rds, unbind_rds
from loop.utils import UserObject

mock_url_write_db = 'loop.data.init_write_db'


def mocked_init_write_db(check_tables=False, create_tables=False):
    if not check_tables and not create_tables:
        return
    db_dict = {'provider': 'sqlite', 'filename': ':memory:'}
    data.DB_TYPE[RDS_WRITE] = data.init_db(
        db_dict, check_tables=True, create_tables=True
    )
    return


class TestGetUserRatings(unittest.TestCase):
    @patch(mock_url_write_db)
    def setUp(self, write_db):
        write_db.side_effect = mocked_init_write_db

        global app
        app = importlib.import_module("loop-api.app")
        setup_rds()

    def tearDown(self):
        unbind_rds()

    def test_get_user_ratings_endpoint(self):
        # Happy path test
        with Client(app.app) as client:
            response = client.http.get(
                f'/ratings',
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.json_body,
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


class TestCreateRating(unittest.TestCase):
    @patch(mock_url_write_db)
    def setUp(self, write_db):
        write_db.side_effect = mocked_init_write_db

        global app
        app = importlib.import_module("loop-api.app")
        setup_rds()

    def tearDown(self):
        unbind_rds()

    def test_create_rating_endpoint(self):
        # Happy path test
        with Client(app.app) as client:
            response = client.http.post(
                f'/ratings',
                headers={'Content-Type': 'application/json'},
                body=json.dumps(
                    {
                        "google_id": 'test_google_id_1',
                        "price": 1,
                        "vibe": 5,
                        "food": 3,
                    }
                ),
            )
            self.assertEqual(response.status_code, 204)

    def test_create_rating_endpoint_pydantic_error_1(self):
        # Test pydantic error
        with Client(app.app) as client:
            response = client.http.post(
                f'/ratings',
                headers={'Content-Type': 'application/json'},
                body=json.dumps(
                    {
                        "google_id": 1,
                        "price": 1,
                        "vibe": 5,
                        "food": 3,
                    }
                ),
            )
            self.assertEqual(response.status_code, 400)

    def test_create_rating_endpoint_pydantic_error_2(self):
        # Test pydantic error
        with Client(app.app) as client:
            response = client.http.post(
                f'/ratings',
                headers={'Content-Type': 'application/json'},
                body=json.dumps(
                    {
                        "google_id": 1,
                        "price": 'average',
                        "vibe": 5,
                        "food": 3,
                    }
                ),
            )
            self.assertEqual(response.status_code, 400)

    def test_create_rating_endpoint_pydantic_error_3(self):
        # Test pydantic error
        with Client(app.app) as client:
            response = client.http.post(
                f'/ratings',
                headers={'Content-Type': 'application/json'},
                body=json.dumps(
                    {
                        "google_id": 1,
                        "price": 1,
                        "vibe": 'good',
                        "food": 3,
                    }
                ),
            )
            self.assertEqual(response.status_code, 400)

    def test_create_rating_endpoint_pydantic_error_4(self):
        # Test pydantic error
        with Client(app.app) as client:
            response = client.http.post(
                f'/ratings',
                headers={'Content-Type': 'application/json'},
                body=json.dumps(
                    {
                        "google_id": 1,
                        "price": 1,
                        "vibe": 5,
                        "food": 'poor',
                    }
                ),
            )
            self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
