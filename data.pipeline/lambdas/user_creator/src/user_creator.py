from typing import Dict

from loop import data
from loop.data_classes import UserCreateObject
from loop.exceptions import CreateUserValidationError


class UserCreator:
    EXPECTED_ATTRIBUTES = ['email', 'given_name', 'family_name']

    def _validate_event(self, event: Dict) -> None:
        if 'userName' not in event:
            raise CreateUserValidationError('userName must be in event.')
        if 'userAttributes' not in event.get('request', str()):
            raise CreateUserValidationError('event must have userAttributes.')
        attributes = event['request']['userAttributes']
        if any([a not in attributes for a in self.EXPECTED_ATTRIBUTES]):
            raise CreateUserValidationError(
                'event attributes must have all '
                f'{", ".join(self.EXPECTED_ATTRIBUTES)}.'
            )

    def create_user(self, event: Dict) -> None:
        self._validate_event(event)
        attributes = event['request']['userAttributes']
        user_create_obj = UserCreateObject(
            cognito_user_name=event['userName'],
            email=attributes['email'],
            first_name=attributes['given_name'],
            last_name=attributes['family_name'],
        )
        data.create_user(user_create_obj)
