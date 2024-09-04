import random
import uuid
from dataclasses import asdict

from loop.constants import logger
from loop.data import (
    DB_SESSION_RETRYABLE,
    create_user,
    get_all_users,
    init_write_db,
)
from loop.data_classes import UserCreateObject
from pony.orm import commit, select

init_write_db()

# Sample data for generating names
FIRST_NAMES = [
    "John",
    "Alice",
    "Robert",
    "Mary",
    "Michael",
    "Linda",
    "William",
    "Elizabeth",
    "James",
    "Patricia",
]
SURNAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
]

TEST_SUFFIX = '_test'
EMAIL_SUFFIX = "@example.com"


def get_raandom_2_digit_int() -> int:
    return random.randint(10, 99)


def create_test_users(n: int) -> None:
    if not isinstance(n, int):
        raise TypeError('n must be an int.')
    for _ in range(n):
        # Generate a random first name and surname
        first_name = random.choice(FIRST_NAMES)
        surname = f'{random.choice(SURNAMES)}{TEST_SUFFIX}'

        # Generate a random email based on the first name and surname
        # We add a random number to the email to avoid duplicates
        random_number = get_raandom_2_digit_int()
        email = (
            f"{first_name.lower()}.{surname.lower()}{random_number}"
            f"{EMAIL_SUFFIX}"
        )
        user_create_job = UserCreateObject(
            cognito_user_name=str(uuid.uuid4()),
            email=email,
            first_name=first_name,
            last_name=surname,
        )
        create_user(user_create_job)
    return


@DB_SESSION_RETRYABLE
def delete_test_users() -> None:
    users = get_all_users()
    test_users = users.filter(lambda user: TEST_SUFFIX in user.last_name)
    test_users.delete(bulk=True)
    commit()
    return


if __name__ == '__main__':
    n = 50
    # create_test_users(n)
    delete_test_users()
