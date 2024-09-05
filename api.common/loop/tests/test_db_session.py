import unittest
from unittest.mock import Mock, call, patch

from loop.db_session import DBSession
from loop.enums import DbType
from loop.exceptions import DbDisconnectFailedError
from pony.orm import Database


class TestDbSession(unittest.TestCase):
    def test_init_db_session(self):
        db_session = DBSession()
        self.assertTrue(
            hasattr(db_session, '_write_db'),
            "DBSession should have a '_write_db' attribute.",
        )
        self.assertFalse(
            hasattr(db_session, '_read_db'),
            "DBSession should not have a '_read_db' attribute.",
        )

    def test_get_item_db_session(self) -> None:
        # Get the write db instance
        db_session = DBSession()
        self.assertIsNone(db_session[DbType.WRITE])

    def test_get_item_db_session_error(self) -> None:
        # Raise an error when indexing with unrecognised value
        db_session = DBSession()
        with self.assertRaises(ValueError):
            db_session['write']

    def test_set_item_db_session(self):
        # Set the write db instance with Database()
        db_session = DBSession()
        db_session[DbType.WRITE] = Database()
        self.assertIsInstance(db_session[DbType.WRITE], Database)

    def test_set_item_db_session_error_1(self):
        # Raise an error when key is unrecognised value
        db_session = DBSession()
        with self.assertRaises(TypeError):
            db_session['write'] = Database()

    def test_set_item_db_session_error_2(self):
        # Raise an error when trying to set a an attribute with a non None or
        # Database entity
        db_session = DBSession()
        with self.assertRaises(DbDisconnectFailedError):
            db_session[DbType.WRITE] = 'database'

    def test_iter_db_session(self):
        db_session = DBSession()
        result = [x for x in db_session]
        self.assertEqual(result, ['_write_db'])

    def test_items_db_session(self):
        db_session = DBSession()
        db_session[DbType.WRITE] = Database()
        result = {
            db_instance_type: db for db_instance_type, db in db_session.items()
        }
        self.assertIn('_write_db', result)
        self.assertIsInstance(result['_write_db'], Database)

    def test_len_db_session(self):
        db_session = DBSession()
        self.assertEqual(len(db_session), 1)


if __name__ == '__main__':
    unittest.main()
