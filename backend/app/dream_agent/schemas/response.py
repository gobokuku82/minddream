"""Response Layer I/O Schemas

Reference: docs/specs/DATA_MODELS.md#ResponseOutput
"""

from pydantic import BaseModel, Field

from app.dream_agent.models import ExecutionResult, Intent, ResponsePayload


class ResponseInput(BaseModel):
    """Response Layer 입력"""

    intent: Intent
    execution_results: dict[str, ExecutionResult] = Field(default_factory=dict)
    session_id: str
    language: str = "ko"


class ResponseOutput(BaseModel):
    """Response Layer 출력"""

    response: ResponsePayload
    report_paths: list[str] = Field(default_factory=list)
