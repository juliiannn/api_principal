from fastapi import status


class ApiException(Exception):
    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ResourceNotFoundException(ApiException):
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class DuplicateResourceException(ApiException):
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_409_CONFLICT)


class InvalidCredentialsException(ApiException):
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class ForbiddenOperationException(ApiException):
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class InvalidRequestException(ApiException):
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class InvalidStatusTransitionException(ApiException):
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)
