from enum import Enum


class UUIDVersion(Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4


class FriendStatusType(Enum):
    FRIENDS = 'Friends'
    PENDING = 'Pending'
    BLOCKED = 'Blocked'
    UNKNOWN = 'Unknown'
