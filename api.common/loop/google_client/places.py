import googlemaps
from loop.exceptions import GoogleApiError
from loop.utils import Location

API_KEY = 'AIzaSyDMxObuOxSIWbVHT9OttXiJrfcGQpO3o3U'


class GooglePlaces:
    def __init__(self) -> None:
        """
        Find developer docs at:

        https://github.com/googlemaps/google-maps-services-python/blob/
        master/googlemaps/places.py
        """
        self.gmaps = googlemaps.Client(key=API_KEY)

    def get_place(self, google_id: str) -> Location:
        """
        Comprehensive details for an individual place.
        google_id: A textual identifier that uniquely identifies a place,
        returned from a Places search.
        """
        if not isinstance(google_id, str):
            raise TypeError('google_id must be of type str')
        place = self.gmaps.place(google_id)
        if place['status'] != 'OK':
            raise GoogleApiError(f'Unable to get place with id: {google_id}')
        result = place['result']
        return Location(
            google_id=google_id,
            address=result['formatted_address'],
            display_name=result['name'],
        )


def find_location(google_id: str) -> Location:
    '''Finds location using google API'''
    google_places = GooglePlaces()
    return google_places.get_place(google_id)
