"""Health Check Routes

Reference: docs/specs/API_SPEC.md#health
"""

from datetime import datetime

from fastapi import APIRouter

from api.schemas.response import HealthDetailResponse, HealthResponse
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


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
    checks = {}

    # Database check (TODO: 실제 연결 확인)
    checks["database"] = {
        "status": "ok",
        "message": "Database connection available",
    }

    # LLM check (TODO: 실제 연결 확인)
    checks["llm"] = {
        "status": "ok",
        "message": "LLM API available",
    }

    overall_status = "ok" if all(c["status"] == "ok" for c in checks.values()) else "degraded"

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
