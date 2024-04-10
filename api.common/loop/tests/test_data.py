import unittest
from unittest.mock import call, patch

from loop import data
from loop.test_setup import setup_rds, unbind_rds


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

    @patch('loop.data.sleep')
    def test_init_db_error(self, mock_sleep):
        pass
