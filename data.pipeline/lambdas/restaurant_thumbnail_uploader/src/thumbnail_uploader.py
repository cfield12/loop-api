import os
from dataclasses import dataclass

from loop.google_client import PhotoDownloader
from loop.s3_service import S3Service

PROJECT = os.environ.get('PROJECT', 'loop')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'develop')
S3_BUCKET = f'{PROJECT}-s3-restaurant-thumbnail-store-{ENVIRONMENT}'
JPEG_SUFFIX = '.jpeg'


@dataclass
class GoogleThumbnailEvent:
    place_id: str
    photo_reference: str


class ThumbnailUploader:
    def __init__(self):
        self.photo_downloader = PhotoDownloader()
        self.s3_uploader = S3Service(S3_BUCKET)

    def upload_thumbnail(self, event: GoogleThumbnailEvent):
        if not isinstance(event, GoogleThumbnailEvent):
            raise TypeError(
                'event must be an instance of GoogleThumbnailEvent.'
            )
        filename = event.place_id + JPEG_SUFFIX
        tmp_filename = self.photo_downloader.download_photo(
            event.photo_reference, filename
        )
        self.s3_uploader.upload_file(tmp_filename, filename)
