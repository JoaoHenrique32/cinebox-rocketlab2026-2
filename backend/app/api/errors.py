"""Tradução de exceções de domínio em respostas HTTP."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import DomainError, InvalidReferenceError, NotFoundError

_STATUS_BY_ERROR: dict[type[DomainError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    InvalidReferenceError: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


async def _domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    del request
    assert isinstance(exc, DomainError)
    status_code = next(
        (code for error, code in _STATUS_BY_ERROR.items() if isinstance(exc, error)),
        status.HTTP_400_BAD_REQUEST,
    )
    return JSONResponse(status_code=status_code, content={"detail": exc.message})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _domain_error_handler)
