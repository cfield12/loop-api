from typing import List, Union

from pydantic import BaseModel, Extra, Field, ValidationError, validator


class CreateLocation(BaseModel):
    google_id: str
    address: str
    display_name: str
