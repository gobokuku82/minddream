# Dream Agent 시스템 아키텍처

## 1. 개요

Dream Agent는 4-Layer Hand-off 아키텍처 기반의 AI 에이전트 시스템입니다.
LangGraph StateGraph를 활용하여 각 레이어 간 상태 전이를 관리합니다.

## 2. 시스템 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                        Dashboard (Web UI)                        │
│                   WebSocket 기반 실시간 통신                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Backend API                              │
│                    FastAPI + LangGraph                           │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│  Tool System  │      │ Domain Agents │      │   LLM Layer   │
│  (YAML 기반)  │      │  (비즈니스)   │      │  (OpenAI)     │
└───────────────┘      └───────────────┘      └───────────────┘
```

## 3. 4-Layer Hand-off 아키텍처

### 3.1 레이어 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                     Cognitive Layer (인지)                       │
│  - 사용자 입력 분석                                              │
│  - Intent 추출                                                   │
│  - 엔티티 인식                                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │ Intent, Entities
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Planning Layer (계획)                        │
│  - Todo 리스트 생성                                              │
│  - 실행 순서 결정                                                │
│  - 도구 선택                                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │ Plan, TodoItems
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Execution Layer (실행)                        │
│  - Supervisor가 조율                                             │
│  - Domain Agent 실행                                             │
│  - 도구 호출                                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │ ExecutionResults
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Response Layer (응답)                        │
│  - 결과 종합                                                     │
│  - 사용자 응답 생성                                              │
│  - 다음 액션 제안                                                │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 데이터 흐름

```
User Input
    │
    ▼
CognitiveInput ──► Cognitive Layer ──► CognitiveOutput
                                            │
                                            ▼
                   PlanningInput ◄── Intent, Entities
                        │
                        ▼
                   Planning Layer ──► PlanningOutput
                                            │
                                            ▼
                   ExecutionInput ◄── Plan, TodoItems
                        │
                        ▼
                   Execution Layer ──► ExecutionOutput
                                            │
                                            ▼
                   ResponseInput ◄── ExecutionResults
                        │
                        ▼
                   Response Layer ──► ResponseOutput
                                            │
                                            ▼
                                      User Response
```

## 4. 핵심 컴포넌트

### 4.1 LangGraph StateGraph

```python
# 상태 그래프 정의
workflow = StateGraph(AgentState)

# 노드 추가
workflow.add_node("cognitive", cognitive_node)
workflow.add_node("planning", planning_node)
workflow.add_node("execution", execution_node)
workflow.add_node("response", response_node)

# 조건부 엣지
workflow.add_conditional_edges(
    "cognitive",
    route_after_cognitive,
    {"planning": "planning", "response": "response"}
)
```

### 4.2 Tool System (Phase 0-3)

| Phase | 기능 | 파일 |
|-------|------|------|
| Phase 0 | YAML 기반 Tool Discovery | `tools/discovery.py`, `tools/loader.py` |
| Phase 1 | ToolSpec ↔ BaseTool 호환 | `tools/compat.py` |
| Phase 2 | Hot Reload, Domain Agent | `tools/hot_reload.py`, `execution/domain/` |
| Phase 3 | Validator, Schema 검증 | `tools/validator.py` |

### 4.3 Domain Agents

```
execution/domain/
├── base_agent.py      # BaseDomainAgent 추상 클래스
├── collection/        # 데이터 수집
│   ├── collector.py
│   └── preprocessor.py
├── analysis/          # 분석
│   ├── sentiment.py
│   ├── keyword.py
│   └── ...
├── insight/           # 인사이트 생성
├── content/           # 콘텐츠 생성
├── report/            # 리포트
└── ops/               # 운영 (dashboard, sales, inventory)
```

## 5. 디렉토리 구조

```
backend/
├── api/
│   └── routes/
│       └── agent.py           # API 라우트
├── app/
│   └── dream_agent/
│       ├── cognitive/         # Cognitive Layer
│       │   ├── cognitive_node.py
│       │   └── intent_parser.py
│       ├── planning/          # Planning Layer
│       │   ├── planning_node.py
│       │   └── plan_generator.py
│       ├── execution/         # Execution Layer
│       │   ├── execution_node.py
│       │   ├── supervisor.py
│       │   └── domain/        # Domain Agents
│       ├── response/          # Response Layer
│       │   └── response_node.py
│       ├── graph/             # LangGraph 정의
│       │   ├── builder.py
│       │   ├── state.py
│       │   └── transitions.py
│       ├── tools/             # Tool System
│       │   ├── discovery.py
│       │   ├── loader.py
│       │   ├── compat.py
│       │   ├── hot_reload.py
│       │   ├── validator.py
│       │   └── definitions/   # YAML 정의
│       ├── models/            # Pydantic 모델
│       └── schemas/           # I/O 스키마
│
dashboard/
├── templates/
│   └── index.html             # 3-Panel Layout
├── static/
│   ├── js/app.js              # WebSocket Client
│   └── css/style.css
└── app.py                     # Flask 서버
```

## 6. 기술 스택

| 영역 | 기술 |
|------|------|
| Backend Framework | FastAPI |
| Workflow Engine | LangGraph (StateGraph) |
| LLM | OpenAI GPT-4 |
| Validation | Pydantic v2 |
| Dashboard | Flask + WebSocket |
| 실시간 통신 | WebSocket |
| 설정 관리 | YAML |
| 테스트 | pytest |

## 7. 확장 포인트

### 7.1 새 도구 추가
1. `tools/definitions/`에 YAML 파일 추가
2. Hot Reload가 자동 감지
3. ToolValidator가 검증

### 7.2 새 Domain Agent 추가
1. `BaseDomainAgent` 상속
2. `@register_domain_agent` 데코레이터 적용
3. `execute()` 메서드 구현

### 7.3 새 레이어 추가
1. `schemas/`에 Input/Output 스키마 정의
2. `graph/transitions.py`에 전이 로직 추가
3. `graph/builder.py`에 노드 등록
