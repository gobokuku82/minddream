"""Execution Layer Node (Mock)

Phase 1: Mock 구현
Phase 2: 실제 Send API 병렬 실행

Reference: docs/specs/ARCHITECTURE.md#Execution-Layer
"""

from datetime import datetime
from typing import Any

from langgraph.types import Command

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionResult
from app.dream_agent.schemas import ExecutionOutput
from app.dream_agent.states.agent_state import AgentState

logger = get_logger(__name__)


async def execution_node(state: AgentState) -> Command[Any]:
    """Execution Layer 노드 함수

    역할:
    1. 실행 가능한 Todo 찾기 (의존성 충족)
    2. Todo 실행 (Phase 2: Send API 병렬)
    3. 결과 저장
    4. 모든 Todo 완료 시 response로

    Args:
        state: 현재 AgentState

    Returns:
        Command with execution_results, todos update
    """
    logger.info(
        "Execution node started",
        session_id=state.get("session_id"),
    )

    session_id = state.get("session_id", "")
    todos = state.get("todos", [])
    execution_results = state.get("execution_results", {})

    # 완료된 Todo IDs
    completed_ids = {
        t["id"] for t in todos
        if t.get("status") == "completed"
    }

    # 실행 가능한 Todo 찾기 (pending + 의존성 충족)
    ready_todos = []
    for todo in todos:
        if todo.get("status") != "pending":
            continue

        depends_on = todo.get("depends_on", [])
        if all(dep_id in completed_ids for dep_id in depends_on):
            ready_todos.append(todo)

    if not ready_todos:
        # 실행할 Todo 없음 → response로
        logger.info(
            "No ready todos, moving to response",
            session_id=session_id,
        )

        output = ExecutionOutput(
            results={k: ExecutionResult(**v) for k, v in execution_results.items()},
            updated_todos=[],
            all_completed=True,
            has_failures=False,
        )

        return Command(
            update={"execution_results": output.results},
            goto="response",
        )

    # === Phase 1: Mock 실행 ===
    # 첫 번째 ready todo만 실행 (Phase 2에서는 Send API로 병렬)
    todo = ready_todos[0]
    todo_id = todo["id"]

    logger.info(
        "Executing todo",
        session_id=session_id,
        todo_id=todo_id,
        tool=todo.get("tool"),
    )

    # Mock 실행 결과
    now = datetime.utcnow()
    result = ExecutionResult(
        success=True,
        data={"mock": True, "message": f"Tool {todo.get('tool')} executed successfully"},
        error=None,
        todo_id=todo_id,
        tool=todo.get("tool", "unknown"),
        started_at=now,
        completed_at=now,
        execution_time_ms=50.0,
    )

    # Todo 상태 업데이트
    updated_todo = {
        **todo,
        "status": "completed",
        "result": result.data,
        "completed_at": now.isoformat(),
        "version": todo.get("version", 1) + 1,
    }

    # 남은 pending 확인
    remaining_pending = sum(
        1 for t in todos
        if t["id"] != todo_id and t.get("status") == "pending"
    )

    next_node = "execution" if remaining_pending > 0 else "response"

    logger.info(
        "Todo completed",
        session_id=session_id,
        todo_id=todo_id,
        remaining_pending=remaining_pending,
        next_node=next_node,
    )

    return Command(
        update={
            "execution_results": {todo_id: result.model_dump()},
            "todos": [updated_todo],
        },
        goto=next_node,
    )
