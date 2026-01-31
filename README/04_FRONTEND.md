# 04. 프론트엔드 (HTML 대시보드)

## 개요

> **목적**: 백엔드 테스트용 HTML 대시보드

프론트엔드는 순수 HTML/CSS/JavaScript로 구성되어 있으며, 백엔드 API 테스트를 위한 간단한 대시보드입니다.

```
dashboard/
├── templates/
│   └── index.html          # 메인 대시보드 UI
└── static/
    ├── css/
    │   └── style.css       # 스타일링
    └── js/
        └── app.js          # WebSocket 클라이언트
```

---

## 대시보드 레이아웃

```
┌──────────────────────────────────────────────────────────────────┐
│  Dream Agent Dashboard                          [● Connected]    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────┐  ┌────────────────────────┐ │
│  │                                │  │  Session Info          │ │
│  │                                │  │  ─────────────         │ │
│  │       Chat Messages            │  │  ID: abc123            │ │
│  │                                │  │  Status: running       │ │
│  │  [User] 라네즈 리뷰 분석해줘    │  │                        │ │
│  │                                │  ├────────────────────────┤ │
│  │  [Agent] 분석을 시작합니다...   │  │  Todo Progress         │ │
│  │                                │  │  ─────────────         │ │
│  │  [System] Todo 1 완료          │  │  ☑ 데이터 수집         │ │
│  │  [System] Todo 2 진행중        │  │  ☐ 전처리              │ │
│  │                                │  │  ☐ 감성 분석           │ │
│  │                                │  │  ☐ 인사이트 생성       │ │
│  │                                │  │                        │ │
│  │                                │  ├────────────────────────┤ │
│  │                                │  │  [Stop] [Clear]        │ │
│  └────────────────────────────────┘  └────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  메시지를 입력하세요...                           [Send]  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## HTML 구조 (index.html)

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>Dream Agent Dashboard</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <!-- 헤더 -->
    <header>
        <h1>Dream Agent Dashboard</h1>
        <span id="connection-status" class="status disconnected">
            ● Disconnected
        </span>
    </header>

    <!-- 메인 컨텐츠 -->
    <main>
        <!-- 채팅 영역 -->
        <section id="chat-section">
            <div id="messages"></div>
        </section>

        <!-- 사이드 패널 -->
        <aside id="side-panel">
            <!-- 세션 정보 -->
            <div id="session-info">
                <h3>Session Info</h3>
                <p>ID: <span id="session-id">-</span></p>
                <p>Status: <span id="agent-status">idle</span></p>
            </div>

            <!-- Todo 진행상황 -->
            <div id="todo-section">
                <h3>Todo Progress</h3>
                <ul id="todo-list"></ul>
            </div>

            <!-- 컨트롤 버튼 -->
            <div id="controls">
                <button id="stop-btn">Stop</button>
                <button id="clear-btn">Clear</button>
            </div>
        </aside>
    </main>

    <!-- 입력 영역 -->
    <footer>
        <input type="text" id="message-input" placeholder="메시지를 입력하세요...">
        <button id="send-btn">Send</button>
    </footer>

    <script src="/static/js/app.js"></script>
</body>
</html>
```

---

## JavaScript 클라이언트 (app.js)

### DreamAgentClient 클래스

```javascript
class DreamAgentClient {
    constructor() {
        this.ws = null;
        this.sessionId = null;
        this.isConnected = false;
    }

    // WebSocket 연결
    connect(sessionId) {
        this.sessionId = sessionId;
        this.ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);

        this.ws.onopen = () => {
            this.isConnected = true;
            this.updateConnectionStatus(true);
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };

        this.ws.onclose = () => {
            this.isConnected = false;
            this.updateConnectionStatus(false);
        };
    }

    // 메시지 처리
    handleMessage(message) {
        switch (message.type) {
            case 'todo_update':
                this.updateTodo(message.data);
                break;
            case 'complete':
                this.showResponse(message.data);
                break;
            case 'error':
                this.showError(message.data);
                break;
            case 'hitl_request':
                this.showHITLPrompt(message.data);
                break;
        }
    }

    // 에이전트 실행
    async runAgent(message) {
        const response = await fetch('/api/agent/run-async', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                session_id: this.sessionId
            })
        });

        const result = await response.json();
        if (!this.isConnected) {
            this.connect(result.session_id);
        }
    }

    // 실행 중지
    async stopAgent() {
        await fetch(`/api/agent/stop/${this.sessionId}`, {
            method: 'POST'
        });
    }

    // UI 업데이트 메서드
    updateConnectionStatus(connected) { ... }
    updateTodo(todoData) { ... }
    showResponse(data) { ... }
    showError(error) { ... }
    addMessage(type, content) { ... }
}

// 초기화
const client = new DreamAgentClient();
```

---

## CSS 스타일 (style.css)

```css
/* 레이아웃 */
body {
    display: flex;
    flex-direction: column;
    height: 100vh;
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background: #1a1a2e;
    color: white;
}

main {
    display: flex;
    flex: 1;
    overflow: hidden;
}

/* 채팅 영역 */
#chat-section {
    flex: 1;
    padding: 1rem;
    overflow-y: auto;
}

/* 메시지 스타일 */
.message {
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    border-radius: 8px;
    max-width: 80%;
}

.message.user {
    background: #e3f2fd;
    margin-left: auto;
}

.message.assistant {
    background: #f5f5f5;
}

.message.system {
    background: #fff3e0;
    font-size: 0.875rem;
}

.message.error {
    background: #ffebee;
    color: #c62828;
}

/* 사이드 패널 */
#side-panel {
    width: 280px;
    background: #f8f9fa;
    padding: 1rem;
    border-left: 1px solid #dee2e6;
}

/* 연결 상태 */
.status {
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.875rem;
}

.status.connected {
    background: #c8e6c9;
    color: #2e7d32;
}

.status.disconnected {
    background: #ffcdd2;
    color: #c62828;
}

/* Todo 리스트 */
#todo-list {
    list-style: none;
    padding: 0;
}

#todo-list li {
    padding: 0.5rem;
    margin-bottom: 0.25rem;
    border-radius: 4px;
    background: white;
}

#todo-list li.completed {
    text-decoration: line-through;
    color: #888;
}

#todo-list li.in_progress {
    border-left: 3px solid #2196f3;
}

/* 입력 영역 */
footer {
    display: flex;
    padding: 1rem;
    background: white;
    border-top: 1px solid #dee2e6;
}

#message-input {
    flex: 1;
    padding: 0.75rem;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    margin-right: 0.5rem;
}

#send-btn {
    padding: 0.75rem 1.5rem;
    background: #1976d2;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

#send-btn:hover {
    background: #1565c0;
}
```

---

## 주요 기능

### 1. 실시간 WebSocket 통신

```javascript
// 연결 → 메시지 전송 → 수신 → UI 업데이트

ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);

    if (msg.type === 'todo_update') {
        // Todo 진행상황 업데이트
        updateTodoUI(msg.data);
    }

    if (msg.type === 'complete') {
        // 최종 응답 표시
        showFinalResponse(msg.data.response);
    }
};
```

### 2. Todo 진행상황 표시

```javascript
function updateTodoUI(todoData) {
    const todoList = document.getElementById('todo-list');
    const todoItem = document.getElementById(`todo-${todoData.id}`);

    if (todoItem) {
        todoItem.className = todoData.status;
        todoItem.querySelector('.progress').textContent =
            `${todoData.progress}%`;
    }
}
```

### 3. 메시지 타입별 스타일링

```javascript
function addMessage(type, content) {
    const messagesEl = document.getElementById('messages');
    const msgEl = document.createElement('div');

    msgEl.className = `message ${type}`;
    msgEl.innerHTML = content;

    messagesEl.appendChild(msgEl);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

// 사용 예
addMessage('user', '라네즈 리뷰 분석해줘');
addMessage('assistant', '분석을 시작합니다...');
addMessage('system', 'Todo 1: 데이터 수집 완료');
addMessage('error', '실행 중 오류가 발생했습니다.');
```

### 4. Keep-Alive (Ping-Pong)

```javascript
// 30초마다 ping 전송
setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
    }
}, 30000);
```

---

## 이벤트 핸들러

```javascript
// 전송 버튼
document.getElementById('send-btn').addEventListener('click', () => {
    const input = document.getElementById('message-input');
    const message = input.value.trim();

    if (message) {
        client.runAgent(message);
        client.addMessage('user', message);
        input.value = '';
    }
});

// Enter 키로 전송
document.getElementById('message-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('send-btn').click();
    }
});

// 중지 버튼
document.getElementById('stop-btn').addEventListener('click', () => {
    client.stopAgent();
});

// 클리어 버튼
document.getElementById('clear-btn').addEventListener('click', () => {
    document.getElementById('messages').innerHTML = '';
    document.getElementById('todo-list').innerHTML = '';
});
```

---

## 접속 방법

```bash
# 1. 백엔드 서버 실행
cd backend
uvicorn api.main:app --reload --port 8000

# 2. 브라우저에서 접속
# http://localhost:8000
```

---

## 향후 개선사항

- [ ] React/Vue 기반 SPA로 전환
- [ ] 실시간 차트 시각화
- [ ] 히스토리 저장/불러오기
- [ ] 다크모드 지원
- [ ] 반응형 디자인 개선
