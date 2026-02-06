"""HITL Routes

Human-in-the-Loop API 엔드포인트

Reference: docs/specs/HITL_SPEC.md
"""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.dream_agent.models import Plan
from app.dream_agent.workflow_managers.hitl_manager import (
    ApprovalHandler,
    PlanEditor,
    get_hitl_manager,
    get_pause_controller,
)

router = APIRouter(prefix="/hitl", tags=["HITL"])
logger = get_logger(__name__)


# ── Request/Response Schemas ──


class ApproveRequest(BaseModel):
    """승인 요청"""

    comment: Optional[str] = Field(None, description="코멘트")


class ModifyRequest(BaseModel):
    """수정 요청"""

    instruction: str = Field(..., description="자연어 수정 명령")
    comment: Optional[str] = Field(None, description="코멘트")


class InputRequest(BaseModel):
    """입력 요청"""

    value: Any = Field(..., description="입력값")
    comment: Optional[str] = Field(None, description="코멘트")


class HITLStatusResponse(BaseModel):
    """HITL 상태 응답"""

    session_id: str
    has_pending_request: bool
    request_type: Optional[str] = None
    message: Optional[str] = None


class HITLActionResponse(BaseModel):
    """HITL 액션 응답"""

    success: bool
    session_id: str
    action: str
    message: str


# ── Endpoints ──


@router.post("/approve/{session_id}")
async def approve_plan(
    session_id: str,
    request: ApproveRequest,
) -> HITLActionResponse:
    """Plan 승인

    Args:
        session_id: 세션 ID
        request: 승인 요청

    Returns:
        승인 결과
    """
    hitl_manager = get_hitl_manager()
    pending = hitl_manager.get_pending_request(session_id)

    if not pending:
        raise HTTPException(
            status_code=404,
            detail={"code": "E4001", "message": "No pending request"},
        )

    success = hitl_manager.submit_response(
        request_id=pending.request_id,
        action="approve",
        comment=request.comment,
    )

    logger.info("Plan approved", session_id=session_id)

    return HITLActionResponse(
        success=success,
        session_id=session_id,
        action="approve",
        message="Plan approved successfully",
    )


@router.post("/reject/{session_id}")
async def reject_plan(
    session_id: str,
    request: ApproveRequest,
) -> HITLActionResponse:
    """Plan 거부

    Args:
        session_id: 세션 ID
        request: 거부 요청

    Returns:
        거부 결과
    """
    hitl_manager = get_hitl_manager()
    pending = hitl_manager.get_pending_request(session_id)

    if not pending:
        raise HTTPException(
            status_code=404,
            detail={"code": "E4001", "message": "No pending request"},
        )

    success = hitl_manager.submit_response(
        request_id=pending.request_id,
        action="reject",
        comment=request.comment,
    )

    logger.info("Plan rejected", session_id=session_id)

    return HITLActionResponse(
        success=success,
        session_id=session_id,
        action="reject",
        message="Plan rejected",
    )


@router.post("/modify/{session_id}")
async def modify_plan(
    session_id: str,
    request: ModifyRequest,
) -> HITLActionResponse:
    """Plan 수정 (자연어 명령)

    Args:
        session_id: 세션 ID
        request: 수정 요청

    Returns:
        수정 결과
    """
    hitl_manager = get_hitl_manager()
    pending = hitl_manager.get_pending_request(session_id)

    if not pending:
        raise HTTPException(
            status_code=404,
            detail={"code": "E4001", "message": "No pending request"},
        )

    # 자연어 명령을 HITL 응답으로 전달
    success = hitl_manager.submit_response(
        request_id=pending.request_id,
        action="modify",
        value=request.instruction,
        comment=request.comment,
    )

    logger.info(
        "Plan modification requested",
        session_id=session_id,
        instruction=request.instruction,
    )

    return HITLActionResponse(
        success=success,
        session_id=session_id,
        action="modify",
        message="Modification request submitted",
    )


@router.post("/input/{session_id}")
async def submit_input(
    session_id: str,
    request: InputRequest,
) -> HITLActionResponse:
    """사용자 입력 제공

    Args:
        session_id: 세션 ID
        request: 입력 요청

    Returns:
        입력 결과
    """
    hitl_manager = get_hitl_manager()
    pending = hitl_manager.get_pending_request(session_id)

    if not pending:
        raise HTTPException(
            status_code=404,
            detail={"code": "E4001", "message": "No pending request"},
        )

    success = hitl_manager.submit_response(
        request_id=pending.request_id,
        action="input",
        value=request.value,
        comment=request.comment,
    )

    logger.info("User input submitted", session_id=session_id)

    return HITLActionResponse(
        success=success,
        session_id=session_id,
        action="input",
        message="Input submitted successfully",
    )


@router.post("/pause/{session_id}")
async def pause_session(session_id: str) -> HITLActionResponse:
    """세션 일시정지

    Args:
        session_id: 세션 ID

    Returns:
        일시정지 결과
    """
    pause_controller = get_pause_controller()
    success = pause_controller.pause(session_id)

    if not success:
        return HITLActionResponse(
            success=False,
            session_id=session_id,
            action="pause",
            message="Session already paused or not running",
        )

    logger.info("Session paused", session_id=session_id)

    return HITLActionResponse(
        success=True,
        session_id=session_id,
        action="pause",
        message="Session paused",
    )


@router.post("/resume/{session_id}")
async def resume_session(session_id: str) -> HITLActionResponse:
    """세션 재개

    Args:
        session_id: 세션 ID

    Returns:
        재개 결과
    """
    pause_controller = get_pause_controller()
    success = pause_controller.resume(session_id)

    if not success:
        return HITLActionResponse(
            success=False,
            session_id=session_id,
            action="resume",
            message="Session not paused",
        )

    logger.info("Session resumed", session_id=session_id)

    return HITLActionResponse(
        success=True,
        session_id=session_id,
        action="resume",
        message="Session resumed",
    )


@router.get("/status/{session_id}")
async def get_hitl_status(session_id: str) -> HITLStatusResponse:
    """HITL 상태 조회

    Args:
        session_id: 세션 ID

    Returns:
        HITL 상태
    """
    hitl_manager = get_hitl_manager()
    pending = hitl_manager.get_pending_request(session_id)

    if pending:
        return HITLStatusResponse(
            session_id=session_id,
            has_pending_request=True,
            request_type=pending.type.value,
            message=pending.message,
        )

    return HITLStatusResponse(
        session_id=session_id,
        has_pending_request=False,
    )


@router.post("/cancel/{session_id}")
async def cancel_request(session_id: str) -> HITLActionResponse:
    """대기 중인 요청 취소

    Args:
        session_id: 세션 ID

    Returns:
        취소 결과
    """
    hitl_manager = get_hitl_manager()
    pending = hitl_manager.get_pending_request(session_id)

    if not pending:
        return HITLActionResponse(
            success=False,
            session_id=session_id,
            action="cancel",
            message="No pending request to cancel",
        )

    success = hitl_manager.cancel_request(pending.request_id)

    logger.info("HITL request cancelled", session_id=session_id)

    return HITLActionResponse(
        success=success,
        session_id=session_id,
        action="cancel",
        message="Request cancelled",
    )
