import os
from datetime import datetime
from time import sleep
from typing import Dict, List, Optional, Union

from loop import exceptions, secrets
from loop.constants import (
    ENVIRONMENT,
    LOOP_TIME_FORMAT,
    MAX_DB_INIT_RETRIES,
    PROJECT,
    RDS_WRITE,
    RETRY_DB_DELAY_SECONDS,
    logger,
)
from loop.data_classes import Location, Rating, UserCreateObject, UserObject
from loop.db_entities import define_entities
from loop.google_client import find_location
from pony.orm import Database
from pony.orm import InternalError as PonyOrmDbInternalError
from pony.orm import (
    MultipleObjectsFoundError,
    OperationalError,
    TransactionError,
    commit,
    db_session,
    select,
)
from pony.orm.core import Query

DB_SESSION_RETRYABLE = db_session(
    retry=5,
    retry_exceptions=(
        TransactionError,
        PonyOrmDbInternalError,
        OperationalError,
    ),
)


def init_db(db_dict=None, check_tables=False, create_tables=False):
    for retry_count in range(MAX_DB_INIT_RETRIES + 1):
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
                if retry_count < MAX_DB_INIT_RETRIES:
                    print(
                        f"Retrying to init db in {RETRY_DB_DELAY_SECONDS} "
                        "secs."
                    )
                    sleep(RETRY_DB_DELAY_SECONDS)
                else:
                    raise exceptions.DbInitFailedError(
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
    user: UserObject, db_instance_type=RDS_WRITE
) -> List[Dict[str, int]]:
    if not isinstance(user, UserObject):
        raise TypeError('User must be an instance of UserObject.')
    ratings = []
    ratings_query = select(
        (
            rating.food,
            rating.price,
            rating.vibe,
            rating.location.display_name,
            rating.location.address,
            rating.location.google_id,
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
    cognito_user_name: str, db_instance_type=RDS_WRITE
) -> UserObject:
    user = DB_TYPE[db_instance_type].User.get(
        cognito_user_name=cognito_user_name
    )
    if not user:
        raise exceptions.BadRequestError('User not found')
    user_id = user.id
    return UserObject(id=user_id, cognito_user_name=user.cognito_user_name)


@DB_SESSION_RETRYABLE
def create_user(user: UserCreateObject, db_instance_type=RDS_WRITE) -> None:
    if not isinstance(user, UserCreateObject):
        raise TypeError('user must be an instance of UserCreateObject')
    DB_TYPE[db_instance_type].User(
        cognito_user_name=user.cognito_user_name,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    commit()
    logger.info(f'Successfully created user in rds: {user.__dict__}')
    return


@DB_SESSION_RETRYABLE
def create_rating(rating: Rating, db_instance_type=RDS_WRITE) -> None:
    if not isinstance(rating, Rating):
        raise TypeError('rating must be an instance of Rating')
    DB_TYPE[db_instance_type].Rating(
        price=rating.price,
        vibe=rating.vibe,
        food=rating.food,
        location=rating.location,
        user=rating.user,
    )
    commit()
    logger.info(f'Successfully created rating in rds: {rating.__dict__}')
    return


@DB_SESSION_RETRYABLE
def create_location_entry(location: Location, db_instance_type=RDS_WRITE):
    if not isinstance(location, Location):
        raise TypeError('user must be an instance of Location')
    location_entry = DB_TYPE[db_instance_type].Location(
        google_id=location.google_id,
        address=location.address,
        display_name=location.display_name,
        latitude=location.coordinates.lat,
        longitude=location.coordinates.lng,
    )
    commit()
    logger.info(f'Successfully created location in rds: {location.__dict__}')
    return location_entry


@DB_SESSION_RETRYABLE
def get_or_create_location_id(
    google_id: str, db_instance_type=RDS_WRITE
) -> int:
    if not isinstance(google_id, str):
        raise TypeError('google_id must be of type string')
    location = DB_TYPE[db_instance_type].Location.get(google_id=google_id)
    if not location:
        location_object: Location = find_location(google_id)
        location = create_location_entry(location_object)
    return location.id


@DB_SESSION_RETRYABLE
def update_object_last_updated_time(db_object) -> None:
    try:
        db_object.last_updated
    except AttributeError as e:
        raise AttributeError(
            f'DB object {db_object} does not have a last_updated field: {e}'
        )
    db_object.last_updated = datetime.utcnow()
    commit()
    return


@DB_SESSION_RETRYABLE
def get_all_users(db_instance_type=RDS_WRITE) -> Query:
    return select(user for user in DB_TYPE[db_instance_type].User)


@DB_SESSION_RETRYABLE
def get_ratings(
    users: List[int],
    place_id: Optional[str] = None,
    db_instance_type=RDS_WRITE,
) -> Dict:
    reviews = list()
    ratings = select(
        rating
        for rating in DB_TYPE[db_instance_type].Rating
        if rating.user.id in users
    )
    if place_id:
        ratings = ratings.filter(
            lambda rating: rating.location.google_id == place_id
        )
    for r in ratings:
        reviews.append(
            {
                'first_name': r.user.first_name,
                'last_name': r.user.last_name,
                'place_id': r.location.google_id,
                'latitude': r.location.latitude,
                'longitude': r.location.longitude,
                'food': r.food,
                'price': r.price,
                'vibe': r.vibe,
                'time_created': r.created.strftime(LOOP_TIME_FORMAT),
            }
        )
    return reviews
