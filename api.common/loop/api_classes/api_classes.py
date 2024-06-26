from typing import List, Union

from pydantic import BaseModel, Extra, Field, ValidationError, validator


class CreateRating(BaseModel):
    google_id: str
    price: int
    vibe: int
    food: int
