import os
import tempfile

from loop.constants import ENVIRONMENT, PROJECT

DEFAULT_RADIUS = 10000


GOOGLE_API_KEY_SECRET = f'{PROJECT}-google-api-key-{ENVIRONMENT}'
SEARCH_FIELDS = [
    'place_id',
    'formatted_address',
    'name',
    'geometry',
]
TEXTQUERY = 'textquery'
TEMPDIR = tempfile.gettempdir()
