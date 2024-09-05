import logging
import os

"""
This file houses all constants used throughout the loop packages's modules.
"""

PROJECT = os.environ.get('PROJECT', 'loop')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'develop')
LOGLEVEL = os.environ.get("LOGLEVEL", "INFO")

logger = logging.getLogger()
logger.setLevel(LOGLEVEL)

LOOP_ADMIN_ID = 1
LOOP_ADMIN_COGNITO_USERNAME = '86125274-40a1-70ec-da28-f779360f7c07'

RDS_WRITE = 'write'

MAX_DB_INIT_RETRIES = 3
RETRY_DB_DELAY_SECONDS = 5

RESTAURANT_THUMBNAILS_BUCKET = (
    f'{PROJECT}-s3-restaurant-thumbnail-store-{ENVIRONMENT}'
)
RESTAURANT_THUMBNAILS_QUEUE = (
    f'{PROJECT}-sqs-restaurant-thumbnail-{ENVIRONMENT}'
)
JPEG_SUFFIX = '.jpeg'
SQS_BATCH_SIZE = 10

MIN_FUZZ_SCORE = 50

AUTH_FLOW = 'ADMIN_USER_PASSWORD_AUTH'
MINIMUM_PASSWORD_LENGTH = 8
VERIFICATION_CODE_LENGTH = 6

COGNITO_SECRET_NAME = f'{PROJECT}-cognito-secret-{ENVIRONMENT}'

LOOP_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

MAX_RATING = 5
MIN_RATING = 1

MAX_MESSAGE_LENGTH = 200

LOOP_ADMIN_GROUP = 'loop_admin'

ADMIN = 'admin'

DELETE_USER_QUEUE = f'{PROJECT}-sqs-delete-user-{ENVIRONMENT}'

RATINGS_PAGE_COUNT = 20

MIN_PAGE_COUNT = 1

SEARCH_USER_PAGE_COUNT = 20

UPDATE_RATING_FIELDS = ['price', 'vibe', 'food', 'message']
