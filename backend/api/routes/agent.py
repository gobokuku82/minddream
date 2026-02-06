"""Agent Routes

Reference: docs/specs/API_SPEC.md#agent
"""

import asyncio
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, WebSocket

from api.schemas.request import AgentRunRequest
from api.schemas.response import AgentRunAsyncResponse, AgentRunResponse
from api.websocket import get_connection_manager, get_websocket_handler
from app.core.errors import AgentError
from app.core.logging import get_logger
from app.dream_agent.orchestrator import get_agent
from app.dream_agent.states.agent_state import create_initial_state
from app.dream_agent.workflow_managers.hitl_manager import get_pause_controller

router = APIRouter(prefix="/agent", tags=["Agent"])
logger = get_logger(__name__)

# 비동기 실행 상태 저장
_async_sessions: dict[str, dict[str, Any]] = {}


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
    pause_controller = get_pause_controller()
    success = pause_controller.pause(session_id, reason="user_stop")

    logger.info("Agent stop requested", session_id=session_id, success=success)

    return {
        "session_id": session_id,
        "status": "stopped" if success else "not_running",
        "message": "Agent stopped" if success else "Session not active",
    }


@router.post("/run-async", response_model=AgentRunAsyncResponse)
async def run_agent_async(
    request: AgentRunRequest,
    background_tasks: BackgroundTasks,
) -> AgentRunAsyncResponse:
    """비동기 에이전트 실행 (백그라운드)

    WebSocket으로 진행 상황 수신

    Args:
        request: 에이전트 실행 요청
        background_tasks: FastAPI BackgroundTasks

    Returns:
        세션 ID와 연결 정보
    """
    session_id = request.session_id or str(uuid.uuid4())

    logger.info(
        "Async agent run started",
        session_id=session_id,
        message_length=len(request.message),
    )

    # 세션 상태 초기화
    _async_sessions[session_id] = {
        "status": "pending",
        "message": request.message,
        "language": request.language,
    }

    # 백그라운드 태스크로 에이전트 실행
    background_tasks.add_task(
        _run_agent_background,
        session_id=session_id,
        message=request.message,
        language=request.language,
    )

    return AgentRunAsyncResponse(
        session_id=session_id,
        status="pending",
        websocket_url=f"/ws/{session_id}",
    )


async def _run_agent_background(
    session_id: str,
    message: str,
    language: str,
) -> None:
    """백그라운드 에이전트 실행"""
    from api.websocket import (
        create_complete,
        create_error,
        create_layer_complete,
        create_layer_start,
    )

    connection_manager = get_connection_manager()

    try:
        _async_sessions[session_id]["status"] = "running"

        # Get agent
        agent = await get_agent()

        # Create initial state
        initial_state = create_initial_state(
            session_id=session_id,
            user_input=message,
            language=language,
        )

        config = {"configurable": {"thread_id": session_id}}

        # Execute with streaming
        async for event in agent.astream_events(initial_state, config=config, version="v2"):
            event_type = event.get("event")

            # 레이어 시작/완료 이벤트 전송
            if event_type == "on_chain_start":
                name = event.get("name", "")
                if name.endswith("_node"):
                    layer = name.replace("_node", "")
                    await connection_manager.send_message(
                        session_id,
                        create_layer_start(layer, session_id),
                    )

            elif event_type == "on_chain_end":
                name = event.get("name", "")
                if name.endswith("_node"):
                    layer = name.replace("_node", "")
                    output = event.get("data", {}).get("output", {})
                    await connection_manager.send_message(
                        session_id,
                        create_layer_complete(layer, output, session_id),
                    )

        # 최종 결과 조회
        final_state = await agent.aget_state(config)
        response_result = final_state.values.get("response_result", {})

        # 완료 메시지 전송
        await connection_manager.send_message(
            session_id,
            create_complete(response_result, session_id),
        )

        _async_sessions[session_id]["status"] = "completed"
        _async_sessions[session_id]["result"] = response_result

        logger.info("Async agent run completed", session_id=session_id)

    except Exception as e:
        logger.exception("Async agent error", session_id=session_id)

        _async_sessions[session_id]["status"] = "failed"
        _async_sessions[session_id]["error"] = str(e)

        await connection_manager.send_message(
            session_id,
            create_error("E5003", str(e), session_id),
        )


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
) -> None:
    """WebSocket 연결 엔드포인트

    Args:
        websocket: WebSocket 연결
        session_id: 세션 ID
    """
    handler = get_websocket_handler()
    await handler.handle_connection(websocket, session_id)
