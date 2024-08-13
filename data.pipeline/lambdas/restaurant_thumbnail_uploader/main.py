import json
import logging
import os

from loop.utils import sqs_batch
from src import GoogleThumbnailEvent, ThumbnailUploader

logger = logging.getLogger()
LOGLEVEL = os.environ.get("LOGLEVEL", "INFO")
logger.setLevel(LOGLEVEL)


def lambda_handler(event, context):
    logger.info(f'Restaurant thumnail upload event detected: {event}')
    try:
        thumbnail_uploader = ThumbnailUploader()
        for message in sqs_batch(event):
            try:
                upload_event = GoogleThumbnailEvent(**message)
                thumbnail_uploader.upload_thumbnail(upload_event)
            except Exception as e:
                logger.error(
                    'Restaurant thumnail upload event failed for event'
                    f': {event} ({e})'
                )
                raise e
    except Exception as e:
        raise e


if __name__ == '__main__':
    photo_ref = (
        'AelY_Cs3YQYtP9Tf8wFt9EDkvzTv4txEHF-drHY4UaY3HFPr4KgkAuEba4MaXeGBvly'
        'TzE9ewRiunWAzWznaQgffkZ-NewQHuWuqXLor0I2VUfP392gXKJTpc-0uxUlG9t-jnf'
        'CeguU-W-BfmR3tVzeN__7rzOX2G5EECwM0aq-n7kr_8hw4'
    )
    event = {
        'Records': [
            {
                'body': json.dumps(
                    {
                        'place_id': 'ChIJEcLP7kUDdkgRw2pqyXOSXzw',
                        'photo_reference': photo_ref,
                    }
                )
            }
        ]
    }
    lambda_handler(event, None)
