import importlib
import unittest
from unittest.mock import patch

from chalice.test import Client
from loop import data
from loop.constants import RDS_WRITE
from loop.test_setup.common import setup_rds, unbind_rds
from loop.utils import UserObject

mock_url_write_db = 'loop.data.init_write_db'


class TestGetUserRatings(unittest.TestCase):
    @patch(mock_url_write_db)
    def setUp(self, write_db):
        def mocked_init_write_db(check_tables=False, create_tables=False):
            if not check_tables and not create_tables:
                return
            db_dict = {'provider': 'sqlite', 'filename': ':memory:'}
            data.DB_TYPE[RDS_WRITE] = data.init_db(
                db_dict, check_tables=True, create_tables=True
            )
            return

        write_db.side_effect = mocked_init_write_db

        global app
        app = importlib.import_module("loop-api.app")
        setup_rds()

    def tearDown(self):
        unbind_rds()

    def test_get_models_endpoint(self):
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


if __name__ == "__main__":
    unittest.main()
