import logging

from chalice import Chalice
from loop.api_classes import (
    ForgotPassword,
    LoginCredentials,
    SignUpCredentials,
    UserCredentials,
    VerifyUser,
)
from loop.auth import CognitoAuth
from loop.exceptions import BadRequestError, LoopException
from pydantic import ValidationError as PydanticValidationError

APP_NAME = 'auth-api'
app = Chalice(app_name=APP_NAME)
app.log.setLevel(logging.INFO)


@app.route('/web/auth/login', methods=['POST'])
@app.route('/auth/login', methods=['POST'])
def login():
    """
    Login.
    ---
    post:
        operationId: login
        summary: Login as a user.
        description: Login as a user.
        security:
            - Qi API Key: []
        parameters:
            -   in: body
                name: login_credentials
                schema:
                    type: object
                required: true
                description: JSON object containing login creds.
        responses:
            200:
                description: OK
                schema:
                    type: object
            default:
                description: Unexpected error
                schema:
                    type: object
    """
    try:
        payload = app.current_request.json_body
        try:
            login_credentials = LoginCredentials(**payload)
        except PydanticValidationError as e:
            raise BadRequestError(
                "; ".join([error["msg"] for error in e.errors()])
            )
        auth_client = CognitoAuth()
        return auth_client.login_user(login_credentials)
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route('/web/auth/signup', methods=['POST'])
@app.route('/auth/signup', methods=['POST'])
def sign_up():
    """
    Sign up.
    ---
    post:
        operationId: signUp
        summary: Sign up a user.
        description: Sign up a user.
        security:
            - Qi API Key: []
        parameters:
            -   in: body
                name: sign_up_credentials
                schema:
                    type: object
                required: true
                description: JSON object containing sign up creds.
        responses:
            200:
                description: OK
                schema:
                    type: object
            default:
                description: Unexpected error
                schema:
                    type: object
    """
    try:
        payload = app.current_request.json_body
        try:
            sign_up_creds = SignUpCredentials(**payload)
        except PydanticValidationError as e:
            raise BadRequestError(
                "; ".join([error["msg"] for error in e.errors()])
            )
        auth_client = CognitoAuth()
        return auth_client.sign_up_user(sign_up_creds)
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route('/web/auth/confirm_signup', methods=['POST'])
@app.route('/auth/confirm_signup', methods=['POST'])
def confirm_sign_up():
    """
    Confirm sign up.
    ---
    post:
        operationId: confirmSignUp
        summary: Confirm sign up of a user.
        description: Confirm sign up of a user.
        security:
            - Qi API Key: []
        parameters:
            -   in: body
                name: verification_code
                schema:
                    type: object
                required: true
                description: JSON object containing verification code.
        responses:
            200:
                description: OK
                schema:
                    type: object
            default:
                description: Unexpected error
                schema:
                    type: object
    """
    try:
        payload = app.current_request.json_body
        try:
            verification_code = VerifyUser(**payload)
        except PydanticValidationError as e:
            raise BadRequestError(
                "; ".join([error["msg"] for error in e.errors()])
            )
        auth_client = CognitoAuth()
        return auth_client.confirm_user(verification_code)
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route('/web/auth/resend_code', methods=['POST'])
@app.route('/auth/resend_code', methods=['POST'])
def resend_code():
    """
    Resend verification code.
    ---
    post:
        operationId: resendCode
        summary: Resend verification code.
        description: Resend verification code.
        security:
            - Qi API Key: []
        parameters:
            -   in: body
                name: user_credentials
                schema:
                    type: object
                required: true
                description: JSON object containing email.
        responses:
            200:
                description: OK
                schema:
                    type: object
            default:
                description: Unexpected error
                schema:
                    type: object
    """
    try:
        payload = app.current_request.json_body
        try:
            user_credentials = UserCredentials(**payload)
        except PydanticValidationError as e:
            raise BadRequestError(
                "; ".join([error["msg"] for error in e.errors()])
            )
        auth_client = CognitoAuth()
        return auth_client.resend_code(user_credentials)
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route('/web/auth/forgot_password', methods=['POST'])
@app.route('/auth/forgot_password', methods=['POST'])
def forgot_password():
    """
    Forgot password.
    ---
    post:
        operationId: forgotPassword
        summary: Forgot password.
        description: Forgot password.
        security:
            - Qi API Key: []
        parameters:
            -   in: body
                name: user_credentials
                schema:
                    type: object
                required: true
                description: JSON object containing email.
        responses:
            200:
                description: OK
                schema:
                    type: object
            default:
                description: Unexpected error
                schema:
                    type: object
    """
    try:
        payload = app.current_request.json_body
        try:
            user_credentials = UserCredentials(**payload)
        except PydanticValidationError as e:
            raise BadRequestError(
                "; ".join([error["msg"] for error in e.errors()])
            )
        auth_client = CognitoAuth()
        return auth_client.initiate_forgot_password(user_credentials)
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)


@app.route('/web/auth/confirm_forgot_password', methods=['POST'])
@app.route('/auth/confirm_forgot_password', methods=['POST'])
def confirm_forgot_password():
    """
    Confirm forgot password.
    ---
    post:
        operationId: confirmForgotPassword
        summary: Confirm forgot password.
        description: Confirm forgot password.
        security:
            - Qi API Key: []
        parameters:
            -   in: body
                name: forgot_password_credentials
                schema:
                    type: object
                required: true
                description: JSON object containing email, new password and
                 verification code.
        responses:
            200:
                description: OK
                schema:
                    type: object
            default:
                description: Unexpected error
                schema:
                    type: object
    """
    try:
        payload = app.current_request.json_body
        try:
            forgot_password_credentials = ForgotPassword(**payload)
        except PydanticValidationError as e:
            raise BadRequestError(
                "; ".join([error["msg"] for error in e.errors()])
            )
        auth_client = CognitoAuth()
        return auth_client.confirm_forgot_password(forgot_password_credentials)
    except LoopException as e:
        raise LoopException.as_chalice_exception(e)
