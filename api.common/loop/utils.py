from loop.constants import LOOP_ADMIN_ID, LOOP_ADMIN_COGNITO_USERNAME


class UserObject(object):
    cognito_user_name = None
    groups = {}
    id = 0

    def __init__(
        self,
        cognito_user_name=None,
        groups={},
        id=id,
    ):
        self.cognito_user_name = cognito_user_name
        self.groups = groups
        self.id = id


def get_admin_user():
    return UserObject(
        id=LOOP_ADMIN_ID,
        cognito_user_name=LOOP_ADMIN_COGNITO_USERNAME
    )
