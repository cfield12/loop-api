import os
from typing import Dict, List, Optional

import googlemaps
from googlemaps.exceptions import ApiError
from loop.api_classes import Coordinates
from loop.data_classes import Location
from loop.exceptions import GoogleApiError
from loop.google_client import (
    DEFAULT_RADIUS,
    GOOGLE_API_KEY_SECRET,
    SEARCH_FIELDS,
    TEMPDIR,
    TEXTQUERY,
)
from loop.secrets import get_secret


def get_coordinates_from_result(result: Dict) -> Coordinates:
    '''
    Where response should look something like:
    {
        'status': 'OK',
        'result': {
            'formatted_address': 'Test Address, Test City',
            'name': 'Test Name',
            'geometry': {
                'location': {'lat': 51.5041392, 'lng': -0.0770409},
                'viewport': {
                    'northeast': {'lat': 51.50544563, 'lng': -0.07565275},
                    'southwest': {'lat': 51.50274766, 'lng': -0.07868495},
                },
            },
            'place_id': 'ChIJEcLP7kUDdkgRw2pqyXOSXzw',
        },
    }
    '''
    if not isinstance(result, dict):
        raise TypeError('result should be a dict.')
    location = result.get('geometry', dict()).get('location')
    if not location:
        raise GoogleApiError('Location not found.')
    if 'lat' not in location or 'lng' not in location:
        raise GoogleApiError('Location missing either lat or lng.')
    return Coordinates(lat=location['lat'], lng=location['lng'])


class GooglePlaces:
    def __init__(self) -> None:
        """
        Find developer docs at:

        https://github.com/googlemaps/google-maps-services-python/blob/
        master/googlemaps/places.py
        """
        google_api_key = get_secret(GOOGLE_API_KEY_SECRET)
        if 'key' not in google_api_key:
            raise ValueError('google api secret must have key.')
        self.gmaps = googlemaps.Client(key=google_api_key['key'])


class PlaceSearcher(GooglePlaces):
    def _validate_place(self, place: Dict) -> None:
        if 'status' not in place:
            raise GoogleApiError('Could not find status in response')
        if place['status'] != 'OK':
            raise GoogleApiError(
                f'Response status is not OK: {place["status"]}'
            )
        if 'result' not in place:
            raise GoogleApiError('Could not find result in response')
        if any([field not in place['result'] for field in SEARCH_FIELDS]):
            missing_fields = [
                field
                for field in SEARCH_FIELDS
                if field not in place['result']
            ]
            raise GoogleApiError(
                f'Response is missing data: {",".join(missing_fields)}'
            )
        if 'location' not in place['result']['geometry']:
            raise GoogleApiError(f'Response is missing coordinates.')

    @staticmethod
    def _get_photo_reference(photos: Optional[List] = None) -> str:
        if not photos:
            return None
        if not isinstance(photos, list):
            raise TypeError('photos must be a list.')
        photo = photos[0]
        if 'photo_reference' not in photo:
            raise GoogleApiError(f'Response is missing a photo reference.')
        return photo['photo_reference']

    def get_place(self, google_id: str) -> Location:
        """
        Comprehensive details for an individual place.
        google_id: A textual identifier that uniquely identifies a place,
        returned from a Places search.
        """
        if not isinstance(google_id, str):
            raise TypeError('google_id must be of type str')
        try:
            place = self.gmaps.place(google_id)
        except ApiError as e:
            raise e
        self._validate_place(place)
        result = place['result']
        coordinates: Coordinates = get_coordinates_from_result(result)
        photo_reference = self._get_photo_reference(result.get('photos'))
        return Location(
            google_id=google_id,
            address=result['formatted_address'],
            display_name=result['name'],
            coordinates=coordinates,
            photo_reference=photo_reference,
            website=result.get('website'),
            phone_number=result.get('formatted_phone_number'),
            price_level=result.get('price_level'),
        )


class PlacesSearcher(GooglePlaces):
    def _validate_search(self, search: dict) -> None:
        if 'status' not in search:
            raise GoogleApiError('Could not find status in response')
        status = search['status']
        if status != 'OK' and status != 'ZERO_RESULTS':
            raise GoogleApiError(
                f'Response status is not OK or ZERO_RESULTS: {status}'
            )
        if 'candidates' not in search:
            raise GoogleApiError(f'Missing candidates')
        if not isinstance(search['candidates'], list):
            raise GoogleApiError(f'Candidates should be a list')

    @staticmethod
    def _get_location_bias(
        coordinates: Coordinates, radius: int = DEFAULT_RADIUS
    ) -> str:
        return f'circle:{radius}@{coordinates.to_coordinate_string()}'

    def search(
        self, search_text: str, coordinates: Coordinates
    ) -> List[Location]:
        """
        A Find Place request takes a text input, and returns a place.
        The text input can be any kind of Places data, for example,
        a name or address.

        https://developers.google.com/maps/documentation/places/web-service/
        search-find-place
        """
        if not isinstance(search_text, str):
            raise TypeError('search_text must be of type str')
        if not isinstance(coordinates, Coordinates):
            raise TypeError('coordinates must be an instance of Coordinates.')
        try:
            response = self.gmaps.find_place(
                search_text,
                TEXTQUERY,
                location_bias=self._get_location_bias(coordinates),
                fields=SEARCH_FIELDS,
            )
        except ApiError as e:
            raise e
        self._validate_search(response)
        return response['candidates']


class PhotoDownloader(GooglePlaces):
    def _validate(self, photo_reference: str, filename: str, max_width: int):
        if not isinstance(photo_reference, str):
            raise TypeError('photo_reference must be of type str')
        if not isinstance(max_width, int):
            raise TypeError('max_width must be of type int')
        if (
            not isinstance(filename, str)
            or '.' not in filename
            or filename.split('.')[1] != 'jpeg'
        ):
            raise ValueError('filename must end in .jpeg')

    def download_photo(
        self,
        photo_reference: str,
        filename: str,
        max_width: int = 250,
    ) -> None:
        """
        Downloads a photo from the Places API.

        photo_reference: A string identifier that uniquely identifies a
        photo, as provided by either a Places search or Places detail request.

        max_width: Specifies the maximum desired width, in pixels.
        """
        self._validate(photo_reference, filename, max_width)
        file_path = os.path.join(TEMPDIR, filename)
        try:
            f = open(file_path, 'wb')
            for chunk in self.gmaps.places_photo(
                photo_reference, max_width=max_width
            ):
                if chunk:
                    f.write(chunk)
            f.close()
            return file_path
        except ApiError as e:
            raise e


def search_place(
    search_term: str, coordinates: Coordinates
) -> List[Dict[str, str]]:
    places_searcher = PlacesSearcher()
    return places_searcher.search(search_term, coordinates)


def find_location(google_id: str) -> Location:
    '''Finds location using google API'''
    place_searcher = PlaceSearcher()
    return place_searcher.get_place(google_id)
