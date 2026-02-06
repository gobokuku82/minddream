"""TodoItem Model

Reference: docs/specs/DATA_MODELS.md#Todo-Models
"""

import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Valid status transitions
VALID_TRANSITIONS: dict[str, list[str]] = {
    "pending": ["in_progress", "blocked", "needs_approval", "cancelled", "skipped"],
    "blocked": ["pending", "cancelled"],
    "needs_approval": ["pending", "cancelled", "skipped"],
    "in_progress": ["completed", "failed"],
    "completed": [],      # final
    "failed": ["pending", "skipped", "cancelled"],  # retry 가능
    "skipped": [],        # final
    "cancelled": [],      # final
}


def validate_transition(current: str, target: str) -> bool:
    """상태 전환 유효성 검사"""
    return target in VALID_TRANSITIONS.get(current, [])


class TodoItem(BaseModel):
    """Todo 아이템 V2 (Immutable)

    V2 Changes:
    - frozen=True: 불변성 보장, 수정 시 새 버전 생성
    - layer: 4개로 통합 (cognitive, planning, execution, response)
    - Flat 구조: metadata 중첩 제거
    """

    model_config = ConfigDict(frozen=True)

    # === Identity ===
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plan_id: Optional[str] = None

    # === Basic Info ===
    task: str  # 작업 설명
    description: Optional[str] = None

    # === Execution ===
    tool: str  # 실행할 도구명
    tool_params: dict[str, Any] = Field(default_factory=dict)

    # === Classification (V2) ===
    layer: Literal["execution"] = "execution"

    # === Status ===
    status: Literal[
        "pending", "in_progress", "completed", "failed",
        "blocked", "skipped", "needs_approval", "cancelled"
    ] = "pending"
    priority: int = Field(default=5, ge=0, le=10)

    # === Dependencies ===
    depends_on: list[str] = Field(default_factory=list)

    # === Execution Config ===
    timeout_sec: int = 300
    max_retries: int = 3
    retry_count: int = 0

    # === Approval ===
    requires_approval: bool = False

    # === Result ===
    result: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None

    # === Timestamps ===
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # === Version ===
    version: int = 1

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: int) -> int:
        if not 0 <= v <= 10:
            raise ValueError("Priority must be between 0 and 10")
        return v

    @field_validator("tool")
    @classmethod
    def validate_tool(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Tool name cannot be empty")
        return v.strip().lower()

    def with_status(self, new_status: str, **kwargs: Any) -> "TodoItem":
        """상태 변경된 새 인스턴스 반환"""
        return self.model_copy(
            update={"status": new_status, "version": self.version + 1, **kwargs}
        )

    def with_result(self, result: dict[str, Any]) -> "TodoItem":
        """결과가 포함된 새 인스턴스 반환"""
        return self.model_copy(
            update={
                "status": "completed",
                "result": result,
                "completed_at": datetime.utcnow(),
                "version": self.version + 1,
            }
        )

    def with_error(self, error_message: str) -> "TodoItem":
        """에러가 포함된 새 인스턴스 반환"""
        return self.model_copy(
            update={
                "status": "failed",
                "error_message": error_message,
                "completed_at": datetime.utcnow(),
                "retry_count": self.retry_count + 1,
                "version": self.version + 1,
            }
        )
