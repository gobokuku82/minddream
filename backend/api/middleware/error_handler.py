"""Error Handler Middleware

전역 에러 핸들링

Reference: docs/specs/API_SPEC.md#error-handling
"""

import traceback
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.errors import AgentError, ErrorCode
from app.core.logging import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """전역 에러 핸들러 미들웨어"""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        try:
            response = await call_next(request)
            return response

        except AgentError as e:
            logger.error(
                "Agent error",
                error_code=e.code.value,
                message=e.message,
                path=request.url.path,
            )

            return JSONResponse(
                status_code=self._get_status_code(e.code),
                content={
                    "success": False,
                    "error": {
                        "code": e.code.value,
                        "message": e.message,
                        "details": e.details,
                    },
                },
            )

        except Exception as e:
            logger.exception(
                "Unexpected error",
                path=request.url.path,
                error=str(e),
            )

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": "E5003",
                        "message": "Internal server error",
                        "details": {"error": str(e)} if logger.isEnabledFor(10) else {},
                    },
                },
            )

    def _get_status_code(self, error_code: ErrorCode) -> int:
        """에러 코드에 따른 HTTP 상태 코드"""
        code_value = error_code.value

        # E1xxx: 입력 에러 (400)
        if code_value.startswith("E1"):
            return 400

        # E2xxx: 인증 에러 (401, 403)
        if code_value.startswith("E2"):
            if code_value in ("E2001", "E2002"):
                return 401
            return 403

        # E3xxx: 리소스 에러 (404, 409)
        if code_value.startswith("E3"):
            if code_value == "E3001":
                return 404
            return 409

        # E4xxx: 외부 서비스 에러 (502, 503, 504)
        if code_value.startswith("E4"):
            if code_value == "E4003":
                return 504
            return 502

        # E5xxx: 내부 에러 (500)
        return 500


def setup_error_handlers(app: FastAPI) -> None:
    """에러 핸들러 설정

    Args:
        app: FastAPI 앱
    """
    app.add_middleware(ErrorHandlerMiddleware)

    @app.exception_handler(AgentError)
    async def agent_error_handler(
        request: Request,
        exc: AgentError,
    ) -> JSONResponse:
        """AgentError 핸들러"""
        logger.error(
            "Agent error",
            error_code=exc.code.value,
            message=exc.message,
        )

        status_code = 500
        code_value = exc.code.value
        if code_value.startswith("E1"):
            status_code = 400
        elif code_value.startswith("E2"):
            status_code = 401
        elif code_value.startswith("E3"):
            status_code = 404
        elif code_value.startswith("E4"):
            status_code = 502

        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "error": exc.to_detail().model_dump(),
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request,
        exc: ValueError,
    ) -> JSONResponse:
        """ValueError 핸들러"""
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {
                    "code": "E1001",
                    "message": str(exc),
                },
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """일반 예외 핸들러"""
        logger.exception("Unhandled exception", error=str(exc))

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "E5003",
                    "message": "Internal server error",
                },
            },
        )
