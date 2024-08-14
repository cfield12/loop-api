from loop.api_classes import Coordinates
from loop.google_client import PhotoDownloader, PlaceSearcher, PlacesSearcher
from loop.s3_service import S3Service

som_saa_google_id = 'ChIJEcLP7kUDdkgRw2pqyXOSXzw'

search_text = 'Bread Street Kitchen'
coordinates = Coordinates(lat=51.507351, lng=-0.127758)

ivy_photo_ref = 'AelY_Cs3YQYtP9Tf8wFt9EDkvzTv4txEHF-drHY4UaY3HFPr4KgkAuEba4MaXeGBvlyTzE9ewRiunWAzWznaQgffkZ-NewQHuWuqXLor0I2VUfP392gXKJTpc-0uxUlG9t-jnfCeguU-W-BfmR3tVzeN__7rzOX2G5EECwM0aq-n7kr_8hw4'
S3_BUCKET = 'test-thumbnails'

filename = 'test3.jpeg'


def get_place() -> None:
    google_places = PlaceSearcher()
    place = google_places.get_place(som_saa_google_id)
    return


def search_place() -> None:
    google_places = PlacesSearcher()
    search = google_places.search(search_text, coordinates)
    return


def download_photo() -> None:
    google_places = PhotoDownloader()
    s3_service = S3Service(S3_BUCKET)
    tmp_filename = google_places.download_photo(ivy_photo_ref, filename)
    s3_service.upload_file(tmp_filename, filename)
    return


if __name__ == '__main__':
    # get_place()
    search_place()
    # download_photo()
