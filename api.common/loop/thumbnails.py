import os

from loop.constants import (
    ENVIRONMENT,
    JPEG_SUFFIX,
    PROJECT,
    RESTAURANT_THUMBNAILS_BUCKET,
    RESTAURANT_THUMBNAILS_QUEUE,
)
from loop.data_classes import UploadThumbnailEvent
from loop.google_client import PhotoDownloader
from loop.queue_service import SqsClient
from loop.s3_service import S3Service


class RestaurantThumbnails:
    def __init__(self):
        self.s3_service = S3Service(RESTAURANT_THUMBNAILS_BUCKET)

    def check_item_exists(self, place_id: str) -> bool:
        key = place_id + JPEG_SUFFIX
        return self.s3_service.item_exists(key)

    def get_object(self, place_id: str) -> None:
        pass


class ThumbnailUploader(RestaurantThumbnails):
    def __init__(self):
        super().__init__()
        self.photo_downloader = PhotoDownloader()

    def upload_thumbnail(self, event: UploadThumbnailEvent):
        if not isinstance(event, UploadThumbnailEvent):
            raise TypeError(
                'event must be an instance of UploadThumbnailEvent.'
            )
        filename = event.place_id + JPEG_SUFFIX
        tmp_filename = self.photo_downloader.download_photo(
            event.photo_reference, filename
        )
        extra_args = {'Metadata': {'Content-Type': 'image/jpeg'}}
        self.s3_service.upload_file(
            tmp_filename, filename, extra_args=extra_args
        )


def check_thumbnail_exists(place_id: str) -> bool:
    thumbnails = RestaurantThumbnails()
    return thumbnails.check_item_exists(place_id)


def upload_thumbnail(event: UploadThumbnailEvent) -> None:
    if not isinstance(event, UploadThumbnailEvent):
        raise TypeError('event should be an instance of UploadThumbnailEvent.')
    queue_service = SqsClient(RESTAURANT_THUMBNAILS_QUEUE)
    return queue_service.send_message(event.to_dict())
