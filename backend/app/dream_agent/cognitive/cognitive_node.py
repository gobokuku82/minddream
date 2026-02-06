"""Cognitive Layer Node

실제 LLM 연동 구현 (Phase 2)

Reference: docs/specs/ARCHITECTURE.md#Cognitive-Layer
"""

import time
from typing import Any

from langgraph.types import Command, interrupt

from app.core.config import settings
from app.core.logging import get_logger
from app.dream_agent.cognitive.clarifier import Clarifier
from app.dream_agent.cognitive.classifier import IntentClassifier
from app.dream_agent.cognitive.extractor import EntityExtractor
from app.dream_agent.models import HITLRequestType
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
    start_time = time.time()

    logger.info(
        "Cognitive node started",
        session_id=state.get("session_id"),
        user_input=state.get("user_input", "")[:100],
    )

    user_input = state.get("user_input", "")
    language = state.get("language", "ko")
    session_id = state.get("session_id", "")

    # 컴포넌트 초기화
    classifier = IntentClassifier()
    extractor = EntityExtractor()
    clarifier = Clarifier()

    try:
        # 1. 의도 분류 (LLM 호출)
        raw_result = await classifier.classify(
            user_input=user_input,
            language=language,
            context=None,  # TODO: 이전 대화 맥락 연동
        )

        # 2. Intent 모델로 변환
        intent = classifier.parse_result(raw_result, user_input, language)

        # 3. 엔티티 정규화
        normalized_entities = extractor.normalize_entities(
            raw_result.get("entities", [])
        )

        # 4. 모호성 확인
        needs_clarification = clarifier.needs_clarification(intent, raw_result)
        clarification_question = None

        if needs_clarification:
            clarification_question = clarifier.get_clarification_question(intent, raw_result)

            logger.info(
                "Clarification needed",
                session_id=session_id,
                question=clarification_question,
            )

            # HITL interrupt로 사용자에게 질문
            # (Phase 3에서 실제 interrupt 연동)
            # 현재는 질문만 기록하고 진행

        # 5. 출력 생성
        processing_time = (time.time() - start_time) * 1000

        output = CognitiveOutput(
            intent=intent,
            requires_clarification=needs_clarification,
            clarification_question=clarification_question,
            context_summary=raw_result.get("context_summary", ""),
            processing_time_ms=processing_time,
            suggested_tools=_suggest_tools(intent),
        )

        logger.info(
            "Cognitive node completed",
            session_id=session_id,
            intent_domain=intent.domain.value,
            confidence=intent.confidence,
            processing_time_ms=processing_time,
        )

        return Command(
            update={"cognitive_result": output.model_dump()},
            goto="planning",
        )

    except Exception as e:
        logger.error(
            "Cognitive node failed",
            session_id=session_id,
            error=str(e),
        )

        # 에러 발생 시 기본 응답
        from app.dream_agent.models import Intent, IntentDomain

        fallback_intent = Intent(
            domain=IntentDomain.INQUIRY,
            category=None,
            subcategory=None,
            confidence=0.3,
            entities=[],
            summary="의도 분류 실패",
            plan_hint="",
            raw_input=user_input,
            language=language,
        )

        output = CognitiveOutput(
            intent=fallback_intent,
            requires_clarification=True,
            clarification_question="요청을 이해하지 못했습니다. 다시 설명해주시겠어요?",
            context_summary="",
            processing_time_ms=(time.time() - start_time) * 1000,
            suggested_tools=[],
        )

        return Command(
            update={
                "cognitive_result": output.model_dump(),
                "error": f"Cognitive layer error: {str(e)}",
            },
            goto="planning",
        )


def _suggest_tools(intent: Any) -> list[str]:
    """의도 기반 도구 추천

    Args:
        intent: 분류된 의도

    Returns:
        추천 도구 리스트
    """
    domain = intent.domain.value if hasattr(intent.domain, "value") else intent.domain

    tool_suggestions = {
        "analysis": ["collector", "preprocessor", "sentiment_analyzer", "keyword_extractor"],
        "content": ["report_generator", "chart_maker"],
        "operation": ["dashboard_builder", "exporter"],
        "inquiry": [],
    }

    return tool_suggestions.get(domain, [])
