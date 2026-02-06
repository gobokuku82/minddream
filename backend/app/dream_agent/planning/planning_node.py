"""Planning Layer Node

실제 LLM 연동 구현 (Phase 2)

Reference: docs/specs/ARCHITECTURE.md#Planning-Layer
"""

import time
from typing import Any

from langgraph.types import Command

from app.core.logging import get_logger
from app.dream_agent.models import Intent, IntentDomain, PlanStatus
from app.dream_agent.planning.dependency import DependencyResolver
from app.dream_agent.planning.planner import PlanGenerator
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
    start_time = time.time()

    logger.info(
        "Planning node started",
        session_id=state.get("session_id"),
    )

    session_id = state.get("session_id", "")
    cognitive_result = state.get("cognitive_result", {})

    # 컴포넌트 초기화
    planner = PlanGenerator()
    resolver = DependencyResolver()

    try:
        # Intent 복원
        intent = _restore_intent(cognitive_result)

        # 사용 가능한 도구 목록 (TODO: Tool Registry에서 조회)
        available_tools = cognitive_result.get("suggested_tools", [])

        # 1. 계획 생성 (LLM 호출)
        raw_result = await planner.generate(
            intent=intent,
            session_id=session_id,
            available_tools=available_tools if available_tools else None,
        )

        # 2. Plan 모델로 변환
        plan = planner.parse_result(raw_result, intent, session_id)

        # 3. 의존성 검증
        is_valid, errors = resolver.validate_dependencies(plan)

        if not is_valid:
            logger.warning(
                "Plan validation failed",
                session_id=session_id,
                errors=errors,
            )
            # 에러가 있어도 일단 진행 (TODO: 에러 처리 강화)

        # 4. Plan 상태 업데이트 (Phase 2: 자동 승인)
        plan = plan.model_copy(update={"status": PlanStatus.APPROVED})

        # 5. 출력 생성
        output = PlanningOutput(
            plan=plan,
            requires_approval=False,  # Phase 3에서 True로 변경
            approval_message="실행 계획이 생성되었습니다.",
        )

        processing_time = (time.time() - start_time) * 1000

        logger.info(
            "Planning node completed",
            session_id=session_id,
            plan_id=plan.plan_id,
            todo_count=len(plan.todos),
            strategy=plan.strategy.value,
            processing_time_ms=processing_time,
        )

        return Command(
            update={
                "planning_result": output.model_dump(),
                "plan": plan.model_dump(),
                "todos": [t.model_dump() for t in plan.todos],
            },
            goto="execution",
        )

    except Exception as e:
        logger.error(
            "Planning node failed",
            session_id=session_id,
            error=str(e),
        )

        # 폴백: 기본 계획 생성
        from app.dream_agent.models import ExecutionStrategy, Plan, TodoItem

        fallback_todo = TodoItem(
            task="요청 처리",
            description="기본 처리",
            tool="default_handler",
            tool_params={},
            priority=5,
        )

        fallback_plan = Plan(
            session_id=session_id,
            status=PlanStatus.APPROVED,
            todos=[fallback_todo],
            dependency_graph={fallback_todo.id: []},
            strategy=ExecutionStrategy.SINGLE,
            intent_summary=cognitive_result.get("context_summary", ""),
        )

        output = PlanningOutput(
            plan=fallback_plan,
            requires_approval=False,
            approval_message="기본 계획으로 진행합니다.",
        )

        return Command(
            update={
                "planning_result": output.model_dump(),
                "plan": fallback_plan.model_dump(),
                "todos": [fallback_todo.model_dump()],
                "error": f"Planning layer error: {str(e)}",
            },
            goto="execution",
        )


def _restore_intent(cognitive_result: dict[str, Any]) -> Intent:
    """cognitive_result에서 Intent 복원

    Args:
        cognitive_result: Cognitive 레이어 결과

    Returns:
        Intent 모델
    """
    intent_data = cognitive_result.get("intent", {})

    # Domain 파싱
    domain_str = intent_data.get("domain", "inquiry")
    try:
        domain = IntentDomain(domain_str)
    except ValueError:
        domain = IntentDomain.INQUIRY

    # Entity 복원
    from app.dream_agent.models import Entity

    entities = []
    for e in intent_data.get("entities", []):
        entities.append(
            Entity(
                type=e.get("type", "unknown"),
                value=e.get("value", ""),
                confidence=e.get("confidence", 0.5),
            )
        )

    return Intent(
        domain=domain,
        category=None,  # 간소화
        subcategory=intent_data.get("subcategory"),
        confidence=intent_data.get("confidence", 0.5),
        entities=entities,
        summary=intent_data.get("summary", ""),
        plan_hint=intent_data.get("plan_hint", ""),
        raw_input=intent_data.get("raw_input", ""),
        language=intent_data.get("language", "ko"),
    )
