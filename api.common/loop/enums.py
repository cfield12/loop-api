from enum import Enum

"""This module contains all loop Enums"""


class UUIDVersion(Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4


class FriendStatusType(Enum):
    FRIENDS = 'Friends'
    PENDING = 'Pending'
    BLOCKED = 'Blocked'
    NOT_FRIENDS = 'Not friends'
    UNKNOWN = 'Unknown'


class FriendRequestType(Enum):
    INBOUND = 'inbound'
    OUTBOUND = 'outbound'
    BOTH = 'both'


class DbType(Enum):
    WRITE = 'write'
