"""Response Layer Node (Mock)

Phase 1: Mock 구현
Phase 2: 실제 포맷 결정 + 생성

Reference: docs/specs/ARCHITECTURE.md#Response-Layer
"""

from typing import Any

from langgraph.graph import END
from langgraph.types import Command

from app.core.logging import get_logger
from app.dream_agent.models import ResponsePayload
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
    logger.info(
        "Response node started",
        session_id=state.get("session_id"),
    )

    session_id = state.get("session_id", "")
    execution_results = state.get("execution_results", {})
    cognitive_result = state.get("cognitive_result", {})
    todos = state.get("todos", [])

    # 완료된 Todo 수
    completed_count = sum(1 for t in todos if t.get("status") == "completed")
    total_count = len(todos)

    # === Phase 1: Mock 응답 생성 ===
    # 실제 구현에서는 LLM으로 응답 생성

    intent_summary = cognitive_result.get("context_summary", "요청")

    response = ResponsePayload(
        format="text",
        text=f"""## 분석 완료

{intent_summary}에 대한 처리가 완료되었습니다.

### 실행 결과
- 총 {total_count}개 작업 중 {completed_count}개 완료
- 모든 작업이 성공적으로 수행되었습니다.

### 다음 단계
추가 분석이 필요하시면 말씀해주세요.""",
        summary=f"{total_count}개 작업 완료",
        attachments=[],
        next_actions=["추가 분석", "보고서 생성", "데이터 내보내기"],
        metadata={
            "completed_todos": completed_count,
            "total_todos": total_count,
        },
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
    )

    return Command(
        update={"response_result": output.model_dump()},
        goto=END,
    )
