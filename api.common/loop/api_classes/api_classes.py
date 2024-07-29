from typing import List, Union

from loop.api_classes.validators import validate_str_uuid
from pydantic import BaseModel, model_validator, validator


class CreateRating(BaseModel):
    google_id: str
    price: int
    vibe: int
    food: int


class FriendValidator(BaseModel):
    cognito_user_name_requestor: str
    cognito_user_name_target: str

    @model_validator(mode="after")
    @classmethod
    def validate_cognito_user_names(cls, values):
        validate_str_uuid(values.cognito_user_name_requestor)
        validate_str_uuid(values.cognito_user_name_target)
        if (
            values.cognito_user_name_requestor
            == values.cognito_user_name_target
        ):
            raise ValueError('User names cannot be the same.')
        return
