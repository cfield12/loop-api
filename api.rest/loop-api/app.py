import os
from functools import wraps
from typing import Union

import jwt
from chalice import Chalice, Response
from loop import data
from loop.api_classes.api_classes import CreateLocation
from loop.exceptions import BadRequestError, LoopException, UnauthorizedError
from loop.utils import UserObject, get_admin_user
from pydantic import ValidationError as PydanticValidationError

LOOP_AUTH_DISABLED = os.environ.get('LOOP_AUTH_DISABLED', False)

APP_NAME = 'loop-api'


def setup_app():
    global app
    app = None
    # Set up database connection (only if not in CI build).
    if "NO_DB" in os.environ:
        app = Chalice(app_name=APP_NAME)
        app.log.info(
            "CI environment; skipping database and Datadog link setup."
        )
    else:
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
                try:
                    cognito_user = jwt.decode(
                        auth_token, options={'verify_signature': False}
                    )
                except jwt.DecodeError as e:
                    raise UnauthorizedError(f'Jwt decode error: {e}')
                except Exception as e:
                    raise UnauthorizedError(f'Unexpected error: {e}')
                if not cognito_user:
                    raise UnauthorizedError("Could not find cognito user")
                cognito_user_name = cognito_user.get('sub')
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
        user_ratings = data.get_user_ratings(user)
        app.log.info(f"Successfully returned user ratings for user {user.id}")
        return user_ratings
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route('/web/location', methods=['POST'], cors=True)
@app.route('/location', methods=['POST'], cors=True)
@get_current_user
def create_location(user: UserObject = None):
    """
    Get user ratings.
    ---
    post:
        operationId: createLocation
        summary: Create a location entry in the db.
        description: Create a location entry in the db.
        security:
            - Qi API Key: []
        consumes:
            -   application/json
        parameters:
            -   in: body
                name: create_location_schema
                schema:
                    type: object
                required: true
                description: JSON object containing location metadata.
        responses:
            204:
                description: OK
            default:
                description: Unexpected error
                schema:
                    type: object
    """
    try:
        payload = app.current_request.json_body
        try:
            validated_params = CreateLocation(**payload)
        except PydanticValidationError as e:
            raise BadRequestError(
                "; ".join([error["msg"] for error in e.errors()])
            )
        data.create_location(validated_params)
        app.log.info(
            f"Successfully created location entry {validated_params.__dict__}"
        )
        return Response(status_code=204, body='')
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)
