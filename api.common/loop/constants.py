from enum import Enum

LOOP_ADMIN_ID = 1
LOOP_ADMIN_COGNITO_USERNAME = '86125274-40a1-70ec-da28-f779360f7c07'

RDS_WRITE = 'write'
DB_INSTANCE_TYPES = [RDS_WRITE]


class UUIDVersion(Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
