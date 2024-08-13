import unittest
from unittest.mock import Mock, call, patch

import googlemaps
from googlemaps.exceptions import ApiError
from loop.api_classes import Coordinates
from loop.exceptions import GoogleApiError
from loop.google_client import (
    PlaceSearcher,
    PlacesSearcher,
    get_coordinates_from_result,
)
from loop.utils import Location

TEST_COORDINATES = Coordinates(lat=1.0, lng=1.0)


class TestSearchPlace(unittest.TestCase):
    @patch('loop.google_client.places.get_secret')
    @patch.object(googlemaps, 'Client')
    def setUp(self, mock_googlemaps, mock_secret):
        mock_secret.return_value = {'key': 'mock_secret'}
        self.mock_googlemaps = mock_googlemaps
        self.place_searcher = PlaceSearcher()

    def tearDown(self):
        self.place_searcher = None

    def test_validate_place_success(self):
        response = {
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
        self.place_searcher._validate_place(response)

    def test_validate_place_no_status_error(self):
        response = {
            'result': {
                'formatted_address': 'Test Address, Test City',
                'name': 'Test Name',
            },
        }
        self.assertRaises(
            GoogleApiError, self.place_searcher._validate_place, response
        )

    def test_validate_place_status_error(self):
        response = {
            'status': 'NOT_OK',
            'result': {
                'formatted_address': 'Test Address, Test City',
                'name': 'Test Name',
            },
        }
        self.assertRaises(
            GoogleApiError, self.place_searcher._validate_place, response
        )

    def test_validate_place_no_result_error(self):
        response = {
            'status': 'OK',
            'outcome': {
                'formatted_address': 'Test Address, Test City',
                'name': 'Test Name',
            },
        }
        self.assertRaises(
            GoogleApiError, self.place_searcher._validate_place, response
        )

    def test_validate_place_invalid_result_key_error(self):
        response = {
            'status': 'OK',
            'result': {
                'address': 'Test Address, Test City',
                'name': 'Test Name',
            },
        }
        self.assertRaises(
            GoogleApiError, self.place_searcher._validate_place, response
        )

    def test_get_place(self):
        address = 'Test Address, Test City'
        name = 'Test Name'
        response = {
            'status': 'OK',
            'result': {
                'formatted_address': address,
                'name': name,
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
        self.mock_googlemaps.return_value.place.return_value = response
        google_id = 'Test_google_id'
        location = self.place_searcher.get_place(google_id)
        self.assertEqual(
            location,
            Location(
                google_id=google_id,
                address=address,
                display_name=name,
                coordinates=get_coordinates_from_result(response['result']),
            ),
        )

    def test_get_place_google_type_error(self):
        google_id = 123456789
        self.assertRaises(TypeError, self.place_searcher.get_place, google_id)

    def test_get_place_api_error(self):
        self.mock_googlemaps.return_value.place.side_effect = ApiError(500)
        google_id = 'Test_google_id'
        self.assertRaises(ApiError, self.place_searcher.get_place, google_id)


class TestSearchPlaces(unittest.TestCase):
    @patch('loop.google_client.places.get_secret')
    @patch.object(googlemaps, 'Client')
    def setUp(self, mock_googlemaps, mock_secret):
        mock_secret.return_value = {'key': 'mock_secret'}
        self.mock_googlemaps = mock_googlemaps
        self.places_searcher = PlacesSearcher()

    def tearDown(self):
        self.places_searcher = None

    def test_validate_search_response(self):
        response = {
            'status': 'OK',
            'candidates': [{'place_id': 'test_place_id'}],
        }
        self.places_searcher._validate_search(response)

    def test_validate_search_response_no_status_error(self):
        response = {
            'candidates': [{'place_id': 'test_place_id'}],
        }
        self.assertRaises(
            GoogleApiError, self.places_searcher._validate_search, response
        )

    def test_validate_search_response_status_error(self):
        response = {
            'status': 'NOT_OK',
            'candidates': [{'place_id': 'test_place_id'}],
        }
        self.assertRaises(
            GoogleApiError, self.places_searcher._validate_search, response
        )

    def test_validate_search_response_no_candidates_error(self):
        response = {
            'status': 'OK',
            'result': [{'place_id': 'test_place_id'}],
        }
        self.assertRaises(
            GoogleApiError, self.places_searcher._validate_search, response
        )

    def test_validate_search_response_candidates_type_error(self):
        response = {
            'status': 'OK',
            'candidates': {'place_id': 'test_place_id'},
        }
        self.assertRaises(
            GoogleApiError, self.places_searcher._validate_search, response
        )

    def test_search(self):
        candidates = [
            {
                'formatted_address': (
                    'Saint Katherine Docks, E Smithfield, '
                    'London E1W 1AT, United Kingdom'
                ),
                'geometry': {
                    'location': {
                        'lat': 51.5074562,
                        'lng': -0.07120989999999999,
                    },
                    'viewport': {
                        'northeast': {
                            'lat': 51.50917822989272,
                            'lng': -0.06975287010727778,
                        },
                        'southwest': {
                            'lat': 51.50647857010728,
                            'lng': -0.07245252989272222,
                        },
                    },
                },
                'name': 'Bravas Tapas',
            }
        ]
        search_response = {
            'candidates': candidates,
            'status': 'OK',
        }
        self.mock_googlemaps.return_value.find_place.return_value = (
            search_response
        )
        text_search = 'Test search'
        locations = self.places_searcher.search(text_search, TEST_COORDINATES)
        self.assertEqual(locations, candidates)

    def test_search_type_error(self):
        text_search = ['Test search']
        self.assertRaises(
            TypeError,
            self.places_searcher.search,
            text_search,
            TEST_COORDINATES,
        )

    def test_search_api_error(self):
        self.mock_googlemaps.return_value.find_place.side_effect = ApiError(
            500
        )
        text_search = 'Test search'
        self.assertRaises(
            ApiError,
            self.places_searcher.search,
            text_search,
            TEST_COORDINATES,
        )


if __name__ == '__main__':
    unittest.main()
