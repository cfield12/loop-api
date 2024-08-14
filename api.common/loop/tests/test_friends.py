import unittest
from unittest.mock import Mock, call, patch

from loop.data import DB_SESSION_RETRYABLE, DB_TYPE, RDS_WRITE
from loop.data_classes import FriendStatus, UserObject
from loop.enums import FriendStatusType
from loop.exceptions import (
    BadRequestError,
    DbNotInitError,
    UnknownFriendStatusTypeError,
)
from loop.friends import FriendWorker, get_user_friends
from loop.test_setup import setup_rds, unbind_rds

USER_1 = UserObject(
    id=1,
    cognito_user_name='test_cognito_user_name',
)
USER_2 = UserObject(
    id=2,
    cognito_user_name='86125274-40a1-70ec-da28-f779360f7c07',
)
USER_3 = UserObject(
    id=3,
    cognito_user_name='60c1f02b-f758-4458-8c41-3b5c9fa20ae0',
)
USER_4 = UserObject(
    id=4,
    cognito_user_name='67ce7049-109f-420f-861b-3f1e7d6824b5',
)


class TestInitFriendWorker(unittest.TestCase):
    def test_init_friend_worker_db_not_init_error(self):
        DB_TYPE[RDS_WRITE] = None
        self.assertRaises(DbNotInitError, FriendWorker, USER_2, USER_3)


class TestFriends(unittest.TestCase):
    def setUp(self):
        setup_rds()

    def tearDown(self):
        unbind_rds()

    def _init_friend_worker(self) -> FriendWorker:
        return FriendWorker(USER_2, USER_3)

    def test_init_friend_worker_type_error(self):
        user = 4
        self.assertRaises(TypeError, FriendWorker, USER_2, user)

    @DB_SESSION_RETRYABLE
    def test_get_friend_status_friends(self):
        friend_worker = self._init_friend_worker()
        friend_status_type = FriendStatusType.FRIENDS
        self.assertEqual(
            friend_worker._get_friend_status(friend_status_type),
            FriendStatus(id=1, status=friend_status_type),
        )

    @DB_SESSION_RETRYABLE
    def test_get_friend_status_pending(self):
        friend_worker = self._init_friend_worker()
        friend_status_type = FriendStatusType.PENDING
        self.assertEqual(
            friend_worker._get_friend_status(friend_status_type),
            FriendStatus(id=2, status=friend_status_type),
        )

    @DB_SESSION_RETRYABLE
    def test_get_friend_status_blocked(self):
        friend_worker = self._init_friend_worker()
        friend_status_type = FriendStatusType.BLOCKED
        self.assertEqual(
            friend_worker._get_friend_status(friend_status_type),
            FriendStatus(id=3, status=friend_status_type),
        )

    @DB_SESSION_RETRYABLE
    def test_get_friend_status_unknown(self):
        friend_worker = self._init_friend_worker()
        friend_status_type = FriendStatusType.UNKNOWN
        self.assertRaises(
            UnknownFriendStatusTypeError,
            friend_worker._get_friend_status,
            friend_status_type,
        )

    @DB_SESSION_RETRYABLE
    def test_get_friend_db_object(self):
        # Show that it order of users doesn't matter when returning the
        # friendship
        friend_worker_1 = FriendWorker(USER_2, USER_3)
        friend_worker_2 = FriendWorker(USER_3, USER_2)

        friendship_1 = friend_worker_1._get_friend_db_object()
        friendship_2 = friend_worker_2._get_friend_db_object()
        self.assertEqual(friendship_1.id, friendship_2.id, 1)

    @DB_SESSION_RETRYABLE
    def test_get_friend_db_object_no_friendship(self):
        friend_worker = FriendWorker(USER_1, USER_3)
        friendship = friend_worker._get_friend_db_object()
        self.assertIsNone(friendship)

    @DB_SESSION_RETRYABLE
    def test_create_friend_entry(self):
        friend_worker = FriendWorker(USER_1, USER_3)
        friend_worker.create_friend_entry()
        friendship = friend_worker._get_friend_db_object()
        self.assertIsNotNone(friendship)

    def test_accept_friend_request_error_1(self):
        '''
        This error is because the person who sent the original request is
        trying to accept that request
        '''
        friend_worker = FriendWorker(USER_3, USER_4)
        self.assertRaises(BadRequestError, friend_worker.accept_friend_request)

    def test_accept_friend_request_error_3(self):
        '''
        This error is because the friend request has already been accepted
        '''
        friend_worker = FriendWorker(USER_2, USER_3)
        self.assertRaises(BadRequestError, friend_worker.accept_friend_request)

    def test_accept_friend_request_error_4(self):
        '''
        This error is because the there is no friend request
        '''
        friend_worker = FriendWorker(USER_1, USER_3)
        self.assertRaises(BadRequestError, friend_worker.accept_friend_request)

    @DB_SESSION_RETRYABLE
    def test_accept_friend_request(self):
        '''
        This error is because the there is no friend request
        '''
        friend_worker = FriendWorker(USER_4, USER_3)
        friend_worker.accept_friend_request()
        friendship = friend_worker._get_friend_db_object()
        self.assertEqual(friendship.status.id, 1)

    @DB_SESSION_RETRYABLE
    def test_delete_friend(self):
        '''
        Test delete friend
        '''
        friend_worker = FriendWorker(USER_2, USER_3)
        friend_worker.delete_friend()
        self.assertIsNone(friend_worker._get_friend_db_object())

    def test_delete_friend_who_arent_friends(self):
        '''
        Test trying to delete a friend where does not exist
        '''
        friend_worker = FriendWorker(USER_1, USER_3)
        self.assertRaises(BadRequestError, friend_worker.delete_friend)

    def test_get_user_friends(self):
        expected_friends = [
            {
                'id': 3,
                'user_name': '60c1f02b-f758-4458-8c41-3b5c9fa20ae0',
                'email': 'test_person_email',
                'first_name': 'Random',
                'last_name': 'Person',
            }
        ]
        user_friends = get_user_friends(USER_2)
        self.assertEqual(user_friends, expected_friends)


if __name__ == '__main__':
    unittest.main()
