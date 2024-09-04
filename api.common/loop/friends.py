import math
import os
from typing import Dict, List, Union

from loop.api_classes import SearchUsers
from loop.constants import (
    MIN_FUZZ_SCORE,
    RDS_WRITE,
    SEARCH_USER_PAGE_COUNT,
    logger,
)
from loop.data import (
    DB_SESSION_RETRYABLE,
    DB_TYPE,
    get_all_users,
    get_ratings,
    update_object_last_updated_time,
)
from loop.data_classes import (
    NULL_USER_SEARCH_PAGE_RESULT,
    FriendStatus,
    PaginatedUserSearch,
    UserObject,
)
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
    def __init__(self, requestor: UserObject) -> None:
        if not isinstance(DB_TYPE[RDS_WRITE], Database):
            raise DbNotInitError(
                'DB must be initialised to use FriendWorker class.'
            )
        if not isinstance(requestor, UserObject):
            raise TypeError(
                'Requestor user supplied here must be instance of UserObject.'
            )
        self.db = DB_TYPE[RDS_WRITE]
        self.requestor = requestor

    def _get_friend_db_object(self, target_user: UserObject):
        return self.db.Friend.get(
            friend_1=self.requestor.id,
            friend_2=target_user.id,
        ) or self.db.Friend.get(
            friend_1=target_user.id,
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

    def _create_friend_entry(self, target_user: UserObject) -> None:
        pending_status = self._get_friend_status(FriendStatusType.PENDING)
        self.db.Friend(
            friend_1=self.requestor.id,
            friend_2=target_user.id,
            status=pending_status.id,
        )

    @DB_SESSION_RETRYABLE
    def create_friend_entry(self, target_user: UserObject) -> None:
        if not isinstance(target_user, UserObject):
            raise TypeError('target_user is an instance of UserObject')
        if self._get_friend_db_object(target_user):
            raise BadRequestError(
                f'Friend entry already exists for users {self.requestor.id} '
                f'and {target_user.id}.'
            )
        self._create_friend_entry(target_user)
        commit()
        logger.info(
            'Successfully created friend entry in rds between users '
            f'{self.requestor.id} and {target_user.id}.'
        )

    @DB_SESSION_RETRYABLE
    def accept_friend_request(self, target_user: UserObject) -> None:
        if not isinstance(target_user, UserObject):
            raise TypeError('target_user is an instance of UserObject')
        friend_object = self._get_friend_db_object(target_user)
        if not friend_object:
            raise BadRequestError(
                'Friend entry does not exist for users '
                f'{self.requestor.id} and {target_user.id}.'
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
            f'{self.requestor.id} (requestor) and {target_user.id} '
            '(target).'
        )

    @DB_SESSION_RETRYABLE
    def delete_friend(self, target_user: UserObject) -> None:
        '''
        The target user is the friend to be deleted.
        '''
        if not isinstance(target_user, UserObject):
            raise TypeError('target_user is an instance of UserObject')
        friend_object = self._get_friend_db_object(target_user)
        if not friend_object:
            raise BadRequestError(
                f'Friend entry does not exist for users '
                f'{self.requestor.id} and {target_user.id}.'
            )
        friend_object.delete()
        commit()
        logger.info(
            'Successfully deleted friendship between users '
            f'{self.requestor.id} (requestor) and {target_user.id}'
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


class UserSearch:
    def __init__(self, user_object: UserObject) -> None:
        if not isinstance(user_object, UserObject):
            raise TypeError('user should be of type UserObject')
        users = get_all_users()
        users = users.filter(lambda user: user.id != user_object.id)
        self.users = select(
            (
                user.id,
                user.cognito_user_name,
                user.first_name,
                user.last_name,
            )
            for user in users
        )
        self.friends = get_user_friend_ids(user_object, include_own_id=False)
        self.pending_friends = [
            request['id']
            for request in get_pending_requests(
                user_object, FriendRequestType.BOTH
            )
        ]
        self._search_users = self._get_search_users()
        self.pages = int()
        self.user_data = list()

    def _get_search_users(self) -> List[Dict[str, Union[int, str]]]:
        search_users = list()
        for user_id, username, first_name, last_name in self.users:
            name = f'{first_name} {last_name}'
            friend_status = (
                FriendStatusType.FRIENDS.value
                if user_id in self.friends
                else (
                    FriendStatusType.PENDING.value
                    if user_id in self.pending_friends
                    else FriendStatusType.NOT_FRIENDS.value
                )
            )
            search_users.append(
                {
                    'id': user_id,
                    'user_name': username,
                    'name': name,
                    'friend_status': friend_status,
                }
            )
        return search_users

    def _refine_users_by_search_term(
        self, search_term: str
    ) -> List[Dict[str, Union[int, str]]]:
        names = list(set([user.get('name') for user in self._search_users]))
        response = process.extract(
            search_term,
            names,
            scorer=fuzz.WRatio,
            processor=default_process,
        )
        matches = [item[0] for item in response if item[1] > MIN_FUZZ_SCORE]
        return sorted(
            [user for user in self._search_users if user['name'] in matches],
            key=lambda x: matches.index(x['name']),
        )

    def refine_search(self, search_users_obj: SearchUsers) -> None:
        if not isinstance(search_users_obj, SearchUsers):
            raise TypeError(
                'search_users_obj should be an instance of SearchUsers'
            )
        search_term = search_users_obj.term
        page_count = search_users_obj.page_count
        if search_term:
            users = self._refine_users_by_search_term(search_term)
        else:
            users = self._search_users
        count = len(users)
        if count == 0:
            return
        pages = math.ceil(count / SEARCH_USER_PAGE_COUNT)
        if page_count > pages:
            raise BadRequestError(
                f'Page does not exist for query. (total pages = {pages}).'
            )
        self.pages = pages
        self.user_data = users[
            (page_count - 1)
            * SEARCH_USER_PAGE_COUNT : page_count
            * SEARCH_USER_PAGE_COUNT
        ]

    def return_search(self) -> PaginatedUserSearch:
        return PaginatedUserSearch(
            user_data=self.user_data, total_pages=self.pages
        )


@DB_SESSION_RETRYABLE
def search_for_users(
    user_object: UserObject, search_users: SearchUsers
) -> List[Dict]:
    user_searcher = UserSearch(user_object)
    user_searcher.refine_search(search_users)
    return user_searcher.return_search()


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
