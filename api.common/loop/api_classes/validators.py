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


def validate_int_thresholds(number: int) -> int:
    if not MIN_RATING <= number <= MAX_RATING:
        raise ValueError('Ratings must be from 1 to 5')
    return number


def validate_message_length(message: str):
    if isinstance(message, str) and len(message) > MAX_MESSAGE_LENGTH:
        raise ValueError('Message must maximum 200 characters.')
    return message
