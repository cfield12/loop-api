import unittest
from unittest.mock import Mock, call, patch

from loop.data_classes import UploadThumbnailEvent
from loop.thumbnails import ThumbnailUploader

TEST_PLACE_ID = 'test_place_id'
TEST_PHOTO_REFERENCE = 'test_photo_reference'
TEST_EVENT = UploadThumbnailEvent(
    place_id=TEST_PLACE_ID, photo_reference=TEST_PHOTO_REFERENCE
)
FILE_NAME = f'{TEST_PLACE_ID}.jpeg'
TMP_FILENAME = f'/tmp/{FILE_NAME}'


class TestThumbnailUploader(unittest.TestCase):
    @patch('loop.thumbnails.PhotoDownloader')
    @patch('loop.thumbnails.S3Service')
    def setUp(self, mock_s3_service, mock_photo_downloader):
        mock_photo_downloader.return_value.download_photo.return_value = (
            TMP_FILENAME
        )
        self.mock_s3_service = mock_s3_service
        self.mock_photo_downloader = mock_photo_downloader
        self.uploader = ThumbnailUploader()

    def tearDown(self):
        self.mock_s3_service = None
        self.mock_photo_downloader = None
        self.uploader = None

    def test_upload_thumbnail(self):
        self.uploader.upload_thumbnail(TEST_EVENT)
        # Check mocks
        self.assertEqual(
            self.mock_photo_downloader.mock_calls[1],
            call().download_photo(TEST_PHOTO_REFERENCE, FILE_NAME),
        )
        self.assertEqual(
            self.mock_s3_service.mock_calls[1],
            call().upload_file(TMP_FILENAME, FILE_NAME),
        )

    def test_upload_thumbnail_type_error(self):
        error_event = {
            'place_id': TEST_PLACE_ID,
            'photo_reference': TEST_PHOTO_REFERENCE,
        }
        self.assertRaises(
            TypeError, self.uploader.upload_thumbnail, error_event
        )


if __name__ == '__main__':
    unittest.main()
