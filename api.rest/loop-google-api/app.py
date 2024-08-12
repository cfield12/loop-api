from chalice import Chalice
from loop.api_classes import Coordinates
from loop.exceptions import LoopException
from loop.google_client import search_place
from pydantic import ValidationError as PydanticValidationError

app = Chalice(app_name='loop-google-api')


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
