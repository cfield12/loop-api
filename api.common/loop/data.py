import math
import os
from datetime import datetime
from time import sleep
from typing import Dict, List, Optional, Union

from loop import exceptions, secrets
from loop.api_classes import PaginatedRatings, UpdateRating
from loop.constants import (
    ENVIRONMENT,
    LOOP_TIME_FORMAT,
    MAX_DB_INIT_RETRIES,
    PROJECT,
    RATINGS_PAGE_COUNT,
    RDS_WRITE,
    RETRY_DB_DELAY_SECONDS,
    logger,
)
from loop.data_classes import (
    Location,
    Rating,
    RatingsPageResults,
    UserCreateObject,
    UserObject,
)
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
    desc,
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
            rating.id,
            rating.food,
            rating.price,
            rating.vibe,
            rating.message,
            rating.location.display_name,
            rating.location.address,
            rating.location.google_id,
        )
        for rating in DB_TYPE[db_instance_type].Rating
        if rating.user.id == user.id
    )
    for (
        id,
        food,
        price,
        vibe,
        message,
        place_name,
        address,
        google_id,
    ) in ratings_query:
        ratings.append(
            {
                'id': id,
                'food': food,
                'price': price,
                'vibe': vibe,
                'message': message,
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
    return UserObject(
        id=user.id,
        cognito_user_name=user.cognito_user_name,
        groups=[group.description for group in user.groups],
    )


@DB_SESSION_RETRYABLE
def get_user_from_email(email: str, db_instance_type=RDS_WRITE) -> UserObject:
    user = DB_TYPE[db_instance_type].User.get(email=email)
    if not user:
        raise exceptions.BadRequestError('User not found')
    return UserObject(
        id=user.id,
        cognito_user_name=user.cognito_user_name,
        groups=[group.description for group in user.groups],
    )


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
        message=rating.message,
    )
    commit()
    logger.info(f'Successfully created rating in rds: {rating.__dict__}')
    return


def _get_rating(rating_id: int, user: UserObject, db_instance_type=RDS_WRITE):
    if not isinstance(rating_id, int):
        raise TypeError('rating_id must be an int.')
    if not isinstance(user, UserObject):
        raise TypeError('user must be an instance of UserObject.')
    rating = DB_TYPE[db_instance_type].Rating.get(id=rating_id, user=user.id)
    if not rating:
        raise exceptions.BadRequestError(
            f'Could not find rating with id {rating_id} for user '
            f'{user.id} to update.'
        )
    return rating


@DB_SESSION_RETRYABLE
def update_rating(
    update_rating: UpdateRating,
    user: UserObject,
    db_instance_type=RDS_WRITE,
) -> None:
    if not isinstance(update_rating, UpdateRating):
        raise TypeError('update_rating must be an instance of UpdateRating')
    rating = _get_rating(update_rating.id, user)
    if update_rating.price:
        rating.price = update_rating.price
    if update_rating.vibe:
        rating.vibe = update_rating.vibe
    if update_rating.food:
        rating.food = update_rating.food
    if update_rating.message:
        rating.message = update_rating.message

    commit()
    logger.info(
        f'Successfully updated rating in rds: {update_rating.__dict__}'
    )
    return


@DB_SESSION_RETRYABLE
def delete_rating(
    rating_id: int,
    user: UserObject,
    db_instance_type=RDS_WRITE,
) -> None:
    if not isinstance(rating_id, int) and (
        isinstance(rating_id, str) and not rating_id.isdigit()
    ):
        raise TypeError('rating_id must be an int.')
    rating = _get_rating(int(rating_id), user)
    rating.delete()
    commit()
    logger.info(f'Successfully deleted rating {rating_id}.')
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


def _get_ratings(
    users: Optional[List[int]],
    place_id: Optional[str],
    db_instance_type=RDS_WRITE,
) -> Query:
    ratings = select(rating for rating in DB_TYPE[db_instance_type].Rating)
    if users:
        ratings = ratings.filter(lambda rating: rating.user.id in users)
    if place_id:
        ratings = ratings.filter(
            lambda rating: rating.location.google_id == place_id
        )
    return ratings.order_by(lambda rating: desc(rating.last_updated))


def _get_serialized_ratings(ratings_query: Query) -> Dict:
    reviews = list()
    for r in ratings_query:
        reviews.append(
            {
                'id': r.id,
                'first_name': r.user.first_name,
                'last_name': r.user.last_name,
                'place_id': r.location.google_id,
                'latitude': r.location.latitude,
                'longitude': r.location.longitude,
                'food': r.food,
                'price': r.price,
                'vibe': r.vibe,
                'message': r.message,
                'time_created': r.created.strftime(LOOP_TIME_FORMAT),
            }
        )
    return reviews


@DB_SESSION_RETRYABLE
def get_ratings(
    users: Optional[List[int]] = None, place_id: Optional[str] = None
) -> Dict:
    reviews = list()
    ratings = _get_ratings(users, place_id)
    return _get_serialized_ratings(ratings)


@DB_SESSION_RETRYABLE
def get_ratings_paginated(
    paginated_ratings: PaginatedRatings,
) -> RatingsPageResults:
    if not isinstance(paginated_ratings, PaginatedRatings):
        raise TypeError(
            'paginated_ratings must be an instance of PaginatedRatings.'
        )
    ratings = _get_ratings(paginated_ratings.users, paginated_ratings.place_id)
    # Paginate
    count = ratings.count()
    pages = math.ceil(count / RATINGS_PAGE_COUNT)
    if paginated_ratings.page_count > pages:
        raise exceptions.BadRequestError(
            f'Page does not exist for query. (total pages = {pages}).'
        )
    # Get page data
    page_results = ratings.page(
        paginated_ratings.page_count, RATINGS_PAGE_COUNT
    )
    return RatingsPageResults(
        page_data=_get_serialized_ratings(page_results), total_pages=pages
    )


@DB_SESSION_RETRYABLE
def delete_user_ratings(user: UserObject, db_instance_type=RDS_WRITE) -> None:
    if not isinstance(user, UserObject):
        raise TypeError('user must be an instance of UserObject.')
    ratings = select(
        rating
        for rating in DB_TYPE[db_instance_type].Rating
        if rating.user.id == user.id
    )
    ratings.delete(bulk=True)
    commit()
    return


@DB_SESSION_RETRYABLE
def delete_user_friendships(
    user: UserObject, db_instance_type=RDS_WRITE
) -> None:
    if not isinstance(user, UserObject):
        raise TypeError('user must be an instance of UserObject.')
    frienships = select(
        f
        for f in DB_TYPE[db_instance_type].Friend
        if f.friend_1.id == user.id or f.friend_2.id == user.id
    )
    frienships.delete(bulk=True)
    commit()
    return


@DB_SESSION_RETRYABLE
def delete_user_entry(user: UserObject, db_instance_type=RDS_WRITE) -> None:
    if not isinstance(user, UserObject):
        raise TypeError('user must be an instance of UserObject.')
    user = DB_TYPE[db_instance_type].User.get(id=user.id)
    if not user:
        raise exceptions.BadRequestError('User not found')
    user.delete()
    commit()
    return
