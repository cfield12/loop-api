import unittest
from unittest.mock import Mock, call, patch

from loop.data import DB_TYPE, RDS_WRITE
from loop.exceptions import UnknownFriendStatusType
from loop.friends import (
    FriendStatus,
    FriendStatusType,
    create_friend_entry,
    get_friend_db_object,
    get_friend_status,
)
from loop.test_setup import setup_rds, unbind_rds
from loop.utils import UserObject


class TestFriends(unittest.TestCase):
    def setUp(self):
        setup_rds()

    def tearDown(self):
        unbind_rds()

    def test_get_friend_status_friends(self):
        friend_status_type = FriendStatusType.FRIENDS
        self.assertEqual(
            get_friend_status(friend_status_type),
            FriendStatus(id=1, status=friend_status_type),
        )

    def test_get_friend_status_pending(self):
        friend_status_type = FriendStatusType.PENDING
        self.assertEqual(
            get_friend_status(friend_status_type),
            FriendStatus(id=2, status=friend_status_type),
        )

    def test_get_friend_status_blocked(self):
        friend_status_type = FriendStatusType.BLOCKED
        self.assertEqual(
            get_friend_status(friend_status_type),
            FriendStatus(id=3, status=friend_status_type),
        )

    def test_get_friend_status_unknown(self):
        friend_status_type = FriendStatusType.UNKNOWN
        self.assertRaises(
            UnknownFriendStatusType, get_friend_status, friend_status_type
        )

    def test_get_friend_db_object(self):
        # Show that it order of users doesn't matter when returning the
        # friendship
        user_2 = UserObject(
            id=2,
            cognito_user_name='test_cognito_user_name_admin',
        )
        user_3 = UserObject(
            id=3,
            cognito_user_name='test_cognito_user_name_person',
        )
        friendship_1 = get_friend_db_object(user_2, user_3)
        friendship_2 = get_friend_db_object(user_3, user_2)
        self.assertEqual(friendship_1.id, friendship_2.id, 1)

    def test_get_friend_db_object_no_friendship(self):
        user_1 = UserObject(
            id=1,
            cognito_user_name='test_cognito_user_name',
        )
        user_3 = UserObject(
            id=3,
            cognito_user_name='test_cognito_user_name_person',
        )
        friendship = get_friend_db_object(user_1, user_3)
        self.assertIsNone(friendship)

    def test_create_friend_entry(self):
        user_1 = UserObject(
            id=1,
            cognito_user_name='test_cognito_user_name',
        )
        user_3 = UserObject(
            id=3,
            cognito_user_name='test_cognito_user_name_person',
        )
        create_friend_entry(user_1, user_3)
        friendship = get_friend_db_object(user_1, user_3)
        self.assertIsNotNone(friendship)


if __name__ == '__main__':
    unittest.main()
