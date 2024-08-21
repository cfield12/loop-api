from typing import Dict, Optional

import boto3
from botocore.exceptions import ClientError
from loop.exceptions import BucketNotFoundError


class S3Service:
    def __init__(self, bucket_name: str) -> None:
        '''
        This class provides functionality for s3 use.

        Docs:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/
        services/s3.html
        '''
        if not isinstance(bucket_name, str):
            raise TypeError('bucket_name must be of type str')
        self.s3 = boto3.client("s3")
        if bucket_name not in [
            b['Name'] for b in self.s3.list_buckets().get('Buckets', list())
        ]:
            raise BucketNotFoundError(f'Could not find bucket {bucket_name}')
        self.bucket_name = bucket_name

    def item_exists(self, key):
        objects = self.s3.list_objects(Bucket=self.bucket_name)
        contents = objects.get('Contents', list())
        if key in [item['Key'] for item in contents]:
            return True
        else:
            return False

    def upload_file(
        self, filename: str, key: str, extra_args: Optional[Dict] = None
    ) -> None:
        try:
            self.s3.upload_file(
                filename, self.bucket_name, key, ExtraArgs=extra_args
            )
        except boto3.exceptions.S3UploadFailedError as e:
            raise e
