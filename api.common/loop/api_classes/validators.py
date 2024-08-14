from uuid import UUID

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
