import unittest
from unittest.mock import Mock, call, patch

import boto3
from botocore.exceptions import ClientError
from loop.secrets import get_db_dict, get_secret


class TestSecrets(unittest.TestCase):
    @patch('loop.secrets.get_secret')
    def test_get_db_secret(self, mock_get_secret):
        mock_get_secret.return_value = {
            'host': 'test_host',
            'user': 'test_user',
            'password': 'test_password',
            'port': 3306,
        }
        secret_name = 'test_rds_secret'
        db_dict = get_db_dict(secret_name)
        self.assertEqual(
            db_dict,
            {
                'host': 'test_host',
                'user': 'test_user',
                'password': 'test_password',
                'port': 3306,
                'database': 'loop',
                'provider': 'mysql',
            },
        )

    @patch.object(boto3, 'session')
    def test_get_secret(self, mock_boto):
        secret_name = 'test_secret'
        secret_value = get_secret(secret_name)
        # Check mocks
        self.assertEqual(
            mock_boto.mock_calls,
            [
                call.Session(),
                call.Session().client(
                    service_name='secretsmanager', region_name='eu-west-2'
                ),
                call.Session()
                .client()
                .get_secret_value(SecretId='test_secret'),
                call.Session()
                .client()
                .get_secret_value()
                .__contains__('SecretString'),
            ],
        )

    @patch.object(boto3, 'session')
    def test_get_secret_add_environment(self, mock_boto):
        secret_name = 'test_secret'
        secret_value = get_secret(secret_name, add_environment=True)
        # Check mocks
        self.assertEqual(
            mock_boto.mock_calls[2],
            call.Session()
            .client()
            .get_secret_value(SecretId='test_secret-test'),
        )

    @patch.object(boto3, 'session')
    def test_get_secret_decryption_failure_exception(self, mock_boto):
        secret_name = 'test_secret'
        error_response = {
            'Error': {'Code': 'DecryptionFailureException', 'Message': 'error'}
        }
        operation_name = 'test'
        mock_boto.Session.return_value.client.return_value.get_secret_value.side_effect = ClientError(
            error_response, operation_name
        )
        self.assertRaises(ClientError, get_secret, secret_name)

    @patch.object(boto3, 'session')
    def test_get_secret_internal_service_error_exception(self, mock_boto):
        secret_name = 'test_secret'
        error_response = {
            'Error': {
                'Code': 'InternalServiceErrorException',
                'Message': 'error',
            }
        }
        operation_name = 'test'
        mock_boto.Session.return_value.client.return_value.get_secret_value.side_effect = ClientError(
            error_response, operation_name
        )
        self.assertRaises(ClientError, get_secret, secret_name)

    @patch.object(boto3, 'session')
    def test_get_secret_invalid_parameter_exception(self, mock_boto):
        secret_name = 'test_secret'
        error_response = {
            'Error': {'Code': 'InvalidParameterException', 'Message': 'error'}
        }
        operation_name = 'test'
        mock_boto.Session.return_value.client.return_value.get_secret_value.side_effect = ClientError(
            error_response, operation_name
        )
        self.assertRaises(ClientError, get_secret, secret_name)

    @patch.object(boto3, 'session')
    def test_get_secret_invalid_request_exception(self, mock_boto):
        secret_name = 'test_secret'
        error_response = {
            'Error': {'Code': 'InvalidRequestException', 'Message': 'error'}
        }
        operation_name = 'test'
        mock_boto.Session.return_value.client.return_value.get_secret_value.side_effect = ClientError(
            error_response, operation_name
        )
        self.assertRaises(ClientError, get_secret, secret_name)

    @patch.object(boto3, 'session')
    def test_get_secret_resource_not_found_exception(self, mock_boto):
        secret_name = 'test_secret'
        error_response = {
            'Error': {'Code': 'ResourceNotFoundException', 'Message': 'error'}
        }
        operation_name = 'test'
        mock_boto.Session.return_value.client.return_value.get_secret_value.side_effect = ClientError(
            error_response, operation_name
        )
        self.assertRaises(ClientError, get_secret, secret_name)


if __name__ == '__main__':
    unittest.main()
