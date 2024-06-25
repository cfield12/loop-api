from loop.google_client import GooglePlaces

som_saa_google_id = 'ChIJEcLP7kUDdkgRw2pqyXOSXzw'

search_text = 'Thdsafjisjfiasd'

ivy_photo_ref = (
    'AUc7tXVMp5olVjNUdLHPCA3X7AlBAU4O07f2Gr6CwzLgW9uL7xxFzx_SZHQtLtRrbmG0p8'
    'cibr8SviMr2t9-MJOX5ftojHBIEyaOmAi3AYM1W-eCwuKSINJdOpQBzIcCi_0Ve8X601jI'
    'se937yU0JFlP_L0Qq20_9KPKpeMgu3avgbgua9_O'
)


def get_place() -> None:
    google_places = GooglePlaces()
    place = google_places.get_place(som_saa_google_id)
    return


def search_place() -> None:
    google_places = GooglePlaces()
    search = google_places.search(search_text)
    return


def download_photo() -> None:
    google_places = GooglePlaces()
    x = google_places.download_photo(ivy_photo_ref)
    return


if __name__ == '__main__':
    # get_place()
    # search_place()
    download_photo()
