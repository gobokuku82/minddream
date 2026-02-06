"""Tool Models

Reference: docs/specs/DATA_MODELS.md#Tool-Models
"""

from typing import Any, Optional

from pydantic import BaseModel, Field

from app.dream_agent.models.enums import ToolCategory, ToolParameterType


class ToolParameter(BaseModel):
    """도구 파라미터 정의"""

    name: str
    type: ToolParameterType
    required: bool = False
    default: Optional[Any] = None
    description: str = ""


class ToolSpec(BaseModel):
    """도구 명세 (YAML에서 로드)"""

    name: str
    description: str
    category: ToolCategory
    executor: str  # executor class path

    # Parameters
    parameters: list[ToolParameter] = Field(default_factory=list)

    # Execution
    timeout_sec: int = 300
    max_retries: int = 3

    # Dependencies
    dependencies: list[str] = Field(default_factory=list)  # 선행 도구
    produces: list[str] = Field(default_factory=list)  # 산출물 키

    # Approval
    requires_approval: bool = False

    # Cost
    has_cost: bool = False
    estimated_cost_usd: float = 0.0
