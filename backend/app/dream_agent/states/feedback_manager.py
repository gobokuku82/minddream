"""Feedback Manager for RLHF Data Collection

This module provides functionality to collect and manage user feedback data
for Reinforcement Learning from Human Feedback (RLHF).
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class FeedbackManager:
    """
    피드백 관리자 - RLHF 데이터 수집을 위한 사용자 피드백 관리

    주요 기능:
    - 사용자 상호작용 로깅
    - 계획서 피드백 기록
    - RLHF 피드백 기록
    - 세션별 데이터 정리
    """

    def __init__(self):
        # In-memory storage (can be replaced with DB later)
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._plan_feedback: Dict[str, Dict[str, Any]] = {}
        self._rlhf_feedback: Dict[str, Dict[str, Any]] = {}
        self._interactions: Dict[str, List[Dict[str, Any]]] = {}

    async def log_user_interaction(
        self,
        session_id: str,
        user_id: int,
        user_input: str,
        language: str = "KOR",
        client_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        사용자 상호작용 로깅

        Args:
            session_id: 세션 ID
            user_id: 사용자 ID
            user_input: 사용자 입력
            language: 언어 코드
            client_info: 클라이언트 정보

        Returns:
            interaction_id: 상호작용 ID
        """
        interaction_id = str(uuid.uuid4())

        interaction = {
            "id": interaction_id,
            "session_id": session_id,
            "user_id": user_id,
            "user_input": user_input,
            "language": language,
            "client_info": client_info or {},
            "timestamp": datetime.now().isoformat()
        }

        if session_id not in self._interactions:
            self._interactions[session_id] = []

        self._interactions[session_id].append(interaction)

        logger.debug(f"Logged user interaction {interaction_id} for session {session_id}")

        return interaction_id

    async def record_plan_feedback(
        self,
        session_id: str,
        user_id: int,
        plan_id: str,
        plan_snapshot: Dict[str, Any],
        action: str,
        reason: Optional[str] = None,
        modifications: Optional[Dict[str, Any]] = None,
        original_todos: Optional[List[Dict[str, Any]]] = None,
        modified_todos: Optional[List[Dict[str, Any]]] = None,
        time_to_decision: Optional[int] = None
    ) -> uuid.UUID:
        """
        계획서 피드백 기록

        Args:
            session_id: 세션 ID
            user_id: 사용자 ID
            plan_id: 계획 ID
            plan_snapshot: 계획 스냅샷
            action: 액션 (approved/modified/rejected)
            reason: 사유
            modifications: 수정 내용
            original_todos: 원본 Todos
            modified_todos: 수정된 Todos
            time_to_decision: 결정까지 걸린 시간 (초)

        Returns:
            feedback_id: 피드백 ID
        """
        feedback_id = uuid.uuid4()

        feedback = {
            "id": str(feedback_id),
            "session_id": session_id,
            "user_id": user_id,
            "plan_id": plan_id,
            "plan_snapshot": plan_snapshot,
            "action": action,
            "reason": reason,
            "modifications": modifications,
            "original_todos": original_todos,
            "modified_todos": modified_todos,
            "time_to_decision": time_to_decision,
            "timestamp": datetime.now().isoformat()
        }

        self._plan_feedback[str(feedback_id)] = feedback

        logger.info(f"Recorded plan feedback {feedback_id}: {action}")

        return feedback_id

    async def record_rlhf_feedback(
        self,
        session_id: str,
        user_id: int,
        response_id: str,
        response_type: str,
        response_snapshot: Dict[str, Any],
        rating: str,
        reason: Optional[str] = None,
        aspects: Optional[Dict[str, int]] = None,
        selected_improvements: Optional[List[str]] = None
    ) -> uuid.UUID:
        """
        RLHF 피드백 기록

        Args:
            session_id: 세션 ID
            user_id: 사용자 ID
            response_id: 응답 ID
            response_type: 응답 타입 (plan/ml_result/biz_result/final_response)
            response_snapshot: 응답 스냅샷
            rating: 평점 (thumbs_up/thumbs_down/neutral)
            reason: 사유
            aspects: 세부 평가 항목
            selected_improvements: 선택된 개선 사항

        Returns:
            feedback_id: 피드백 ID
        """
        feedback_id = uuid.uuid4()

        feedback = {
            "id": str(feedback_id),
            "session_id": session_id,
            "user_id": user_id,
            "response_id": response_id,
            "response_type": response_type,
            "response_snapshot": response_snapshot,
            "rating": rating,
            "reason": reason,
            "aspects": aspects,
            "selected_improvements": selected_improvements,
            "timestamp": datetime.now().isoformat()
        }

        self._rlhf_feedback[str(feedback_id)] = feedback

        logger.info(f"Recorded RLHF feedback {feedback_id}: {rating}")

        return feedback_id

    def cleanup_session(self, session_id: str) -> None:
        """
        세션 정리 - 메모리에서 세션 데이터 제거

        Args:
            session_id: 세션 ID
        """
        if session_id in self._sessions:
            del self._sessions[session_id]

        if session_id in self._interactions:
            del self._interactions[session_id]

        logger.debug(f"Cleaned up session {session_id}")

    def get_session_interactions(self, session_id: str) -> List[Dict[str, Any]]:
        """세션의 모든 상호작용 조회"""
        return self._interactions.get(session_id, [])

    def get_plan_feedback(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        """계획 피드백 조회"""
        return self._plan_feedback.get(feedback_id)

    def get_rlhf_feedback(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        """RLHF 피드백 조회"""
        return self._rlhf_feedback.get(feedback_id)


# Singleton instance
feedback_manager = FeedbackManager()