from dataclasses import dataclass
from enum import Enum

from loop.constants import LOOP_ADMIN_COGNITO_USERNAME, LOOP_ADMIN_ID


class UserObject(object):
    cognito_user_name = None
    groups = {}
    id = 0

    def __init__(
        self,
        cognito_user_name=None,
        groups={},
        id=id,
    ):
        self.cognito_user_name = cognito_user_name
        self.groups = groups
        self.id = id


def get_admin_user():
    return UserObject(
        id=LOOP_ADMIN_ID, cognito_user_name=LOOP_ADMIN_COGNITO_USERNAME
    )


@dataclass
class UserCreateObject:
    cognito_user_name: str
    email: str
    first_name: str
    last_name: str


@dataclass
class Location:
    google_id: str
    address: str
    display_name: str


@dataclass
class Rating:
    location: int
    user: int
    price: int
    food: int
    vibe: int


class UUIDVersion(Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
