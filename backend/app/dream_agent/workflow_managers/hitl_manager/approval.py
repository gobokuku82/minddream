"""Approval Handler

Plan 승인 워크플로우

Reference: docs/specs/HITL_SPEC.md#Approval
"""

from datetime import datetime
from typing import Any, Optional

from app.core.logging import get_logger
from app.dream_agent.models import (
    HITLRequestType,
    HITLResponse,
    Plan,
    PlanChange,
    PlanStatus,
)

logger = get_logger(__name__)


class ApprovalHandler:
    """승인 핸들러

    Plan 승인/수정/거부 처리
    """

    def process_approval(
        self,
        plan: Plan,
        response: HITLResponse,
    ) -> tuple[Plan, bool]:
        """승인 응답 처리

        Args:
            plan: 현재 Plan
            response: HITL 응답

        Returns:
            (업데이트된 Plan, 승인 여부)
        """
        action = response.action

        logger.info(
            "Processing approval",
            plan_id=plan.plan_id,
            action=action,
        )

        if action == "approve":
            return self._handle_approve(plan, response)

        elif action == "reject":
            return self._handle_reject(plan, response)

        elif action == "modify":
            # 수정은 별도 처리 (PlanEditor 사용)
            return plan, False

        else:
            logger.warning("Unknown approval action", action=action)
            return plan, False

    def _handle_approve(
        self,
        plan: Plan,
        response: HITLResponse,
    ) -> tuple[Plan, bool]:
        """승인 처리"""
        change = PlanChange(
            change_type="approve",
            reason=response.comment or "사용자 승인",
            actor="user",
            affected_todo_ids=[],
            change_data={"response_id": response.request_id},
        )

        updated_plan = plan.model_copy(
            update={
                "status": PlanStatus.APPROVED,
                "approved_at": datetime.utcnow(),
                "changes": plan.changes + [change],
            }
        )

        logger.info("Plan approved", plan_id=plan.plan_id)
        return updated_plan, True

    def _handle_reject(
        self,
        plan: Plan,
        response: HITLResponse,
    ) -> tuple[Plan, bool]:
        """거부 처리"""
        change = PlanChange(
            change_type="reject",
            reason=response.comment or "사용자 거부",
            actor="user",
            affected_todo_ids=[],
            change_data={"response_id": response.request_id},
        )

        updated_plan = plan.model_copy(
            update={
                "status": PlanStatus.CANCELLED,
                "changes": plan.changes + [change],
            }
        )

        logger.info("Plan rejected", plan_id=plan.plan_id)
        return updated_plan, False

    def create_approval_message(self, plan: Plan, language: str = "ko") -> str:
        """승인 요청 메시지 생성

        Args:
            plan: 승인 대상 Plan
            language: 언어

        Returns:
            승인 요청 메시지
        """
        todos_summary = "\n".join([
            f"  {i+1}. {t.task} ({t.tool})"
            for i, t in enumerate(plan.todos)
        ])

        if language == "ko":
            return f"""## 실행 계획 승인 요청

다음 작업을 실행할까요?

{todos_summary}

예상 소요 시간: {plan.estimated_duration_sec}초
"""
        else:
            return f"""## Execution Plan Approval

Do you want to execute the following tasks?

{todos_summary}

Estimated time: {plan.estimated_duration_sec} seconds
"""

    def get_approval_options(self, language: str = "ko") -> list[str]:
        """승인 선택지 반환"""
        if language == "ko":
            return ["승인", "수정", "거부"]
        return ["Approve", "Modify", "Reject"]
