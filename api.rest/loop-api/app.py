import os
from functools import wraps
from typing import Union

import jwt
from chalice import Chalice, Response
from loop import data, friends
from loop.api_classes import AddFriend, CreateRating
from loop.exceptions import BadRequestError, LoopException, UnauthorizedError
from loop.utils import Rating, UserObject, get_admin_user
from pydantic import ValidationError as PydanticValidationError

LOOP_AUTH_DISABLED = os.environ.get("LOOP_AUTH_DISABLED", "0").lower() == "1"

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


@app.route('/web/ratings', methods=['POST'], cors=True)
@app.route('/ratings', methods=['POST'], cors=True)
@get_current_user
def create_rating(user: UserObject = None):
    """
    Create user ratings.
    ---
    post:
        operationId: createRating
        summary: Create a rating entry in the db.
        description: Create a rating entry in the db.
        security:
            - Qi API Key: []
        consumes:
            -   application/json
        parameters:
            -   in: body
                name: create_rating_schema
                schema:
                    type: object
                required: true
                description: JSON object containing rating metadata.
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
            validated_params = CreateRating(**payload)
        except PydanticValidationError as e:
            raise BadRequestError(
                "; ".join([error["msg"] for error in e.errors()])
            )
        google_location_id = validated_params.google_id
        location_id = data.get_or_create_location_id(google_location_id)
        rating = Rating(
            location=location_id,
            user=user.id,
            price=validated_params.price,
            vibe=validated_params.vibe,
            food=validated_params.food,
        )
        data.create_rating(rating)
        app.log.info(f"Successfully created rating entry {rating.__dict__}")
        return Response(status_code=204, body='')
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route('/web/friends/{user_name}', methods=['POST'], cors=True)
@app.route('/friends/{user_name}', methods=['POST'], cors=True)
@get_current_user
def add_friend(user_name=str(), user: UserObject = None):
    """
    Add friend.
    ---
    post:
        operationId: addFriend
        summary: Add a friend.
        description: Add a record in the friend table with status pending.
        security:
            - Qi API Key: []
        consumes:
            -   application/json
        parameters:
            -   in: path
                name: user_name
                type: string
                required: true
                description: Cognito user name of friend the user is trying to
                 add.
        responses:
            204:
                description: OK
            default:
                description: Unexpected error
                schema:
                    type: object
    """
    try:
        try:
            validated_params = AddFriend(
                cognito_user_name_requestor=user.cognito_user_name,
                cognito_user_name_requestee=user_name,
            )
        except PydanticValidationError as e:
            raise BadRequestError(
                "; ".join([error["msg"] for error in e.errors()])
            )
        requestor_user: UserObject = data.get_user_from_cognito_username(
            validated_params.cognito_user_name_requestor
        )
        target_user: UserObject = data.get_user_from_cognito_username(
            validated_params.cognito_user_name_requestee
        )
        friends.create_friend_entry(requestor_user, target_user)
        return Response(status_code=204, body='')
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route('/web/friends/{user_name}', methods=['PUT'], cors=True)
@app.route('/friends/{user_name}', methods=['PUT'], cors=True)
@get_current_user
def accept_friend(user_name=str(), user: UserObject = None):
    """
    Add friend.
    ---
    put:
        operationId: acceptFriend
        summary: Accept a friend request.
        description: Update a record in the friend table with status friends.
        security:
            - Qi API Key: []
        consumes:
            -   application/json
        parameters:
            -   in: path
                name: user_name
                type: string
                required: true
                description: Cognito user name of user whose request is being
                 accepted.
        responses:
            204:
                description: OK
            default:
                description: Unexpected error
                schema:
                    type: object
    """
    try:
        try:
            validated_params = AddFriend(
                cognito_user_name_requestor=user_name,
                cognito_user_name_requestee=user.cognito_user_name,
            )
        except PydanticValidationError as e:
            raise BadRequestError(
                "; ".join([error["msg"] for error in e.errors()])
            )
        requestor_user: UserObject = data.get_user_from_cognito_username(
            validated_params.cognito_user_name_requestor
        )
        acceptor_user: UserObject = data.get_user_from_cognito_username(
            validated_params.cognito_user_name_requestee
        )
        friends.accept_friend_request(acceptor_user, requestor_user)
        return Response(status_code=204, body='')
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)
