import unittest
from unittest.mock import Mock, call, patch

import boto3
from botocore.exceptions import ClientError
from loop.queue_service import SqsClient

TEST_QUEUE_NAME = 'test_queue_name'


class TestSqsService(unittest.TestCase):
    @patch.object(boto3, 'resource')
    def test_send_message(self, mock_boto3):
        queue = SqsClient(TEST_QUEUE_NAME)
        queue.send_message('hello')
        self.assertEqual(
            mock_boto3.mock_calls,
            [
                call('sqs'),
                call().get_queue_by_name(QueueName='test_queue_name'),
                call().get_queue_by_name().send_message(MessageBody='hello'),
            ],
        )

    @patch.object(boto3, 'resource')
    def test_send_message_client_error(self, mock_boto3):
        error_response = {
            'Error': {'Code': 'MessageSendJubb', 'Message': 'error'}
        }
        operation_name = 'test'
        mock_boto3.return_value.get_queue_by_name.return_value.send_message.side_effect = ClientError(  # noqa
            error_response, operation_name
        )
        queue = SqsClient(TEST_QUEUE_NAME)
        self.assertRaises(ClientError, queue.send_message, 'hello')

    def test_init_type_error(self):
        self.assertRaises(TypeError, SqsClient, {'hello'})

    @patch.object(boto3, 'resource')
    def test_init_client_error(self, mock_boto3):
        error_response = {
            'Error': {'Code': 'MessageQueueJubb', 'Message': 'error'}
        }
        operation_name = 'test'
        mock_boto3.return_value.get_queue_by_name.side_effect = ClientError(
            error_response, operation_name
        )
        self.assertRaises(ClientError, SqsClient, TEST_QUEUE_NAME)


if __name__ == '__main__':
    unittest.main()
