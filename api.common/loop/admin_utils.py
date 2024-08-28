from typing import Dict

from loop.api_classes import UserCredentials
from loop.auth import CognitoAuth
from loop.constants import DELETE_USER_QUEUE, logger
from loop.data import (
    DB_SESSION_RETRYABLE,
    DB_TYPE,
    RDS_WRITE,
    delete_user_entry,
    delete_user_friendships,
    delete_user_ratings,
    get_user_from_email,
)
from loop.data_classes import UserObject
from loop.exceptions import BadRequestError
from loop.queue_service import SqsClient
from pony.orm import commit


def _get_rating(rating_id: int, db_instance_type=RDS_WRITE):
    rating = DB_TYPE[db_instance_type].Rating.get(id=rating_id)
    if not rating:
        raise BadRequestError(f'Could not find rating with id {rating_id}.')
    else:
        return rating


@DB_SESSION_RETRYABLE
def delete_rating(rating_id: int) -> None:
    rating = _get_rating(rating_id)
    rating.delete()
    commit()
    return


def delete_user(user_credentials: UserCredentials) -> Dict:
    if not isinstance(user_credentials, UserCredentials):
        raise TypeError(
            'user_credentials must be an instance of UserCredentials.'
        )
    """
    We want to:
    a) Delete user from user table in RDS as well as all ratings and
        friendships associated.
    b) Delete user from Cognito.
    """
    # Send message to delete user from RDS Lambda.

    queue_service = SqsClient(DELETE_USER_QUEUE)
    queue_service.send_message(user_credentials.model_dump())
    logger.info(
        f'Sent message to delete user queue ({user_credentials.email})'
    )

    # Delete user from Cognito.
    auth_client = CognitoAuth()
    return auth_client.admin_delete_user(user_credentials)


def delete_user_from_rds(user_credentials: UserCredentials) -> Dict:
    if not isinstance(user_credentials, UserCredentials):
        raise TypeError(
            'user_credentials must be an instance of UserCredentials.'
        )
    user: UserObject = get_user_from_email(user_credentials.email)
    """
    We want to:
    a) Delete user's ratings.
    b) Delete user's groups.
    c) Delete user's frienships.
    d) Delete user.
    """
    delete_user_ratings(user)
    delete_user_friendships(user)
    delete_user_entry(user)
    logger.info(f'Successfully deleted user {user_credentials.email}')
    return
