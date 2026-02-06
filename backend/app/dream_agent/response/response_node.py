"""Response Layer Node

실제 구현 (Phase 2)

Reference: docs/specs/ARCHITECTURE.md#Response-Layer
"""

import time
from typing import Any

from langgraph.graph import END
from langgraph.types import Command

from app.core.logging import get_logger
from app.dream_agent.models import Intent, IntentDomain
from app.dream_agent.response.aggregator import ResultAggregator
from app.dream_agent.response.formatter import FormatDecider, ResponseFormatter
from app.dream_agent.schemas import ResponseOutput
from app.dream_agent.states.agent_state import AgentState

logger = get_logger(__name__)


async def response_node(state: AgentState) -> Command[Any]:
    """Response Layer 노드 함수

    역할:
    1. 모든 실행 결과 집계
    2. 출력 포맷 결정 (text, image, pdf 등)
    3. 응답 생성

    Args:
        state: 현재 AgentState

    Returns:
        Command with response_result update and goto=END
    """
    start_time = time.time()

    logger.info(
        "Response node started",
        session_id=state.get("session_id"),
    )

    session_id = state.get("session_id", "")
    execution_results = state.get("execution_results", {})
    cognitive_result = state.get("cognitive_result", {})
    todos = state.get("todos", [])
    language = state.get("language", "ko")

    # 컴포넌트 초기화
    aggregator = ResultAggregator()
    format_decider = FormatDecider()
    formatter = ResponseFormatter()

    try:
        # Intent 복원
        intent = _restore_intent(cognitive_result)

        # 1. 결과 집계
        aggregated = aggregator.aggregate(execution_results)

        # 2. 포맷 결정
        format_type = format_decider.decide(intent, execution_results)

        # 3. 요약 생성 (LLM)
        summary_result = await aggregator.summarize(
            aggregated=aggregated,
            intent=intent,
            language=language,
        )

        # 4. 응답 포맷팅
        response = formatter.format(
            format_type=summary_result.get("format", format_type),
            content=summary_result,
            intent=intent,
            language=language,
        )

        # 메타데이터 추가
        completed_count = sum(1 for t in todos if t.get("status") == "completed")
        response = response.model_copy(
            update={
                "metadata": {
                    **response.metadata,
                    "completed_todos": completed_count,
                    "total_todos": len(todos),
                    "processing_time_ms": (time.time() - start_time) * 1000,
                }
            }
        )

        output = ResponseOutput(
            response=response,
            report_paths=[],
        )

        logger.info(
            "Response node completed",
            session_id=session_id,
            format=response.format,
            completed_todos=completed_count,
            processing_time_ms=(time.time() - start_time) * 1000,
        )

        return Command(
            update={"response_result": output.model_dump()},
            goto=END,
        )

    except Exception as e:
        logger.error(
            "Response node failed",
            session_id=session_id,
            error=str(e),
        )

        # 폴백 응답
        from app.dream_agent.models import ResponsePayload

        completed_count = sum(1 for t in todos if t.get("status") == "completed")

        fallback_response = ResponsePayload(
            format="text",
            text=f"작업이 완료되었습니다. ({completed_count}/{len(todos)} 완료)",
            summary="작업 완료",
            attachments=[],
            next_actions=[],
            metadata={"error": str(e)},
        )

        output = ResponseOutput(
            response=fallback_response,
            report_paths=[],
        )

        return Command(
            update={
                "response_result": output.model_dump(),
                "error": f"Response layer error: {str(e)}",
            },
            goto=END,
        )


def _restore_intent(cognitive_result: dict[str, Any]) -> Intent:
    """cognitive_result에서 Intent 복원"""
    intent_data = cognitive_result.get("intent", {})

    domain_str = intent_data.get("domain", "inquiry")
    try:
        domain = IntentDomain(domain_str)
    except ValueError:
        domain = IntentDomain.INQUIRY

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
        category=None,
        subcategory=intent_data.get("subcategory"),
        confidence=intent_data.get("confidence", 0.5),
        entities=entities,
        summary=intent_data.get("summary", ""),
        plan_hint=intent_data.get("plan_hint", ""),
        raw_input=intent_data.get("raw_input", ""),
        language=intent_data.get("language", "ko"),
    )
