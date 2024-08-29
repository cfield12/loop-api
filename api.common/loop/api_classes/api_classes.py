from copy import deepcopy
from typing import Dict, List, Optional, Union

from loop.api_classes.validators import (
    validate_code,
    validate_email_address,
    validate_int,
    validate_message_length,
    validate_str_uuid,
)
from loop.constants import MAX_RATING, MIN_PAGE_COUNT, MIN_RATING
from pydantic import BaseModel, model_validator, validator


class CreateRating(BaseModel):
    google_id: str
    price: int
    vibe: int
    food: int
    message: Optional[str] = None

    @validator("price", "vibe", "food")
    @classmethod
    def validate_rating(cls, rating: int):
        return validate_int(rating, max_count=MAX_RATING, min_count=MIN_RATING)

    @validator("message")
    @classmethod
    def validate_message_len(cls, message: str):
        return validate_message_length(message)


class UpdateRating(BaseModel):
    id: int
    price: Optional[int] = None
    vibe: Optional[int] = None
    food: Optional[int] = None
    message: Optional[str] = None

    @validator("price", "vibe", "food")
    @classmethod
    def validate_rating(cls, rating: int):
        return (
            validate_int(rating, max_count=MAX_RATING, min_count=MIN_RATING)
            if rating
            else None
        )

    @validator("message")
    @classmethod
    def validate_message_len(cls, message: str):
        return validate_message_length(message) if message else None


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


class Coordinates(BaseModel):
    lat: float
    lng: float

    def to_dict(self) -> Dict[str, str]:
        return deepcopy(self.__dict__)

    def to_coordinate_string(self) -> str:
        return f"{self.lat},{self.lng}"


class UserCredentials(BaseModel):
    email: str

    @validator("email")
    @classmethod
    def validate_email(cls, email: str):
        return validate_email_address(email)


class LoginCredentials(UserCredentials):
    password: str


class SignUpCredentials(LoginCredentials):
    first_name: str
    last_name: str


class VerifyUser(UserCredentials):
    code: str

    @validator("code")
    @classmethod
    def validate_verification_code(cls, code: str):
        return validate_code(code)


class ForgotPassword(VerifyUser):
    password: str


class PaginatedRatings(BaseModel):
    page_count: int
    users: Optional[List[int]] = None
    place_id: Optional[str] = None

    @validator("page_count")
    @classmethod
    def validate_page_count(cls, page_count: int):
        return validate_int(page_count, min_count=MIN_PAGE_COUNT)
