"""Domain Models

Pydantic 도메인 모델
"""

from app.dream_agent.models.enums import (
    ExecutionStrategy,
    HITLRequestType,
    IntentCategory,
    IntentDomain,
    Layer,
    PlanStatus,
    SessionStatus,
    TodoStatus,
    ToolCategory,
    ToolParameterType,
)
from app.dream_agent.models.execution import ExecutionContext, ExecutionResult
from app.dream_agent.models.hitl import HITLRequest, HITLResponse
from app.dream_agent.models.intent import Entity, Intent
from app.dream_agent.models.plan import Plan, PlanChange, PlanVersion
from app.dream_agent.models.response import Attachment, ResponsePayload
from app.dream_agent.models.todo import TodoItem, validate_transition
from app.dream_agent.models.tool import ToolParameter, ToolSpec

__all__ = [
    # Enums
    "IntentDomain",
    "IntentCategory",
    "Layer",
    "ExecutionStrategy",
    "TodoStatus",
    "PlanStatus",
    "SessionStatus",
    "HITLRequestType",
    "ToolCategory",
    "ToolParameterType",
    # Intent
    "Entity",
    "Intent",
    # Todo
    "TodoItem",
    "validate_transition",
    # Plan
    "Plan",
    "PlanChange",
    "PlanVersion",
    # Execution
    "ExecutionResult",
    "ExecutionContext",
    # Response
    "ResponsePayload",
    "Attachment",
    # HITL
    "HITLRequest",
    "HITLResponse",
    # Tool
    "ToolSpec",
    "ToolParameter",
]
