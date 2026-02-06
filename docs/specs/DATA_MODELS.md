# Data Models Specification

**Version**: 2.0 | **Date**: 2026-02-06 | **Status**: Draft

---

## 1. Overview

Dream Agent V2의 Pydantic 데이터 모델 정의서입니다. 4-Layer 아키텍처의 각 레이어에서 사용되는 데이터 구조를 정의합니다.

### 1.1 Model Categories

| Category | Location | Purpose |
|----------|----------|---------|
| **Domain Models** | `models/` | 비즈니스 로직 (Intent, Todo, Plan 등) |
| **Layer Schemas** | `schemas/` | 레이어 간 I/O 계약 |
| **Agent State** | `states/` | LangGraph 그래프 상태 (TypedDict) |
| **API Schemas** | `api/schemas/` | REST API 요청/응답 |

### 1.2 Type Strategy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Type Strategy                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  AgentState (TypedDict)                                          │    │
│  │  ├── 그래프 전체에서 공유되는 "상태 컨테이너"                       │    │
│  │  ├── Reducer로 자동 병합                                          │    │
│  │  └── Checkpointer로 저장/복구                                     │    │
│  │                                                                   │    │
│  │  ┌─────────────────────────────────────────────────────────┐     │    │
│  │  │  Pydantic Models (Intent, Todo, Plan, etc.)              │     │    │
│  │  │  ├── 데이터 검증 & 직렬화                                  │     │    │
│  │  │  └── State 내부에 저장되는 "데이터 객체"                   │     │    │
│  │  └─────────────────────────────────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Enums

### 2.1 Intent Enums

```python
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
```

### 2.2 Layer & Execution Enums

```python
class Layer(str, Enum):
    """4-Layer 아키텍처 (V2)"""
    COGNITIVE = "cognitive"
    PLANNING = "planning"
    EXECUTION = "execution"    # V2: ml_execution + biz_execution 통합
    RESPONSE = "response"

class ExecutionStrategy(str, Enum):
    """실행 전략 (V2 신규)"""
    SINGLE = "single"          # 단일 Todo 실행
    SEQUENTIAL = "sequential"  # 순차 실행
    PARALLEL = "parallel"      # 병렬 실행 (Send API)
    SWARM = "swarm"            # 동적 스웜
    CYCLIC = "cyclic"          # 반복 실행
```

### 2.3 Status Enums

```python
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
```

---

## 3. Intent Models

### 3.1 Entity

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class Entity(BaseModel):
    """추출된 엔티티"""
    type: str                        # brand, product, date_range, platform, etc.
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        frozen = True  # 불변
```

**Entity Types:**

| Type | Description | Example |
|------|-------------|---------|
| `brand` | 브랜드명 | 라네즈, 설화수 |
| `product` | 제품명 | 워터뱅크 크림 |
| `date_range` | 기간 | 최근 3개월, 2025년 1분기 |
| `platform` | 플랫폼 | 네이버, 올리브영 |
| `category` | 제품 카테고리 | 스킨케어, 메이크업 |
| `competitor` | 경쟁사 | 이니스프리, 에뛰드 |

### 3.2 Intent

```python
class Intent(BaseModel):
    """분류된 의도"""
    domain: IntentDomain
    category: Optional[IntentCategory] = None
    subcategory: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)

    # Entities
    entities: List[Entity] = Field(default_factory=list)

    # Context
    summary: str = ""
    plan_hint: str = ""          # 어떤 계획이 필요한지 힌트
    raw_input: str = ""
    language: str = "ko"

    class Config:
        frozen = True
```

### 3.3 CognitiveOutput (Layer I/O)

```python
class CognitiveOutput(BaseModel):
    """Cognitive Layer 출력"""
    intent: Intent
    requires_clarification: bool = False
    clarification_question: Optional[str] = None
    context_summary: str = ""
    processing_time_ms: float = 0.0

    # V2: 다음 레이어 힌트
    suggested_tools: List[str] = Field(default_factory=list)
```

---

## 4. Todo Models

### 4.1 TodoItem (V2 - Immutable)

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional, List, Dict, Any
import uuid

class TodoItem(BaseModel, frozen=True):
    """Todo 아이템 V2 (Immutable)

    V2 Changes:
    - frozen=True: 불변성 보장, 수정 시 새 버전 생성
    - layer: 4개로 통합 (cognitive, planning, execution, response)
    - Flat 구조: metadata 중첩 제거
    """

    # === Identity ===
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plan_id: Optional[str] = None

    # === Basic Info ===
    task: str                    # 작업 설명
    description: Optional[str] = None

    # === Execution ===
    tool: str                    # 실행할 도구명
    tool_params: Dict[str, Any] = Field(default_factory=dict)

    # === Classification (V2) ===
    layer: Literal["execution"] = "execution"  # V2: execution 전용

    # === Status ===
    status: Literal[
        "pending", "in_progress", "completed", "failed",
        "blocked", "skipped", "needs_approval", "cancelled"
    ] = "pending"
    priority: int = Field(default=5, ge=0, le=10)

    # === Dependencies ===
    depends_on: List[str] = Field(default_factory=list)

    # === Execution Config ===
    timeout_sec: int = 300
    max_retries: int = 3
    retry_count: int = 0

    # === Approval ===
    requires_approval: bool = False

    # === Result ===
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    # === Timestamps ===
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # === Version ===
    version: int = 1

    def with_status(self, new_status: str, **kwargs) -> "TodoItem":
        """상태 변경된 새 인스턴스 반환"""
        return self.model_copy(update={"status": new_status, "version": self.version + 1, **kwargs})
```

### 4.2 Todo Status Transitions

```python
VALID_TRANSITIONS = {
    "pending": ["in_progress", "blocked", "needs_approval", "cancelled", "skipped"],
    "blocked": ["pending", "cancelled"],
    "needs_approval": ["pending", "cancelled", "skipped"],
    "in_progress": ["completed", "failed"],
    "completed": [],      # final
    "failed": ["pending", "skipped", "cancelled"],  # retry 가능
    "skipped": [],        # final
    "cancelled": [],      # final
}

def validate_transition(current: str, target: str) -> bool:
    return target in VALID_TRANSITIONS.get(current, [])
```

**State Diagram:**
```
                              ┌─────────────┐
                              │   pending   │
                              └──────┬──────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
     ┌───────────────┐      ┌─────────────┐      ┌───────────────┐
     │    blocked    │      │ in_progress │      │needs_approval │
     └───────┬───────┘      └──────┬──────┘      └───────┬───────┘
             │                     │                      │
             └──────────┬──────────┴───────────┬──────────┘
                        │                      │
                        ▼                      ▼
               ┌───────────────┐      ┌───────────────┐
               │   completed   │      │    failed     │
               └───────────────┘      └───────┬───────┘
                                              │
                                              ▼
                                     ┌───────────────┐
                                     │   skipped /   │
                                     │   cancelled   │
                                     └───────────────┘
```

---

## 5. Plan Models

### 5.1 PlanChange

```python
class PlanChange(BaseModel):
    """플랜 변경 이력"""
    change_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    change_type: Literal[
        "create", "add_todo", "remove_todo", "modify_todo",
        "reorder", "approve", "reject", "nl_edit"
    ]
    reason: str
    actor: str = "system"        # system | user | hitl
    affected_todo_ids: List[str] = Field(default_factory=list)
    change_data: Dict[str, Any] = Field(default_factory=dict)

    # NL Edit
    user_instruction: Optional[str] = None
```

### 5.2 PlanVersion

```python
class PlanVersion(BaseModel):
    """플랜 버전 스냅샷"""
    version: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    todos_snapshot: List[Dict[str, Any]]  # TodoItem.model_dump() 리스트
    change_id: str
    change_summary: str
```

### 5.3 Plan

```python
class Plan(BaseModel):
    """실행 계획"""
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    version: int = 1
    status: PlanStatus = PlanStatus.DRAFT

    # === Todos ===
    todos: List[TodoItem] = Field(default_factory=list)

    # === Dependency Graph ===
    dependency_graph: Dict[str, List[str]] = Field(default_factory=dict)
    # { "todo_001": [], "todo_002": ["todo_001"], ... }

    # === Execution Strategy (V2) ===
    strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL

    # === Estimates ===
    estimated_duration_sec: int = 0
    estimated_cost_usd: float = 0.0

    # === Visualization ===
    mermaid_diagram: Optional[str] = None

    # === History ===
    versions: List[PlanVersion] = Field(default_factory=list)
    changes: List[PlanChange] = Field(default_factory=list)

    # === Context ===
    intent_summary: str = ""

    # === Timestamps ===
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def get_ready_todos(self) -> List[TodoItem]:
        """실행 가능한 Todo 목록 (의존성 충족, pending 상태)"""
        completed_ids = {t.id for t in self.todos if t.status == "completed"}
        return [
            t for t in self.todos
            if t.status == "pending"
            and all(dep_id in completed_ids for dep_id in t.depends_on)
        ]

    def get_statistics(self) -> Dict[str, int]:
        """Todo 통계"""
        stats = {"total": 0, "pending": 0, "in_progress": 0, "completed": 0, "failed": 0}
        for todo in self.todos:
            stats["total"] += 1
            stats[todo.status] = stats.get(todo.status, 0) + 1
        return stats

    def get_progress_percentage(self) -> float:
        """진행률 (0.0 ~ 100.0)"""
        if not self.todos:
            return 0.0
        completed = sum(1 for t in self.todos if t.status == "completed")
        return (completed / len(self.todos)) * 100
```

### 5.4 PlanningOutput (Layer I/O)

```python
class PlanningOutput(BaseModel):
    """Planning Layer 출력"""
    plan: Plan
    requires_approval: bool = True
    approval_message: str = "실행 계획을 검토해주세요."
```

---

## 6. Execution Models

### 6.1 ExecutionResult

```python
class ExecutionResult(BaseModel):
    """도구 실행 결과"""
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

    # Metadata
    todo_id: str
    tool: str
    started_at: datetime
    completed_at: datetime
    execution_time_ms: float = 0.0

    # Resource Usage
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
```

### 6.2 ExecutionContext

```python
class ExecutionContext(BaseModel):
    """실행 컨텍스트 (도구에 전달)"""
    session_id: str
    plan_id: str
    language: str = "ko"

    # 이전 Todo 결과 참조
    previous_results: Dict[str, Any] = Field(default_factory=dict)

    # 공유 데이터
    collected_data: Optional[Dict] = None
    preprocessed_data: Optional[Dict] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### 6.3 ExecutionOutput (Layer I/O)

```python
class ExecutionOutput(BaseModel):
    """Execution Layer 출력"""
    results: Dict[str, ExecutionResult]  # todo_id → result
    updated_todos: List[TodoItem]
    all_completed: bool = False
    has_failures: bool = False
```

---

## 7. Response Models

### 7.1 Attachment

```python
class Attachment(BaseModel):
    """응답 첨부파일"""
    type: Literal["image", "pdf", "video", "chart", "table", "file"]
    title: str
    url: str                     # 파일 URL 또는 base64
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### 7.2 ResponsePayload

```python
class ResponsePayload(BaseModel):
    """최종 응답"""
    format: Literal["text", "image", "pdf", "video", "mixed"] = "text"
    text: str                    # 메인 텍스트 응답
    summary: str = ""            # 한줄 요약
    attachments: List[Attachment] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)  # 추천 후속 작업
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### 7.3 ResponseOutput (Layer I/O)

```python
class ResponseOutput(BaseModel):
    """Response Layer 출력"""
    response: ResponsePayload
    report_paths: List[str] = Field(default_factory=list)
```

---

## 8. Tool Models

### 8.1 ToolParameter

```python
class ToolParameterType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"

class ToolParameter(BaseModel):
    """도구 파라미터 정의"""
    name: str
    type: ToolParameterType
    required: bool = False
    default: Optional[Any] = None
    description: str = ""
```

### 8.2 ToolSpec

```python
class ToolCategory(str, Enum):
    DATA = "data"
    ANALYSIS = "analysis"
    CONTENT = "content"
    OPS = "ops"

class ToolSpec(BaseModel):
    """도구 명세 (YAML에서 로드)"""
    name: str
    description: str
    category: ToolCategory
    executor: str                # executor class path

    # Parameters
    parameters: List[ToolParameter] = Field(default_factory=list)

    # Execution
    timeout_sec: int = 300
    max_retries: int = 3

    # Dependencies
    dependencies: List[str] = Field(default_factory=list)  # 선행 도구
    produces: List[str] = Field(default_factory=list)      # 산출물 키

    # Approval
    requires_approval: bool = False

    # Cost
    has_cost: bool = False
    estimated_cost_usd: float = 0.0
```

---

## 9. AgentState (LangGraph)

### 9.1 AgentState Definition

```python
from typing import TypedDict, Annotated, Optional, List
from langgraph.graph import add_messages

class AgentState(TypedDict, total=False):
    """LangGraph 에이전트 상태

    주의: TypedDict입니다 (Pydantic BaseModel 아님!)
    Reducer를 통해 상태가 자동 병합됩니다.
    """

    # ─── Input ───
    session_id: str
    user_input: str
    language: str                # "ko", "en", "ja"

    # ─── Layer Results (구조화된 dict) ───
    cognitive_result: dict       # CognitiveOutput.model_dump()
    planning_result: dict        # PlanningOutput.model_dump()
    execution_results: Annotated[dict, results_reducer]  # todo_id → result
    response_result: dict        # ResponseOutput.model_dump()

    # ─── Plan & Todos ───
    plan: dict                   # Plan.model_dump()
    todos: Annotated[list, todo_reducer]  # TodoItem 리스트

    # ─── Control ───
    error: Optional[str]

    # ─── HITL ───
    hitl_pending: Optional[dict]  # 현재 대기 중인 HITL 요청

    # ─── Learning (비침습적) ───
    trace: Annotated[list, lambda a, b: a + b]  # append-only 로그
```

### 9.2 Reducers

```python
def todo_reducer(existing: List[dict], updates: List[dict]) -> List[dict]:
    """Todo 리스트 병합 (ID 기반)

    동작:
    1. 같은 ID → 업데이트로 교체
    2. 새 ID → 추가
    3. completed/failed/skipped → 덮어쓰기 방지 (final state)
    """
    existing_map = {t["id"]: t for t in existing}
    final_statuses = {"completed", "failed", "skipped", "cancelled"}

    for update in updates:
        todo_id = update["id"]
        if todo_id in existing_map:
            # Final status면 덮어쓰기 방지
            if existing_map[todo_id].get("status") not in final_statuses:
                existing_map[todo_id] = update
        else:
            existing_map[todo_id] = update

    return list(existing_map.values())


def results_reducer(existing: dict, new: dict) -> dict:
    """실행 결과 병합

    동작:
    1. 재귀적 딕셔너리 병합
    2. 동일 todo_id → 최신 결과로 교체
    """
    merged = {**existing}
    for key, value in new.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged
```

### 9.3 State Flow Example

```python
# 노드가 반환할 때 - 변경된 것만 반환
async def execution_node(state: AgentState) -> Command:
    todo = state["todos"][0]
    result = await execute_tool(todo)

    updated_todo = {**todo, "status": "completed", "result": result.data}

    return Command(
        update={
            "todos": [updated_todo],  # Reducer가 병합
            "execution_results": {todo["id"]: result.model_dump()}
        },
        goto="response" if all_done else "execution"
    )


# LangGraph 내부에서 자동 병합
state["todos"] = todo_reducer(
    state["todos"],      # 기존 목록
    [updated_todo]       # 새로운/업데이트 항목
)
```

---

## 10. HITL Models

### 10.1 HITLRequest

```python
class HITLRequestType(str, Enum):
    PLAN_REVIEW = "plan_review"
    APPROVAL = "approval"
    CLARIFICATION = "clarification"
    INPUT = "input"

class HITLRequest(BaseModel):
    """HITL 요청"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    type: HITLRequestType

    # Request Data
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)

    # Options
    options: List[str] = Field(default_factory=list)  # ["approve", "modify", "reject"]
    input_type: Optional[str] = None  # text, choice, number

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    timeout_sec: int = 300
    timeout_at: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.timeout_at is None:
            self.timeout_at = self.created_at + timedelta(seconds=self.timeout_sec)
```

### 10.2 HITLResponse

```python
class HITLResponse(BaseModel):
    """HITL 응답"""
    request_id: str
    action: str                  # approve, reject, skip, modify, etc.
    value: Optional[Any] = None  # 입력값
    comment: Optional[str] = None
    responded_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## 11. Validation Rules

### 11.1 Field Validators

```python
from pydantic import field_validator

class TodoItem(BaseModel, frozen=True):
    # ...

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: int) -> int:
        if not 0 <= v <= 10:
            raise ValueError("Priority must be between 0 and 10")
        return v

    @field_validator("tool")
    @classmethod
    def validate_tool(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Tool name cannot be empty")
        return v.strip().lower()
```

### 11.2 Model Validators

```python
from pydantic import model_validator

class Plan(BaseModel):
    # ...

    @model_validator(mode="after")
    def validate_dependencies(self) -> "Plan":
        """의존성 순환 검사"""
        todo_ids = {t.id for t in self.todos}

        for todo in self.todos:
            for dep_id in todo.depends_on:
                if dep_id not in todo_ids:
                    raise ValueError(f"Unknown dependency: {dep_id}")

        # 순환 검사
        if self._has_cycle():
            raise ValueError("Circular dependency detected")

        return self

    def _has_cycle(self) -> bool:
        """DFS로 순환 검사"""
        # ... implementation
```

---

## 12. Serialization

### 12.1 JSON Encoders

```python
from datetime import datetime
from pydantic import ConfigDict

class BaseModelWithConfig(BaseModel):
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
        },
        use_enum_values=True,
    )
```

### 12.2 Model Export

```python
# Dict로 변환
todo_dict = todo.model_dump()

# JSON 문자열로 변환
todo_json = todo.model_dump_json()

# 특정 필드만 포함
todo_partial = todo.model_dump(include={"id", "task", "status"})

# 특정 필드 제외
todo_without_result = todo.model_dump(exclude={"result"})
```

---

## Related Documents

- [ARCHITECTURE.md](ARCHITECTURE.md) - 시스템 아키텍처
- [HITL_SPEC.md](HITL_SPEC.md) - HITL 시스템
- [API_SPEC.md](API_SPEC.md) - REST API
- [DB_SCHEMA.md](DB_SCHEMA.md) - 데이터베이스 스키마

---

*Last Updated: 2026-02-06*
