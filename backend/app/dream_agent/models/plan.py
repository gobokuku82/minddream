"""Plan Models

Reference: docs/specs/DATA_MODELS.md#Plan-Models
"""

import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from app.dream_agent.models.enums import ExecutionStrategy, PlanStatus
from app.dream_agent.models.todo import TodoItem


class PlanChange(BaseModel):
    """플랜 변경 이력"""

    change_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    change_type: Literal[
        "create", "add_todo", "remove_todo", "modify_todo",
        "reorder", "approve", "reject", "nl_edit"
    ]
    reason: str
    actor: str = "system"  # system | user | hitl
    affected_todo_ids: list[str] = Field(default_factory=list)
    change_data: dict[str, Any] = Field(default_factory=dict)

    # NL Edit
    user_instruction: Optional[str] = None


class PlanVersion(BaseModel):
    """플랜 버전 스냅샷"""

    version: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    todos_snapshot: list[dict[str, Any]]  # TodoItem.model_dump() 리스트
    change_id: str
    change_summary: str


class Plan(BaseModel):
    """실행 계획"""

    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    version: int = 1
    status: PlanStatus = PlanStatus.DRAFT

    # === Todos ===
    todos: list[TodoItem] = Field(default_factory=list)

    # === Dependency Graph ===
    dependency_graph: dict[str, list[str]] = Field(default_factory=dict)

    # === Execution Strategy (V2) ===
    strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL

    # === Estimates ===
    estimated_duration_sec: int = 0
    estimated_cost_usd: float = 0.0

    # === Visualization ===
    mermaid_diagram: Optional[str] = None

    # === History ===
    versions: list[PlanVersion] = Field(default_factory=list)
    changes: list[PlanChange] = Field(default_factory=list)

    # === Context ===
    intent_summary: str = ""

    # === Timestamps ===
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_dependencies(self) -> "Plan":
        """의존성 순환 검사"""
        if not self.todos:
            return self

        todo_ids = {t.id for t in self.todos}

        for todo in self.todos:
            for dep_id in todo.depends_on:
                if dep_id not in todo_ids:
                    raise ValueError(f"Unknown dependency: {dep_id}")

        if self._has_cycle():
            raise ValueError("Circular dependency detected")

        return self

    def _has_cycle(self) -> bool:
        """DFS로 순환 검사"""
        if not self.todos:
            return False

        # Build adjacency list
        graph: dict[str, list[str]] = {}
        for todo in self.todos:
            graph[todo.id] = todo.depends_on

        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for todo_id in graph:
            if todo_id not in visited:
                if dfs(todo_id):
                    return True

        return False

    def get_ready_todos(self) -> list[TodoItem]:
        """실행 가능한 Todo 목록 (의존성 충족, pending 상태)"""
        completed_ids = {t.id for t in self.todos if t.status == "completed"}
        return [
            t for t in self.todos
            if t.status == "pending"
            and all(dep_id in completed_ids for dep_id in t.depends_on)
        ]

    def get_statistics(self) -> dict[str, int]:
        """Todo 통계"""
        stats: dict[str, int] = {
            "total": 0,
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0,
            "blocked": 0,
            "skipped": 0,
        }
        for todo in self.todos:
            stats["total"] += 1
            if todo.status in stats:
                stats[todo.status] += 1

        return stats

    def get_progress_percentage(self) -> float:
        """진행률 (0.0 ~ 100.0)"""
        if not self.todos:
            return 0.0
        completed = sum(1 for t in self.todos if t.status == "completed")
        return (completed / len(self.todos)) * 100
