"""Execution Layer I/O Schemas

Reference: docs/specs/DATA_MODELS.md#ExecutionOutput
"""

from pydantic import BaseModel, Field

from app.dream_agent.models import ExecutionResult, Plan, TodoItem


class ExecutionInput(BaseModel):
    """Execution Layer 입력"""

    plan: Plan
    session_id: str
    language: str = "ko"


class ExecutionOutput(BaseModel):
    """Execution Layer 출력"""

    results: dict[str, ExecutionResult] = Field(default_factory=dict)  # todo_id → result
    updated_todos: list[TodoItem] = Field(default_factory=list)
    all_completed: bool = False
    has_failures: bool = False
