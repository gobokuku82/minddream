"""API Request Schemas

Reference: docs/specs/API_SPEC.md
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    """에이전트 실행 요청"""

    message: str = Field(..., min_length=1, max_length=10000, description="사용자 메시지")
    session_id: Optional[str] = Field(None, description="기존 세션 ID (재개 시)")
    language: str = Field("ko", description="언어 코드")
    config: dict[str, Any] = Field(default_factory=dict, description="추가 설정")


class AgentRunAsyncRequest(BaseModel):
    """에이전트 비동기 실행 요청"""

    message: str = Field(..., min_length=1, max_length=10000, description="사용자 메시지")
    session_id: Optional[str] = Field(None, description="기존 세션 ID (재개 시)")
    language: str = Field("ko", description="언어 코드")
    config: dict[str, Any] = Field(default_factory=dict, description="추가 설정")


class HITLApproveRequest(BaseModel):
    """HITL 승인 요청"""

    approved: bool = Field(..., description="승인 여부")
    modifications: list[dict[str, Any]] = Field(
        default_factory=list, description="수정 사항"
    )
    comment: Optional[str] = Field(None, description="코멘트")


class HITLInputRequest(BaseModel):
    """HITL 입력 요청"""

    value: Any = Field(..., description="입력값")
    comment: Optional[str] = Field(None, description="코멘트")
