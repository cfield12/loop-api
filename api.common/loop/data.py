import logging
import os
from time import sleep
from typing import Dict, List, Union

from loop.utils import UserObject
from pony.orm import (
    commit,
    Database,
    db_session,
    MultipleObjectsFoundError,
    OperationalError,
    select,
    TransactionError
)
from pony.orm import InternalError as PonyOrmDbInternalError


from loop.constants import RDS_WRITE
from loop.db_entities import define_entities
from loop import exceptions
from loop import secrets

ENVIRONMENT = os.environ.get('ENVIRONMENT', 'develop')
PROJECT = os.environ.get('PROJECT', 'loop')

logger = logging.getLogger()
LOGLEVEL = os.environ.get("LOGLEVEL", "INFO")
logger.setLevel(LOGLEVEL)

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

DB_SESSION_RETRYABLE = db_session(
    retry=5,
    retry_exceptions=(
        TransactionError,
        PonyOrmDbInternalError,
        OperationalError,
    ),
)


def init_db(db_dict=None, check_tables=False, create_tables=False):
    for retry_count in range(MAX_RETRIES + 1):
        try:
            db = Database()
            define_entities(db)
            db.bind(**db_dict)
            db.generate_mapping(
                check_tables=check_tables, create_tables=create_tables
            )
            return db
        except Exception as error:
            if "was already bound" in repr(error):
                print("Reusing DB connection: %s" % error)
                return
            elif "Mapping was already generated" in repr(error):
                print("Already mapped: %s" % error)
                return
            else:
                if retry_count < MAX_RETRIES:
                    print(
                        f"Retrying to init db in {RETRY_DELAY_SECONDS} secs."
                    )
                    sleep(RETRY_DELAY_SECONDS)
                else:
                    raise ValueError(
                        'Failed to initialise database in data.py.'
                    )


DB_TYPE = {RDS_WRITE: None}


def init_write_db(check_tables=False, create_tables=False):
    instance = os.environ.get(
        'RDS_SECRET_NAME',
        f'{PROJECT}-secret-rds-connection-{ENVIRONMENT}',
    )
    db_dict = secrets.get_db_dict(instance)
    write_db = init_db(db_dict, check_tables, create_tables)
    DB_TYPE[RDS_WRITE] = write_db


def disconnect_db():
    for instance_type, db in DB_TYPE.items():
        try:
            if isinstance(db, Database):
                db.disconnect()
            elif db is None:
                continue
            else:
                raise exceptions.DbDisconnectFailedError(
                    f'Unknown db type: {type(db)}.'
                )
        except Exception as error:
            raise exceptions.DbDisconnectFailedError(
                f'Failed to disconnect {instance_type} database ({error}).'
            )


@DB_SESSION_RETRYABLE
def get_user_ratings(
    user: UserObject,
    db_instance_type=RDS_WRITE
) -> List[Dict[str, int]]:
    ratings = []
    ratings_query = select(
        (
            rating.food,
            rating.price,
            rating.vibe,
            rating.location.display_name,
            rating.location.address,
            rating.location.google_id
        )
        for rating in DB_TYPE[db_instance_type].Rating
        if rating.user.id == user.id
    )
    for (
        food,
        price,
        vibe,
        place_name,
        address,
        google_id,
    ) in ratings_query:
        ratings.append(
            {
                'food': food,
                'price': price,
                'vibe': vibe,
                'place_name': place_name,
                'address': address,
                'google_id': google_id,
            }
        )
    return ratings


@DB_SESSION_RETRYABLE
def get_user_from_cognito_username(
    cognito_user_name: str,
    db_instance_type=RDS_WRITE
) -> UserObject:
    user = DB_TYPE[db_instance_type].User.get(
        cognito_user_name=cognito_user_name
    )
    if not user:
        raise exceptions.UnauthorizedError('User not found')
    user_id = user.id
    user = UserObject(id=user_id, cognito_user_name=user.cognito_user_name)
    return user
