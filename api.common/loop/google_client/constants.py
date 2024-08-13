import os
import tempfile

DEFAULT_RADIUS = 10000
PROJECT = os.environ.get('PROJECT', 'loop')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'develop')

GOOGLE_API_KEY_SECRET = f'{PROJECT}-google-api-key-{ENVIRONMENT}'
SEARCH_FIELDS = [
    'place_id',
    'formatted_address',
    'name',
    'geometry',
]
TEXTQUERY = 'textquery'
TEMPDIR = tempfile.gettempdir()
