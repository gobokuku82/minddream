"""AgentState Definition

LangGraph StateGraph에서 사용되는 상태 컨테이너
TypedDict 기반 (Pydantic BaseModel 아님)

Reference: docs/specs/DATA_MODELS.md#AgentState
"""

from typing import Annotated, Any, Optional

from typing_extensions import TypedDict

from app.dream_agent.states.reducers import (
    results_reducer,
    todo_reducer,
    trace_reducer,
)


class AgentState(TypedDict, total=False):
    """LangGraph 에이전트 상태

    주의: TypedDict입니다 (Pydantic BaseModel 아님!)
    Reducer를 통해 상태가 자동 병합됩니다.

    Attributes:
        session_id: 세션 식별자
        user_input: 사용자 입력
        language: 언어 코드 ("ko", "en", "ja")

        cognitive_result: CognitiveOutput.model_dump()
        planning_result: PlanningOutput.model_dump()
        execution_results: todo_id → ExecutionResult.model_dump()
        response_result: ResponseOutput.model_dump()

        plan: Plan.model_dump()
        todos: TodoItem 리스트 (dict 형태)

        error: 에러 메시지
        hitl_pending: 현재 대기 중인 HITL 요청

        trace: 실행 트레이스 로그 (append-only)
    """

    # ─── Input ───
    session_id: str
    user_input: str
    language: str  # "ko", "en", "ja"

    # ─── Layer Results (구조화된 dict) ───
    cognitive_result: dict[str, Any]
    planning_result: dict[str, Any]
    execution_results: Annotated[dict[str, Any], results_reducer]
    response_result: dict[str, Any]

    # ─── Plan & Todos ───
    plan: dict[str, Any]
    todos: Annotated[list[dict[str, Any]], todo_reducer]

    # ─── Control ───
    error: Optional[str]

    # ─── HITL ───
    hitl_pending: Optional[dict[str, Any]]

    # ─── Learning (비침습적) ───
    trace: Annotated[list[dict[str, Any]], trace_reducer]


def create_initial_state(
    session_id: str,
    user_input: str,
    language: str = "ko",
) -> AgentState:
    """초기 상태 생성

    Args:
        session_id: 세션 ID
        user_input: 사용자 입력
        language: 언어 코드

    Returns:
        초기화된 AgentState
    """
    return AgentState(
        session_id=session_id,
        user_input=user_input,
        language=language,
        cognitive_result={},
        planning_result={},
        execution_results={},
        response_result={},
        plan={},
        todos=[],
        error=None,
        hitl_pending=None,
        trace=[],
    )
