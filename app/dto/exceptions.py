import typing


class ErrorProtocol(typing.Protocol):
    detail: str
    code: typing.ClassVar[str]


class APIError(Exception):
    code: typing.ClassVar[str]

    def __init__(self, detail: str) -> None:
        self.detail = detail

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"

    def __repr__(self) -> str:
        return f"{self.code}: {self.detail}"


class NotFoundError(APIError):
    code = "not_found"


class AlreadyExistsError(APIError):
    code = "already_exists"


class UpdateForbiddenError(APIError):
    code = "update_forbidden"


class PermissionScopeError(APIError):
    code = "permission_scope_error"


class ClientError(APIError):
    code = "client_error"


class AuthenticationError(APIError):
    code = "authentication_error"
