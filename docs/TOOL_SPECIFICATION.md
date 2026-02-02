# Tool Specification (도구 스펙 문서)

## 1. 개요

Dream Agent의 도구 시스템은 YAML 기반 선언적 정의를 사용합니다.
이 문서는 도구 정의 형식, 검증 규칙, 확장 방법을 설명합니다.

## 2. YAML 도구 정의 형식

### 2.1 기본 구조

```yaml
# tools/definitions/{tool_name}.yaml

# === 필수 필드 ===
name: tool_name              # 고유 식별자 (snake_case)
version: "1.0.0"             # 시맨틱 버전
layer: execution             # 실행 레이어
domain: analysis             # 도메인 영역
description: "도구 설명"      # 도구 설명

# === 스키마 정의 ===
input_schema:                # 입력 JSON Schema
  type: object
  properties:
    param1:
      type: string
      description: "파라미터 설명"
  required: ["param1"]

output_schema:               # 출력 JSON Schema
  type: object
  properties:
    result:
      type: string

# === 선택 필드 ===
dependencies: []             # 의존 도구 목록
produces: []                 # 생성하는 데이터 유형
tags: []                     # 검색용 태그
config: {}                   # 추가 설정
```

### 2.2 필드 설명

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `name` | string | ✅ | 고유 식별자. snake_case 형식 |
| `version` | string | ✅ | 시맨틱 버전 (x.y.z) |
| `layer` | string | ✅ | 실행 레이어 (collection, analysis, insight, content, report, ops) |
| `domain` | string | ✅ | 도메인 (data, analysis, insight, content, business) |
| `description` | string | ✅ | 도구 설명 |
| `input_schema` | object | ✅ | 입력 JSON Schema |
| `output_schema` | object | ✅ | 출력 JSON Schema |
| `dependencies` | array | ❌ | 의존하는 도구 이름 목록 |
| `produces` | array | ❌ | 생성하는 데이터 유형 |
| `tags` | array | ❌ | 검색/분류용 태그 |
| `config` | object | ❌ | 도구별 추가 설정 |

## 3. 레이어 정의

### 3.1 레이어 목록

| 레이어 | 설명 | 실행 순서 |
|--------|------|-----------|
| `collection` | 데이터 수집 | 1 |
| `analysis` | 데이터 분석 | 2 |
| `insight` | 인사이트 생성 | 3 |
| `content` | 콘텐츠 생성 | 4 |
| `report` | 리포트 생성 | 5 |
| `ops` | 운영 작업 | 6 |

### 3.2 레이어 → Executor 매핑

```python
LAYER_TO_EXECUTOR = {
    "collection": "collection_executor",
    "analysis": "analysis_executor",
    "insight": "insight_executor",
    "content": "content_executor",
    "report": "report_executor",
    "ops": "ops_executor",
}
```

## 4. 도메인 정의

| 도메인 | 설명 | 예시 도구 |
|--------|------|-----------|
| `data` | 데이터 수집/처리 | collector, preprocessor |
| `analysis` | 분석 | sentiment, keyword, absa |
| `insight` | 인사이트 도출 | insight_generator |
| `content` | 콘텐츠 생성 | ad_creative, storyboard |
| `business` | 비즈니스 운영 | dashboard, sales, inventory |

## 5. 현재 정의된 도구

### 5.1 Collection Layer

#### preprocessor
```yaml
name: preprocessor
version: "1.0.0"
layer: collection
domain: data
description: "수집된 데이터를 분석 가능한 형태로 전처리"
dependencies: ["collector"]
produces: ["preprocessed_data"]
```

#### google_trends
```yaml
name: google_trends
version: "1.0.0"
layer: collection
domain: data
description: "Google Trends 데이터 수집"
dependencies: []
produces: ["trend_data"]
```

### 5.2 Analysis Layer

#### sentiment_analyzer
```yaml
name: sentiment_analyzer
version: "1.0.0"
layer: analysis
domain: analysis
description: "텍스트 감성 분석"
dependencies: ["preprocessor"]
produces: ["sentiment_result"]
```

#### keyword_analyzer
```yaml
name: keyword_analyzer
version: "1.0.0"
layer: analysis
domain: analysis
description: "키워드 추출 및 분석"
dependencies: ["preprocessor"]
produces: ["keyword_result"]
```

#### absa_analyzer
```yaml
name: absa_analyzer
version: "1.0.0"
layer: analysis
domain: analysis
description: "속성 기반 감성 분석 (Aspect-Based Sentiment Analysis)"
dependencies: ["preprocessor"]
produces: ["absa_result"]
```

#### problem_classifier
```yaml
name: problem_classifier
version: "1.0.0"
layer: analysis
domain: analysis
description: "문제/이슈 분류"
dependencies: ["preprocessor"]
produces: ["problem_classification"]
```

#### hashtag_analyzer
```yaml
name: hashtag_analyzer
version: "1.0.0"
layer: analysis
domain: analysis
description: "해시태그 분석 및 추천"
dependencies: ["keyword_analyzer"]
produces: ["hashtag_result"]
```

#### competitor_analyzer
```yaml
name: competitor_analyzer
version: "1.0.0"
layer: analysis
domain: analysis
description: "경쟁사 분석"
dependencies: ["preprocessor"]
produces: ["competitor_result"]
```

### 5.3 Insight Layer

#### insight_generator
```yaml
name: insight_generator
version: "1.0.0"
layer: insight
domain: insight
description: "분석 결과 기반 인사이트 생성"
dependencies: ["sentiment_analyzer", "keyword_analyzer"]
produces: ["insights"]
```

#### insight_with_trends
```yaml
name: insight_with_trends
version: "1.0.0"
layer: insight
domain: insight
description: "트렌드 데이터 포함 인사이트 생성"
dependencies: ["insight_generator", "google_trends"]
produces: ["insights_with_trends"]
```

### 5.4 Content Layer

#### ad_creative_agent
```yaml
name: ad_creative_agent
version: "1.0.0"
layer: content
domain: content
description: "광고 크리에이티브 생성"
dependencies: ["insight_generator"]
produces: ["ad_creative"]
```

#### storyboard_agent
```yaml
name: storyboard_agent
version: "1.0.0"
layer: content
domain: content
description: "스토리보드 생성"
dependencies: ["ad_creative_agent"]
produces: ["storyboard"]
```

#### video_agent
```yaml
name: video_agent
version: "1.0.0"
layer: content
domain: content
description: "영상 기획/생성"
dependencies: ["storyboard_agent"]
produces: ["video_plan"]
```

### 5.5 Ops Layer

#### dashboard_agent
```yaml
name: dashboard_agent
version: "1.0.0"
layer: ops
domain: business
description: "대시보드 생성"
dependencies: []
produces: ["dashboard"]
```

#### sales_agent
```yaml
name: sales_agent
version: "1.0.0"
layer: ops
domain: business
description: "매출 분석"
dependencies: []
produces: ["sales_analysis"]
```

#### inventory_agent
```yaml
name: inventory_agent
version: "1.0.0"
layer: ops
domain: business
description: "재고 관리"
dependencies: []
produces: ["inventory_status"]
```

## 6. 의존성 그래프

```
collector
    │
    ▼
preprocessor
    │
    ├──────────────────────────────────────┐
    ▼                                      ▼
sentiment_analyzer                   keyword_analyzer
    │                                      │
    │                                      ├───► hashtag_analyzer
    │                                      │
    ├──────────────┬───────────────────────┤
    ▼              ▼                       ▼
insight_generator ◄────────────────────────┘
    │
    ├───► insight_with_trends ◄── google_trends
    │
    ▼
ad_creative_agent
    │
    ▼
storyboard_agent
    │
    ▼
video_agent
```

## 7. 검증 규칙

### 7.1 필수 필드 검증
- `name`: 비어있지 않아야 함, snake_case
- `version`: 시맨틱 버전 형식
- `layer`: 허용된 레이어 중 하나
- `domain`: 비어있지 않아야 함
- `input_schema`: 유효한 JSON Schema
- `output_schema`: 유효한 JSON Schema

### 7.2 의존성 검증
- 모든 의존 도구가 존재해야 함
- 순환 의존성 불허
- 자기 자신 의존 불허

### 7.3 스키마 검증
- `type` 필드 필수
- `properties`는 object 타입에 필수
- `required` 배열의 항목은 properties에 존재해야 함

## 8. 새 도구 추가 방법

### Step 1: YAML 파일 생성

```bash
# tools/definitions/my_new_tool.yaml 생성
```

### Step 2: 기본 구조 작성

```yaml
name: my_new_tool
version: "1.0.0"
layer: analysis        # 적절한 레이어 선택
domain: analysis       # 적절한 도메인 선택
description: "새 도구 설명"

input_schema:
  type: object
  properties:
    input_data:
      type: string
      description: "입력 데이터"
  required: ["input_data"]

output_schema:
  type: object
  properties:
    result:
      type: object
      description: "분석 결과"

dependencies:
  - preprocessor       # 필요한 의존 도구

produces:
  - my_new_result      # 생성하는 데이터 유형
```

### Step 3: Hot Reload 확인

파일 저장 시 자동으로 로드됩니다.
로그에서 확인:
```
INFO: Tool reloaded: my_new_tool
```

### Step 4: 검증

```python
from dream_agent.tools import validate_tool_spec, get_tool_discovery

discovery = get_tool_discovery()
spec = discovery.get_spec("my_new_tool")
result = validate_tool_spec(spec)

if not result.valid:
    print(result.errors)
```

## 9. Best Practices

1. **명확한 이름**: 도구의 기능을 나타내는 명확한 이름 사용
2. **버전 관리**: 변경 시 버전 업데이트
3. **의존성 최소화**: 필요한 의존성만 선언
4. **스키마 상세화**: 입출력 스키마를 상세히 정의
5. **태그 활용**: 검색 용이성을 위한 태그 추가
