from datetime import datetime

import mock
from loop import data
from loop.constants import DB_INSTANCE_TYPES
from pony.orm import db_session
from pony.orm.core import BindingError

INSTANCE = {'provider': 'sqlite', 'filename': ':memory:'}


@mock.patch('loop.secrets.get_db_dict')
def setup_rds(mock_get_db_dict: mock.MagicMock):
    """
    Create a SQLite database for use with tests.
    """
    # Create in-memory database.
    try:
        mock_get_db_dict.return_value = INSTANCE

        data.init_write_db(check_tables=True, create_tables=True)
    except BindingError as e:
        unbind_rds()
        setup_rds()
    except Exception as e:
        print(e)
        return

    with db_session:
        for db_instance_type in DB_INSTANCE_TYPES:
            user = data.DB_TYPE[db_instance_type].User(
                created=datetime(2000, 1, 1),
                last_updated=datetime(2000, 1, 1),
                cognito_user_name='test_cognito_user_name',
                email='test_email',
                first_name='Test',
                last_name='User',
            )
            admin_user = data.DB_TYPE[db_instance_type].User(
                created=datetime(2000, 1, 1),
                last_updated=datetime(2000, 1, 1),
                cognito_user_name='test_cognito_user_name_admin',
                email='admin_test_email',
                first_name='Admin',
                last_name='User',
            )
            location_1 = data.DB_TYPE[db_instance_type].Location(
                google_id='test_google_id_1',
                address='14 Lambert Street, London, N1 1JE',
                display_name='Home',
                created=datetime(2000, 1, 1),
                last_updated=datetime(2000, 1, 1),
            )
            location_2 = data.DB_TYPE[db_instance_type].Location(
                google_id='test_google_id_2',
                address='15 Noel Road, London, N1 8HQ',
                display_name="Baggins'",
                created=datetime(2000, 1, 1),
                last_updated=datetime(2000, 1, 1),
            )
            location_3 = data.DB_TYPE[db_instance_type].Location(
                google_id='test_google_id_3',
                address='38 Huntingdon Street, London, N1 1BP',
                display_name='JFs',
                created=datetime(2000, 1, 1),
                last_updated=datetime(2000, 1, 1),
            )
            location_4 = data.DB_TYPE[db_instance_type].Location(
                google_id='ChIJobyn_rQcdkgRE042NxgeR1k',
                address='43A Commercial Street, London',
                display_name='som saa',
            )
            rating_1 = data.DB_TYPE[db_instance_type].Rating(
                price=4,
                vibe=5,
                food=3,
                location=location_1,
                user=admin_user,
                created=datetime(2000, 1, 1),
                last_updated=datetime(2000, 1, 1),
            )
            rating_2 = data.DB_TYPE[db_instance_type].Rating(
                price=5,
                vibe=5,
                food=5,
                location=location_3,
                user=admin_user,
                created=datetime(2000, 1, 1),
                last_updated=datetime(2000, 1, 1),
            )
            rating_1 = data.DB_TYPE[db_instance_type].Rating(
                price=4,
                vibe=4,
                food=3,
                location=location_1,
                user=user,
                created=datetime(2000, 1, 1),
                last_updated=datetime(2000, 1, 1),
            )
            rating_1 = data.DB_TYPE[db_instance_type].Rating(
                price=4,
                vibe=5,
                food=5,
                location=location_2,
                user=user,
                created=datetime(2000, 1, 1),
                last_updated=datetime(2000, 1, 1),
            )


def unbind_rds():
    for db_instance_type in DB_INSTANCE_TYPES:
        data.DB_TYPE[db_instance_type].provider = None
        data.DB_TYPE[db_instance_type].schema = None
