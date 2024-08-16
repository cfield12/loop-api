import unittest
from unittest.mock import Mock, call, patch

import boto3
from loop.exceptions import BucketNotFoundError
from loop.s3_service import S3Service

TEST_BUCKET_NAME = 'test_bucket'


class TestS3Service(unittest.TestCase):
    @patch.object(boto3, 'client')
    def setUp(self, mock_boto_client):
        mock_boto_client.return_value.list_buckets.return_value = {
            'Buckets': [{'Name': 'test_bucket'}, {'Name': 'test_other_bucket'}]
        }
        self.mock_boto_client = mock_boto_client
        self.s3_service = S3Service(TEST_BUCKET_NAME)

    def tearDown(self):
        self.mock_boto_client = None
        self.s3_service = None

    def test_item_exists_true(self):
        self.mock_boto_client.return_value.list_objects.return_value = {
            'Contents': [{'Key': 'test.pdf'}]
        }
        key = 'test.pdf'
        response: bool = self.s3_service.item_exists(key)
        self.assertTrue(response)

    def test_item_exists_false(self):
        self.mock_boto_client.return_value.list_objects.return_value = {
            'Contents': [{'Key': 'test.pdf'}]
        }
        key = 'other_test.pdf'
        response: bool = self.s3_service.item_exists(key)
        self.assertFalse(response)

    def test_upload_file(self):
        key = 'other_test.pdf'
        file_name = f'/tmp/{key}'
        self.s3_service.upload_file(file_name, key)
        self.assertEqual(
            self.mock_boto_client.mock_calls[2],
            call().upload_file(
                '/tmp/other_test.pdf', 'test_bucket', 'other_test.pdf'
            ),
        )

    def test_upload_file_error(self):
        key = 'other_test.pdf'
        file_name = f'/tmp/{key}'
        self.mock_boto_client.return_value.upload_file.side_effect = (
            boto3.exceptions.S3UploadFailedError
        )
        self.assertRaises(
            boto3.exceptions.S3UploadFailedError,
            self.s3_service.upload_file,
            file_name,
            key,
        )


class TestS3ServiceInit(unittest.TestCase):
    @patch.object(boto3, 'client')
    def test_unknown_bucket_error(self, mock_boto_client):
        mock_boto_client.return_value.list_buckets.return_value = {
            'Buckets': [{'Name': 'test_bucket'}, {'Name': 'test_other_bucket'}]
        }
        self.assertRaises(BucketNotFoundError, S3Service, 'Unknown bucket')

    def test_bucket_name_type_error(self):
        self.assertRaises(TypeError, S3Service, {'Error bucket name'})


if __name__ == '__main__':
    unittest.main()
