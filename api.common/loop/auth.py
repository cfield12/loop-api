from typing import Dict, List

import boto3
from loop.api_classes import (
    ForgotPassword,
    LoginCredentials,
    SignUpCredentials,
    UserCredentials,
    VerifyUser,
)
from loop.constants import (
    ADMIN,
    AUTH_FLOW,
    COGNITO_SECRET_NAME,
    MINIMUM_PASSWORD_LENGTH,
)
from loop.exceptions import (
    BadRequestError,
    ConflictError,
    UnauthorizedError,
    UnknownCognitoError,
)
from loop.secrets import get_secret


class CognitoAuth:
    def __init__(self, is_admin=False):
        self._auth_client = boto3.client('cognito-idp')
        cognito_secret = get_secret(COGNITO_SECRET_NAME)
        if (
            'user_pool_id' not in cognito_secret
            or 'client_id' not in cognito_secret
        ):
            raise ValueError(
                'cognito secret missing user_pool_id or client_id'
            )
        self._user_pool_id = cognito_secret['user_pool_id']
        self._client_id = cognito_secret['client_id']
        self.is_admin = is_admin

    def _get_user_groups(self, username: str) -> List[Dict]:
        try:
            user_groups = self._auth_client.admin_list_groups_for_user(
                UserPoolId=self._user_pool_id, Username=username
            )
        except self._auth_client.exceptions.UserNotFoundException as e:
            raise ConflictError("The user does not exist.")
        except Exception as e:
            raise e
        if "Groups" not in user_groups:
            raise UnknownCognitoError(
                'Unknown cognito error returning user groups - '
                f'response: {user_groups}'
            )
        return user_groups['Groups']

    def _check_is_admin(self, username: str) -> bool:
        user_groups = self._get_user_groups(username)
        if ADMIN in [group['GroupName'] for group in user_groups]:
            return True
        else:
            return False

    def _initiate_auth(self, login_credentials: LoginCredentials) -> Dict:
        try:
            return self._auth_client.admin_initiate_auth(
                UserPoolId=self._user_pool_id,
                ClientId=self._client_id,
                AuthFlow=AUTH_FLOW,
                AuthParameters={
                    'USERNAME': login_credentials.email,
                    'PASSWORD': login_credentials.password,
                },
                ClientMetadata={
                    'username': login_credentials.email,
                    'password': login_credentials.password,
                },
            )
        except self._auth_client.exceptions.UserNotFoundException as e:
            raise ConflictError("The user does not exist.")
        except self._auth_client.exceptions.NotAuthorizedException as e:
            raise BadRequestError("The username or password is incorrect.")
        except self._auth_client.exceptions.UserNotConfirmedException as e:
            raise BadRequestError("User is not confirmed.")
        except Exception as e:
            raise e

    def login_user(self, login_credentials: LoginCredentials) -> Dict:
        if not isinstance(login_credentials, LoginCredentials):
            raise TypeError(
                'login_credentials must be an instance of LoginCredentials'
            )
        if self.is_admin and not self._check_is_admin(login_credentials.email):
            raise UnauthorizedError('Requires admin access.')
        auth_response = self._initiate_auth(login_credentials)
        if "AuthenticationResult" not in auth_response:
            raise UnknownCognitoError(
                f'Unknown cognito error - response: {auth_response}'
            )
        auth_response = auth_response["AuthenticationResult"]
        return auth_response

    def _sign_up(self, sign_up_creds: SignUpCredentials) -> Dict:
        try:
            return self._auth_client.sign_up(
                ClientId=self._client_id,
                Username=sign_up_creds.email,
                Password=sign_up_creds.password,
                UserAttributes=[
                    {'Name': "given_name", 'Value': sign_up_creds.first_name},
                    {'Name': "family_name", 'Value': sign_up_creds.last_name},
                    {'Name': "email", 'Value': sign_up_creds.email},
                ],
                ValidationData=[
                    {'Name': "given_name", 'Value': sign_up_creds.first_name},
                    {'Name': "family_name", 'Value': sign_up_creds.last_name},
                    {'Name': "email", 'Value': sign_up_creds.email},
                ],
            )
        except self._auth_client.exceptions.UsernameExistsException as e:
            raise ConflictError("This username already exists.")
        except self._auth_client.exceptions.InvalidPasswordException as e:
            raise BadRequestError(
                f"Password should be at least {MINIMUM_PASSWORD_LENGTH} "
                "characters and contain at least 1 number, uppercase letter "
                "and lowercase letter."
            )
        except Exception as e:
            raise e

    def sign_up_user(self, sign_up_credentials: SignUpCredentials) -> Dict:
        if not isinstance(sign_up_credentials, SignUpCredentials):
            raise TypeError(
                'sign_up_credentials must be an instance of SignUpCredentials'
            )
        if self.is_admin and not self._check_is_admin(
            sign_up_credentials.email
        ):
            raise UnauthorizedError('Requires admin access.')
        return self._sign_up(sign_up_credentials)

    def confirm_user(self, verify_object: VerifyUser) -> Dict:
        if not isinstance(verify_object, VerifyUser):
            raise TypeError('verify_object must be an instance of VerifyUser.')
        if self.is_admin and not self._check_is_admin(verify_object.email):
            raise UnauthorizedError('Requires admin access.')
        try:
            return self._auth_client.confirm_sign_up(
                ClientId=self._client_id,
                Username=verify_object.email,
                ConfirmationCode=verify_object.code,
                ForceAliasCreation=False,
            )
        except self._auth_client.exceptions.UserNotFoundException:
            raise ConflictError("Username does not exist.")
        except self._auth_client.exceptions.CodeMismatchException:
            raise BadRequestError("Invalid Verification code.")
        except self._auth_client.exceptions.NotAuthorizedException:
            raise BadRequestError("User is already confirmed.")
        except Exception as e:
            raise e

    def resend_code(self, user_credentials: UserCredentials) -> Dict:
        if not isinstance(user_credentials, UserCredentials):
            raise TypeError(
                'user_credentials must be an instance of UserCredentials.'
            )
        if self.is_admin and not self._check_is_admin(user_credentials.email):
            raise UnauthorizedError('Requires admin access.')
        try:
            return self._auth_client.resend_confirmation_code(
                ClientId=self._client_id,
                Username=user_credentials.email,
            )
        except self._auth_client.exceptions.UserNotFoundException:
            raise ConflictError("Username does not exist.")
        except self._auth_client.exceptions.InvalidParameterException:
            raise BadRequestError("User is already confirmed.")
        except Exception as e:
            raise e

    def initiate_forgot_password(
        self, user_credentials: UserCredentials
    ) -> Dict:
        if not isinstance(user_credentials, UserCredentials):
            raise TypeError(
                'user_credentials must be an instance of UserCredentials.'
            )
        if self.is_admin and not self._check_is_admin(user_credentials.email):
            raise UnauthorizedError('Requires admin access.')
        try:
            return self._auth_client.forgot_password(
                ClientId=self._client_id,
                Username=user_credentials.email,
            )
        except self._auth_client.exceptions.UserNotFoundException:
            raise ConflictError("Username does not exist.")
        except self._auth_client.exceptions.InvalidParameterException:
            raise BadRequestError("User is not confirmed.")
        except Exception as e:
            raise e

    def confirm_forgot_password(
        self, forgot_password_credentials: ForgotPassword
    ) -> Dict:
        if not isinstance(forgot_password_credentials, ForgotPassword):
            raise TypeError(
                'forgot_password_credentials must be an instance of '
                'ForgotPassword.'
            )
        if self.is_admin and not self._check_is_admin(
            forgot_password_credentials.email
        ):
            raise UnauthorizedError('Requires admin access.')
        try:
            return self._auth_client.confirm_forgot_password(
                ClientId=self._client_id,
                Username=forgot_password_credentials.email,
                ConfirmationCode=forgot_password_credentials.code,
                Password=forgot_password_credentials.password,
            )
        except self._auth_client.exceptions.UserNotFoundException:
            raise ConflictError("Username does not exist.")
        except self._auth_client.exceptions.CodeMismatchException:
            raise BadRequestError("Invalid Verification code.")
        except Exception as e:
            raise e

    def admin_delete_user(self, user_credentials: UserCredentials) -> Dict:
        if not isinstance(user_credentials, UserCredentials):
            raise TypeError(
                'user_credentials must be an instance of UserCredentials.'
            )
        try:
            return self._auth_client.admin_delete_user(
                UserPoolId=self._user_pool_id,
                Username=user_credentials.email,
            )
        except self._auth_client.exceptions.UserNotFoundException:
            raise ConflictError("Username does not exist.")
        except Exception as e:
            raise e
