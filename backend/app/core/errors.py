"""Error Codes and Exceptions

Reference: docs/specs/ERROR_CODES.md
"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel


class ErrorCategory(str, Enum):
    """에러 카테고리"""
    SESSION = "SESSION"      # E1xxx: 세션 관련
    LAYER = "LAYER"          # E2xxx: 레이어 처리
    EXECUTION = "EXECUTION"  # E3xxx: 도구 실행
    HITL = "HITL"            # E4xxx: HITL
    SYSTEM = "SYSTEM"        # E5xxx: 시스템


class ErrorCode(str, Enum):
    """에러 코드"""

    # === E1xxx: Session ===
    SESSION_NOT_FOUND = "E1001"
    SESSION_EXPIRED = "E1002"
    SESSION_INVALID_STATE = "E1003"
    SESSION_LIMIT_EXCEEDED = "E1004"

    # === E2xxx: Layer Processing ===
    COGNITIVE_CLASSIFICATION_FAILED = "E2001"
    COGNITIVE_AMBIGUOUS_INTENT = "E2002"
    PLANNING_GENERATION_FAILED = "E2101"
    PLANNING_VALIDATION_FAILED = "E2102"
    PLANNING_CIRCULAR_DEPENDENCY = "E2103"
    EXECUTION_FAILED = "E2201"
    EXECUTION_TIMEOUT = "E2202"
    EXECUTION_ALL_RETRIES_EXHAUSTED = "E2203"
    RESPONSE_GENERATION_FAILED = "E2301"

    # === E3xxx: Tool Execution ===
    TOOL_NOT_FOUND = "E3001"
    TOOL_PARAMETER_INVALID = "E3002"
    TOOL_EXECUTION_ERROR = "E3003"
    TOOL_TIMEOUT = "E3004"
    TOOL_EXTERNAL_API_ERROR = "E3005"

    # === E4xxx: HITL ===
    HITL_TIMEOUT = "E4001"
    HITL_INVALID_ACTION = "E4002"
    HITL_ALREADY_RESPONDED = "E4003"
    HITL_CANCELLED = "E4004"

    # === E5xxx: System ===
    DATABASE_ERROR = "E5001"
    LLM_API_ERROR = "E5002"
    INTERNAL_ERROR = "E5003"
    VALIDATION_ERROR = "E5004"
    RATE_LIMIT_EXCEEDED = "E5005"


# Error Code -> Message mapping
ERROR_MESSAGES: dict[ErrorCode, str] = {
    # Session
    ErrorCode.SESSION_NOT_FOUND: "세션을 찾을 수 없습니다.",
    ErrorCode.SESSION_EXPIRED: "세션이 만료되었습니다.",
    ErrorCode.SESSION_INVALID_STATE: "잘못된 세션 상태입니다.",
    ErrorCode.SESSION_LIMIT_EXCEEDED: "세션 제한을 초과했습니다.",

    # Layer
    ErrorCode.COGNITIVE_CLASSIFICATION_FAILED: "의도 분류에 실패했습니다.",
    ErrorCode.COGNITIVE_AMBIGUOUS_INTENT: "의도가 불명확합니다. 추가 정보가 필요합니다.",
    ErrorCode.PLANNING_GENERATION_FAILED: "계획 생성에 실패했습니다.",
    ErrorCode.PLANNING_VALIDATION_FAILED: "계획 검증에 실패했습니다.",
    ErrorCode.PLANNING_CIRCULAR_DEPENDENCY: "순환 의존성이 감지되었습니다.",
    ErrorCode.EXECUTION_FAILED: "실행에 실패했습니다.",
    ErrorCode.EXECUTION_TIMEOUT: "실행 시간이 초과되었습니다.",
    ErrorCode.EXECUTION_ALL_RETRIES_EXHAUSTED: "모든 재시도가 실패했습니다.",
    ErrorCode.RESPONSE_GENERATION_FAILED: "응답 생성에 실패했습니다.",

    # Tool
    ErrorCode.TOOL_NOT_FOUND: "도구를 찾을 수 없습니다.",
    ErrorCode.TOOL_PARAMETER_INVALID: "도구 파라미터가 올바르지 않습니다.",
    ErrorCode.TOOL_EXECUTION_ERROR: "도구 실행 중 오류가 발생했습니다.",
    ErrorCode.TOOL_TIMEOUT: "도구 실행 시간이 초과되었습니다.",
    ErrorCode.TOOL_EXTERNAL_API_ERROR: "외부 API 호출에 실패했습니다.",

    # HITL
    ErrorCode.HITL_TIMEOUT: "사용자 응답 대기 시간이 초과되었습니다.",
    ErrorCode.HITL_INVALID_ACTION: "잘못된 HITL 액션입니다.",
    ErrorCode.HITL_ALREADY_RESPONDED: "이미 응답된 요청입니다.",
    ErrorCode.HITL_CANCELLED: "HITL 요청이 취소되었습니다.",

    # System
    ErrorCode.DATABASE_ERROR: "데이터베이스 오류가 발생했습니다.",
    ErrorCode.LLM_API_ERROR: "LLM API 호출에 실패했습니다.",
    ErrorCode.INTERNAL_ERROR: "내부 서버 오류가 발생했습니다.",
    ErrorCode.VALIDATION_ERROR: "입력 검증에 실패했습니다.",
    ErrorCode.RATE_LIMIT_EXCEEDED: "요청 한도를 초과했습니다.",
}


class ErrorDetail(BaseModel):
    """API 에러 응답 상세"""
    code: str
    message: str
    details: Optional[dict[str, Any]] = None
    layer: Optional[str] = None
    todo_id: Optional[str] = None


class AgentError(Exception):
    """Base Agent Exception"""

    def __init__(
        self,
        code: ErrorCode,
        message: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        layer: Optional[str] = None,
        todo_id: Optional[str] = None,
    ):
        self.code = code
        self.message = message or ERROR_MESSAGES.get(code, "Unknown error")
        self.details = details
        self.layer = layer
        self.todo_id = todo_id
        super().__init__(self.message)

    def to_detail(self) -> ErrorDetail:
        """Convert to API response format"""
        return ErrorDetail(
            code=self.code.value,
            message=self.message,
            details=self.details,
            layer=self.layer,
            todo_id=self.todo_id,
        )


class SessionError(AgentError):
    """Session related errors"""
    pass


class LayerError(AgentError):
    """Layer processing errors"""
    pass


class ExecutionError(AgentError):
    """Execution related errors"""
    pass


class HITLError(AgentError):
    """HITL related errors"""
    pass


class SystemError(AgentError):
    """System level errors"""
    pass
