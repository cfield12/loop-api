import logging
import os
from dataclasses import dataclass
from enum import Enum

from loop.constants import RDS_WRITE
from loop.data import DB_SESSION_RETRYABLE, DB_TYPE
from loop.exceptions import BadRequestError, UnknownFriendStatusType
from loop.utils import UserObject
from pony.orm import commit

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


@DB_SESSION_RETRYABLE
def get_friend_status(
    friend_status_type: FriendStatusType, db_instance_type=RDS_WRITE
) -> FriendStatus:
    if not isinstance(friend_status_type, FriendStatusType):
        raise TypeError(
            'friend_status must be an instance of FriendStatusType.'
        )
    friend_status_obj = DB_TYPE[db_instance_type].Friend_status.get(
        description=friend_status_type.value
    )
    if not friend_status_obj:
        raise UnknownFriendStatusType(
            f'Unknown friend status supplied: {friend_status_type.value}'
        )
    return FriendStatus(id=friend_status_obj.id, status=friend_status_type)


@DB_SESSION_RETRYABLE
def get_friend_db_object(
    user_1: UserObject, user_2: UserObject, db_instance_type=RDS_WRITE
):
    return DB_TYPE[db_instance_type].Friend.get(
        friend_1=user_1.id,
        friend_2=user_2.id,
    ) or DB_TYPE[db_instance_type].Friend.get(
        friend_1=user_2.id,
        friend_2=user_1.id,
    )


def _create_friend_entry(
    requestor: UserObject, target: UserObject, db_instance_type=RDS_WRITE
):
    pending_status = get_friend_status(FriendStatusType.PENDING)
    if get_friend_db_object(requestor, target):
        raise BadRequestError(
            f'Friend entry already exists for users {requestor.id} and '
            f'{target.id}.'
        )
    friend_entry = DB_TYPE[db_instance_type].Friend(
        friend_1=requestor.id,
        friend_2=target.id,
        status=pending_status.id,
    )
    commit()
    logger.info(
        'Successfully created friend entry in rds between users '
        f'{requestor.id} and {target.id}.'
    )
    return


@DB_SESSION_RETRYABLE
def create_friend_entry(requestor: UserObject, target: UserObject):
    if not isinstance(requestor, UserObject) or not isinstance(
        target, UserObject
    ):
        raise TypeError('Users supplied here must be instances of UserObject.')
    return _create_friend_entry(requestor, target)
