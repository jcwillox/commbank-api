class CommBankException(Exception):
    """
    Base class for all commbank specific exceptions,
    this may not cover all possible exceptions such as network or JSON decoding errors.
    """


class LoginFailedException(CommBankException):
    """Raised when the login failed."""


class BadResponseException(CommBankException):
    """Raised when a response from the website is not formatted correctly."""
