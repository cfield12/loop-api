import argparse
import enum
import json
import logging
import os
import pickle
import sys
from typing import List

import boto3
from loop.local_secrets import LocalSecretsManager

SECRET_LIST = 'SecretList'
EXIT_FAILURE = 1

AWS_ACCESS_KEY_ID = 'AWS_ACCESS_KEY_ID'
AWS_SECRET_ACCESS_KEY = 'AWS_SECRET_ACCESS_KEY'
AWS_DEFAULT_REGION = 'AWS_DEFAULT_REGION'
SECRETS_MANAGER = 'secretsmanager'

QI_COGNITO_STAGING_SECRET_NAME = 'qi-secret-cognito-staging'


class AwsRegions(enum.Enum):
    EU_WEST_2 = 'eu-west-2'


SUPPORTED_REGIONS = [
    AwsRegions.EU_WEST_2,
]

DEFAULT_REGION = AwsRegions.EU_WEST_2

logger = logging.getLogger('secretsmanager-generator')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--pickled-filename',
        required=False,
        help="Filename of locally cached secrets file",
    )

    parser.add_argument(
        '--aws-region',
        required=False,
        default=DEFAULT_REGION,
        choices=SUPPORTED_REGIONS,
        help="AWS region name (e.g. us-west-1, eu-west-1, us-east-2)",
    )

    return parser.parse_args()


class Secret(object):

    FIELD_NAME = 'name'
    FIELD_ARN = 'arn'
    FIELD_SECRET_VALUE = 'secret_value'

    GET_SECRET_RESP_FIELD_NAME_ARN = 'ARN'
    GET_SECRET_RESP_FIELD_NAME_NAME = 'Name'
    GET_SECRET_RESP_FIELD_SECRET_STRING = 'SecretString'

    def __init__(
        self, name: str, arn: str, secret_value: str, get_secret_resp
    ):

        self.name = name
        self.arn = arn
        self.secret_value = secret_value
        self.get_secret_resp = get_secret_resp

    def __repr__(self):
        return f'<{self.__class__.__name__ } name={self.name}>'

    @classmethod
    def from_dict(cls, payload: dict):

        if (
            cls.FIELD_NAME not in payload
            or cls.FIELD_ARN not in payload
            or cls.FIELD_SECRET_VALUE not in payload
        ):

            raise ValueError("Unable to create %s from payload" % cls.__name__)

        return cls(
            name=payload[cls.FIELD_NAME],
            arn=payload[cls.FIELD_ARN],
            secret_value=payload[cls.FIELD_SECRET_VALUE],
        )

    def to_dict(self):
        dict_ = {
            self.FIELD_NAME: self.name,
            self.FIELD_ARN: self.arn,
            self.FIELD_SECRET_VALUE: self.secret_avlue,
        }
        return dict_

    @classmethod
    def parse_from_listed_secrets_and_fetch_secret_value(
        cls, list_secret_payload: dict, secrets_manager_client=None
    ):

        if not list_secret_payload or not isinstance(
            list_secret_payload, dict
        ):
            raise ValueError(
                "Invalid payload. Expected dict; received: %s"
                % type(list_secret_payload)
            )

        if not (
            arn := list_secret_payload.get(cls.GET_SECRET_RESP_FIELD_NAME_ARN)
        ):
            raise ValueError("Missing %s" % cls.GET_SECRET_RESP_FIELD_NAME_ARN)

        if not (
            name := list_secret_payload.get(
                cls.GET_SECRET_RESP_FIELD_NAME_NAME
            )
        ):
            raise ValueError(
                "Missing %s" % cls.GET_SECRET_RESP_FIELD_NAME_NAME
            )

        if not secrets_manager_client:
            raise ValueError("Expected boto3 secrets manager client")

        logger.info("Fetching secret for %s", name)

        secret_value_resp = secrets_manager_client.get_secret_value(
            SecretId=arn
        )

        assert (
            cls.GET_SECRET_RESP_FIELD_NAME_ARN in secret_value_resp
            and secret_value_resp[cls.GET_SECRET_RESP_FIELD_NAME_ARN] == arn
        )

        assert (
            cls.GET_SECRET_RESP_FIELD_NAME_NAME in secret_value_resp
            and secret_value_resp[cls.GET_SECRET_RESP_FIELD_NAME_NAME] == name
        )

        assert cls.GET_SECRET_RESP_FIELD_SECRET_STRING in secret_value_resp

        secret_string: str = secret_value_resp[
            cls.GET_SECRET_RESP_FIELD_SECRET_STRING
        ]
        assert isinstance(secret_string, str)

        try:
            secret_string_as_dict: dict = json.loads(secret_string)
        except json.decoder.JSONDecodeError as error:
            logger.warning("Failed to secret (%s) decode as json" % name)
            return None

        return cls(
            name=name,
            arn=arn,
            secret_value=secret_string_as_dict,
            get_secret_resp=secret_value_resp,
        )


def setup_logging(verbose=False):

    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = '%(asctime)s - %(process)d:%(thread)d:%(threadName)s - %(name)s - %(levelname)s - %(message)s'

    logging.basicConfig(
        level=log_level, format=log_format, handlers=[logging.StreamHandler()]
    )


def generate_secrets_cache(
    pickled_filename: str = None,
    aws_access_key_id: str = None,
    aws_secret_access_key: str = None,
    aws_region: str = None,
):

    secrets_manager = boto3.client(
        SECRETS_MANAGER,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region,
    )

    loop_counter = 0
    next_token_params = {}
    secrets_lists = []
    while list_secrets_resp := secrets_manager.list_secrets(
        **next_token_params
    ):

        if (
            not list_secrets_resp
            or SECRET_LIST not in list_secrets_resp
            or not (secrets_list := list_secrets_resp[SECRET_LIST])
            or not isinstance(secrets_list, list)
        ):

            logger.error("Invalid response: %s", list_secrets_resp)
            sys.exit(EXIT_FAILURE)

        logger.info(
            "Found %d secrets (loop=%d)", len(secrets_list), loop_counter
        )
        secrets_lists.extend(secrets_list)

        next_token = list_secrets_resp.get('NextToken')
        loop_counter += 1

        if not next_token:
            logger.warning("No additional pagination. Breaking")
            break

        next_token_params = {'NextToken': next_token}

    logger.info("Found %d secrets", len(secrets_lists))
    secrets = [
        Secret.parse_from_listed_secrets_and_fetch_secret_value(
            resp, secrets_manager
        )
        for resp in secrets_lists
    ]

    assert len(secrets) == len(secrets_lists)
    # filter none
    secrets = [secret for secret in secrets if secret is not None]
    logger.info("Secrets parsed successfully: %d", len(secrets))

    assert all(isinstance(secret, Secret) for secret in secrets)
    LocalSecretsManager.marshall(secrets, pickled_filename)
    local_secrets_manager: LocalSecretsManager = (
        LocalSecretsManager.unmarshall(pickled_filename)
    )


def main():

    setup_logging()
    cli_args = parse_args()
    pickled_filename = cli_args.pickled_filename

    assert cli_args.aws_region in SUPPORTED_REGIONS

    aws_access_key_id = os.environ.get(AWS_ACCESS_KEY_ID)
    aws_secret_access_key = os.environ.get(AWS_SECRET_ACCESS_KEY)
    aws_region = os.environ.get(AWS_DEFAULT_REGION, cli_args.aws_region)

    logger.info("Fetching secrets from %s", aws_region)

    if not aws_access_key_id or not aws_secret_access_key:

        logger.error(
            "Missing %s or %s Environment Variables",
            AWS_ACCESS_KEY_ID,
            AWS_SECRET_ACCESS_KEY,
        )
        sys.exit(EXIT_FAILURE)

    generate_secrets_cache(pickled_filename)


if __name__ == "__main__":
    main()
