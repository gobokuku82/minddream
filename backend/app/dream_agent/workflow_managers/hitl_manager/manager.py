"""HITL Manager

Human-in-the-Loop 요청/응답 관리

Reference: docs/specs/HITL_SPEC.md
"""

import asyncio
from datetime import datetime
from typing import Any, Optional

from app.core.logging import get_logger
from app.dream_agent.models import HITLRequest, HITLRequestType, HITLResponse

logger = get_logger(__name__)


class HITLManager:
    """HITL 관리자

    interrupt 요청을 관리하고 사용자 응답을 처리
    """

    def __init__(self):
        # session_id → HITLRequest
        self._pending_requests: dict[str, HITLRequest] = {}
        # request_id → asyncio.Event
        self._response_events: dict[str, asyncio.Event] = {}
        # request_id → HITLResponse
        self._responses: dict[str, HITLResponse] = {}

    def create_request(
        self,
        session_id: str,
        request_type: HITLRequestType,
        message: str,
        data: Optional[dict[str, Any]] = None,
        options: Optional[list[str]] = None,
        timeout_sec: int = 300,
    ) -> HITLRequest:
        """HITL 요청 생성

        Args:
            session_id: 세션 ID
            request_type: 요청 타입
            message: 사용자에게 표시할 메시지
            data: 추가 데이터 (Plan 등)
            options: 선택지
            timeout_sec: 타임아웃 (초)

        Returns:
            생성된 HITLRequest
        """
        request = HITLRequest(
            session_id=session_id,
            type=request_type,
            message=message,
            data=data or {},
            options=options or [],
            timeout_sec=timeout_sec,
        )

        self._pending_requests[session_id] = request
        self._response_events[request.request_id] = asyncio.Event()

        logger.info(
            "HITL request created",
            request_id=request.request_id,
            session_id=session_id,
            type=request_type.value,
        )

        return request

    async def wait_for_response(
        self,
        request_id: str,
        timeout: Optional[float] = None,
    ) -> Optional[HITLResponse]:
        """응답 대기

        Args:
            request_id: 요청 ID
            timeout: 타임아웃 (초)

        Returns:
            HITLResponse 또는 None (타임아웃)
        """
        event = self._response_events.get(request_id)
        if not event:
            return None

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            return self._responses.get(request_id)
        except asyncio.TimeoutError:
            logger.warning("HITL response timeout", request_id=request_id)
            return None

    def submit_response(
        self,
        request_id: str,
        action: str,
        value: Optional[Any] = None,
        comment: Optional[str] = None,
    ) -> bool:
        """응답 제출

        Args:
            request_id: 요청 ID
            action: 액션 (approve, reject, skip, modify 등)
            value: 입력값
            comment: 코멘트

        Returns:
            성공 여부
        """
        event = self._response_events.get(request_id)
        if not event:
            logger.warning("HITL request not found", request_id=request_id)
            return False

        response = HITLResponse(
            request_id=request_id,
            action=action,
            value=value,
            comment=comment,
            responded_at=datetime.utcnow(),
        )

        self._responses[request_id] = response
        event.set()

        logger.info(
            "HITL response submitted",
            request_id=request_id,
            action=action,
        )

        return True

    def get_pending_request(self, session_id: str) -> Optional[HITLRequest]:
        """세션의 대기 중인 요청 조회"""
        return self._pending_requests.get(session_id)

    def cancel_request(self, request_id: str) -> bool:
        """요청 취소"""
        event = self._response_events.get(request_id)
        if not event:
            return False

        # 취소 응답 생성
        response = HITLResponse(
            request_id=request_id,
            action="cancelled",
            value=None,
            comment="Request cancelled",
        )

        self._responses[request_id] = response
        event.set()

        logger.info("HITL request cancelled", request_id=request_id)
        return True

    def cleanup(self, session_id: str) -> None:
        """세션 정리"""
        request = self._pending_requests.pop(session_id, None)
        if request:
            self._response_events.pop(request.request_id, None)
            self._responses.pop(request.request_id, None)


# 싱글톤
_hitl_manager: Optional[HITLManager] = None


def get_hitl_manager() -> HITLManager:
    """HITL Manager 싱글톤 반환"""
    global _hitl_manager
    if _hitl_manager is None:
        _hitl_manager = HITLManager()
    return _hitl_manager
