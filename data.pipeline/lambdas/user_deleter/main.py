import json

from loop.admin_utils import delete_user_from_rds
from loop.api_classes import UserCredentials
from loop.constants import logger
from loop.data import init_write_db
from loop.utils import sqs_batch

init_write_db()


def lambda_handler(event, context):
    logger.info(f'Delete user event detected: {event}')
    try:
        for message in sqs_batch(event):
            try:
                user_credentials = UserCredentials(**message)
                delete_user_from_rds(user_credentials)
            except Exception as e:
                logger.error(
                    'Delete user failed for message' f': {message} ({e})'
                )
    except Exception as e:
        raise e


if __name__ == '__main__':
    event = {
        'Records': [{'body': json.dumps({'email': 'cefield12@gmail.com'})}]
    }
    lambda_handler(event, None)
