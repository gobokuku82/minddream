"""Planning Layer I/O Schema

Planning Layer의 입출력 스키마를 정의합니다.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from ..models.intent import Intent
from ..models.todo import TodoItem
from ..models.plan import Plan


class PlanningInput(BaseModel):
    """Planning Layer 입력"""
    intent: Intent
    session_id: str
    context: Dict[str, Any] = Field(default_factory=dict)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    # 기존 Plan이 있는 경우 (재계획)
    existing_plan: Optional[Plan] = None
    replan_instruction: Optional[str] = None


class PlanningOutput(BaseModel):
    """Planning Layer 출력"""
    plan: Plan
    todos: List[TodoItem] = Field(default_factory=list)
    estimated_duration_sec: int = 0
    estimated_cost: float = 0.0
    requires_approval: bool = False
    approval_message: Optional[str] = None
    mermaid_diagram: Optional[str] = None
