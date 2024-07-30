import logging
import os
from dataclasses import dataclass
from enum import Enum

from loop.constants import RDS_WRITE
from loop.data import (
    DB_SESSION_RETRYABLE,
    DB_TYPE,
    update_object_last_updated_time,
)
from loop.exceptions import (
    BadRequestError,
    DbNotInitError,
    UnknownFriendStatusTypeError,
)
from loop.utils import UserObject
from pony.orm import Database, commit

logger = logging.getLogger()
LOGLEVEL = os.environ.get("LOGLEVEL", "INFO")
logger.setLevel(LOGLEVEL)


class FriendStatusType(Enum):
    FRIENDS = 'Friends'
    PENDING = 'Pending'
    BLOCKED = 'Blocked'
    UNKNOWN = 'Unknown'


@dataclass
class FriendStatus:
    id: int
    status: FriendStatusType


@dataclass
class Friendship:
    friend_1: UserObject
    friend_2: UserObject
    status: FriendStatus


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
