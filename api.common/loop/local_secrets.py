import enum
import logging
import os
import pickle
from typing import List

logger = logging.getLogger(__name__)


class FileMode(enum.Enum):

    READ = 'r'
    WRITE = 'w'
    BINARY = 'b'

    def __add__(self, other):
        if not isinstance(other, FileMode):
            raise ValueError("Expected FileMode")

        return str(self.value) + str(other.value)

    def __or__(self, other):
        if not isinstance(other, FileMode):
            raise ValueError("Expected FileMode")
        return self.__add__(other)


class LocalSecretsManager(object):
    """Secrets manager that operates off of locally pickled secrets."""

    LOCAL_PICKLED_FILENAME = 'secrets.pickle'

    def __init__(self, secrets_list: List):

        self.secrets_lookup_by_name_map = {}
        for secret in secrets_list:
            assert secret.name not in self.secrets_lookup_by_name_map
            self.secrets_lookup_by_name_map[secret.name] = secret.secret_value

    def get_secret(self, name: str):

        if name not in self.secrets_lookup_by_name_map:
            raise RuntimeError("Missing %s from local map" % name)
        return self.secrets_lookup_by_name_map[name]

    @classmethod
    def marshall(cls, secrets_list, filename: str = None):

        instance = cls(secrets_list)

        pickled_filename = (
            filename or cls.local_pickled_filename_absolute_path()
        )

        with open(pickled_filename, 'wb') as fh:
            pickle.dump(instance, fh)

        assert os.path.exists(pickled_filename)

    @classmethod
    def local_pickled_filename_absolute_path(cls):
        cur_dir = os.path.dirname(__file__)
        filename = os.path.join(cur_dir, cls.LOCAL_PICKLED_FILENAME)
        logger.info("Locally pickled filename: %s", filename)
        return filename

    @classmethod
    def unmarshall(cls, pickle_filename: str = None):

        pickled_filename = (
            pickle_filename or cls.local_pickled_filename_absolute_path()
        )
        logger.info("Pickling from %s", pickled_filename)

        try:

            with open(pickled_filename, FileMode.READ | FileMode.BINARY) as fh:
                return pickle.load(fh)

        except IOError as error:
            logger.error("Unable to load %s", pickled_filename)

        logger.warning("Initialzing empty LocalSecrets Manager")
        empty_secrets_list = []
        return cls(empty_secrets_list)


# assert that local secrets.pickle exists in local directory
