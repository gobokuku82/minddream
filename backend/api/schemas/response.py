"""API Response Schemas

Reference: docs/specs/API_SPEC.md
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class AgentRunResponse(BaseModel):
    """에이전트 실행 응답"""

    success: bool = Field(..., description="성공 여부")
    session_id: str = Field(..., description="세션 ID")
    response: dict[str, Any] = Field(default_factory=dict, description="응답 데이터")
    error: Optional[dict[str, Any]] = Field(None, description="에러 정보")


class AgentRunAsyncResponse(BaseModel):
    """에이전트 비동기 실행 응답"""

    session_id: str = Field(..., description="세션 ID")
    websocket_url: str = Field(..., description="WebSocket URL")
    status: str = Field("started", description="상태")


class SessionStatusResponse(BaseModel):
    """세션 상태 응답"""

    session_id: str
    status: str
    current_layer: Optional[str] = None
    progress: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    """헬스체크 응답"""

    status: str = Field("ok", description="상태")
    version: str = Field(..., description="버전")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthDetailResponse(BaseModel):
    """상세 헬스체크 응답"""

    status: str = Field("ok", description="상태")
    version: str = Field(..., description="버전")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: dict[str, dict[str, Any]] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """에러 응답"""

    success: bool = False
    error: dict[str, Any] = Field(..., description="에러 정보")
