# Interface Contract (인터페이스 계약)

## 1. 개요

이 문서는 Dream Agent 시스템의 모든 레이어 간 인터페이스 계약을 정의합니다.
모든 개발자는 이 계약을 준수해야 합니다.

## 2. 레이어 간 인터페이스

### 2.1 Cognitive Layer I/O

```python
# 입력: schemas/cognitive.py
class CognitiveInput(BaseModel):
    user_input: str          # 필수: 사용자 입력
    session_id: str          # 필수: 세션 ID
    context: Dict[str, Any]  # 선택: 이전 컨텍스트

# 출력: schemas/cognitive.py
class CognitiveOutput(BaseModel):
    intent: Intent           # 필수: 파싱된 Intent
    entities: List[Entity]   # 필수: 추출된 엔티티
    confidence: float        # 필수: 신뢰도 (0.0-1.0)
    requires_clarification: bool  # 선택: 추가 질문 필요 여부
```

**계약 조건:**
- `user_input`은 빈 문자열 불가
- `confidence`는 0.0 이상 1.0 이하
- `intent.intent_type`은 반드시 설정되어야 함

### 2.2 Planning Layer I/O

```python
# 입력: schemas/planning.py
class PlanningInput(BaseModel):
    intent: Intent           # 필수: Cognitive에서 전달
    session_id: str          # 필수: 세션 ID
    context: Dict[str, Any]  # 선택: 컨텍스트
    constraints: Dict        # 선택: 제약 조건
    existing_plan: Plan      # 선택: 재계획 시 기존 Plan
    replan_instruction: str  # 선택: 재계획 지시

# 출력: schemas/planning.py
class PlanningOutput(BaseModel):
    plan: Plan               # 필수: 생성된 Plan
    todos: List[TodoItem]    # 필수: 최소 1개 이상
    estimated_duration_sec: int   # 선택: 예상 시간
    estimated_cost: float    # 선택: 예상 비용
    requires_approval: bool  # 선택: 사용자 승인 필요 여부
    mermaid_diagram: str     # 선택: 시각화 다이어그램
```

**계약 조건:**
- `todos`는 최소 1개 이상이어야 함
- `session_id`는 빈 문자열 불가
- `intent.intent_type`은 None 불가

### 2.3 Execution Layer I/O

```python
# 입력: schemas/execution.py
class ExecutionInput(BaseModel):
    todo: TodoItem           # 필수: 실행할 Todo
    context: ExecutionContext  # 필수: 실행 컨텍스트
    previous_results: Dict   # 선택: 이전 실행 결과
    use_mock: bool           # 선택: Mock 실행 여부

# 출력: schemas/execution.py
class ExecutionOutput(BaseModel):
    result: ExecutionResult  # 필수: 실행 결과
    updated_todo: TodoItem   # 필수: 업데이트된 Todo
    intermediate_data: Dict  # 선택: 중간 데이터
    next_todos: List[str]    # 선택: 다음 실행 Todo IDs
    requires_user_input: bool    # 선택: 사용자 입력 필요
    user_input_message: str  # 선택: 사용자 입력 메시지
```

**계약 조건:**
- `todo.status`는 'pending' 또는 'in_progress'만 허용
- `todo.tool`은 반드시 지정되어야 함
- 실행 실패 시 `updated_todo.status`는 'completed' 불가

### 2.4 Response Layer I/O

```python
# 입력: schemas/response.py
class ResponseInput(BaseModel):
    user_input: str          # 필수: 원본 사용자 입력
    language: str            # 선택: 응답 언어 (기본: "ko")
    intent_summary: str      # 선택: Intent 요약
    ml_result: MLResult      # 선택: ML 분석 결과
    biz_result: BizResult    # 선택: 비즈니스 결과
    execution_results: Dict  # 선택: 실행 결과
    error: str               # 선택: 에러 메시지

# 출력: schemas/response.py
class ResponseOutput(BaseModel):
    response_text: str       # 필수: 응답 텍스트
    summary: str             # 선택: 요약
    attachments: List[str]   # 선택: 첨부 파일
    next_actions: List[str]  # 선택: 다음 액션 제안
    metadata: Dict           # 선택: 메타데이터
```

**계약 조건:**
- `response_text`는 빈 문자열 불가
- `language`는 'ko', 'en', 'ja', 'zh' 중 하나

## 3. 도구 인터페이스

### 3.1 ToolSpec (YAML 정의)

```yaml
# tools/definitions/*.yaml
name: tool_name           # 필수: 고유 식별자
version: "1.0.0"          # 필수: 시맨틱 버전
layer: execution          # 필수: 실행 레이어
domain: analysis          # 필수: 도메인

input_schema:             # 필수: 입력 스키마
  type: object
  properties:
    param1:
      type: string
      description: "설명"
  required: ["param1"]

output_schema:            # 필수: 출력 스키마
  type: object
  properties:
    result:
      type: string

dependencies: []          # 선택: 의존 도구
produces: []              # 선택: 생성 데이터
```

### 3.2 BaseTool 인터페이스

```python
class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """도구 이름 (고유 식별자)"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """도구 설명"""
        pass

    @abstractmethod
    async def execute(self, input: ToolInput) -> ToolOutput:
        """도구 실행"""
        pass
```

### 3.3 BaseDomainAgent 인터페이스

```python
class BaseDomainAgent(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """에이전트 이름"""
        pass

    @property
    @abstractmethod
    def domain(self) -> str:
        """도메인 (analysis, content, ops 등)"""
        pass

    @property
    @abstractmethod
    def supported_tools(self) -> List[str]:
        """지원하는 도구 목록"""
        pass

    @abstractmethod
    async def execute(self, input: ToolInput) -> ToolOutput:
        """에이전트 실행"""
        pass
```

## 4. API 인터페이스

### 4.1 REST API

```
POST /api/agent/run
Content-Type: application/json

Request:
{
    "user_input": string,     // 필수
    "session_id": string,     // 선택 (자동 생성)
    "context": object         // 선택
}

Response:
{
    "session_id": string,
    "response": string,
    "execution_results": object,
    "next_actions": string[],
    "metadata": object
}
```

### 4.2 WebSocket API

```
# 연결
ws://localhost:5000/ws

# 메시지 형식 (Client → Server)
{
    "type": "run" | "cancel" | "status",
    "payload": {
        "user_input": string,
        "session_id": string
    }
}

# 메시지 형식 (Server → Client)
{
    "type": "progress" | "todo_update" | "response" | "error",
    "payload": {
        "layer": string,
        "status": string,
        "data": object
    }
}
```

## 5. 데이터 모델 계약

### 5.1 Intent

```python
class Intent(BaseModel):
    intent_type: IntentType  # 필수: ANALYSIS, CONTENT, OPERATION 등
    sub_type: str            # 선택: 세부 유형
    confidence: float        # 필수: 0.0-1.0
    raw_query: str           # 필수: 원본 쿼리
```

### 5.2 TodoItem

```python
class TodoItem(BaseModel):
    id: str                  # 필수: UUID
    title: str               # 필수: 제목
    description: str         # 선택: 설명
    status: str              # 필수: pending | in_progress | completed | failed
    tool: str                # 필수: 실행 도구 이름
    layer: str               # 필수: execution 레이어
    priority: int            # 선택: 우선순위 (1-10)
    dependencies: List[str]  # 선택: 의존 Todo IDs
```

### 5.3 ExecutionResult

```python
class ExecutionResult(BaseModel):
    success: bool            # 필수: 성공 여부
    output: Any              # 필수: 실행 결과
    error: str               # 선택: 에러 메시지
    execution_time_ms: int   # 선택: 실행 시간
    metadata: Dict           # 선택: 메타데이터
```

## 6. 에러 코드

| 코드 | 이름 | 설명 |
|------|------|------|
| E001 | INVALID_INPUT | 입력 검증 실패 |
| E002 | INTENT_PARSE_FAILED | Intent 파싱 실패 |
| E003 | PLAN_GENERATION_FAILED | Plan 생성 실패 |
| E004 | TOOL_NOT_FOUND | 도구를 찾을 수 없음 |
| E005 | EXECUTION_FAILED | 실행 실패 |
| E006 | RESPONSE_GENERATION_FAILED | 응답 생성 실패 |
| E007 | VALIDATION_FAILED | 스키마 검증 실패 |
| E008 | DEPENDENCY_CYCLE | 순환 의존성 감지 |

## 7. 버전 관리 규칙

- **Major 변경**: 기존 계약을 깨는 변경 (예: 필수 필드 추가)
- **Minor 변경**: 하위 호환 기능 추가 (예: 선택 필드 추가)
- **Patch 변경**: 버그 수정, 문서 개선

모든 인터페이스 변경은 이 문서에 먼저 반영되어야 합니다.
