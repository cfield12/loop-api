import unittest
from unittest.mock import Mock, call, patch

import googlemaps
from googlemaps.exceptions import ApiError
from loop.exceptions import GoogleApiError
from loop.google_client import GooglePlaces
from loop.utils import Location


class TestGooglePlaces(unittest.TestCase):
    @patch.object(googlemaps, 'Client')
    def setUp(self, mock_googlemaps):
        self.mock_googlemaps = mock_googlemaps
        self.google_places = GooglePlaces()

    def tearDown(self):
        self.google_places = None

    def test_validate_place_success(self):
        response = {
            'status': 'OK',
            'result': {
                'formatted_address': 'Test Address, Test City',
                'name': 'Test Name',
            },
        }
        self.google_places._validate_place(response)

    def test_validate_place_no_status_error(self):
        response = {
            'result': {
                'formatted_address': 'Test Address, Test City',
                'name': 'Test Name',
            },
        }
        self.assertRaises(
            GoogleApiError, self.google_places._validate_place, response
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
            GoogleApiError, self.google_places._validate_place, response
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
            GoogleApiError, self.google_places._validate_place, response
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
            GoogleApiError, self.google_places._validate_place, response
        )

    def test_get_place(self):
        address = 'Test Address, Test City'
        name = 'Test Name'
        response = {
            'status': 'OK',
            'result': {
                'formatted_address': address,
                'name': name,
            },
        }
        self.mock_googlemaps.return_value.place.return_value = response
        google_id = 'Test_google_id'
        location = self.google_places.get_place(google_id)
        self.assertEqual(
            location,
            Location(google_id=google_id, address=address, display_name=name),
        )

    def test_get_place_google_type_error(self):
        google_id = 123456789
        self.assertRaises(TypeError, self.google_places.get_place, google_id)

    def test_get_place_api_error(self):
        self.mock_googlemaps.return_value.place.side_effect = ApiError(500)
        google_id = 'Test_google_id'
        self.assertRaises(ApiError, self.google_places.get_place, google_id)

    def test_validate_search_response(self):
        response = {
            'status': 'OK',
            'candidates': [{'place_id': 'test_place_id'}],
        }
        self.google_places._validate_search(response)

    def test_validate_search_response_no_status_error(self):
        response = {
            'candidates': [{'place_id': 'test_place_id'}],
        }
        self.assertRaises(
            GoogleApiError, self.google_places._validate_search, response
        )

    def test_validate_search_response_status_error(self):
        response = {
            'status': 'NOT_OK',
            'candidates': [{'place_id': 'test_place_id'}],
        }
        self.assertRaises(
            GoogleApiError, self.google_places._validate_search, response
        )

    def test_validate_search_response_no_candidates_error(self):
        response = {
            'status': 'OK',
            'result': [{'place_id': 'test_place_id'}],
        }
        self.assertRaises(
            GoogleApiError, self.google_places._validate_search, response
        )

    def test_validate_search_response_candidates_type_error(self):
        response = {
            'status': 'OK',
            'candidates': {'place_id': 'test_place_id'},
        }
        self.assertRaises(
            GoogleApiError, self.google_places._validate_search, response
        )

    def test_search(self):
        place_response = {
            'status': 'OK',
            'result': {
                'formatted_address': 'Test Address, Test City',
                'name': 'Test Name',
            },
        }
        search_response = {
            'status': 'OK',
            'candidates': [{'place_id': 'test_place_id'}],
        }
        self.mock_googlemaps.return_value.find_place.return_value = (
            search_response
        )
        self.mock_googlemaps.return_value.place.return_value = place_response
        text_search = 'Test search'
        locations = self.google_places.search(text_search)
        self.assertEqual(
            locations,
            [
                Location(
                    google_id='test_place_id',
                    address='Test Address, Test City',
                    display_name='Test Name',
                )
            ],
        )

    def test_search_type_error(self):
        text_search = ['Test search']
        self.assertRaises(TypeError, self.google_places.search, text_search)

    def test_search_api_error(self):
        self.mock_googlemaps.return_value.find_place.side_effect = ApiError(
            500
        )
        text_search = 'Test search'
        self.assertRaises(ApiError, self.google_places.search, text_search)


if __name__ == '__main__':
    unittest.main()
