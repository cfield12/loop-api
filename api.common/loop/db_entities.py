from datetime import datetime

from pony.orm import (
    Database,
    Optional,
    PrimaryKey,
    Required,
    Set,
    composite_key,
)


def define_entities(db: Database):
    class User(db.Entity):
        """
        List of all users.
        """

        id = PrimaryKey(int, auto=True)
        created = Optional(datetime)
        last_updated = Optional(datetime)
        cognito_user_name = Required(str)
        email = Required(str)
        first_name = Required(str)
        last_name = Required(str)
        ratings = Set('Rating')
        friend_1 = Set('Friend', reverse='friend_1')
        friend_2 = Set('Friend', reverse='friend_2')
        groups = Set('Group')

    class Group(db.Entity):
        """
        List of all groups.
        """

        id = PrimaryKey(int, auto=True)
        description = Optional(str, nullable=True)
        users = Set(User)

    class Location(db.Entity):
        """
        List of all locations.
        """

        id = PrimaryKey(int, auto=True)
        google_id = Required(str)
        address = Required(str)
        display_name = Required(str)
        latitude = Required(float)
        longitude = Required(float)
        created = Optional(datetime)
        last_updated = Optional(datetime)
        ratings = Set('Rating')

    class Rating(db.Entity):
        id = PrimaryKey(int, auto=True)
        price = Required(int)
        vibe = Required(int)
        food = Required(int)
        location = Required(Location)
        user = Required(User)
        created = Optional(datetime)
        last_updated = Optional(datetime)
        message = Optional(str, nullable=True)

    class Friend_status(db.Entity):
        id = PrimaryKey(int, auto=True)
        description = Required(str)
        status = Set('Friend')

    class Friend(db.Entity):
        id = PrimaryKey(int, auto=True)
        friend_1 = Required(User, reverse='friend_1')
        friend_2 = Required(User, reverse='friend_2')
        status = Required(Friend_status)
        created = Optional(datetime)
        last_updated = Optional(datetime)
