# Dream Agent 문서 인덱스

> 마지막 업데이트: 2025-02-03
> 문서 버전: 1.0.0

---

## 문서 상태 범례

| 아이콘 | 의미 |
|--------|------|
| ✅ | 구현 완료 / 검증됨 |
| ⚠️ | 부분 구현 / 검토 필요 |
| ❌ | 미구현 |
| 🔧 | 사용자 결정 필요 |

---

## 문서 목록

### 1. [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md) ✅
**시스템 아키텍처 문서**

| 섹션 | 내용 | 상태 |
|------|------|------|
| 5-Layer 아키텍처 | cognitive → planning → ml_execution → biz_execution → response | ✅ |
| 디렉토리 구조 | 실제 코드베이스 반영 (orchestrator/, 아님 graph/) | ✅ |
| Tool System | Phase 0-3 구현 완료 | ✅ |
| Domain Agents | 위치 및 구조 | ✅ |

### 2. [INTERFACE_CONTRACT.md](./INTERFACE_CONTRACT.md) ✅
**인터페이스 계약 문서**

| 섹션 | 내용 | 상태 |
|------|------|------|
| Layer I/O 스키마 | Cognitive, Planning, Execution, Response | ✅ |
| 데이터 모델 | Intent, TodoItem, ExecutionResult, Entity | ✅ |
| REST API | /api/agent/run, /run-async, /status, /stop | ✅ |
| WebSocket API | 실시간 업데이트 프로토콜 | ✅ |
| 에러 코드 | 표준 에러 코드 체계 | 🔧 |

### 3. [PLANNING.md](./PLANNING.md) ⚠️
**프로젝트 기획서**

| 섹션 | 내용 | 상태 |
|------|------|------|
| 기능 명세 | 레이어별 기능 현황 | ⚠️ 일부 미구현 |
| 도구 현황 | 18개 YAML 정의, 일부 Agent 미구현 | ⚠️ |
| 마일스톤 | Phase 0.5-3 완료, Phase 4-5 예정 | ⚠️ |
| 보안 요구사항 | 인증, 암호화 등 | 🔧 |

### 4. [TOOL_SPECIFICATION.md](./TOOL_SPECIFICATION.md) ✅
**도구 스펙 문서**

| 섹션 | 내용 | 상태 |
|------|------|------|
| YAML 형식 | 실제 사용 형식 (parameters 배열) | ✅ |
| 도구 목록 | 18개 도구 정의 | ✅ |
| 의존성 그래프 | 도구 간 의존 관계 | ✅ |
| Agent 매핑 | YAML ↔ Domain Agent 연동 | ⚠️ 5개 미구현 |

### 5. [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) ⚠️
**개발 가이드**

| 섹션 | 내용 | 상태 |
|------|------|------|
| 환경 설정 | Python, 의존성, 환경변수 | ✅ |
| 코딩 컨벤션 | 스타일, 명명 규칙, Import 순서 | ✅ |
| 테스트 가이드 | pytest 사용법, 구조 | ⚠️ 커버리지 미측정 |
| 배포 체크리스트 | 배포 전 확인 사항 | 🔧 |

---

## 빠른 참조

### 핵심 경로

```
backend/app/dream_agent/
├── schemas/           # I/O 스키마 정의
├── models/            # 데이터 모델
├── tools/definitions/ # YAML 도구 정의 (18개)
├── orchestrator/      # LangGraph 워크플로우
└── execution/domain/  # Domain Agents
```

### 주요 클래스

| 클래스 | 위치 | 용도 |
|--------|------|------|
| `Intent` | models/intent.py | 의도 분류 결과 |
| `TodoItem` | models/todo.py | 실행 작업 단위 |
| `Plan` | models/plan.py | 실행 계획 |
| `ExecutionResult` | models/execution.py | 실행 결과 |
| `MLResult`, `BizResult` | models/results.py | ML/비즈니스 결과 |
| `BaseDomainAgent` | execution/domain/base_agent.py | Agent 기본 클래스 |
| `ToolSpec` | models/tool.py | YAML 도구 스펙 |

### 추가 폴더 구조

```
workflow_manager/
├── hitl_manager/        # Human-in-the-Loop
│   ├── decision_manager.py
│   ├── input_requester.py
│   ├── pause_controller.py
│   ├── plan_editor.py
│   ├── nl_plan_modifier.py
│   └── replan_manager.py
├── feedback_manager/    # 피드백 관리
│   ├── feedback_manager.py
│   ├── plan_edit_logger.py
│   ├── query_logger.py
│   └── result_evaluator.py
├── approval_manager.py
├── base_manager.py
├── manager_registry.py
└── todo_failure_recovery.py

states/                  # LangGraph 상태
├── base.py
├── reducers.py
└── accessors.py

schemas/tool_io/         # Tool I/O 스키마
├── base.py
├── sentiment.py
├── keyword.py
├── collector.py
└── insight.py
```

### 주요 함수

```python
# 도구 시스템
from backend.app.dream_agent.tools import (
    get_tool_discovery,      # YAML 도구 조회
    get_tool_registry,       # 클래스 기반 도구
    validate_all_tools,      # 전체 검증
    get_tool_dependencies,   # 의존성 조회
)

# Domain Agent
from backend.app.dream_agent.execution.domain import (
    get_domain_agent_registry,
    get_domain_agent,
)
```

---

## 🔧 사용자 결정 필요 항목 요약

### 기술 결정

| 항목 | 현재 | 옵션 | 문서 |
|------|------|------|------|
| 세션 저장소 | In-memory | Redis / PostgreSQL | SYSTEM_ARCHITECTURE |
| 에러 코드 체계 | 미정의 | 표준 코드 적용 여부 | INTERFACE_CONTRACT |
| 테스트 커버리지 | 미측정 | 목표 설정 필요 | DEVELOPMENT_GUIDE |
| CI/CD | 없음 | GitHub Actions 등 | DEVELOPMENT_GUIDE |
| 모니터링 | 없음 | Prometheus 등 | DEVELOPMENT_GUIDE |

### 기능 결정

| 항목 | 현재 | 옵션 | 문서 |
|------|------|------|------|
| inventory_agent | 유일하게 미구현 | 구현 / 제거 | PLANNING |
| sales_agent 이름 | YAML↔Agent 불일치 | 이름 통일 | TOOL_SPECIFICATION |
| 인증 시스템 | 없음 | JWT / OAuth | PLANNING |
| 다국어 지원 | ko만 테스트 | 실제 테스트 범위 | PLANNING |

---

## 다음 단계 (권장)

### 즉시 필요

1. **inventory_agent 구현 또는 제거 결정**
   - 현재 유일하게 미구현된 Agent
   - YAML은 존재하나 Agent 파일 없음

2. **sales_agent 이름 통일**
   - YAML: `sales_agent`
   - Agent: `sales_material_generator.py`
   - 둘 중 하나로 통일 필요

3. **에러 코드 체계 확정**
   - INTERFACE_CONTRACT.md 6장 참조

4. **테스트 커버리지 목표 설정**
   - DEVELOPMENT_GUIDE.md 5.3장 참조

### 중기 목표

1. CI/CD 파이프라인 구축
2. 모니터링 시스템 도입
3. 배포 환경 결정 (AWS/GCP/On-premise)

### 장기 목표

1. 운영 환경 배포
2. 성능 최적화 (병렬 실행)
3. 보안 강화 (인증, 암호화)

---

## 문서 기여

문서 수정 시:
1. 변경 사항에 맞게 상태 아이콘 업데이트
2. INDEX.md 관련 섹션 업데이트
3. 커밋 메시지: `docs(<문서명>): <변경 내용>`

예시:
```
docs(PLANNING): Phase 4 마일스톤 업데이트
docs(INTERFACE_CONTRACT): 에러 코드 체계 확정
```
