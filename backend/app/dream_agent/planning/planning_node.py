"""Planning Layer Node (Mock)

Phase 1: Mock 구현
Phase 2: 실제 LLM 연동 + Tool Catalog

Reference: docs/specs/ARCHITECTURE.md#Planning-Layer
"""

from typing import Any

from langgraph.types import Command

from app.core.logging import get_logger
from app.dream_agent.models import (
    ExecutionStrategy,
    Intent,
    Plan,
    PlanStatus,
    TodoItem,
)
from app.dream_agent.schemas import PlanningOutput
from app.dream_agent.states.agent_state import AgentState

logger = get_logger(__name__)


async def planning_node(state: AgentState) -> Command[Any]:
    """Planning Layer 노드 함수

    역할:
    1. Tool Registry 조회
    2. LLM으로 Plan 생성
    3. 의존성 그래프 검증
    4. (Phase 3) interrupt()로 Plan 승인 요청

    Args:
        state: 현재 AgentState

    Returns:
        Command with plan, todos update and goto="execution"
    """
    logger.info(
        "Planning node started",
        session_id=state.get("session_id"),
    )

    session_id = state.get("session_id", "")
    cognitive_result = state.get("cognitive_result", {})

    # Intent 복원 (from dict)
    intent_data = cognitive_result.get("intent", {})

    # === Phase 1: Mock 구현 ===
    # 실제 구현에서는 LLM + Tool Catalog로 Plan 생성

    # Mock Todos
    todo_1 = TodoItem(
        task="데이터 수집",
        description="리뷰 데이터를 수집합니다.",
        tool="collector",
        tool_params={"source": "naver", "limit": 100},
        priority=1,
        depends_on=[],
    )

    todo_2 = TodoItem(
        task="데이터 전처리",
        description="수집된 데이터를 정제합니다.",
        tool="preprocessor",
        tool_params={},
        priority=2,
        depends_on=[todo_1.id],
    )

    todo_3 = TodoItem(
        task="감성 분석",
        description="감성 분석을 수행합니다.",
        tool="sentiment_analyzer",
        tool_params={"model": "default"},
        priority=3,
        depends_on=[todo_2.id],
    )

    todos = [todo_1, todo_2, todo_3]

    # Mock Plan
    plan = Plan(
        session_id=session_id,
        status=PlanStatus.APPROVED,  # Phase 1에서는 자동 승인
        todos=todos,
        dependency_graph={
            todo_1.id: [],
            todo_2.id: [todo_1.id],
            todo_3.id: [todo_2.id],
        },
        strategy=ExecutionStrategy.SEQUENTIAL,
        estimated_duration_sec=60,
        estimated_cost_usd=0.0,
        intent_summary=cognitive_result.get("context_summary", ""),
    )

    output = PlanningOutput(
        plan=plan,
        requires_approval=False,  # Phase 1에서는 자동 승인
        approval_message="실행 계획이 생성되었습니다.",
    )

    logger.info(
        "Planning node completed",
        session_id=session_id,
        plan_id=plan.plan_id,
        todo_count=len(todos),
    )

    return Command(
        update={
            "planning_result": output.model_dump(),
            "plan": plan.model_dump(),
            "todos": [t.model_dump() for t in todos],
        },
        goto="execution",
    )
