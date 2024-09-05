from loop.constants import logger
from loop.data import disconnect_db, init_write_db
from src import UserCreator

# Initialise database outside lambda handler
init_write_db()


def lambda_handler(event, context):
    logger.info(f'User creator event detected: {event}')
    user_creator = UserCreator()
    try:
        if event['triggerSource'] == 'PostConfirmation_ConfirmSignUp':
            user_creator.create_user(event)
        return event
    except Exception as e:
        logger.error(f'User creator event failed for event: {event} ({e})')
        raise e
    finally:
        disconnect_db()


if __name__ == '__main__':
    event = {
        'userName': '26f29234-c0e1-704f-3b56-2eade7808df9',
        'triggerSource': 'PostConfirmation_ConfirmSignUp',
        'request': {
            'userAttributes': {
                'given_name': 'Charlie',
                'family_name': 'Field',
                'email': 'charlie.field98@gmail.com',
            }
        },
    }
    lambda_handler(event, None)
