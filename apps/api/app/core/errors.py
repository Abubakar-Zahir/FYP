from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException


class ApiError(Exception):
    """An expected failure. `code` is a stable string the frontend can rely on (rules.md 3b.3)."""

    def __init__(
        self, status_code: int, code: str, message: str, details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


def _error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = {"error": {"code": code, "message": message, "details": details or {}}}
    return JSONResponse(status_code=status_code, content=body, headers=headers)


async def _handle_api_error(_: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, ApiError)  # noqa: S101
    headers = {"WWW-Authenticate": "Bearer"} if error.status_code == status.HTTP_401_UNAUTHORIZED else None
    return _error_response(error.status_code, error.code, error.message, error.details, headers)


async def _handle_validation_error(_: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, RequestValidationError)  # noqa: S101
    # Only location and message: `input` would echo user data back and into logs.
    fields = [{"location": list(item["loc"]), "message": item["msg"]} for item in error.errors()]
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "validation_error",
        "The request is not valid.",
        {"fields": fields},
    )


async def _handle_http_exception(_: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, HTTPException)  # noqa: S101
    phrase = HTTPStatus(error.status_code).phrase
    code = phrase.lower().replace(" ", "_").replace("-", "_")
    headers = dict(error.headers) if error.headers else None
    return _error_response(error.status_code, code, str(error.detail), headers=headers)


def register_error_handlers(application: FastAPI) -> None:
    application.add_exception_handler(ApiError, _handle_api_error)
    application.add_exception_handler(RequestValidationError, _handle_validation_error)
    application.add_exception_handler(HTTPException, _handle_http_exception)
