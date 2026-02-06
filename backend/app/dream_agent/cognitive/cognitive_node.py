"""Cognitive Layer Node (Mock)

Phase 1: Mock 구현
Phase 2: 실제 LLM 연동

Reference: docs/specs/ARCHITECTURE.md#Cognitive-Layer
"""

from typing import Any

from langgraph.types import Command

from app.core.logging import get_logger
from app.dream_agent.models import Entity, Intent, IntentDomain
from app.dream_agent.schemas import CognitiveOutput
from app.dream_agent.states.agent_state import AgentState

logger = get_logger(__name__)


async def cognitive_node(state: AgentState) -> Command[Any]:
    """Cognitive Layer 노드 함수

    역할:
    1. 사용자 의도 분류 (domain → category → subcategory)
    2. 엔티티 추출
    3. 모호성 탐지 (필요시 interrupt로 질문)

    Args:
        state: 현재 AgentState

    Returns:
        Command with cognitive_result update and goto="planning"
    """
    logger.info(
        "Cognitive node started",
        session_id=state.get("session_id"),
        user_input=state.get("user_input", "")[:100],
    )

    user_input = state.get("user_input", "")
    language = state.get("language", "ko")

    # === Phase 1: Mock 구현 ===
    # 실제 구현에서는 LLM을 사용하여 의도 분류
    mock_intent = Intent(
        domain=IntentDomain.ANALYSIS,
        category=None,
        subcategory=None,
        confidence=0.85,
        entities=[
            Entity(type="brand", value="테스트 브랜드", confidence=0.9),
        ],
        summary=f"사용자 요청: {user_input[:50]}...",
        plan_hint="데이터 수집 및 분석이 필요합니다.",
        raw_input=user_input,
        language=language,
    )

    output = CognitiveOutput(
        intent=mock_intent,
        requires_clarification=False,
        clarification_question=None,
        context_summary=f"사용자가 분석을 요청했습니다.",
        processing_time_ms=100.0,
        suggested_tools=["collector", "analyzer"],
    )

    logger.info(
        "Cognitive node completed",
        session_id=state.get("session_id"),
        intent_domain=mock_intent.domain.value,
        confidence=mock_intent.confidence,
    )

    return Command(
        update={"cognitive_result": output.model_dump()},
        goto="planning",
    )
