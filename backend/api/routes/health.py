"""Health Check Routes

Reference: docs/specs/API_SPEC.md#health
"""

import asyncio
from datetime import datetime
from typing import Any

from fastapi import APIRouter

from api.schemas.response import HealthDetailResponse, HealthResponse
from api.websocket import get_connection_manager
from app.core.config import settings
from app.core.logging import get_logger
from app.dream_agent.orchestrator import get_checkpointer

router = APIRouter(prefix="/health", tags=["Health"])
logger = get_logger(__name__)


async def _check_database() -> dict[str, Any]:
    """데이터베이스 연결 체크"""
    try:
        checkpointer = await get_checkpointer()
        if checkpointer:
            return {
                "status": "ok",
                "message": "Database connection available",
            }
        return {
            "status": "ok",
            "message": "Using memory checkpointer",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database error: {str(e)}",
        }


async def _check_llm() -> dict[str, Any]:
    """LLM API 연결 체크"""
    try:
        from app.dream_agent.llm_manager import get_llm_client

        client = get_llm_client("cognitive")
        # 간단한 테스트 (실제 호출 X)
        if client:
            return {
                "status": "ok",
                "message": "LLM client configured",
            }
        return {
            "status": "warning",
            "message": "LLM client not configured",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"LLM error: {str(e)}",
        }


def _check_websocket() -> dict[str, Any]:
    """WebSocket 상태 체크"""
    try:
        manager = get_connection_manager()
        return {
            "status": "ok",
            "message": f"Active connections: {manager.get_connection_count()}",
            "connections": manager.get_connection_count(),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"WebSocket error: {str(e)}",
        }


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """기본 헬스체크"""
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
    )


@router.get("/ready", response_model=HealthDetailResponse)
async def readiness_check() -> HealthDetailResponse:
    """Readiness 체크 (의존성 확인)"""
    # 병렬로 체크 실행
    db_check, llm_check = await asyncio.gather(
        _check_database(),
        _check_llm(),
    )

    checks = {
        "database": db_check,
        "llm": llm_check,
        "websocket": _check_websocket(),
    }

    # 전체 상태 결정
    statuses = [c["status"] for c in checks.values()]
    if all(s == "ok" for s in statuses):
        overall_status = "ok"
    elif any(s == "error" for s in statuses):
        overall_status = "degraded"
    else:
        overall_status = "warning"

    return HealthDetailResponse(
        status=overall_status,
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
        checks=checks,
    )


@router.get("/live", response_model=HealthResponse)
async def liveness_check() -> HealthResponse:
    """Liveness 체크 (프로세스 생존 확인)"""
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
    )


@router.get("/metrics")
async def get_metrics() -> dict[str, Any]:
    """간단한 메트릭 반환"""
    from app.dream_agent.workflow_managers.learning_manager import get_trace_logger

    trace_logger = get_trace_logger()

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "websocket_connections": get_connection_manager().get_connection_count(),
        "layer_stats": trace_logger.get_layer_stats(),
    }
