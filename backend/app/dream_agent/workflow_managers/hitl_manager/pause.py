"""Pause Controller

실행 일시정지/재개 제어

Reference: docs/specs/HITL_SPEC.md#Pause-Resume
"""

from datetime import datetime
from typing import Any, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class PauseController:
    """Pause/Resume 제어기"""

    def __init__(self):
        # session_id → pause state
        self._pause_states: dict[str, dict[str, Any]] = {}

    def pause(self, session_id: str, reason: str = "user_request") -> bool:
        """실행 일시정지

        Args:
            session_id: 세션 ID
            reason: 정지 이유

        Returns:
            성공 여부
        """
        if session_id in self._pause_states:
            logger.warning("Session already paused", session_id=session_id)
            return False

        self._pause_states[session_id] = {
            "paused_at": datetime.utcnow(),
            "reason": reason,
        }

        logger.info("Session paused", session_id=session_id, reason=reason)
        return True

    def resume(self, session_id: str) -> bool:
        """실행 재개

        Args:
            session_id: 세션 ID

        Returns:
            성공 여부
        """
        if session_id not in self._pause_states:
            logger.warning("Session not paused", session_id=session_id)
            return False

        state = self._pause_states.pop(session_id)
        pause_duration = (datetime.utcnow() - state["paused_at"]).total_seconds()

        logger.info(
            "Session resumed",
            session_id=session_id,
            pause_duration_sec=pause_duration,
        )
        return True

    def is_paused(self, session_id: str) -> bool:
        """일시정지 상태 확인"""
        return session_id in self._pause_states

    def get_pause_info(self, session_id: str) -> Optional[dict[str, Any]]:
        """일시정지 정보 조회"""
        return self._pause_states.get(session_id)

    def cleanup(self, session_id: str) -> None:
        """세션 정리"""
        self._pause_states.pop(session_id, None)


# 싱글톤
_pause_controller: Optional[PauseController] = None


def get_pause_controller() -> PauseController:
    """Pause Controller 싱글톤 반환"""
    global _pause_controller
    if _pause_controller is None:
        _pause_controller = PauseController()
    return _pause_controller
