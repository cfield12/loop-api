from abc import ABC, abstractmethod

import boto3
from botocore.exceptions import ClientError
from loop.constants import SQS_BATCH_SIZE
from loop.utils import conditional_dump


class SqsClient:
    '''
    Class that deals with SQS.
    '''

    def __init__(self, queue_name: str) -> None:
        if not isinstance(queue_name, str):
            raise TypeError('queue_name must be of type str')
        try:
            self.queue = boto3.resource('sqs').get_queue_by_name(
                QueueName=queue_name
            )
        except ClientError as e:
            logger.error(
                "ClientError when initialising SqsClient with queue name "
                f"{queue_name}: {e}."
            )
            raise e
        except Exception as e:
            raise e

    def send_message(self, message: any) -> None:
        message = conditional_dump(message)
        try:
            self.queue.send_message(MessageBody=message)
        except ClientError as e:
            logger.error(f'botocore client error: {e}')
            raise e
        except Exception as e:
            raise e
