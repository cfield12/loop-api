import unittest
from unittest.mock import Mock, call, patch

from loop.data import DB_TYPE, RDS_WRITE
from loop.exceptions import BadRequestError, UnknownFriendStatusType
from loop.friends import (
    FriendStatus,
    FriendStatusType,
    accept_friend_request,
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

    def test_accept_friend_request_error_1(self):
        '''
        This error is because the person who sent the original request is
        trying to accept that request
        '''
        user_1 = UserObject(
            id=3,
            cognito_user_name='60c1f02b-f758-4458-8c41-3b5c9fa20ae0',
        )
        user_2 = UserObject(
            id=4,
            cognito_user_name='67ce7049-109f-420f-861b-3f1e7d6824b5',
        )
        self.assertRaises(
            BadRequestError, accept_friend_request, user_1, user_2
        )

    def test_accept_friend_request_error_2(self):
        '''
        This error is because the users passed in the args must be an instance
        of UserObject
        '''
        user_1 = UserObject(
            id=3,
            cognito_user_name='60c1f02b-f758-4458-8c41-3b5c9fa20ae0',
        )
        user_2 = 4
        self.assertRaises(TypeError, accept_friend_request, user_1, user_2)

    def test_accept_friend_request_error_3(self):
        '''
        This error is because the friend request has already been accepted
        '''
        user_1 = UserObject(
            id=2,
            cognito_user_name='86125274-40a1-70ec-da28-f779360f7c07',
        )
        user_2 = UserObject(
            id=3,
            cognito_user_name='60c1f02b-f758-4458-8c41-3b5c9fa20ae0',
        )
        self.assertRaises(
            BadRequestError, accept_friend_request, user_1, user_2
        )

    def test_accept_friend_request_error_4(self):
        '''
        This error is because the there is no friend request
        '''
        user_1 = UserObject(
            id=1,
            cognito_user_name='test_cognito_user_name',
        )
        user_2 = UserObject(
            id=3,
            cognito_user_name='60c1f02b-f758-4458-8c41-3b5c9fa20ae0',
        )
        self.assertRaises(
            BadRequestError, accept_friend_request, user_1, user_2
        )

    def test_accept_friend_request(self):
        '''
        This error is because the there is no friend request
        '''
        user_1 = UserObject(
            id=4,
            cognito_user_name='67ce7049-109f-420f-861b-3f1e7d6824b5',
        )
        user_2 = UserObject(
            id=3,
            cognito_user_name='60c1f02b-f758-4458-8c41-3b5c9fa20ae0',
        )
        accept_friend_request(user_1, user_2)
        friendship = get_friend_db_object(user_1, user_2)
        self.assertEqual(friendship.status.id, 1)


if __name__ == '__main__':
    unittest.main()
