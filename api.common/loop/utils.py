import json
from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Dict

from loop.api_classes import Coordinates
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
    coordinates: Coordinates
    photo_reference: str = None
    website: str = None
    phone_number: str = None
    price_level: int = None

    def to_dict(self) -> Dict[str, str]:
        d = deepcopy(asdict(self))
        d['coordinates'] = d['coordinates'].model_dump()
        return d


@dataclass
class Rating:
    location: int
    user: int
    price: int
    food: int
    vibe: int


def conditional_load(body):
    if isinstance(body, str):
        body = json.loads(body)
    return body


def sqs_batch(event):
    # Load the event.
    event = conditional_load(event)

    if 'Records' not in event:
        raise ValueError('Unexpected SQS batch format.')

    # Pull out records.
    for message in event['Records']:
        yield conditional_load(message.get('body'))
