import logging
import os

from loop.data import init_write_db
from src import UserCreator

logger = logging.getLogger()
LOGLEVEL = os.environ.get("LOGLEVEL", "INFO")
logger.setLevel(LOGLEVEL)

# Initialise database outside lambda handler
init_write_db()


def lambda_handler(event, context):
    logger.info(f'User creator event detected: {event}')
    user_creator = UserCreator()
    try:
        user_creator.create_user(event)
        return event
    except Exception as e:
        logger.error(f'User creator event failed for event: {event} ({e})')
        raise e


if __name__ == '__main__':
    event = {
        'userName': '26f29234-c0e1-704f-3b56-2eade7808df9',
        'request': {
            'userAttributes': {
                'given_name': 'Charlie',
                'family_name': 'Field',
                'email': 'charlie.field98@gmail.com',
            }
        },
    }
    lambda_handler(event, None)
