"""Core Decorators

비침습적 로깅 및 학습 데코레이터

Reference: docs/specs/LEARNING_SPEC.md
"""

import time
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from app.core.logging import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def trace_log(
    layer: str,
    action: str,
    include_input: bool = True,
    include_output: bool = True,
) -> Callable[[F], F]:
    """트레이스 로깅 데코레이터

    실행 정보를 TraceLogger에 기록

    Args:
        layer: 레이어 이름 (cognitive, planning, execution, response)
        action: 액션 이름 (classify_intent, generate_plan, ...)
        include_input: 입력 로깅 여부
        include_output: 출력 로깅 여부

    Example:
        @trace_log(layer="cognitive", action="classify_intent")
        async def classify_intent(user_input: str) -> Intent:
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            from app.dream_agent.workflow_managers.learning_manager import (
                get_trace_logger,
            )

            trace_logger = get_trace_logger()
            start_time = time.time()
            success = True
            error_msg: Optional[str] = None
            result = None

            # 입력 데이터 추출
            input_data: dict[str, Any] = {}
            if include_input:
                if args:
                    input_data["args"] = [
                        str(arg)[:500] for arg in args
                    ]  # 최대 500자
                if kwargs:
                    input_data["kwargs"] = {
                        k: str(v)[:500] for k, v in kwargs.items()
                    }

            try:
                result = await func(*args, **kwargs)
                return result

            except Exception as e:
                success = False
                error_msg = str(e)
                raise

            finally:
                duration_ms = (time.time() - start_time) * 1000

                # 출력 데이터 추출
                output_data: dict[str, Any] = {}
                if include_output and result is not None:
                    try:
                        if hasattr(result, "model_dump"):
                            output_data = result.model_dump()
                        elif isinstance(result, dict):
                            output_data = result
                        else:
                            output_data = {"value": str(result)[:1000]}
                    except Exception:
                        output_data = {"value": str(result)[:1000]}

                # 트레이스 로그
                trace_logger.log(
                    layer=layer,
                    action=action,
                    input_data=input_data,
                    output_data=output_data,
                    duration_ms=duration_ms,
                    success=success,
                    error=error_msg,
                )

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            from app.dream_agent.workflow_managers.learning_manager import (
                get_trace_logger,
            )

            trace_logger = get_trace_logger()
            start_time = time.time()
            success = True
            error_msg: Optional[str] = None
            result = None

            input_data: dict[str, Any] = {}
            if include_input:
                if args:
                    input_data["args"] = [str(arg)[:500] for arg in args]
                if kwargs:
                    input_data["kwargs"] = {k: str(v)[:500] for k, v in kwargs.items()}

            try:
                result = func(*args, **kwargs)
                return result

            except Exception as e:
                success = False
                error_msg = str(e)
                raise

            finally:
                duration_ms = (time.time() - start_time) * 1000

                output_data: dict[str, Any] = {}
                if include_output and result is not None:
                    try:
                        if hasattr(result, "model_dump"):
                            output_data = result.model_dump()
                        elif isinstance(result, dict):
                            output_data = result
                        else:
                            output_data = {"value": str(result)[:1000]}
                    except Exception:
                        output_data = {"value": str(result)[:1000]}

                trace_logger.log(
                    layer=layer,
                    action=action,
                    input_data=input_data,
                    output_data=output_data,
                    duration_ms=duration_ms,
                    success=success,
                    error=error_msg,
                )

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


def log_execution_time(
    description: Optional[str] = None,
) -> Callable[[F], F]:
    """실행 시간 로깅 데코레이터

    Args:
        description: 로그 설명

    Example:
        @log_execution_time("Intent Classification")
        async def classify_intent(user_input: str) -> Intent:
            ...
    """

    def decorator(func: F) -> F:
        func_name = func.__name__
        desc = description or func_name

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.debug(
                    f"{desc} completed",
                    duration_ms=round(duration_ms, 2),
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"{desc} failed",
                    duration_ms=round(duration_ms, 2),
                    error=str(e),
                )
                raise

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.debug(
                    f"{desc} completed",
                    duration_ms=round(duration_ms, 2),
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"{desc} failed",
                    duration_ms=round(duration_ms, 2),
                    error=str(e),
                )
                raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


def retry(
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable[[F], F]:
    """재시도 데코레이터

    Args:
        max_attempts: 최대 시도 횟수
        delay_seconds: 초기 대기 시간
        backoff: 대기 시간 증가 배수
        exceptions: 재시도할 예외 타입

    Example:
        @retry(max_attempts=3, delay_seconds=1.0)
        async def call_external_api():
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            import asyncio

            last_exception = None
            delay = delay_seconds

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Retry attempt {attempt}/{max_attempts}",
                            function=func.__name__,
                            error=str(e),
                            delay_seconds=delay,
                        )
                        await asyncio.sleep(delay)
                        delay *= backoff
                    else:
                        logger.error(
                            f"All retry attempts failed",
                            function=func.__name__,
                            max_attempts=max_attempts,
                        )

            raise last_exception  # type: ignore

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            import time as time_module

            last_exception = None
            delay = delay_seconds

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Retry attempt {attempt}/{max_attempts}",
                            function=func.__name__,
                            error=str(e),
                            delay_seconds=delay,
                        )
                        time_module.sleep(delay)
                        delay *= backoff
                    else:
                        logger.error(
                            f"All retry attempts failed",
                            function=func.__name__,
                            max_attempts=max_attempts,
                        )

            raise last_exception  # type: ignore

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator
