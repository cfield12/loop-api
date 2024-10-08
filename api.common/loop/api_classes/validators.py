import re
from uuid import UUID

from loop.constants import (
    MAX_MESSAGE_LENGTH,
    MAX_RATING,
    MIN_RATING,
    VERIFICATION_CODE_LENGTH,
)
from loop.enums import UUIDVersion


def validate_str_uuid(str_uuid: str, version: UUIDVersion = UUIDVersion.FOUR):
    if not isinstance(str_uuid, str):
        raise TypeError('str_uuid should be a str.')
    if not isinstance(version, UUIDVersion):
        raise TypeError('version should be an instance of UUIDVersion.')
    try:
        return UUID(str_uuid, version=version.value)
    except ValueError:
        raise ValueError('Invalid str uuid.')


def validate_code(code: str, code_length=VERIFICATION_CODE_LENGTH):
    if not code.isdigit():
        raise ValueError('Code must contain only numbers')
    if len(code) != code_length:
        raise ValueError(f'Code must contain {code_length} characters')
    return code


def validate_email_address(email: str):
    if not re.match(
        r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", email
    ):
        raise ValueError('Must be valid email format.')
    return email


def validate_message_length(message: str):
    if not message:
        return None
    if isinstance(message, str) and len(message) > MAX_MESSAGE_LENGTH:
        raise ValueError('Message must maximum 200 characters.')
    return message


def validate_int(number: int, max_count=None, min_count=None):
    if max_count and number > max_count:
        raise ValueError(f'Number cannot exceed the maximum ({max_count})')
    if min_count and number < min_count:
        raise ValueError(
            f'Count cannot be lower than the minimum ({min_count})'
        )
    return number
