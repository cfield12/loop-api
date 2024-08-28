import json
from copy import deepcopy
from typing import Dict, Generator, List

from loop.api_classes import Coordinates
from loop.constants import (
    LOOP_ADMIN_COGNITO_USERNAME,
    LOOP_ADMIN_GROUP,
    LOOP_ADMIN_ID,
)
from loop.data_classes import UserObject


def get_admin_user():
    return UserObject(
        id=LOOP_ADMIN_ID,
        cognito_user_name=LOOP_ADMIN_COGNITO_USERNAME,
        groups=[LOOP_ADMIN_GROUP],
    )


def conditional_load(body):
    if isinstance(body, str):
        body = json.loads(body)
    return body


def conditional_dump(body):
    if not isinstance(body, str):
        body = json.dumps(body)
    return body


def sqs_batch(event: Dict[str, List]) -> Generator:
    # Load the event.
    event = conditional_load(event)

    if 'Records' not in event:
        raise ValueError('Unexpected SQS batch format.')

    # Pull out records.
    for message in event['Records']:
        yield conditional_load(message.get('body'))
