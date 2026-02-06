"""Planning Layer I/O Schemas

Reference: docs/specs/DATA_MODELS.md#PlanningOutput
"""

from pydantic import BaseModel, Field

from app.dream_agent.models import Intent, Plan


class PlanningInput(BaseModel):
    """Planning Layer 입력"""

    intent: Intent
    session_id: str
    language: str = "ko"
    suggested_tools: list[str] = Field(default_factory=list)
    context_summary: str = ""


class PlanningOutput(BaseModel):
    """Planning Layer 출력"""

    plan: Plan
    requires_approval: bool = True
    approval_message: str = "실행 계획을 검토해주세요."
