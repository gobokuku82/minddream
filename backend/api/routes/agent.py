"""Agent Routes

Reference: docs/specs/API_SPEC.md#agent
"""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from api.schemas.request import AgentRunRequest
from api.schemas.response import AgentRunResponse
from app.core.errors import AgentError
from app.core.logging import get_logger
from app.dream_agent.orchestrator import get_agent
from app.dream_agent.states.agent_state import create_initial_state

router = APIRouter(prefix="/agent", tags=["Agent"])
logger = get_logger(__name__)


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(request: AgentRunRequest) -> AgentRunResponse:
    """동기 에이전트 실행

    Args:
        request: 에이전트 실행 요청

    Returns:
        에이전트 실행 결과
    """
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())

    logger.info(
        "Agent run started",
        session_id=session_id,
        message_length=len(request.message),
    )

    try:
        # Get agent
        agent = await get_agent()

        # Create initial state
        initial_state = create_initial_state(
            session_id=session_id,
            user_input=request.message,
            language=request.language,
        )

        # Run config
        config = {"configurable": {"thread_id": session_id}}

        # Execute agent
        result = await agent.ainvoke(initial_state, config=config)

        # Extract response
        response_result = result.get("response_result", {})
        response_data = response_result.get("response", {})

        logger.info(
            "Agent run completed",
            session_id=session_id,
        )

        return AgentRunResponse(
            success=True,
            session_id=session_id,
            response=response_data,
            error=None,
        )

    except AgentError as e:
        logger.error(
            "Agent error",
            session_id=session_id,
            error_code=e.code.value,
            error_message=e.message,
        )
        return AgentRunResponse(
            success=False,
            session_id=session_id,
            response={},
            error=e.to_detail().model_dump(),
        )

    except Exception as e:
        logger.exception(
            "Unexpected error",
            session_id=session_id,
        )
        raise HTTPException(
            status_code=500,
            detail={"code": "E5003", "message": str(e)},
        )


@router.get("/status/{session_id}")
async def get_agent_status(session_id: str) -> dict[str, Any]:
    """에이전트 세션 상태 조회

    Args:
        session_id: 세션 ID

    Returns:
        세션 상태
    """
    # TODO: 실제 상태 조회 구현
    return {
        "session_id": session_id,
        "status": "unknown",
        "message": "Status check not implemented yet",
    }


@router.post("/stop/{session_id}")
async def stop_agent(session_id: str) -> dict[str, Any]:
    """에이전트 실행 중지

    Args:
        session_id: 세션 ID

    Returns:
        중지 결과
    """
    # TODO: 실제 중지 구현
    logger.info("Agent stop requested", session_id=session_id)

    return {
        "session_id": session_id,
        "status": "stopped",
        "message": "Stop not implemented yet",
    }
