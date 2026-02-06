# WebSocket Protocol Specification

**Version**: 2.0 | **Date**: 2026-02-06 | **Status**: Draft

---

## 1. Overview

Dream Agent V2의 실시간 통신을 위한 WebSocket 프로토콜 명세입니다.

### 1.1 Design Goals

| Goal | Description |
|------|-------------|
| **Real-time Updates** | Todo 진행상황, Layer 전환 실시간 알림 |
| **HITL Support** | 양방향 통신으로 사용자 개입 지원 |
| **Session Binding** | 세션 기반 연결 관리 |
| **Reconnection** | 연결 복구 및 상태 동기화 |
| **Multi-client** | 동일 세션에 여러 클라이언트 지원 |

### 1.2 Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            Frontend                                      │
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │  WebSocket      │  │  Message        │  │  State                  │  │
│  │  Client         │  │  Handler        │  │  Manager                │  │
│  │                 │  │                 │  │                         │  │
│  │  • connect()    │  │  • onMessage()  │  │  • todos[]              │  │
│  │  • send()       │  │  • dispatch()   │  │  • plan                 │  │
│  │  • reconnect()  │  │                 │  │  • hitlPending          │  │
│  └────────┬────────┘  └────────┬────────┘  └─────────────────────────┘  │
│           │                    │                                         │
└───────────┼────────────────────┼─────────────────────────────────────────┘
            │                    │
            │  WebSocket Connection (wss://)
            │                    │
┌───────────┼────────────────────┼─────────────────────────────────────────┐
│           │                    │                   Backend               │
│  ┌────────▼────────────────────▼────────┐                               │
│  │           WebSocket Handler           │                               │
│  │                                       │                               │
│  │  ┌───────────────────────────────┐   │                               │
│  │  │    Connection Manager         │   │                               │
│  │  │    • session_connections{}    │   │                               │
│  │  │    • broadcast(session_id)    │   │                               │
│  │  │    • send_to_client(ws_id)    │   │                               │
│  │  └───────────────────────────────┘   │                               │
│  │                                       │                               │
│  │  ┌───────────────┐ ┌───────────────┐ │                               │
│  │  │ Message       │ │ HITL          │ │                               │
│  │  │ Router        │ │ Handler       │ │                               │
│  │  └───────┬───────┘ └───────┬───────┘ │                               │
│  └──────────┼─────────────────┼─────────┘                               │
│             │                 │                                          │
│  ┌──────────▼─────────────────▼──────────────────────────────────────┐  │
│  │                     LangGraph Agent                                │  │
│  │                                                                    │  │
│  │  Cognitive ──► Planning ──► Execution ──► Response                │  │
│  │      │            │             │                                  │  │
│  │   [event]     [event]       [event]                                │  │
│  │      │            │             │                                  │  │
│  │      └────────────┴─────────────┴──► CallbackManager ──► WS Send   │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Connection Management

### 2.1 Endpoint

```
WS  /ws/{session_id}
WSS /ws/{session_id}  (Production)
```

### 2.2 Connection Lifecycle

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Connection Lifecycle                              │
└─────────────────────────────────────────────────────────────────────┘

1. CONNECT
   Client ──[WS Handshake]──► Server
   └── Headers: { Authorization: Bearer <token> }  // optional

2. AUTHENTICATE (optional, if auth required)
   Client ──[auth]──► Server
   Server ──[auth_result]──► Client

3. SYNC (reconnection)
   Server ──[session_state]──► Client
   └── 현재 세션 상태 동기화

4. ACTIVE
   Server ◄══[bidirectional messages]══► Client

5. DISCONNECT
   └── Client 종료 또는 타임아웃
```

### 2.3 Connection Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | 세션 식별자 |
| `client_id` | string | No (query) | 클라이언트 식별자 (멀티 클라이언트용) |
| `resume_from` | string | No (query) | 재연결 시 마지막 메시지 ID |

**Example:**
```
ws://localhost:8000/ws/sess_abc123?client_id=browser_1&resume_from=msg_xyz
```

### 2.4 Multi-Client Support

동일 세션에 여러 클라이언트가 연결 가능:

```python
# Backend: ConnectionManager
class ConnectionManager:
    def __init__(self):
        # session_id → { client_id → WebSocket }
        self.connections: Dict[str, Dict[str, WebSocket]] = {}

    async def broadcast(self, session_id: str, message: dict):
        """세션의 모든 클라이언트에게 전송"""
        if session_id in self.connections:
            for ws in self.connections[session_id].values():
                await ws.send_json(message)

    async def send_to_client(self, session_id: str, client_id: str, message: dict):
        """특정 클라이언트에게만 전송"""
        if session_id in self.connections:
            if client_id in self.connections[session_id]:
                await self.connections[session_id][client_id].send_json(message)
```

---

## 3. Message Format

### 3.1 Base Message Structure

모든 메시지는 다음 구조를 따릅니다:

```typescript
interface BaseMessage {
  type: string;              // 메시지 타입
  session_id: string;        // 세션 ID
  message_id?: string;       // 메시지 고유 ID (재전송 방지)
  timestamp: string;         // ISO 8601 형식
  data?: any;                // 페이로드
}
```

### 3.2 Server → Client Messages

#### 3.2.1 Connection Messages

**Session State (연결/재연결 시)**
```json
{
  "type": "session_state",
  "session_id": "sess_abc123",
  "message_id": "msg_001",
  "timestamp": "2026-02-06T10:00:00Z",
  "data": {
    "status": "executing",
    "current_layer": "execution",
    "plan": {
      "id": "plan_xyz789",
      "status": "approved",
      "total_todos": 5
    },
    "todos": [...],
    "hitl_pending": null,
    "last_message_id": "msg_000"
  }
}
```

**Heartbeat (30초 간격)**
```json
{
  "type": "ping",
  "session_id": "sess_abc123",
  "timestamp": "2026-02-06T10:00:30Z"
}
```

#### 3.2.2 Layer Events

**Layer Start**
```json
{
  "type": "layer_start",
  "session_id": "sess_abc123",
  "message_id": "msg_002",
  "timestamp": "2026-02-06T10:00:01Z",
  "data": {
    "layer": "cognitive",
    "description": "의도 분석 시작"
  }
}
```

**Layer Complete**
```json
{
  "type": "layer_complete",
  "session_id": "sess_abc123",
  "message_id": "msg_003",
  "timestamp": "2026-02-06T10:00:05Z",
  "data": {
    "layer": "cognitive",
    "result": {
      "intent": {
        "domain": "analysis",
        "category": "sentiment_analysis",
        "confidence": 0.94
      },
      "entities": [
        {"type": "brand", "value": "라네즈", "confidence": 0.98}
      ]
    },
    "next_layer": "planning",
    "duration_ms": 4000
  }
}
```

#### 3.2.3 Plan Events

**Plan Generated**
```json
{
  "type": "plan_generated",
  "session_id": "sess_abc123",
  "message_id": "msg_004",
  "timestamp": "2026-02-06T10:00:10Z",
  "data": {
    "plan_id": "plan_xyz789",
    "version": 1,
    "status": "pending_approval",
    "todos": [
      {
        "id": "todo_001",
        "task": "올리브영 리뷰 수집",
        "tool": "collector",
        "status": "pending",
        "priority": 10,
        "depends_on": []
      },
      {
        "id": "todo_002",
        "task": "감성 분석",
        "tool": "sentiment_analyzer",
        "status": "pending",
        "priority": 8,
        "depends_on": ["todo_001"]
      }
    ],
    "dependency_graph": {
      "todo_001": [],
      "todo_002": ["todo_001"]
    },
    "estimated_duration_sec": 120,
    "mermaid_diagram": "graph LR\n  A[데이터 수집] --> B[감성 분석]"
  }
}
```

**Plan Approved**
```json
{
  "type": "plan_approved",
  "session_id": "sess_abc123",
  "message_id": "msg_006",
  "timestamp": "2026-02-06T10:00:25Z",
  "data": {
    "plan_id": "plan_xyz789",
    "approved_by": "user",
    "execution_starting": true
  }
}
```

**Plan Modified**
```json
{
  "type": "plan_modified",
  "session_id": "sess_abc123",
  "message_id": "msg_007",
  "timestamp": "2026-02-06T10:00:30Z",
  "data": {
    "plan_id": "plan_xyz789",
    "old_version": 1,
    "new_version": 2,
    "changes": [
      {"action": "add", "todo_id": "todo_003", "task": "경쟁사 분석"},
      {"action": "remove", "todo_id": "todo_005"}
    ],
    "updated_todos": [...]
  }
}
```

#### 3.2.4 Execution Events

**Todo Started**
```json
{
  "type": "todo_started",
  "session_id": "sess_abc123",
  "message_id": "msg_010",
  "timestamp": "2026-02-06T10:00:30Z",
  "data": {
    "todo_id": "todo_001",
    "task": "올리브영 리뷰 수집",
    "tool": "collector",
    "estimated_duration_sec": 30
  }
}
```

**Todo Progress**
```json
{
  "type": "todo_progress",
  "session_id": "sess_abc123",
  "message_id": "msg_011",
  "timestamp": "2026-02-06T10:00:45Z",
  "data": {
    "todo_id": "todo_001",
    "progress_percentage": 65,
    "current_step": "페이지 3/5 수집 중",
    "items_processed": 650,
    "items_total": 1000
  }
}
```

**Todo Completed**
```json
{
  "type": "todo_completed",
  "session_id": "sess_abc123",
  "message_id": "msg_012",
  "timestamp": "2026-02-06T10:01:00Z",
  "data": {
    "todo_id": "todo_001",
    "task": "올리브영 리뷰 수집",
    "status": "completed",
    "result_summary": {
      "collected_count": 987,
      "date_range": "2025-12-06 ~ 2026-02-05"
    },
    "duration_ms": 30000,
    "next_todos": ["todo_002"]
  }
}
```

**Todo Failed**
```json
{
  "type": "todo_failed",
  "session_id": "sess_abc123",
  "message_id": "msg_013",
  "timestamp": "2026-02-06T10:01:00Z",
  "data": {
    "todo_id": "todo_001",
    "task": "올리브영 리뷰 수집",
    "status": "failed",
    "error": {
      "code": "TOOL_EXECUTION_FAILED",
      "message": "Rate limit exceeded",
      "recoverable": true
    },
    "retry_count": 1,
    "max_retries": 3
  }
}
```

**Execution Progress**
```json
{
  "type": "execution_progress",
  "session_id": "sess_abc123",
  "message_id": "msg_014",
  "timestamp": "2026-02-06T10:02:00Z",
  "data": {
    "total_todos": 5,
    "completed": 2,
    "in_progress": 1,
    "pending": 2,
    "failed": 0,
    "progress_percentage": 40,
    "current_todo": {
      "id": "todo_003",
      "task": "키워드 분석"
    }
  }
}
```

#### 3.2.5 HITL Events

**Plan Review Request**
```json
{
  "type": "hitl_plan_review",
  "session_id": "sess_abc123",
  "message_id": "msg_005",
  "timestamp": "2026-02-06T10:00:15Z",
  "data": {
    "request_id": "hitl_001",
    "plan_id": "plan_xyz789",
    "plan": {
      "todos": [...],
      "dependency_graph": {...},
      "estimated_duration_sec": 120,
      "estimated_cost_usd": 0.05,
      "mermaid_diagram": "..."
    },
    "message": "실행 계획을 검토해주세요.",
    "options": ["approve", "modify", "reject"],
    "timeout_sec": 300
  }
}
```

**Approval Request (특정 Todo)**
```json
{
  "type": "hitl_approval_request",
  "session_id": "sess_abc123",
  "message_id": "msg_020",
  "timestamp": "2026-02-06T10:03:00Z",
  "data": {
    "request_id": "hitl_002",
    "todo_id": "todo_004",
    "todo": {
      "id": "todo_004",
      "task": "영상 콘텐츠 생성",
      "tool": "video_generator",
      "estimated_cost_usd": 0.50
    },
    "reason": "비용이 발생하는 작업입니다. 승인이 필요합니다.",
    "options": ["approve", "skip", "reject"],
    "timeout_sec": 600
  }
}
```

**Input Request**
```json
{
  "type": "hitl_input_request",
  "session_id": "sess_abc123",
  "message_id": "msg_021",
  "timestamp": "2026-02-06T10:03:30Z",
  "data": {
    "request_id": "hitl_003",
    "field": "date_range",
    "question": "분석할 기간을 선택해주세요.",
    "input_type": "choice",
    "options": [
      {"value": "1m", "label": "최근 1개월"},
      {"value": "3m", "label": "최근 3개월"},
      {"value": "6m", "label": "최근 6개월"},
      {"value": "custom", "label": "직접 입력"}
    ],
    "required": true,
    "default_value": "3m",
    "timeout_sec": 300
  }
}
```

**Clarification Request (Cognitive Layer)**
```json
{
  "type": "hitl_clarification",
  "session_id": "sess_abc123",
  "message_id": "msg_022",
  "timestamp": "2026-02-06T10:00:03Z",
  "data": {
    "request_id": "hitl_004",
    "original_input": "리뷰 분석해줘",
    "ambiguity": "브랜드가 명시되지 않았습니다.",
    "question": "어떤 브랜드의 리뷰를 분석할까요?",
    "input_type": "text",
    "suggestions": ["라네즈", "설화수", "이니스프리"],
    "required": true,
    "timeout_sec": 300
  }
}
```

**Pause Notification**
```json
{
  "type": "hitl_paused",
  "session_id": "sess_abc123",
  "message_id": "msg_025",
  "timestamp": "2026-02-06T10:04:00Z",
  "data": {
    "paused_by": "user",
    "reason": "중간 결과 확인",
    "current_todo": "todo_003",
    "completed_todos": ["todo_001", "todo_002"],
    "can_resume": true
  }
}
```

#### 3.2.6 Completion Events

**Session Complete**
```json
{
  "type": "complete",
  "session_id": "sess_abc123",
  "message_id": "msg_100",
  "timestamp": "2026-02-06T10:10:00Z",
  "data": {
    "status": "success",
    "response": {
      "format": "mixed",
      "text": "라네즈 리뷰 분석 결과입니다...",
      "summary": "전반적으로 긍정적 반응 (78%)",
      "attachments": [
        {
          "type": "chart",
          "title": "감성 분석 결과",
          "url": "/reports/sess_abc123/sentiment_chart.png"
        }
      ],
      "next_actions": [
        "경쟁사 비교 분석",
        "월간 트렌드 모니터링"
      ]
    },
    "statistics": {
      "total_todos": 5,
      "completed": 5,
      "failed": 0,
      "execution_time_ms": 45000,
      "tokens_used": 15000,
      "cost_usd": 0.08
    },
    "report_paths": [
      "/reports/sess_abc123/full_report.json",
      "/reports/sess_abc123/trend_report.pdf"
    ]
  }
}
```

**Session Failed**
```json
{
  "type": "failed",
  "session_id": "sess_abc123",
  "message_id": "msg_101",
  "timestamp": "2026-02-06T10:10:00Z",
  "data": {
    "status": "failed",
    "error": {
      "code": "EXECUTION_FAILED",
      "message": "분석 실행 중 오류가 발생했습니다.",
      "failed_todo": "todo_003",
      "recoverable": false
    },
    "partial_results": {
      "completed_todos": ["todo_001", "todo_002"],
      "available_data": {...}
    }
  }
}
```

#### 3.2.7 Error Events

```json
{
  "type": "error",
  "session_id": "sess_abc123",
  "message_id": "msg_err_001",
  "timestamp": "2026-02-06T10:05:00Z",
  "data": {
    "code": "TOOL_TIMEOUT",
    "message": "데이터 수집 시간 초과",
    "context": {
      "todo_id": "todo_001",
      "tool": "collector"
    },
    "recoverable": true,
    "suggested_action": "retry"
  }
}
```

---

## 4. Client → Server Messages

### 4.1 Connection Messages

**Pong (Heartbeat 응답)**
```json
{
  "type": "pong",
  "session_id": "sess_abc123",
  "timestamp": "2026-02-06T10:00:30Z"
}
```

### 4.2 HITL Responses

**Plan Response**
```json
{
  "type": "hitl_plan_response",
  "session_id": "sess_abc123",
  "data": {
    "request_id": "hitl_001",
    "action": "approve",
    "comment": "계획 승인합니다."
  }
}
```

```json
{
  "type": "hitl_plan_response",
  "session_id": "sess_abc123",
  "data": {
    "request_id": "hitl_001",
    "action": "modify",
    "instruction": "경쟁사 분석도 추가해주고, 영상 생성은 빼줘"
  }
}
```

**Approval Response**
```json
{
  "type": "hitl_approval_response",
  "session_id": "sess_abc123",
  "data": {
    "request_id": "hitl_002",
    "todo_id": "todo_004",
    "action": "approve",
    "comment": "영상 생성 승인"
  }
}
```

```json
{
  "type": "hitl_approval_response",
  "session_id": "sess_abc123",
  "data": {
    "request_id": "hitl_002",
    "todo_id": "todo_004",
    "action": "skip",
    "reason": "이번에는 영상 불필요"
  }
}
```

**Input Response**
```json
{
  "type": "hitl_input_response",
  "session_id": "sess_abc123",
  "data": {
    "request_id": "hitl_003",
    "field": "date_range",
    "value": "3m"
  }
}
```

**Clarification Response**
```json
{
  "type": "hitl_clarification_response",
  "session_id": "sess_abc123",
  "data": {
    "request_id": "hitl_004",
    "value": "라네즈"
  }
}
```

### 4.3 Control Commands

**Pause**
```json
{
  "type": "control_pause",
  "session_id": "sess_abc123",
  "data": {
    "reason": "중간 결과 확인 필요"
  }
}
```

**Resume**
```json
{
  "type": "control_resume",
  "session_id": "sess_abc123",
  "data": {
    "modifications": []
  }
}
```

**Cancel**
```json
{
  "type": "control_cancel",
  "session_id": "sess_abc123",
  "data": {
    "reason": "사용자 취소"
  }
}
```

**Retry Todo**
```json
{
  "type": "control_retry",
  "session_id": "sess_abc123",
  "data": {
    "todo_id": "todo_003"
  }
}
```

**Skip Todo**
```json
{
  "type": "control_skip",
  "session_id": "sess_abc123",
  "data": {
    "todo_id": "todo_004",
    "reason": "이번에는 불필요"
  }
}
```

---

## 5. Connection States & Reconnection

### 5.1 Connection States

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Connection State Machine                         │
└─────────────────────────────────────────────────────────────────────┘

                    ┌─────────────┐
                    │ DISCONNECTED│
                    └──────┬──────┘
                           │ connect()
                           ▼
                    ┌─────────────┐
                    │ CONNECTING  │
                    └──────┬──────┘
                           │ onOpen
                           ▼
                    ┌─────────────┐
         ┌─────────│ CONNECTED   │◄────────┐
         │         └──────┬──────┘         │
         │                │                 │ reconnect success
         │ ping timeout   │ auth/sync      │
         │                ▼                 │
         │         ┌─────────────┐         │
         │         │   ACTIVE    │─────────┤
         │         └──────┬──────┘         │
         │                │                 │
         │ error/close    │ pause           │
         │                ▼                 │
         │         ┌─────────────┐         │
         └────────►│ RECONNECTING│─────────┘
                   └──────┬──────┘
                          │ max retries exceeded
                          ▼
                   ┌─────────────┐
                   │   FAILED    │
                   └─────────────┘
```

### 5.2 Reconnection Strategy

```typescript
interface ReconnectionConfig {
  maxRetries: number;        // 최대 재시도 횟수 (default: 5)
  initialDelay: number;      // 초기 지연 시간 ms (default: 1000)
  maxDelay: number;          // 최대 지연 시간 ms (default: 30000)
  backoffMultiplier: number; // 지연 증가 배수 (default: 2)
}

// 재시도 지연 계산
delay = min(initialDelay * (backoffMultiplier ^ retryCount), maxDelay)

// Example: 1s, 2s, 4s, 8s, 16s (capped at maxDelay)
```

### 5.3 State Synchronization

재연결 시 상태 동기화 절차:

```
1. Client: Connect with resume_from=<last_message_id>
2. Server: 세션 상태 조회
3. Server: session_state 메시지 전송 (현재 상태)
4. Server: 누락된 메시지 재전송 (resume_from 이후)
5. Client: 상태 동기화 완료
```

---

## 6. Error Handling

### 6.1 Error Categories

| Category | Code Range | Description |
|----------|------------|-------------|
| Connection | 1000-1999 | WebSocket 연결 오류 |
| Authentication | 2000-2999 | 인증/권한 오류 |
| Session | 3000-3999 | 세션 관련 오류 |
| Execution | 4000-4999 | 실행 오류 |
| HITL | 5000-5999 | HITL 관련 오류 |

### 6.2 Error Codes

```typescript
enum WebSocketErrorCode {
  // Connection
  WS_CONNECTION_FAILED = 1001,
  WS_CONNECTION_TIMEOUT = 1002,
  WS_INVALID_MESSAGE = 1003,

  // Authentication
  WS_AUTH_REQUIRED = 2001,
  WS_AUTH_FAILED = 2002,
  WS_TOKEN_EXPIRED = 2003,

  // Session
  WS_SESSION_NOT_FOUND = 3001,
  WS_SESSION_EXPIRED = 3002,
  WS_SESSION_INVALID_STATE = 3003,

  // Execution
  WS_EXECUTION_FAILED = 4001,
  WS_TODO_FAILED = 4002,
  WS_TOOL_TIMEOUT = 4003,

  // HITL
  WS_HITL_TIMEOUT = 5001,
  WS_HITL_INVALID_RESPONSE = 5002,
  WS_HITL_REQUEST_EXPIRED = 5003
}
```

### 6.3 Error Recovery

| Error Type | Recovery Strategy |
|------------|-------------------|
| Connection Lost | 자동 재연결 + 상태 동기화 |
| Session Expired | 새 세션 생성 안내 |
| Todo Failed | retry 또는 skip 선택 |
| HITL Timeout | 기본값 적용 또는 취소 |

---

## 7. Security

### 7.1 Authentication

```typescript
// Option 1: Query Parameter (development)
ws://localhost:8000/ws/sess_abc123?token=<jwt>

// Option 2: First Message (recommended)
{
  "type": "auth",
  "data": {
    "token": "<jwt>",
    "api_key": "<api_key>"  // optional
  }
}
```

### 7.2 Authorization

- 세션 소유자만 연결 가능
- HITL 응답은 권한 있는 사용자만
- 관리자는 모든 세션 모니터링 가능

### 7.3 Rate Limiting

| Action | Limit |
|--------|-------|
| Connect | 10/min per user |
| Messages | 100/min per connection |
| HITL Responses | 30/min per session |

---

## 8. Frontend Integration

### 8.1 React Hook Example

```typescript
// hooks/useAgentWebSocket.ts

interface UseAgentWebSocketOptions {
  sessionId: string;
  onLayerStart?: (data: LayerStartData) => void;
  onTodoUpdate?: (data: TodoUpdateData) => void;
  onHitlRequest?: (data: HitlRequestData) => void;
  onComplete?: (data: CompleteData) => void;
  onError?: (error: WebSocketError) => void;
}

function useAgentWebSocket(options: UseAgentWebSocketOptions) {
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [sessionState, setSessionState] = useState<SessionState | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    const ws = new WebSocket(`${WS_URL}/ws/${options.sessionId}`);

    ws.onopen = () => {
      setConnectionState('connected');
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleMessage(message);
    };

    ws.onclose = (event) => {
      setConnectionState('disconnected');
      if (!event.wasClean) {
        scheduleReconnect();
      }
    };

    wsRef.current = ws;
  }, [options.sessionId]);

  const sendHitlResponse = useCallback((requestId: string, response: HitlResponse) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: `hitl_${response.type}_response`,
        session_id: options.sessionId,
        data: {
          request_id: requestId,
          ...response
        }
      }));
    }
  }, [options.sessionId]);

  const pause = useCallback(() => {
    send({ type: 'control_pause', data: {} });
  }, []);

  const resume = useCallback(() => {
    send({ type: 'control_resume', data: {} });
  }, []);

  return {
    connectionState,
    sessionState,
    connect,
    disconnect,
    sendHitlResponse,
    pause,
    resume
  };
}
```

### 8.2 Message Handler Pattern

```typescript
// handlers/messageHandler.ts

type MessageHandler = (data: any) => void;

const messageHandlers: Record<string, MessageHandler> = {
  session_state: (data) => {
    store.dispatch(setSessionState(data));
  },

  layer_start: (data) => {
    store.dispatch(setCurrentLayer(data.layer));
  },

  todo_started: (data) => {
    store.dispatch(updateTodo({ id: data.todo_id, status: 'in_progress' }));
  },

  todo_progress: (data) => {
    store.dispatch(updateTodoProgress(data));
  },

  todo_completed: (data) => {
    store.dispatch(updateTodo({ id: data.todo_id, status: 'completed', result: data.result_summary }));
  },

  hitl_plan_review: (data) => {
    store.dispatch(setHitlPending({ type: 'plan_review', data }));
    showPlanReviewModal(data);
  },

  hitl_approval_request: (data) => {
    store.dispatch(setHitlPending({ type: 'approval', data }));
    showApprovalModal(data);
  },

  complete: (data) => {
    store.dispatch(setSessionComplete(data));
  },

  error: (data) => {
    handleError(data);
  }
};

function handleMessage(message: BaseMessage) {
  const handler = messageHandlers[message.type];
  if (handler) {
    handler(message.data);
  } else {
    console.warn('Unknown message type:', message.type);
  }
}
```

---

## 9. Backend Implementation

### 9.1 WebSocket Handler

```python
# api/websocket/handler.py

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)

        # 세션 상태 동기화
        await self.send_session_state(session_id, websocket)

    async def disconnect(self, session_id: str, websocket: WebSocket):
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)

    async def broadcast(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                await connection.send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(session_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await handle_client_message(session_id, data)
    except WebSocketDisconnect:
        await manager.disconnect(session_id, websocket)
```

### 9.2 Event Emission from LangGraph

```python
# workflow_managers/callback_manager/websocket_callback.py

from langgraph.types import StreamWriter

class WebSocketCallbackHandler:
    def __init__(self, session_id: str, connection_manager: ConnectionManager):
        self.session_id = session_id
        self.manager = connection_manager

    async def on_layer_start(self, layer: str):
        await self.manager.broadcast(self.session_id, {
            "type": "layer_start",
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"layer": layer}
        })

    async def on_todo_update(self, todo_id: str, status: str, progress: int = None):
        await self.manager.broadcast(self.session_id, {
            "type": "todo_progress" if progress else "todo_started",
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "todo_id": todo_id,
                "status": status,
                "progress_percentage": progress
            }
        })
```

---

## 10. Testing

### 10.1 WebSocket Test Client

```python
# tests/test_websocket.py

import pytest
import asyncio
from websockets import connect

@pytest.mark.asyncio
async def test_websocket_connection():
    async with connect(f"ws://localhost:8000/ws/test_session") as ws:
        # 연결 후 session_state 수신
        message = await ws.recv()
        data = json.loads(message)
        assert data["type"] == "session_state"

@pytest.mark.asyncio
async def test_hitl_flow():
    async with connect(f"ws://localhost:8000/ws/test_session") as ws:
        # Plan review 대기
        while True:
            message = json.loads(await ws.recv())
            if message["type"] == "hitl_plan_review":
                # Plan 승인
                await ws.send(json.dumps({
                    "type": "hitl_plan_response",
                    "session_id": "test_session",
                    "data": {
                        "request_id": message["data"]["request_id"],
                        "action": "approve"
                    }
                }))
                break

        # Complete 대기
        while True:
            message = json.loads(await ws.recv())
            if message["type"] == "complete":
                assert message["data"]["status"] == "success"
                break
```

---

## Related Documents

- [API_SPEC.md](API_SPEC.md) - REST API 명세
- [HITL_SPEC.md](HITL_SPEC.md) - HITL 시스템 상세
- [SESSION_SPEC.md](SESSION_SPEC.md) - 세션 관리
- [ERROR_CODES.md](ERROR_CODES.md) - 에러 코드 체계

---

*Last Updated: 2026-02-06*
