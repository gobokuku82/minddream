"""HITL Models

Reference: docs/specs/DATA_MODELS.md#HITL-Models
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator

from app.dream_agent.models.enums import HITLRequestType


class HITLRequest(BaseModel):
    """HITL 요청"""

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    type: HITLRequestType

    # Request Data
    message: str
    data: dict[str, Any] = Field(default_factory=dict)

    # Options
    options: list[str] = Field(default_factory=list)  # ["approve", "modify", "reject"]
    input_type: Optional[str] = None  # text, choice, number

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    timeout_sec: int = 300
    timeout_at: Optional[datetime] = None

    @model_validator(mode="after")
    def set_timeout(self) -> "HITLRequest":
        if self.timeout_at is None:
            object.__setattr__(
                self,
                "timeout_at",
                self.created_at + timedelta(seconds=self.timeout_sec),
            )
        return self

    def is_expired(self) -> bool:
        """요청 만료 여부 확인"""
        if self.timeout_at is None:
            return False
        return datetime.utcnow() > self.timeout_at


class HITLResponse(BaseModel):
    """HITL 응답"""

    request_id: str
    action: str  # approve, reject, skip, modify, etc.
    value: Optional[Any] = None  # 입력값
    comment: Optional[str] = None
    responded_at: datetime = Field(default_factory=datetime.utcnow)
