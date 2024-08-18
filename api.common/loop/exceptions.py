import chalice


class LoopException(Exception):
    STATUS_CODE = 500

    @staticmethod
    def as_chalice_exception(e):
        if not hasattr(e, 'STATUS_CODE'):
            # Forward on any no loop errors, i.e. Python generic errors
            # like ValueError, Exception etc
            return e

        # Get names of all ChaliceViewError subclass exceptions
        chalice_errors = {
            str(error.__name__).split(".")[-1]: error
            for error in chalice.ChaliceViewError.__subclasses__()
        }

        # Get name of inbound error
        inbound_error = e.__class__.__name__.split(".")[-1]

        # Natively map whatever common exceptions there are between
        # Loop and Chalice.

        if inbound_error in chalice_errors:
            chalice_error = chalice_errors[inbound_error](" ".join(e.args))
        else:
            chalice_error = chalice.ChaliceViewError(" ".join(e.args))

        chalice_error.STATUS_CODE = e.STATUS_CODE

        return chalice_error


class BadRequestError(LoopException):
    STATUS_CODE = 400


class BadRequestParameterError(chalice.BadRequestError):
    def __init__(self, message):
        super().__init__(message)


class UnauthorizedError(LoopException):
    STATUS_CODE = 401


class ForbiddenError(LoopException):
    STATUS_CODE = 403


class NotFoundError(LoopException):
    STATUS_CODE = 404


class MethodNotAllowedError(LoopException):
    STATUS_CODE = 405


class RequestTimeoutError(LoopException):
    STATUS_CODE = 408


class ConflictError(LoopException):
    STATUS_CODE = 409


class UnprocessableEntityError(LoopException):
    STATUS_CODE = 422


class TooManyRequestsError(LoopException):
    STATUS_CODE = 429


class Error(Exception):
    '''Base class for other exceptions'''


class DbInitFailedError(Error):
    '''Raised when db initialisation fails'''

    def __init__(self, message):
        self.message = message


class DbNotInitError(Error):
    '''Raised when db not initialised'''

    def __init__(self, message):
        self.message = message


class DbDisconnectFailedError(Error):
    '''Raised when db disconnect fails'''

    def __init__(self, message):
        self.message = message


class CreateUserValidationError(Error):
    '''Raised when incorrect user create inputs'''

    def __init__(self, message):
        self.message = message


class GoogleApiError(Error):
    '''Raised when Google returns an error'''

    def __init__(self, message):
        self.message = message


class UnknownFriendStatusTypeError(Error):
    '''Unknown Friend status error'''

    def __init__(self, message):
        self.message = message


class BucketNotFoundError(Error):
    '''Bucket not found error'''

    def __init__(self, message):
        self.message = message


class UnknownCognitoError(Error):
    '''Unknown Cognito error'''

    def __init__(self, message):
        self.message = message
