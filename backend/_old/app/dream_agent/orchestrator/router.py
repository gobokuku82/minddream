"""Router - 실행 상태 유틸리티

실패율 계산 및 실행 건강도 모니터링.

NOTE: 라우팅 함수 (route_to_execution, route_after_execution)는
      Hand-off 패턴으로 전환됨 — 각 노드가 Command(goto=...)로 직접 라우팅.
      - planning_node → _determine_next_node_after_planning()
      - execution_node → _determine_next_node()
"""

from typing import Dict, Any
from backend.app.dream_agent.states import AgentState
from backend.app.dream_agent.states.accessors import get_todos
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


# ============================================================
# Phase 3.5 - 실패율 임계값
# ============================================================

FAILURE_THRESHOLD = 0.5  # 50% 이상 실패 시 기본 임계값

FAILURE_THRESHOLDS = {
    "warning": 0.3,     # 30% 이상: 경고 로깅
    "critical": 0.5,    # 50% 이상: 사용자 알림 권고
    "abort": 0.8,       # 80% 이상: 실행 중단 권고
}


def calculate_failure_rate(state: AgentState) -> Dict[str, Any]:
    """
    실행 레이어의 실패율 계산

    Args:
        state: 현재 상태

    Returns:
        {
            "rate": float,      # 실패율 (0.0 ~ 1.0)
            "failed": int,      # 실패한 Todo 수
            "total": int,       # 전체 실행 Todo 수
            "level": str,       # "normal" | "warning" | "critical" | "abort"
        }
    """
    all_todos = get_todos(state)

    # execution layer의 Todo만 대상 (ml_execution, biz_execution 포함)
    execution_todos = [
        t for t in all_todos
        if t.layer in ["execution", "ml_execution", "biz_execution"]
    ]

    if not execution_todos:
        return {
            "rate": 0.0,
            "failed": 0,
            "total": 0,
            "level": "normal"
        }

    failed = sum(1 for t in execution_todos if t.status == "failed")
    total = len(execution_todos)
    rate = failed / total

    # 레벨 결정
    if rate >= FAILURE_THRESHOLDS["abort"]:
        level = "abort"
    elif rate >= FAILURE_THRESHOLDS["critical"]:
        level = "critical"
    elif rate >= FAILURE_THRESHOLDS["warning"]:
        level = "warning"
    else:
        level = "normal"

    return {
        "rate": rate,
        "failed": failed,
        "total": total,
        "level": level
    }


def get_execution_health(state: AgentState) -> Dict[str, Any]:
    """
    실행 상태 건강도 요약 (Frontend 표시용)

    Args:
        state: 현재 상태

    Returns:
        {
            "status": "healthy" | "degraded" | "critical",
            "failure_rate": float,
            "completed": int,
            "failed": int,
            "pending": int,
            "message": str
        }
    """
    all_todos = get_todos(state)
    execution_todos = [
        t for t in all_todos
        if t.layer in ["execution", "ml_execution", "biz_execution"]
    ]

    if not execution_todos:
        return {
            "status": "healthy",
            "failure_rate": 0.0,
            "completed": 0,
            "failed": 0,
            "pending": 0,
            "message": "No execution todos"
        }

    completed = sum(1 for t in execution_todos if t.status == "completed")
    failed = sum(1 for t in execution_todos if t.status == "failed")
    pending = sum(1 for t in execution_todos if t.status in ["pending", "in_progress"])
    total = len(execution_todos)

    failure_rate = failed / total if total > 0 else 0

    if failure_rate >= FAILURE_THRESHOLDS["critical"]:
        status = "critical"
        message = f"{failure_rate:.0%} 실패율: 실행 중단 권고"
    elif failure_rate >= FAILURE_THRESHOLDS["warning"]:
        status = "degraded"
        message = f"{failure_rate:.0%} 실패율: 주의 필요"
    else:
        status = "healthy"
        message = f"{completed}/{total} 완료"

    return {
        "status": status,
        "failure_rate": failure_rate,
        "completed": completed,
        "failed": failed,
        "pending": pending,
        "message": message
    }
