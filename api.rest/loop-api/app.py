from functools import wraps
import jwt
import os
from typing import Union

from chalice import Chalice, Response

from loop import data
from loop.exceptions import LoopException, UnauthorizedError
from loop.utils import get_admin_user, UserObject

LOOP_AUTH_DISABLED = os.environ.get('LOOP_AUTH_DISABLED', False)

APP_NAME = 'loop-api'


def setup_app():
    global app
    app = None
    data.init_write_db()
    app = Chalice(app_name=APP_NAME)


setup_app()


def get_current_user(func):
    @wraps(func)
    def _get_current_user(*args, **kwargs):
        if LOOP_AUTH_DISABLED:
            user = get_admin_user()
        else:
            try:
                auth_token = app.current_request.headers.get('auth-token')
                if not auth_token:
                    raise UnauthorizedError("Authorization header is expected")
                cognito_user = jwt.decode(
                    auth_token,
                    options={'verify_signature': False}
                )
                if not cognito_user:
                    raise UnauthorizedError("Could not find cognito user")
                cognito_user_name = cognito_user.get('username')
                if not cognito_user_name:
                    raise UnauthorizedError("Could not find cognito username")
                user = data.get_user_from_cognito_username(cognito_user_name)
            except LoopException as e:
                raise LoopException.as_chalice_exception(e)
        kwargs["user"] = user
        return func(*args, **kwargs)

    return _get_current_user


@app.route('/web/ratings', methods=['GET'], cors=True)
@app.route('/ratings', methods=['GET'], cors=True)
@get_current_user
def get_user_ratings(user: UserObject = None):
    """
    Get user ratings.
    ---
    get:
        operationId: getUserRatings
        summary: Get the users ratings.
        description: Get the users ratings.
        security:
            - API Key: []
        responses:
            200:
                description: OK
                schema:
                    type: object
            default:
                description: Unexpected error
                schema:
                    type: object
    """
    try:
        return data.get_user_ratings(user)
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)
