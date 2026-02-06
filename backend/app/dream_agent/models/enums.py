"""Shared Enums for Models

Reference: docs/specs/DATA_MODELS.md#Core-Enums
"""

from enum import Enum


class IntentDomain(str, Enum):
    """최상위 의도 도메인 (4개)"""
    ANALYSIS = "analysis"      # 분석 요청
    CONTENT = "content"        # 콘텐츠 생성
    OPERATION = "operation"    # 운영 작업
    INQUIRY = "inquiry"        # 정보 조회


class IntentCategory(str, Enum):
    """도메인 하위 카테고리"""
    # Analysis
    SENTIMENT = "sentiment"
    KEYWORD = "keyword"
    TREND = "trend"
    COMPETITOR = "competitor"

    # Content
    REPORT = "report"
    VIDEO = "video"
    AD = "ad"

    # Operation
    SALES = "sales"
    INVENTORY = "inventory"
    DASHBOARD = "dashboard"

    # Inquiry
    GENERAL = "general"
    FAQ = "faq"


class Layer(str, Enum):
    """4-Layer 아키텍처 (V2)"""
    COGNITIVE = "cognitive"
    PLANNING = "planning"
    EXECUTION = "execution"
    RESPONSE = "response"


class ExecutionStrategy(str, Enum):
    """실행 전략 (V2 신규)"""
    SINGLE = "single"          # 단일 Todo 실행
    SEQUENTIAL = "sequential"  # 순차 실행
    PARALLEL = "parallel"      # 병렬 실행 (Send API)
    SWARM = "swarm"            # 동적 스웜
    CYCLIC = "cyclic"          # 반복 실행


class TodoStatus(str, Enum):
    """Todo 상태"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
    NEEDS_APPROVAL = "needs_approval"
    CANCELLED = "cancelled"


class PlanStatus(str, Enum):
    """Plan 상태"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SessionStatus(str, Enum):
    """Session 상태"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    HITL_WAITING = "hitl_waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class HITLRequestType(str, Enum):
    """HITL 요청 타입"""
    PLAN_REVIEW = "plan_review"
    APPROVAL = "approval"
    CLARIFICATION = "clarification"
    INPUT = "input"


class ToolCategory(str, Enum):
    """도구 카테고리"""
    DATA = "data"
    ANALYSIS = "analysis"
    CONTENT = "content"
    OPS = "ops"


class ToolParameterType(str, Enum):
    """도구 파라미터 타입"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
