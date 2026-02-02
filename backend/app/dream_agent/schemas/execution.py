"""Execution Layer I/O Schema

Execution Layer의 입출력 스키마를 정의합니다.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from ..models.todo import TodoItem
from ..models.execution import ExecutionResult, ExecutionContext


class ExecutionInput(BaseModel):
    """Execution Layer 입력"""
    todo: TodoItem
    context: ExecutionContext
    previous_results: Dict[str, Any] = Field(default_factory=dict)
    use_mock: bool = False


class ExecutionOutput(BaseModel):
    """Execution Layer 출력"""
    result: ExecutionResult
    updated_todo: TodoItem
    intermediate_data: Dict[str, Any] = Field(default_factory=dict)
    # 다음 실행을 위한 정보
    next_todos: List[str] = Field(default_factory=list)
    requires_user_input: bool = False
    user_input_message: Optional[str] = None
