import logging

import requests
from chalice import Chalice
from loop.api_classes import Coordinates
from loop.exceptions import LoopException
from loop.google_client import find_location, search_place
from loop.utils import Location
from pydantic import ValidationError as PydanticValidationError

app = Chalice(app_name='loop-google-api')
app.log.setLevel(logging.INFO)


@app.route('/web/restaurant_search/{search_term}', methods=['GET'], cors=True)
@app.route('/restaurant_search/{search_term}', methods=['GET'], cors=True)
def search_restaurant(search_term=str()):
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


@app.route('/web/restaurant/{place_id}', methods=['GET'], cors=True)
@app.route('/restaurant/{place_id}', methods=['GET'], cors=True)
def get_restaurant(place_id=str()):
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
        return location.to_dict()
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)
