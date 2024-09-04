import logging
import os
from functools import wraps
from typing import Union

import jwt
import requests
from chalice import Chalice, CognitoUserPoolAuthorizer, Response
from loop import admin_utils, data
from loop.api_classes import (
    Coordinates,
    CreateRating,
    FriendValidator,
    PaginatedRatings,
    SearchUsers,
    UpdateRating,
    UserCredentials,
)
from loop.auth import CognitoAuth
from loop.constants import COGNITO_SECRET_NAME, LOOP_ADMIN_GROUP
from loop.data_classes import (
    Location,
    PaginatedUserSearch,
    Rating,
    RatingsPageResults,
    UploadThumbnailEvent,
    UserObject,
)
from loop.enums import FriendRequestType
from loop.exceptions import (
    BadRequestError,
    LoopException,
    NoCurrentUserError,
    UnauthorizedError,
)
from loop.friends import (
    FriendWorker,
    get_pending_requests,
    get_ratings_for_place_and_friends,
    get_user_friend_ids,
    get_user_friends,
    search_for_users,
)
from loop.google_client import find_location, search_place
from loop.secrets import get_secret
from loop.thumbnails import check_thumbnail_exists, upload_thumbnail
from loop.utils import get_admin_user
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
        app.log.setLevel(logging.INFO)


setup_app()


def get_required_cognito_authorizer() -> CognitoUserPoolAuthorizer:
    if not LOOP_AUTH_DISABLED:
        cognito_secret = get_secret(COGNITO_SECRET_NAME)
        if 'arn' not in cognito_secret:
            raise ValueError('cognito secret missing arn.')
        cognito_user_pool_arn = cognito_secret['arn']
        cognito_authorizer = CognitoUserPoolAuthorizer(
            'cognito_authorizer', provider_arns=[cognito_user_pool_arn]
        )
        app.log.info(
            f"Setting up cognito authorizer with arn: {cognito_user_pool_arn}."
        )
        return cognito_authorizer


COGNITO_AUTHORIZER = get_required_cognito_authorizer()


def _get_user_from_authorization() -> UserObject:
    auth_token = app.current_request.headers.get('Authorization')
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
    return data.get_user_from_cognito_username(cognito_user_name)


def get_current_user(func):
    @wraps(func)
    def _get_current_user(*args, **kwargs):
        try:
            kwargs["user"] = (
                get_admin_user()
                if LOOP_AUTH_DISABLED
                else _get_user_from_authorization()
            )
        except LoopException as e:
            raise LoopException.as_chalice_exception(e)
        return func(*args, **kwargs)

    return _get_current_user


def access_admin(func):
    @wraps(func)
    def _access_admin(*args, **kwargs):
        try:
            if 'user' not in kwargs:
                raise NoCurrentUserError(
                    'Must get the current user before checking for admin '
                    'rights.'
                )
            if LOOP_ADMIN_GROUP not in kwargs['user'].groups:
                raise UnauthorizedError('Requires admin access.')
        except LoopException as e:
            raise LoopException.as_chalice_exception(e)
        func_payload = func(*args, **kwargs)
        return func_payload

    return _access_admin


# -----------------------------------------------------------------------------
# USER ENDPOINTS
# -----------------------------------------------------------------------------


@app.route(
    '/ratings', methods=['GET'], cors=True, authorizer=COGNITO_AUTHORIZER
)
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


@app.route(
    '/friends_ratings',
    methods=['GET'],
    cors=True,
    authorizer=COGNITO_AUTHORIZER,
)
@get_current_user
def get_all_ratings(user: UserObject = None):
    """
    Get all ratings.
    ---
    get:
        operationId: getAllRatings
        summary: Get the user and their friend's ratings.
        description: Get the user and their friend's ratings.
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
        users = get_user_friend_ids(user)
        ratings = data.get_ratings(users)
        app.log.info(f"Successfully returned all ratings for user {user.id}.")
        return ratings
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route(
    '/ratings', methods=['POST'], cors=True, authorizer=COGNITO_AUTHORIZER
)
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
            200:
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
            message=validated_params.message,
        )
        data.create_rating(rating)
        app.log.info(f"Successfully created rating entry {rating.__dict__}")
        return Response(status_code=200, body='')
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route(
    '/ratings/{rating_id}',
    methods=['PUT'],
    cors=True,
    authorizer=COGNITO_AUTHORIZER,
)
@get_current_user
def update_rating(rating_id: int, user: UserObject = None):
    """
    Update user ratings.
    ---
    put:
        operationId: updateRating
        summary: Update a rating entry in the db.
        description: Update a rating entry in the db.
        security:
            - Qi API Key: []
        consumes:
            -   application/json
        parameters:
            -   in: path
                name: rating_id
                type: string
                required: true
                description: Rating id of rating to update.
            -   in: body
                name: update_rating_schema
                schema:
                    type: object
                required: true
                description: JSON object containing rating metadata.
        responses:
            200:
                description: OK
            default:
                description: Unexpected error
                schema:
                    type: object
    """
    try:
        payload = app.current_request.json_body
        try:
            validated_params = UpdateRating(id=rating_id, **payload)
        except PydanticValidationError as e:
            raise BadRequestError(
                "; ".join([error["msg"] for error in e.errors()])
            )
        data.update_rating(validated_params, user)
        app.log.info(
            f"Successfully updated rating entry {validated_params.__dict__}"
        )
        return Response(status_code=200, body='')
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route(
    '/ratings/{rating_id}',
    methods=['DELETE'],
    cors=True,
    authorizer=COGNITO_AUTHORIZER,
)
@get_current_user
def delete_rating(rating_id: int, user: UserObject = None):
    """
    Delete a user rating.
    ---
    put:
        operationId: deleteRating
        summary: Delete a rating entry in the db.
        description: Delete a rating entry in the db.
        security:
            - Qi API Key: []
        consumes:
            -   application/json
        parameters:
            -   in: path
                name: rating_id
                type: string
                required: true
                description: Rating id of rating to delete.
        responses:
            200:
                description: OK
            default:
                description: Unexpected error
                schema:
                    type: object
    """
    try:
        data.delete_rating(rating_id, user)
        app.log.info(
            f"Successfully deleted rating entry {rating_id} "
            f"for user {user.id}."
        )
        return Response(status_code=200, body='')
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route(
    '/friends/{user_name}',
    methods=['POST'],
    cors=True,
    authorizer=COGNITO_AUTHORIZER,
)
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
            200:
                description: OK
            default:
                description: Unexpected error
                schema:
                    type: object
    """
    try:
        try:
            validated_params = FriendValidator(
                cognito_user_name_requestor=user.cognito_user_name,
                cognito_user_name_target=user_name,
            )
        except PydanticValidationError as e:
            raise BadRequestError(
                "; ".join([error["msg"] for error in e.errors()])
            )
        target_user: UserObject = data.get_user_from_cognito_username(
            validated_params.cognito_user_name_target
        )
        friend_worker = FriendWorker(user)
        friend_worker.create_friend_entry(target_user)
        return Response(status_code=200, body='')
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route(
    '/friends/{user_name}',
    methods=['PUT'],
    cors=True,
    authorizer=COGNITO_AUTHORIZER,
)
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
            200:
                description: OK
            default:
                description: Unexpected error
                schema:
                    type: object
    """
    try:
        try:
            validated_params = FriendValidator(
                cognito_user_name_requestor=user.cognito_user_name,
                cognito_user_name_target=user_name,
            )
        except PydanticValidationError as e:
            raise BadRequestError(
                "; ".join([error["msg"] for error in e.errors()])
            )
        target_user: UserObject = data.get_user_from_cognito_username(
            validated_params.cognito_user_name_target
        )
        friend_worker = FriendWorker(user)
        friend_worker.accept_friend_request(target_user)
        return Response(status_code=200, body='')
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route(
    '/friends/{user_name}',
    methods=['DELETE'],
    cors=True,
    authorizer=COGNITO_AUTHORIZER,
)
@get_current_user
def delete_friend(user_name=str(), user: UserObject = None):
    """
    Delete friend.
    ---
    put:
        operationId: deleteFriend
        summary: Delete a friend.
        description: Delete record in friend table.
        security:
            - Qi API Key: []
        consumes:
            -   application/json
        parameters:
            -   in: path
                name: user_name
                type: string
                required: true
                description: Cognito user name of user whose friendship is
                 being deleted.
        responses:
            200:
                description: OK
            default:
                description: Unexpected error
                schema:
                    type: object
    """
    try:
        try:
            validated_params = FriendValidator(
                cognito_user_name_requestor=user.cognito_user_name,
                cognito_user_name_target=user_name,
            )
        except PydanticValidationError as e:
            raise BadRequestError(
                "; ".join([error["msg"] for error in e.errors()])
            )
        target_user: UserObject = data.get_user_from_cognito_username(
            validated_params.cognito_user_name_target
        )
        friend_worker = FriendWorker(user)
        friend_worker.delete_friend(target_user)
        return Response(body=str())
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route(
    '/friends', methods=['GET'], cors=True, authorizer=COGNITO_AUTHORIZER
)
@get_current_user
def list_friends(user: UserObject = None):
    """
    List friends.
    ---
    get:
        operationId: listFriends
        summary: List your friend.
        description: List a user's friends.
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
        user_friends = get_user_friends(user)
        app.log.info(
            f"Successfully returned user's friends for user {user.id}"
        )
        return user_friends
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route(
    '/search_users', methods=['GET'], cors=True, authorizer=COGNITO_AUTHORIZER
)
@get_current_user
def search_users(user: UserObject = None):
    """
    List friends.
    ---
    get:
        operationId: searchUsers
        summary: Search users.
        description: Search all users.
        security:
            - API Key: []
        parameters:
            -   in: query
                name: term
                type: string
                required: true
                description: Search term to search users for.
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
        query_params = app.current_request.query_params or {}
        try:
            search_user_obj = SearchUsers(**query_params)
        except PydanticValidationError as e:
            raise BadRequestError(
                "; ".join([error["msg"] for error in e.errors()])
            )
        users: PaginatedUserSearch = search_for_users(user, search_user_obj)
        app.log.info(
            f"Successfully searched for users with search term "
            f"{search_user_obj.term} for user {user.id}"
        )
        return users.to_dict()
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route(
    '/restaurant_search/{search_term}',
    methods=['GET'],
    cors=True,
    authorizer=COGNITO_AUTHORIZER,
)
@get_current_user
def search_restaurant(search_term=str(), user: UserObject = None):
    """
    Search restaurant.
    ---
    get:
        operationId: searchRestaurant
        summary: Search for a restaurant.
        description: Search for a restaurant using Google API.
        security:
            - Qi API Key: []
        parameters:
            -   in: path
                name: search_term
                type: string
                required: true
                description: Restaurant search term.
            -   in: query
                name: lat
                type: string
                required: false
                description: Latitude of base location bias on.
            -   in: query
                name: lng
                type: string
                required: false
                description: Longitude of base location bias on.
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
        search_term = requests.utils.unquote(search_term)
        query_params = app.current_request.query_params or {}
        try:
            coordinates = Coordinates(
                lat=query_params.get('lat'),
                lng=query_params.get('lng'),
            )
        except PydanticValidationError as e:
            raise BadRequestError(
                "; ".join([error["msg"] for error in e.errors()])
            )
        app.log.info(
            f"Searching Google API with term: {search_term} and "
            f"coordinates: {coordinates.to_dict()}"
        )
        return search_place(search_term, coordinates)
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route(
    '/restaurant/{place_id}',
    methods=['GET'],
    cors=True,
    authorizer=COGNITO_AUTHORIZER,
)
@get_current_user
def get_restaurant(place_id=str(), user: UserObject = None):
    """
    Get restaurant.
    ---
    get:
        operationId: getRestaurant
        summary: Get a restaurant's info.
        description: Get a restaurant's information using Google API.
        security:
            - Qi API Key: []
        parameters:
            -   in: path
                name: place_id
                type: string
                required: true
                description: Google's place_id.
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
        place_id = requests.utils.unquote(place_id)
        app.log.info(
            "Getting restaurant information with Google API "
            f"for place_id: {place_id}."
        )
        location: Location = find_location(place_id)
        """
        Here we need to check to see if an image for this location is stored
        in s3
        """
        if location.photo_reference and not check_thumbnail_exists(place_id):
            upload_thumbnail(
                UploadThumbnailEvent(
                    place_id=place_id, photo_reference=location.photo_reference
                )
            )
        location = location.to_dict()
        """
        Add on user's friends/own reviews of this location.
        """
        reviews: List[Dict] = get_ratings_for_place_and_friends(place_id, user)
        if reviews:
            location['reviews'] = reviews
        return location
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route(
    '/pending_friends/outbound',
    methods=['GET'],
    cors=True,
    authorizer=COGNITO_AUTHORIZER,
)
@get_current_user
def get_outbound_pending_friends(user: UserObject = None):
    """
    List outbound pending friends.
    ---
    get:
        operationId: getOutboundPendingFriends
        summary: List outbound pendings friends.
        description: List a user's outbound pending friends.
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
        outbound_requests = get_pending_requests(
            user, FriendRequestType.OUTBOUND
        )
        app.log.info(
            "Successfully returned user's outbound friend requests"
            f" for user {user.id}"
        )
        return outbound_requests
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route(
    '/pending_friends/inbound',
    methods=['GET'],
    cors=True,
    authorizer=COGNITO_AUTHORIZER,
)
@get_current_user
def get_inbound_pending_friends(user: UserObject = None):
    """
    List inbound pending friends.
    ---
    get:
        operationId: getInboundPendingFriends
        summary: List inbound pendings friends.
        description: List a user's inbound pending friends.
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
        inbound_requests = get_pending_requests(
            user, FriendRequestType.INBOUND
        )
        app.log.info(
            "Successfully returned user's inbound friend requests"
            f" for user {user.id}"
        )
        return inbound_requests
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


# -----------------------------------------------------------------------------
# ADMIN ENDPOINTS
# -----------------------------------------------------------------------------


@app.route(
    '/admin/ratings', methods=['GET'], cors=True, authorizer=COGNITO_AUTHORIZER
)
@get_current_user
@access_admin
def get_admin_ratings(user: UserObject = None):
    """
    Get paginated ratings (admin).
    ---
    get:
        operationId: getAdminRatings
        summary: Get paginated ratings (admin).
        description: Get paginated ratings (admin).
        security:
            - API Key: []
        parameters:
            -   in: query
                name: page_count
                type: integer
                required: false
                description: Page count.
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
        query_params = app.current_request.query_params or {}
        try:
            validated_params = PaginatedRatings(**query_params)
        except PydanticValidationError as e:
            raise BadRequestError(
                "; ".join([error["msg"] for error in e.errors()])
            )
        results: RatingsPageResults = data.get_ratings_paginated(
            validated_params
        )
        app.log.info(
            f"Successfully returned page {validated_params.page_count} "
            "ratings (admin)."
        )
        return results.to_dict()
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route(
    '/admin/ratings/{rating_id}',
    methods=['DELETE'],
    cors=True,
    authorizer=COGNITO_AUTHORIZER,
)
@get_current_user
@access_admin
def admin_delete_rating(rating_id: int, user: UserObject = None):
    """
    Admin delete a user rating.
    ---
    put:
        operationId: adminDeleteRating
        summary: Delete a rating entry in the db.
        description: Delete a rating entry in the db.
        security:
            - Qi API Key: []
        consumes:
            -   application/json
        parameters:
            -   in: path
                name: rating_id
                type: string
                required: true
                description: Rating id of rating to delete.
        responses:
            200:
                description: OK
            default:
                description: Unexpected error
                schema:
                    type: object
    """
    try:
        admin_utils.delete_rating(rating_id)
        app.log.info(f"Successfully deleted rating entry {rating_id}.")
        return Response(status_code=200, body='')
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route(
    '/admin/user/{email}',
    methods=['DELETE'],
    cors=True,
    authorizer=COGNITO_AUTHORIZER,
)
@get_current_user
@access_admin
def admin_delete_user(email: str, user: UserObject = None):
    """
    Admin delete a user.
    ---
    put:
        operationId: adminDeleteUser
        summary: Delete a user from db/cognito.
        description: Delete a user from db/cognito.
        security:
            - Qi API Key: []
        consumes:
            -   application/json
        parameters:
            -   in: path
                name: email
                type: string
                required: true
                description: Email of user to delete.
        responses:
            200:
                description: OK
            default:
                description: Unexpected error
                schema:
                    type: object
    """
    try:
        try:
            user_credentials = UserCredentials(email=email)
        except PydanticValidationError as e:
            raise BadRequestError(
                "; ".join([error["msg"] for error in e.errors()])
            )
        return admin_utils.delete_user(user_credentials)
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)
