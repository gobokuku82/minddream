"""Cognitive Layer I/O Schemas

Reference: docs/specs/DATA_MODELS.md#CognitiveOutput
"""

from typing import Any, Optional

from pydantic import BaseModel, Field

from app.dream_agent.models import Intent


class CognitiveInput(BaseModel):
    """Cognitive Layer 입력"""

    user_input: str
    language: str = "ko"
    session_id: str
    context: Optional[dict[str, Any]] = None  # 이전 대화 맥락


class CognitiveOutput(BaseModel):
    """Cognitive Layer 출력"""

    intent: Intent
    requires_clarification: bool = False
    clarification_question: Optional[str] = None
    context_summary: str = ""
    processing_time_ms: float = 0.0

    # V2: 다음 레이어 힌트
    suggested_tools: list[str] = Field(default_factory=list)
