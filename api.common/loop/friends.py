import os
from typing import Dict, List

from loop.constants import MIN_FUZZ_SCORE, RDS_WRITE, logger
from loop.data import (
    DB_SESSION_RETRYABLE,
    DB_TYPE,
    get_all_users,
    get_ratings,
    update_object_last_updated_time,
)
from loop.data_classes import FriendStatus, UserObject
from loop.enums import FriendRequestType, FriendStatusType
from loop.exceptions import (
    BadRequestError,
    DbNotInitError,
    UnknownFriendStatusTypeError,
)
from pony.orm import Database, commit, select
from pony.orm.core import Query
from rapidfuzz import fuzz, process
from rapidfuzz.utils import default_process


class FriendWorker:
    def __init__(self, requestor: UserObject, target: UserObject) -> None:
        if not isinstance(DB_TYPE[RDS_WRITE], Database):
            raise DbNotInitError(
                'DB must be initialised to use FriendWorker class.'
            )
        if not isinstance(requestor, UserObject) or not isinstance(
            target, UserObject
        ):
            raise TypeError(
                'Users supplied here must be instances of UserObject.'
            )
        self.db = DB_TYPE[RDS_WRITE]
        self.requestor = requestor
        self.target = target

    def _get_friend_db_object(self):
        return self.db.Friend.get(
            friend_1=self.requestor.id,
            friend_2=self.target.id,
        ) or self.db.Friend.get(
            friend_1=self.target.id,
            friend_2=self.requestor.id,
        )

    def _get_friend_status(
        self,
        friend_status_type: FriendStatusType,
    ) -> FriendStatus:
        if not isinstance(friend_status_type, FriendStatusType):
            raise TypeError(
                'friend_status must be an instance of FriendStatusType.'
            )
        friend_status_obj = self.db.Friend_status.get(
            description=friend_status_type.value
        )
        if not friend_status_obj:
            raise UnknownFriendStatusTypeError(
                f'Unknown friend status supplied: {friend_status_type.value}'
            )
        return FriendStatus(id=friend_status_obj.id, status=friend_status_type)

    def _create_friend_entry(self) -> None:
        pending_status = self._get_friend_status(FriendStatusType.PENDING)
        self.db.Friend(
            friend_1=self.requestor.id,
            friend_2=self.target.id,
            status=pending_status.id,
        )

    @DB_SESSION_RETRYABLE
    def create_friend_entry(self) -> None:
        if self._get_friend_db_object():
            raise BadRequestError(
                f'Friend entry already exists for users {self.requestor.id} '
                f'and {self.target.id}.'
            )
        self._create_friend_entry()
        commit()
        logger.info(
            'Successfully created friend entry in rds between users '
            f'{self.requestor.id} and {self.target.id}.'
        )

    @DB_SESSION_RETRYABLE
    def accept_friend_request(self) -> None:
        friend_object = self._get_friend_db_object()
        if not friend_object:
            raise BadRequestError(
                'Friend entry does not exist for users '
                f'{self.requestor.id} and {self.target.id}.'
            )
        friend_status = self._get_friend_status(FriendStatusType.FRIENDS)
        if friend_object.status.id == friend_status.id:
            raise BadRequestError(f'Friend request already accepted.')
        if friend_object.friend_2.id != self.requestor.id:
            raise BadRequestError(
                'Friend request can only be accepted by user '
                f'{self.requestor.id}.'
            )
        friend_object.status = friend_status.id
        update_object_last_updated_time(friend_object)
        commit()
        logger.info(
            'Successfully accepted friend request between users '
            f'{self.requestor.id} (requestor) and {self.target.id} '
            '(target).'
        )

    @DB_SESSION_RETRYABLE
    def delete_friend(self) -> None:
        '''
        The target user is the friend to be deleted.
        '''
        friend_object = self._get_friend_db_object()
        if not friend_object:
            raise BadRequestError(
                f'Friend entry does not exist for users '
                f'{self.requestor.id} and {self.target.id}.'
            )
        friend_object.delete()
        commit()
        logger.info(
            'Successfully deleted friendship between users '
            f'{self.requestor.id} (requestor) and {self.target.id}'
            ' (target).'
        )


def _get_friends_from_query(query: Query, user: UserObject) -> List:
    friends = []
    for user_1, user_2 in query:
        if user_1.id == user.id:
            friend = user_2
        else:
            friend = user_1
        friend_dict = {
            'id': friend.id,
            'user_name': friend.cognito_user_name,
            'email': friend.email,
            'first_name': friend.first_name,
            'last_name': friend.last_name,
        }
        friends.append(friend_dict)
    return friends


@DB_SESSION_RETRYABLE
def get_user_friends(user: UserObject) -> List:
    if not isinstance(user, UserObject):
        raise TypeError('user should be of type UserObject')
    friends_query = select(
        (friend.friend_1, friend.friend_2)
        for friend in DB_TYPE[RDS_WRITE].Friend
        if ((friend.friend_1.id == user.id) or (friend.friend_2.id == user.id))
        and friend.status.description == FriendStatusType.FRIENDS.value
    )
    return _get_friends_from_query(friends_query, user)


def get_user_friend_ids(user: UserObject, include_own_id=True) -> List[int]:
    """
    This function returns a list of user's friend ids.

    It has the option to include the user's id.
    """
    if not isinstance(user, UserObject):
        raise TypeError('user should be of type UserObject')
    users = [friend['id'] for friend in get_user_friends(user)]
    if include_own_id:
        users.append(user.id)
    return users


@DB_SESSION_RETRYABLE
def search_for_users(user_object: UserObject, search_term: str) -> List[Dict]:
    '''
    In this function we search users using RapidFuzz string matching.
    '''
    if not isinstance(user_object, UserObject):
        raise TypeError('user should be of type UserObject')
    if not isinstance(search_term, str):
        raise TypeError('search_term should be of type str')
    search_term = search_term.strip()
    users = get_all_users()
    users = users.filter(lambda user: user.id != user_object.id)
    users = select(
        (
            user.id,
            user.cognito_user_name,
            user.first_name,
            user.last_name,
        )
        for user in users
    )
    users_friends = get_user_friend_ids(user_object, include_own_id=False)
    pending_friends = [
        request['id']
        for request in get_pending_requests(
            user_object, FriendRequestType.BOTH
        )
    ]
    search_users = dict()
    for user_id, username, first_name, last_name in users:
        name = f'{first_name} {last_name}'
        friend_status = (
            FriendStatusType.FRIENDS.value
            if user_id in users_friends
            else (
                FriendStatusType.PENDING.value
                if user_id in pending_friends
                else FriendStatusType.NOT_FRIENDS.value
            )
        )
        search_users[name] = {
            'id': user_id,
            'user_name': username,
            'name': name,
            'friend_status': friend_status,
        }
    names = [name for name in search_users]
    if not search_term:
        return [search_users[user] for user in search_users]
    response = process.extract(
        search_term, names, scorer=fuzz.WRatio, processor=default_process
    )
    matches = [item[0] for item in response if item[1] > MIN_FUZZ_SCORE]
    return [search_users[name] for name in matches]


@DB_SESSION_RETRYABLE
def get_ratings_for_place_and_friends(place_id: str, user: UserObject) -> List:
    if not isinstance(user, UserObject):
        raise TypeError('user should be of type UserObject')
    users_friends: List[int] = get_user_friend_ids(user)
    return get_ratings(users_friends, place_id=place_id)


@DB_SESSION_RETRYABLE
def get_pending_requests(
    user: UserObject, request_type: FriendRequestType
) -> List:
    if not isinstance(user, UserObject):
        raise TypeError('user should be of type UserObject')
    friends_query = select(
        friend
        for friend in DB_TYPE[RDS_WRITE].Friend
        if friend.status.description == FriendStatusType.PENDING.value
    )
    if request_type == FriendRequestType.INBOUND:
        friends_query = friends_query.filter(
            lambda friend: friend.friend_2.id == user.id
        )
    elif request_type == FriendRequestType.OUTBOUND:
        friends_query = friends_query.filter(
            lambda friend: friend.friend_1.id == user.id
        )
    elif request_type == FriendRequestType.BOTH:
        friends_query = friends_query.filter(
            lambda friend: friend.friend_1.id == user.id
            or friend.friend_2.id == user.id
        )
    else:
        raise TypeError('request_type should be of type FriendRequestType.')
    friends_query = select(
        (friend.friend_1, friend.friend_2) for friend in friends_query
    )
    return _get_friends_from_query(friends_query, user)
