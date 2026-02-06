"""Execution Layer Node

실제 구현 (Phase 2)

Reference: docs/specs/ARCHITECTURE.md#Execution-Layer
"""

from datetime import datetime
from typing import Any

from langgraph.types import Command

from app.core.logging import get_logger
from app.dream_agent.execution.strategy import ExecutionCoordinator, StrategyDecider
from app.dream_agent.execution.supervisor import ExecutionSupervisor
from app.dream_agent.models import ExecutionContext, ExecutionResult, Plan, TodoItem
from app.dream_agent.states.agent_state import AgentState

logger = get_logger(__name__)


async def execution_node(state: AgentState) -> Command[Any]:
    """Execution Layer 노드 함수

    역할:
    1. 실행 가능한 Todo 찾기 (의존성 충족)
    2. Todo 실행 (Supervisor 통해)
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
    plan_data = state.get("plan", {})
    todos_data = state.get("todos", [])
    execution_results = state.get("execution_results", {})

    # 컴포넌트 초기화
    supervisor = ExecutionSupervisor()
    coordinator = ExecutionCoordinator()

    # 완료된 Todo IDs (execution_results에 있는 것 + status가 completed인 것)
    completed_ids = set(execution_results.keys())
    for t in todos_data:
        if t.get("status") == "completed":
            completed_ids.add(t["id"])

    # 실행 가능한 Todo 찾기
    ready_todos = []
    for todo_dict in todos_data:
        # 이미 완료됨
        if todo_dict["id"] in completed_ids:
            continue

        # 상태 확인
        if todo_dict.get("status") not in ("pending", None):
            continue

        # 의존성 확인
        depends_on = todo_dict.get("depends_on", [])
        if all(dep_id in completed_ids for dep_id in depends_on):
            ready_todos.append(todo_dict)

    # 우선순위순 정렬
    ready_todos.sort(key=lambda t: t.get("priority", 5))

    if not ready_todos:
        # 실행할 Todo 없음 → response로
        logger.info(
            "No ready todos, moving to response",
            session_id=session_id,
            completed_count=len(completed_ids),
            total_count=len(todos_data),
        )

        return Command(
            update={},
            goto="response",
        )

    # 실행 컨텍스트 생성
    context = ExecutionContext(
        session_id=session_id,
        plan_id=plan_data.get("plan_id", ""),
        language=state.get("language", "ko"),
        previous_results={k: v.get("data", {}) for k, v in execution_results.items()},
    )

    # 첫 번째 ready todo 실행
    # TODO: Phase 2+ 에서 Send API로 병렬 실행
    todo_dict = ready_todos[0]
    todo = _dict_to_todo(todo_dict)

    logger.info(
        "Executing todo",
        session_id=session_id,
        todo_id=todo.id,
        tool=todo.tool,
        ready_count=len(ready_todos),
    )

    # 실행
    result = await supervisor.execute(todo, context)

    # Todo 상태 업데이트
    updated_todo_dict = {
        **todo_dict,
        "status": "completed" if result.success else "failed",
        "result": result.data if result.success else None,
        "error_message": result.error if not result.success else None,
        "completed_at": datetime.utcnow().isoformat(),
        "version": todo_dict.get("version", 1) + 1,
    }

    # 실패 시 재시도 카운트 증가
    if not result.success:
        updated_todo_dict["retry_count"] = todo_dict.get("retry_count", 0) + 1

        # 재시도 가능하면 pending으로 복구
        max_retries = todo_dict.get("max_retries", 3)
        if updated_todo_dict["retry_count"] < max_retries:
            updated_todo_dict["status"] = "pending"
            logger.info(
                "Todo will be retried",
                todo_id=todo.id,
                retry_count=updated_todo_dict["retry_count"],
            )

    # 남은 pending 확인
    new_completed_ids = completed_ids | {todo.id} if result.success else completed_ids
    remaining_pending = sum(
        1 for t in todos_data
        if t["id"] not in new_completed_ids and t.get("status") in ("pending", None)
    )

    # 다음 노드 결정
    next_node = "execution" if remaining_pending > 0 else "response"

    logger.info(
        "Todo execution completed",
        session_id=session_id,
        todo_id=todo.id,
        success=result.success,
        remaining_pending=remaining_pending,
        next_node=next_node,
    )

    return Command(
        update={
            "execution_results": {todo.id: result.model_dump()},
            "todos": [updated_todo_dict],
        },
        goto=next_node,
    )


def _dict_to_todo(todo_dict: dict[str, Any]) -> TodoItem:
    """dict를 TodoItem으로 변환"""
    return TodoItem(
        id=todo_dict["id"],
        plan_id=todo_dict.get("plan_id"),
        task=todo_dict.get("task", ""),
        description=todo_dict.get("description"),
        tool=todo_dict.get("tool", "unknown"),
        tool_params=todo_dict.get("tool_params", {}),
        status=todo_dict.get("status", "pending"),
        priority=todo_dict.get("priority", 5),
        depends_on=todo_dict.get("depends_on", []),
        timeout_sec=todo_dict.get("timeout_sec", 300),
        max_retries=todo_dict.get("max_retries", 3),
        retry_count=todo_dict.get("retry_count", 0),
    )
