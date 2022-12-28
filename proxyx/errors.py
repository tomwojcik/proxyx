import typing

from starlette import status
from starlette.exceptions import HTTPException

from proxyx.settings import HIDE_ERROR_MESSAGE


class ProxyxError(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: typing.Optional[str] = None,
        headers: typing.Optional[dict] = None,
    ) -> None:
        if HIDE_ERROR_MESSAGE:
            status_code = status.HTTP_400_BAD_REQUEST
            detail = "Bad request"
        super().__init__(
            status_code=status_code, detail=detail, headers=headers
        )
