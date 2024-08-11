import json
import logging
import os

import boto3
from botocore.exceptions import ClientError
from loop.local_secrets import LocalSecretsManager

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOGLEVEL", "INFO"))

# Handle region control.
REGION = boto3.session.Session().region_name

# Optional override container for development.
SECRET_OVERRIDES = {}

SECRET_OVERRIDES = LocalSecretsManager.unmarshall().secrets_lookup_by_name_map
assert isinstance(SECRET_OVERRIDES, dict)


def get_secret(secret_name, add_environment=False, region=REGION):

    if add_environment:
        secret_name = '{}-{}'.format(secret_name, os.environ["ENVIRONMENT"])

    if secret_name in SECRET_OVERRIDES:
        return SECRET_OVERRIDES[secret_name]

    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region)

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        logger.error(f'Error getting secret {secret_name}: {str(e)}')
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise e
    else:
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            secret = json.loads(secret)
            return secret
        else:
            # Dead code disabling for now
            # decoded_binary_secret = base64.b64decode
            # (get_secret_value_response['SecretBinary'])
            # return binary_secret_data
            pass


def get_db_dict(secret_name):
    db_dict = get_secret(secret_name)
    db_dict.update(
        {"database": "loop", "provider": "mysql", "port": int(db_dict['port'])}
    )
    return db_dict
