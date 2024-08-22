from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Dict, Optional

from loop.api_classes import Coordinates
from loop.enums import FriendStatusType


@dataclass
class UserObject:
    id: int
    cognito_user_name: str
    groups: Optional[list] = None


@dataclass
class UserCreateObject:
    cognito_user_name: str
    email: str
    first_name: str
    last_name: str


@dataclass
class Location:
    google_id: str
    address: str
    display_name: str
    coordinates: Coordinates
    photo_reference: str = None
    website: str = None
    phone_number: str = None
    price_level: int = None

    def to_dict(self) -> Dict[str, str]:
        d = deepcopy(asdict(self))
        d['coordinates'] = d['coordinates'].model_dump()
        return d


@dataclass
class Rating:
    location: int
    user: int
    price: int
    food: int
    vibe: int
    message: Optional[str] = None


@dataclass
class UploadThumbnailEvent:
    place_id: str
    photo_reference: str

    def to_dict(self) -> Dict[str, str]:
        return deepcopy(asdict(self))


@dataclass
class FriendStatus:
    id: int
    status: FriendStatusType
