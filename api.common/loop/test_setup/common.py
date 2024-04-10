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
            read_group_admin = data.DB_TYPE[db_instance_type].User(
                name='qi_admin'
            )


def unbind_rds():
    for db_instance_type in DB_INSTANCE_TYPES:
        data.DB_TYPE[db_instance_type].provider = None
        data.DB_TYPE[db_instance_type].schema = None
