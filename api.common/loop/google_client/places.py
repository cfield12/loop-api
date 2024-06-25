from typing import Dict, List

import googlemaps
from googlemaps.exceptions import ApiError
from loop.constants import GOOGLE_API_KEY
from loop.exceptions import GoogleApiError
from loop.utils import Location


class GooglePlaces:
    PLACES_FIELDS = ['formatted_address', 'name']

    def __init__(self) -> None:
        """
        Find developer docs at:

        https://github.com/googlemaps/google-maps-services-python/blob/
        master/googlemaps/places.py
        """
        self.gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

    def _validate_place(self, place: Dict) -> None:
        if 'status' not in place:
            raise GoogleApiError('Could not find status in response')
        if place['status'] != 'OK':
            raise GoogleApiError(
                f'Response status is not OK: {place["status"]}'
            )
        if 'result' not in place:
            raise GoogleApiError('Could not find result in response')
        if any([field not in place['result'] for field in self.PLACES_FIELDS]):
            missing_fields = [
                field
                for field in self.PLACES_FIELDS
                if field not in place['result']
            ]
            raise GoogleApiError(
                f'Response is missing data: {",".join(missing_fields)}'
            )

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
        return Location(
            google_id=google_id,
            address=result['formatted_address'],
            display_name=result['name'],
        )

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

    def search(self, search_text: str) -> List[Location]:
        """
        A Find Place request takes a text input, and returns a place.
        The text input can be any kind of Places data, for example,
        a name or address.
        """
        if not isinstance(search_text, str):
            raise TypeError('search_text must be of type str')
        try:
            response = self.gmaps.find_place(search_text, 'textquery')
        except ApiError as e:
            raise e
        self._validate_search(response)
        return [
            self.get_place(candidate['place_id'])
            for candidate in response['candidates']
        ]

    def download_photo(
        self, photo_reference: str, max_width: int = 250
    ) -> None:
        """
        Downloads a photo from the Places API.

        photo_reference: A string identifier that uniquely identifies a
        photo, as provided by either a Places search or Places detail request.

        max_width: Specifies the maximum desired width, in pixels.
        """
        if not isinstance(photo_reference, str):
            raise TypeError('photo_reference must be of type str')
        if not isinstance(max_width, int):
            raise TypeError('max_width must be of type int')
        try:
            f = open('test.jpeg', 'wb')
            for chunk in self.gmaps.places_photo(
                photo_reference, max_width=max_width
            ):
                if chunk:
                    f.write(chunk)
            f.close()
        except ApiError as e:
            raise e


def find_location(google_id: str) -> Location:
    '''Finds location using google API'''
    google_places = GooglePlaces()
    return google_places.get_place(google_id)
