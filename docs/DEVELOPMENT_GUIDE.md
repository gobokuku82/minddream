# Development Guide (개발 가이드)

## 1. 개발 환경 설정

### 1.1 필수 요구사항

| 항목 | 버전 | 비고 |
|------|------|------|
| Python | 3.10+ | 필수 |
| Node.js | 18+ | Dashboard 개발 시 |
| Git | 2.30+ | 버전 관리 |

### 1.2 설치

```bash
# 1. 저장소 클론
git clone <repository-url>
cd mind_dream/beta_v001

# 2. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경 변수 설정
cp .env.example .env
# .env 파일에 API 키 설정
```

### 1.3 환경 변수

```bash
# .env
OPENAI_API_KEY=sk-...
LANGCHAIN_API_KEY=lsv2_...
ENVIRONMENT=development
DEBUG=true
```

## 2. 프로젝트 구조

```
beta_v001/
├── backend/
│   ├── api/                 # API 라우트
│   │   └── routes/
│   │       └── agent.py
│   ├── app/
│   │   └── dream_agent/     # 핵심 에이전트
│   │       ├── cognitive/   # Cognitive Layer
│   │       ├── planning/    # Planning Layer
│   │       ├── execution/   # Execution Layer
│   │       ├── response/    # Response Layer
│   │       ├── graph/       # LangGraph 정의
│   │       ├── tools/       # Tool System
│   │       ├── models/      # Pydantic 모델
│   │       └── schemas/     # I/O 스키마
│   └── tests/               # 테스트
│
├── dashboard/               # Web UI
│   ├── templates/
│   ├── static/
│   └── app.py
│
├── docs/                    # 문서
└── README/                  # README 파일들
```

## 3. 코딩 컨벤션

### 3.1 Python 스타일

```python
# PEP 8 준수
# Black formatter 사용 권장

# 타입 힌트 필수
def process_data(input_data: str) -> Dict[str, Any]:
    """함수 설명.

    Args:
        input_data: 입력 데이터

    Returns:
        처리된 결과
    """
    pass

# Pydantic v2 스타일
class MyModel(BaseModel):
    field: str = Field(description="필드 설명")

    @field_validator('field')
    @classmethod
    def validate_field(cls, v):
        if not v:
            raise ValueError("field cannot be empty")
        return v
```

### 3.2 명명 규칙

| 항목 | 규칙 | 예시 |
|------|------|------|
| 파일명 | snake_case | `sentiment_analyzer.py` |
| 클래스 | PascalCase | `SentimentAnalyzer` |
| 함수/변수 | snake_case | `analyze_sentiment()` |
| 상수 | UPPER_SNAKE | `MAX_RETRIES` |
| YAML 도구명 | snake_case | `sentiment_analyzer` |

### 3.3 Import 순서

```python
# 1. 표준 라이브러리
import os
from typing import Dict, Any, List

# 2. 서드파티
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage

# 3. 로컬
from ..models.intent import Intent
from ..tools import get_tool_registry
```

## 4. 개발 워크플로우

### 4.1 브랜치 전략

```
main                 # 프로덕션
  └── develop        # 개발 통합
       ├── feature/xxx   # 기능 개발
       ├── fix/xxx       # 버그 수정
       └── refactor/xxx  # 리팩토링
```

### 4.2 커밋 메시지

```
<type>(<scope>): <description>

예시:
feat(tools): YAML 기반 Tool Discovery 시스템
fix(execution): Todo 상태 업데이트 버그 수정
refactor(models): Pydantic v2 마이그레이션
docs(readme): API 문서 업데이트
test(tools): ToolValidator 단위 테스트 추가
```

### 4.3 PR 체크리스트

- [ ] 테스트 통과
- [ ] 타입 힌트 추가
- [ ] 문서 업데이트 (필요시)
- [ ] INTERFACE_CONTRACT 준수
- [ ] 코드 리뷰 완료

## 5. 테스트 가이드

### 5.1 테스트 실행

```bash
# 전체 테스트
pytest

# 특정 테스트
pytest tests/unit/tools/test_tool_system.py

# 커버리지 포함
pytest --cov=backend/app
```

### 5.2 테스트 구조

```python
# tests/unit/tools/test_my_tool.py

import pytest
from backend.app.dream_agent.tools import get_tool_discovery

class TestMyTool:
    """MyTool 테스트"""

    @pytest.fixture
    def discovery(self):
        return get_tool_discovery()

    def test_tool_exists(self, discovery):
        """도구 존재 확인"""
        spec = discovery.get_spec("my_tool")
        assert spec is not None

    def test_tool_execution(self):
        """도구 실행 테스트"""
        # Given
        input_data = {"key": "value"}

        # When
        result = execute_tool("my_tool", input_data)

        # Then
        assert result.success
```

### 5.3 Mock 사용

```python
from unittest.mock import Mock, patch

@patch('backend.app.dream_agent.tools.execute_tool')
def test_with_mock(mock_execute):
    mock_execute.return_value = Mock(success=True)
    # 테스트 로직
```

## 6. 사전 조율 사항

### 6.1 레이어 간 데이터 전달

| 항목 | 합의 |
|------|------|
| 데이터 형식 | Pydantic 모델 사용 |
| 필수/선택 필드 | INTERFACE_CONTRACT 참조 |
| 에러 전파 | 각 레이어에서 처리, 다음 레이어로 에러 정보 전달 |
| 컨텍스트 공유 | AgentState를 통한 상태 공유 |

### 6.2 도구 개발 규칙

| 항목 | 규칙 |
|------|------|
| 정의 위치 | `tools/definitions/*.yaml` |
| 이름 형식 | snake_case, 고유해야 함 |
| 의존성 | 순환 의존성 금지 |
| 스키마 | JSON Schema 형식 필수 |
| 검증 | ToolValidator 통과 필수 |

### 6.3 API 변경 절차

1. INTERFACE_CONTRACT 문서 업데이트
2. 관련 팀 리뷰 및 승인
3. 스키마 변경 구현
4. 테스트 작성/수정
5. 문서 업데이트

### 6.4 에러 핸들링 규칙

```python
# 1. 검증 에러는 즉시 발생
if not valid:
    raise ValueError("Invalid input")

# 2. 실행 에러는 ExecutionResult로 반환
try:
    result = execute()
except Exception as e:
    return ExecutionResult(
        success=False,
        error=str(e)
    )

# 3. 치명적 에러는 로깅 후 상위로 전파
except CriticalError as e:
    logger.error(f"Critical error: {e}")
    raise
```

### 6.5 로깅 규칙

```python
import logging

logger = logging.getLogger(__name__)

# 레벨 가이드
logger.debug("상세 디버그 정보")      # 개발 시
logger.info("일반 정보")              # 주요 이벤트
logger.warning("경고")                # 잠재적 문제
logger.error("에러")                  # 실제 문제
logger.critical("치명적 에러")        # 시스템 중단
```

## 7. 성능 가이드라인

### 7.1 비동기 처리

```python
# 올바른 예
async def process():
    result1, result2 = await asyncio.gather(
        fetch_data1(),
        fetch_data2()
    )

# 잘못된 예
async def process():
    result1 = await fetch_data1()
    result2 = await fetch_data2()  # 불필요한 순차 실행
```

### 7.2 캐싱

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_tool_spec(name: str) -> ToolSpec:
    """자주 조회되는 도구 스펙 캐싱"""
    return discovery.get_spec(name)
```

### 7.3 지연 로딩

```python
# 필요할 때만 로드
def get_heavy_resource():
    if not hasattr(get_heavy_resource, '_cache'):
        get_heavy_resource._cache = load_heavy_resource()
    return get_heavy_resource._cache
```

## 8. 배포 체크리스트

### 8.1 배포 전 확인

- [ ] 모든 테스트 통과
- [ ] 환경 변수 설정 완료
- [ ] 의존성 버전 고정 (requirements.txt)
- [ ] 로그 레벨 적절히 설정
- [ ] 민감 정보 제거

### 8.2 모니터링 항목

- API 응답 시간
- 에러율
- 도구 실행 성공률
- LLM API 사용량
- 메모리/CPU 사용량

## 9. 문제 해결

### 9.1 자주 발생하는 문제

| 문제 | 원인 | 해결 |
|------|------|------|
| Import Error | 순환 참조 | TYPE_CHECKING 사용 |
| Validation Error | 스키마 불일치 | INTERFACE_CONTRACT 확인 |
| Tool Not Found | YAML 로드 실패 | 파일 경로/형식 확인 |
| Circular Dependency | 도구 의존성 순환 | 의존성 그래프 검토 |

### 9.2 디버깅 팁

```python
# 1. 상태 로깅
logger.debug(f"Current state: {state}")

# 2. 도구 검증
from dream_agent.tools import validate_all_tools
result = validate_all_tools()
print(result.errors)

# 3. 의존성 확인
from dream_agent.tools import get_tool_dependencies
deps = get_tool_dependencies("my_tool")
print(deps)
```

## 10. 연락처

문제 발생 시:
1. GitHub Issues 등록
2. 팀 슬랙 채널 문의
3. 담당자 직접 연락
