from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exception.api_error import build_error_body
from app.exception.api_exception import ApiException


def register_exception_handlers(app: FastAPI) -> None:
    """Registra los manejadores globales de errores (equivale a @RestControllerAdvice)."""

    @app.exception_handler(ApiException)
    async def api_exception_handler(request: Request, exc: ApiException):
        return JSONResponse(
            status_code=exc.status_code,
            content=build_error_body(exc.status_code, "Business Error", exc.message, request.url.path),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        messages = "; ".join(f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors())
        return JSONResponse(status_code=400, content=build_error_body(400, "Bad Request", messages, request.url.path))

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=build_error_body(500, "Internal Server Error", "Internal server error", request.url.path),
        )
