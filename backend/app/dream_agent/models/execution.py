"""Execution Models

Reference: docs/specs/DATA_MODELS.md#Execution-Models
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ExecutionResult(BaseModel):
    """도구 실행 결과"""

    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

    # Metadata
    todo_id: str
    tool: str
    started_at: datetime
    completed_at: datetime
    execution_time_ms: float = 0.0

    # Resource Usage
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None


class ExecutionContext(BaseModel):
    """실행 컨텍스트 (도구에 전달)"""

    session_id: str
    plan_id: str
    language: str = "ko"

    # 이전 Todo 결과 참조
    previous_results: dict[str, Any] = Field(default_factory=dict)

    # 공유 데이터
    collected_data: Optional[dict[str, Any]] = None
    preprocessed_data: Optional[dict[str, Any]] = None

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)
