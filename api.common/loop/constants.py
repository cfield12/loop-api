import logging
import os

PROJECT = os.environ.get('PROJECT', 'loop')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'develop')
LOGLEVEL = os.environ.get("LOGLEVEL", "INFO")

logger = logging.getLogger()
logger.setLevel(LOGLEVEL)

LOOP_ADMIN_ID = 1
LOOP_ADMIN_COGNITO_USERNAME = '86125274-40a1-70ec-da28-f779360f7c07'

RDS_WRITE = 'write'
DB_INSTANCE_TYPES = [RDS_WRITE]

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
