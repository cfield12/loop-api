from typing import Iterator, Optional, Tuple

from loop.enums import DbType
from pony.orm import Database

"""
This module defines the DBSession class, which manages database session
instances for a system. The class is designed to handle one or more database
instances, with the ability to extend to additional types in the future
(e.g., read and write databases).

Key Features:
- **Dynamic Attribute Management**: The class attributes representing database
 instances (e.g., `_write_db`) are dynamically initialized based on the
 `_db_instances` list.
- **Indexing Support**: The class allows accessing and setting database
 instances using custom indexing with a `DbType` enum (e.g., `DbType.WRITE`).
- **Iteration and Items Support**: DBSession supports iteration over the
 database instances (both attribute names and values) using `__iter__` and
 `items()`. This allows the class to behave somewhat like a dictionary.
- **Len Support**: The `__len__` method returns the number of database
 instances managed by the class.

This design allows for flexible management of database instances and future
 extensibility if additional database types (e.g., read-only) are added.
"""


class DBSession:
    """
    This class holds the database session(s) - We have the opportunity to
    add a read instance later down the line.
    """

    _db_instances = ['_write_db']

    def __init__(self) -> None:
        """
        Here we assign the class attributes for the different db instances.
        """
        for instance in self._db_instances:
            setattr(self, instance, None)

    def __getitem__(self, db_type_item: DbType) -> Optional[Database]:
        """
        Allowing accessing to the _write_db attribute using an index.
        """
        if db_type_item == DbType.WRITE:
            return self._write_db
        raise TypeError('Must index DBSession with DbType instance.')

    def __setitem__(
        self, db_type_item: DbType, db: Optional[Database]
    ) -> None:
        """
        Allowing setting the _write_db attribute using an index.
        """
        if db_type_item == DbType.WRITE:
            self._write_db = db
        else:
            raise TypeError(
                'Must set DBSession attribute with DbType instance.'
            )

    def __iter__(self) -> Iterator[str]:
        """
        Allow iteration over the db instances.
        """
        for instance in self._db_instances:
            yield instance

    def items(self) -> Iterator[Tuple[str, Optional[Database]]]:
        """
        Return an iterator of key-value pairs,
        like the dictionary items() method.
        """
        for instance in self._db_instances:
            yield instance, getattr(self, instance)

    def __len__(self) -> int:
        """
        Return the number of db instances we allow for iteration.
        """
        return len(self._db_instances)
