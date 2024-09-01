import unittest
from unittest.mock import Mock, call, patch

import boto3
from loop.api_classes import (
    ForgotPassword,
    LoginCredentials,
    SignUpCredentials,
    UserCredentials,
    VerifyUser,
)
from loop.auth import CognitoAuth
from loop.exceptions import (
    BadRequestError,
    ConflictError,
    UnauthorizedError,
    UnknownCognitoError,
)

COGNITO_CLIENT = boto3.client('cognito-idp')


TEST_CODE = '123456'
TEST_FIRST_NAME = 'Test'
TEST_SURNAME = 'User'
TEST_EMAIL = 'test_email@test.com'
TEST_PASSWORD = 'test_password'
TEST_LOGIN_CREDS = LoginCredentials(email=TEST_EMAIL, password=TEST_PASSWORD)
ERROR_RESPONSE = {
    'error_response': {'Error': {'Code': 'test', 'Message': 'error'}},
    'operation_name': 'test',
}
TEST_SIGNUP_CREDENTIALS = SignUpCredentials(
    email=TEST_EMAIL,
    password=TEST_PASSWORD,
    first_name=TEST_FIRST_NAME,
    last_name=TEST_SURNAME,
)
TEST_VERIFY_USER = VerifyUser(email=TEST_EMAIL, code=TEST_CODE)
TEST_USER_CREDENTIALS = UserCredentials(email=TEST_EMAIL)
TEST_FORGOT_PASSWORD = ForgotPassword(
    email=TEST_EMAIL, code=TEST_CODE, password=TEST_PASSWORD
)


class TestCognitoAuthInit(unittest.TestCase):
    @patch('loop.auth.get_secret')
    @patch.object(boto3, 'client')
    def test_cognito_auth_init(self, mock_boto, mock_secret):
        mock_secret.return_value = {
            'user_pool_id': 'test_user_pool_id',
            'client_id': 'test_client_id',
        }
        auth = CognitoAuth()
        self.assertTrue(mock_secret.called)
        self.assertEqual(mock_boto.call_args, call('cognito-idp'))

    @patch('loop.auth.get_secret')
    @patch.object(boto3, 'client')
    def test_cognito_auth_init_error_missing_client_id(
        self, mock_boto, mock_secret
    ):
        mock_secret.return_value = {'user_pool_id': 'test_user_pool_id'}
        self.assertRaises(ValueError, CognitoAuth)

    @patch('loop.auth.get_secret')
    @patch.object(boto3, 'client')
    def test_cognito_auth_init_error_missing_user_pool_id(
        self, mock_boto, mock_secret
    ):
        mock_secret.return_value = {'client_id': 'test_client_id'}
        self.assertRaises(ValueError, CognitoAuth)


class TestCognitoAuth(unittest.TestCase):
    @patch('loop.auth.get_secret')
    @patch.object(boto3, 'client')
    def setUp(self, mock_boto, mock_secret):
        mock_secret.return_value = {
            'user_pool_id': 'test_user_pool_id',
            'client_id': 'test_client_id',
        }
        self.cognito_auth = CognitoAuth()
        self.mock_boto = mock_boto
        self.mock_boto.return_value.exceptions.UserNotFoundException = (
            COGNITO_CLIENT.exceptions.UserNotFoundException
        )
        self.mock_boto.return_value.exceptions.NotAuthorizedException = (
            COGNITO_CLIENT.exceptions.NotAuthorizedException
        )
        self.mock_boto.return_value.exceptions.UserNotConfirmedException = (
            COGNITO_CLIENT.exceptions.UserNotConfirmedException
        )
        self.mock_boto.return_value.exceptions.UsernameExistsException = (
            COGNITO_CLIENT.exceptions.UsernameExistsException
        )
        self.mock_boto.return_value.exceptions.InvalidPasswordException = (
            COGNITO_CLIENT.exceptions.InvalidPasswordException
        )
        self.mock_boto.return_value.exceptions.NotAuthorizedException = (
            COGNITO_CLIENT.exceptions.NotAuthorizedException
        )
        self.mock_boto.return_value.exceptions.InvalidParameterException = (
            COGNITO_CLIENT.exceptions.InvalidParameterException
        )
        self.mock_boto.return_value.exceptions.CodeMismatchException = (
            COGNITO_CLIENT.exceptions.CodeMismatchException
        )

    def tearDown(self):
        self.cognito_auth = None

    def test_initiate_auth(self):
        self.cognito_auth._initiate_auth(TEST_LOGIN_CREDS)
        self.assertEqual(
            self.mock_boto.mock_calls[1],
            call().admin_initiate_auth(
                UserPoolId='test_user_pool_id',
                ClientId='test_client_id',
                AuthFlow='ADMIN_USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': 'test_email@test.com',
                    'PASSWORD': 'test_password',
                },
                ClientMetadata={
                    'username': 'test_email@test.com',
                    'password': 'test_password',
                },
            ),
        )

    def test_initiate_auth_user_not_exists_error(self):
        self.mock_boto.return_value.admin_initiate_auth.side_effect = (
            COGNITO_CLIENT.exceptions.UserNotFoundException(**ERROR_RESPONSE)
        )
        self.assertRaises(
            ConflictError, self.cognito_auth._initiate_auth, TEST_LOGIN_CREDS
        )

    def test_initiate_auth_username_or_password_incorrect(self):
        self.mock_boto.return_value.admin_initiate_auth.side_effect = (
            COGNITO_CLIENT.exceptions.NotAuthorizedException(**ERROR_RESPONSE)
        )
        self.assertRaises(
            BadRequestError, self.cognito_auth._initiate_auth, TEST_LOGIN_CREDS
        )

    def test_initiate_auth_user_not_confirmed(self):
        self.mock_boto.return_value.admin_initiate_auth.side_effect = (
            COGNITO_CLIENT.exceptions.UserNotConfirmedException(
                **ERROR_RESPONSE
            )
        )
        self.assertRaises(
            BadRequestError, self.cognito_auth._initiate_auth, TEST_LOGIN_CREDS
        )

    def test_initiate_auth_unknown_error(self):
        self.mock_boto.return_value.admin_initiate_auth.side_effect = (
            ValueError()
        )
        self.assertRaises(
            ValueError, self.cognito_auth._initiate_auth, TEST_LOGIN_CREDS
        )

    def test_login(self):
        self.mock_boto.return_value.admin_initiate_auth.return_value = {
            'AuthenticationResult': {}
        }
        response = self.cognito_auth.login_user(TEST_LOGIN_CREDS)
        self.assertEqual(response, {})

    def test_login_admin(self):
        self.mock_boto.return_value.admin_initiate_auth.return_value = {
            'AuthenticationResult': {}
        }
        response = self.cognito_auth.login_user(TEST_LOGIN_CREDS)
        self.assertEqual(response, {})

    def test_login_type_error(self):
        self.assertRaises(
            TypeError,
            self.cognito_auth.login_user,
            {'email': TEST_EMAIL, 'password': TEST_PASSWORD},
        )

    def test_login_unexpected_payload_error(self):
        self.mock_boto.return_value.admin_initiate_auth.return_value = {}
        self.assertRaises(
            UnknownCognitoError,
            self.cognito_auth.login_user,
            TEST_LOGIN_CREDS,
        )

    def test_sign_up(self):
        self.cognito_auth._sign_up(TEST_SIGNUP_CREDENTIALS)
        self.assertEqual(
            self.mock_boto.mock_calls[1],
            call().sign_up(
                ClientId='test_client_id',
                Username='test_email@test.com',
                Password='test_password',
                UserAttributes=[
                    {'Name': 'given_name', 'Value': 'Test'},
                    {'Name': 'family_name', 'Value': 'User'},
                    {'Name': 'email', 'Value': 'test_email@test.com'},
                ],
                ValidationData=[
                    {'Name': 'given_name', 'Value': 'Test'},
                    {'Name': 'family_name', 'Value': 'User'},
                    {'Name': 'email', 'Value': 'test_email@test.com'},
                ],
            ),
        )

    def test_sign_up_name_already_exists(self):
        self.mock_boto.return_value.sign_up.side_effect = (
            COGNITO_CLIENT.exceptions.UsernameExistsException(**ERROR_RESPONSE)
        )
        self.assertRaises(
            ConflictError, self.cognito_auth._sign_up, TEST_SIGNUP_CREDENTIALS
        )

    def test_sign_up_bad_password_error(self):
        self.mock_boto.return_value.sign_up.side_effect = (
            COGNITO_CLIENT.exceptions.InvalidPasswordException(
                **ERROR_RESPONSE
            )
        )
        self.assertRaises(
            BadRequestError,
            self.cognito_auth._sign_up,
            TEST_SIGNUP_CREDENTIALS,
        )

    def test_sign_up_unknown_error(self):
        self.mock_boto.return_value.sign_up.side_effect = ValueError()
        self.assertRaises(
            ValueError,
            self.cognito_auth._sign_up,
            TEST_SIGNUP_CREDENTIALS,
        )

    def test_sign_up_user(self):
        self.cognito_auth.sign_up_user(TEST_SIGNUP_CREDENTIALS)
        self.assertTrue(self.mock_boto.return_value.sign_up.called)

    def test_sign_up_user_type_error(self):
        self.assertRaises(TypeError, self.cognito_auth.sign_up_user, {})

    def test_confirm_user(self):
        self.cognito_auth.confirm_user(TEST_VERIFY_USER)
        self.assertEqual(
            self.mock_boto.mock_calls[1],
            call().confirm_sign_up(
                ClientId='test_client_id',
                Username='test_email@test.com',
                ConfirmationCode='123456',
                ForceAliasCreation=False,
            ),
        )

    def test_confirm_user_username_not_exists(self):
        self.mock_boto.return_value.confirm_sign_up.side_effect = (
            COGNITO_CLIENT.exceptions.UserNotFoundException(**ERROR_RESPONSE)
        )
        self.assertRaises(
            ConflictError,
            self.cognito_auth.confirm_user,
            TEST_VERIFY_USER,
        )

    def test_confirm_user_invalid_code(self):
        self.mock_boto.return_value.confirm_sign_up.side_effect = (
            COGNITO_CLIENT.exceptions.CodeMismatchException(**ERROR_RESPONSE)
        )
        self.assertRaises(
            BadRequestError,
            self.cognito_auth.confirm_user,
            TEST_VERIFY_USER,
        )

    def test_confirm_user_already_confirmed(self):
        self.mock_boto.return_value.confirm_sign_up.side_effect = (
            COGNITO_CLIENT.exceptions.NotAuthorizedException(**ERROR_RESPONSE)
        )
        self.assertRaises(
            BadRequestError,
            self.cognito_auth.confirm_user,
            TEST_VERIFY_USER,
        )

    def test_confirm_user_unknown_error(self):
        self.mock_boto.return_value.confirm_sign_up.side_effect = ValueError()
        self.assertRaises(
            ValueError,
            self.cognito_auth.confirm_user,
            TEST_VERIFY_USER,
        )

    def test_confirm_user_type_error(self):
        self.assertRaises(TypeError, self.cognito_auth.confirm_user, {})

    def test_resend_code(self):
        self.cognito_auth.resend_code(TEST_USER_CREDENTIALS)
        self.assertEqual(
            self.mock_boto.mock_calls[1],
            call().resend_confirmation_code(
                ClientId='test_client_id',
                Username='test_email@test.com',
            ),
        )

    def test_resend_code_username_not_exists(self):
        self.mock_boto.return_value.resend_confirmation_code.side_effect = (
            COGNITO_CLIENT.exceptions.UserNotFoundException(**ERROR_RESPONSE)
        )
        self.assertRaises(
            ConflictError,
            self.cognito_auth.resend_code,
            TEST_USER_CREDENTIALS,
        )

    def test_resend_code_user_already_confirmed(self):
        self.mock_boto.return_value.resend_confirmation_code.side_effect = (
            COGNITO_CLIENT.exceptions.InvalidParameterException(
                **ERROR_RESPONSE
            )
        )
        self.assertRaises(
            BadRequestError,
            self.cognito_auth.resend_code,
            TEST_USER_CREDENTIALS,
        )

    def test_resend_code_unknown_error(self):
        self.mock_boto.return_value.resend_confirmation_code.side_effect = (
            ValueError()
        )
        self.assertRaises(
            ValueError,
            self.cognito_auth.resend_code,
            TEST_USER_CREDENTIALS,
        )

    def test_resend_code_type_error(self):
        self.assertRaises(TypeError, self.cognito_auth.resend_code, {})

    def test_initiate_forgot_password(self):
        self.cognito_auth.initiate_forgot_password(TEST_USER_CREDENTIALS)
        self.assertEqual(
            self.mock_boto.mock_calls[1],
            call().forgot_password(
                ClientId='test_client_id',
                Username='test_email@test.com',
            ),
        )

    def test_forgot_password_type_error(self):
        self.assertRaises(
            TypeError, self.cognito_auth.initiate_forgot_password, {}
        )

    def test_forgot_password_user_name_not_exists(self):
        self.mock_boto.return_value.forgot_password.side_effect = (
            COGNITO_CLIENT.exceptions.UserNotFoundException(**ERROR_RESPONSE)
        )
        self.assertRaises(
            ConflictError,
            self.cognito_auth.initiate_forgot_password,
            TEST_USER_CREDENTIALS,
        )

    def test_forgot_password_user_not_confirmed(self):
        self.mock_boto.return_value.forgot_password.side_effect = (
            COGNITO_CLIENT.exceptions.InvalidParameterException(
                **ERROR_RESPONSE
            )
        )
        self.assertRaises(
            BadRequestError,
            self.cognito_auth.initiate_forgot_password,
            TEST_USER_CREDENTIALS,
        )

    def test_forgot_password_unknown_error(self):
        self.mock_boto.return_value.forgot_password.side_effect = ValueError()
        self.assertRaises(
            ValueError,
            self.cognito_auth.initiate_forgot_password,
            TEST_USER_CREDENTIALS,
        )

    def test_confirm_forgot_password(self):
        self.cognito_auth.confirm_forgot_password(TEST_FORGOT_PASSWORD)
        self.assertEqual(
            self.mock_boto.mock_calls[1],
            call().confirm_forgot_password(
                ClientId='test_client_id',
                Username='test_email@test.com',
                ConfirmationCode='123456',
                Password='test_password',
            ),
        )

    def test_confirm_forgot_password_type_error(self):
        self.assertRaises(
            TypeError, self.cognito_auth.confirm_forgot_password, {}
        )

    def test_confirm_forgot_password_username_not_exists(self):
        self.mock_boto.return_value.confirm_forgot_password.side_effect = (
            COGNITO_CLIENT.exceptions.UserNotFoundException(**ERROR_RESPONSE)
        )
        self.assertRaises(
            ConflictError,
            self.cognito_auth.confirm_forgot_password,
            TEST_FORGOT_PASSWORD,
        )

    def test_confirm_forgot_password_invalid_code(self):
        self.mock_boto.return_value.confirm_forgot_password.side_effect = (
            COGNITO_CLIENT.exceptions.CodeMismatchException(**ERROR_RESPONSE)
        )
        self.assertRaises(
            BadRequestError,
            self.cognito_auth.confirm_forgot_password,
            TEST_FORGOT_PASSWORD,
        )

    def test_confirm_forgot_password_unknown_error(self):
        self.mock_boto.return_value.confirm_forgot_password.side_effect = (
            ValueError()
        )
        self.assertRaises(
            ValueError,
            self.cognito_auth.confirm_forgot_password,
            TEST_FORGOT_PASSWORD,
        )

    def test_admin_delete_user(self):
        self.cognito_auth.admin_delete_user(TEST_USER_CREDENTIALS)
        self.assertEqual(
            self.mock_boto.mock_calls[1],
            call().admin_delete_user(
                UserPoolId='test_user_pool_id', Username='test_email@test.com'
            ),
        )

    def test_admin_delete_user_type_error(self):
        self.assertRaises(TypeError, self.cognito_auth.admin_delete_user, {})

    def test_admin_delete_username_not_exists(self):
        self.mock_boto.return_value.admin_delete_user.side_effect = (
            COGNITO_CLIENT.exceptions.UserNotFoundException(**ERROR_RESPONSE)
        )
        self.assertRaises(
            ConflictError,
            self.cognito_auth.admin_delete_user,
            TEST_USER_CREDENTIALS,
        )

    def test_admin_delete_user_unknown_error(self):
        self.mock_boto.return_value.admin_delete_user.side_effect = (
            ValueError()
        )
        self.assertRaises(
            ValueError,
            self.cognito_auth.admin_delete_user,
            TEST_USER_CREDENTIALS,
        )


class TestCognitoAuthAdmin(unittest.TestCase):
    @patch('loop.auth.get_secret')
    @patch.object(boto3, 'client')
    def setUp(self, mock_boto, mock_secret):
        mock_secret.return_value = {
            'user_pool_id': 'test_user_pool_id',
            'client_id': 'test_client_id',
        }
        self.cognito_auth = CognitoAuth(is_admin=True)
        self.mock_boto = mock_boto
        self.mock_boto.return_value.exceptions.UserNotFoundException = (
            COGNITO_CLIENT.exceptions.UserNotFoundException
        )
        self.mock_boto.return_value.exceptions.NotAuthorizedException = (
            COGNITO_CLIENT.exceptions.NotAuthorizedException
        )
        self.mock_boto.return_value.exceptions.UserNotConfirmedException = (
            COGNITO_CLIENT.exceptions.UserNotConfirmedException
        )
        self.mock_boto.return_value.exceptions.UsernameExistsException = (
            COGNITO_CLIENT.exceptions.UsernameExistsException
        )
        self.mock_boto.return_value.exceptions.InvalidPasswordException = (
            COGNITO_CLIENT.exceptions.InvalidPasswordException
        )
        self.mock_boto.return_value.exceptions.NotAuthorizedException = (
            COGNITO_CLIENT.exceptions.NotAuthorizedException
        )
        self.mock_boto.return_value.exceptions.InvalidParameterException = (
            COGNITO_CLIENT.exceptions.InvalidParameterException
        )
        self.mock_boto.return_value.exceptions.CodeMismatchException = (
            COGNITO_CLIENT.exceptions.CodeMismatchException
        )

    def tearDown(self):
        self.cognito_auth = None

    def test_login_fail(self):
        self.mock_boto.return_value.admin_initiate_auth.return_value = {
            'AuthenticationResult': {}
        }
        self.mock_boto.return_value.admin_list_groups_for_user.return_value = {
            'Groups': []
        }
        self.assertRaises(
            UnauthorizedError, self.cognito_auth.login_user, TEST_LOGIN_CREDS
        )

    def test_login(self):
        self.mock_boto.return_value.admin_initiate_auth.return_value = {
            'AuthenticationResult': {}
        }
        self.mock_boto.return_value.admin_list_groups_for_user.return_value = {
            'Groups': [{'GroupName': 'admin'}]
        }
        response = self.cognito_auth.login_user(TEST_LOGIN_CREDS)
        self.assertEqual(response, {})

    def test_sign_up_fail(self):
        self.mock_boto.return_value.admin_list_groups_for_user.return_value = {
            'Groups': []
        }
        self.assertRaises(
            UnauthorizedError,
            self.cognito_auth.sign_up_user,
            TEST_SIGNUP_CREDENTIALS,
        )

    def test_sign_up(self):
        self.mock_boto.return_value.admin_list_groups_for_user.return_value = {
            'Groups': [{'GroupName': 'admin'}]
        }
        self.cognito_auth.sign_up_user(TEST_SIGNUP_CREDENTIALS)
        self.assertTrue(self.mock_boto.return_value.sign_up.called)

    def test_confirm_user_fail(self):
        self.mock_boto.return_value.admin_list_groups_for_user.return_value = {
            'Groups': []
        }
        self.assertRaises(
            UnauthorizedError,
            self.cognito_auth.confirm_user,
            TEST_VERIFY_USER,
        )

    def test_confirm_user(self):
        self.mock_boto.return_value.admin_list_groups_for_user.return_value = {
            'Groups': [{'GroupName': 'admin'}]
        }
        self.cognito_auth.confirm_user(TEST_VERIFY_USER)
        self.assertTrue(self.mock_boto.return_value.confirm_sign_up.called)

    def test_resend_code_fail(self):
        self.mock_boto.return_value.admin_list_groups_for_user.return_value = {
            'Groups': []
        }
        self.assertRaises(
            UnauthorizedError,
            self.cognito_auth.resend_code,
            TEST_USER_CREDENTIALS,
        )

    def test_resend_code(self):
        self.mock_boto.return_value.admin_list_groups_for_user.return_value = {
            'Groups': [{'GroupName': 'admin'}]
        }
        self.cognito_auth.resend_code(TEST_USER_CREDENTIALS)
        self.assertTrue(
            self.mock_boto.return_value.resend_confirmation_code.called
        )

    def test_initiate_forgot_password_fail(self):
        self.mock_boto.return_value.admin_list_groups_for_user.return_value = {
            'Groups': []
        }
        self.assertRaises(
            UnauthorizedError,
            self.cognito_auth.initiate_forgot_password,
            TEST_USER_CREDENTIALS,
        )

    def test_initiate_forgot_password(self):
        self.mock_boto.return_value.admin_list_groups_for_user.return_value = {
            'Groups': [{'GroupName': 'admin'}]
        }
        self.cognito_auth.initiate_forgot_password(TEST_USER_CREDENTIALS)
        self.assertTrue(self.mock_boto.return_value.forgot_password.called)

    def test_confirm_forgot_password_fail(self):
        self.mock_boto.return_value.admin_list_groups_for_user.return_value = {
            'Groups': []
        }
        self.assertRaises(
            UnauthorizedError,
            self.cognito_auth.confirm_forgot_password,
            TEST_FORGOT_PASSWORD,
        )

    def test_confirm_forgot_password(self):
        self.mock_boto.return_value.admin_list_groups_for_user.return_value = {
            'Groups': [{'GroupName': 'admin'}]
        }
        self.cognito_auth.confirm_forgot_password(TEST_FORGOT_PASSWORD)
        self.assertTrue(
            self.mock_boto.return_value.confirm_forgot_password.called
        )


if __name__ == '__main__':
    unittest.main()
