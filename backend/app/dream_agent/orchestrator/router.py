"""Graph Routing Functions

조건부 라우팅 함수 정의
"""

from typing import Literal

from app.dream_agent.states.agent_state import AgentState


def route_after_cognitive(
    state: AgentState,
) -> Literal["planning", "__end__"]:
    """Cognitive 후 라우팅

    Args:
        state: 현재 상태

    Returns:
        다음 노드 이름
    """
    # 에러 발생 시 종료
    if state.get("error"):
        return "__end__"

    # 명확화 필요 시 (HITL로 처리됨)
    cognitive_result = state.get("cognitive_result", {})
    if cognitive_result.get("requires_clarification"):
        # interrupt()로 처리되므로 여기 도달하면 명확화 완료된 상태
        pass

    return "planning"


def route_after_planning(
    state: AgentState,
) -> Literal["execution", "__end__"]:
    """Planning 후 라우팅

    Args:
        state: 현재 상태

    Returns:
        다음 노드 이름
    """
    # 에러 발생 시 종료
    if state.get("error"):
        return "__end__"

    return "execution"


def route_after_execution(
    state: AgentState,
) -> Literal["execution", "response", "__end__"]:
    """Execution 후 라우팅

    Args:
        state: 현재 상태

    Returns:
        다음 노드 이름
    """
    # 에러 발생 시 종료
    if state.get("error"):
        return "__end__"

    # 모든 Todo 완료 확인
    todos = state.get("todos", [])
    if not todos:
        return "response"

    pending_count = sum(
        1 for t in todos
        if t.get("status") in ("pending", "in_progress", "blocked")
    )

    if pending_count == 0:
        return "response"

    # 아직 실행할 Todo가 있음
    return "execution"


def should_continue_execution(state: AgentState) -> bool:
    """실행 계속 여부 판단

    Args:
        state: 현재 상태

    Returns:
        True면 실행 계속
    """
    if state.get("error"):
        return False

    todos = state.get("todos", [])
    if not todos:
        return False

    # 실행 가능한 Todo가 있는지 확인
    completed_ids = {
        t["id"] for t in todos
        if t.get("status") == "completed"
    }

    for todo in todos:
        if todo.get("status") != "pending":
            continue

        # 의존성 확인
        depends_on = todo.get("depends_on", [])
        if all(dep_id in completed_ids for dep_id in depends_on):
            return True

    return False
