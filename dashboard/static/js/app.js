/**
 * Dream Agent Dashboard - Frontend JavaScript
 */

class DreamAgentClient {
    constructor() {
        this.ws = null;
        this.sessionId = null;
        this.apiBase = 'http://localhost:8000';
        this.wsBase = 'ws://localhost:8000';

        // DOM Elements
        this.elements = {
            chatMessages: document.getElementById('chatMessages'),
            chatForm: document.getElementById('chatForm'),
            userInput: document.getElementById('userInput'),
            sendBtn: document.getElementById('sendBtn'),
            stopBtn: document.getElementById('stopBtn'),
            clearBtn: document.getElementById('clearBtn'),
            connectionStatus: document.getElementById('connectionStatus'),
            sessionId: document.getElementById('sessionId'),
            agentStatus: document.getElementById('agentStatus'),
            todoList: document.getElementById('todoList'),
        };

        this.init();
    }

    init() {
        // Event listeners
        this.elements.chatForm.addEventListener('submit', (e) => this.handleSubmit(e));
        this.elements.stopBtn.addEventListener('click', () => this.stopAgent());
        this.elements.clearBtn.addEventListener('click', () => this.clearChat());

        // Initial state
        this.updateConnectionStatus(false);
    }

    // ========== WebSocket ==========

    connectWebSocket(sessionId) {
        if (this.ws) {
            this.ws.close();
        }

        this.ws = new WebSocket(`${this.wsBase}/ws/${sessionId}`);

        this.ws.onopen = () => {
            console.log('[WS] Connected');
            this.updateConnectionStatus(true);
        };

        this.ws.onclose = () => {
            console.log('[WS] Disconnected');
            this.updateConnectionStatus(false);
        };

        this.ws.onerror = (error) => {
            console.error('[WS] Error:', error);
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleWSMessage(message);
        };
    }

    handleWSMessage(message) {
        console.log('[WS] Message:', message);

        switch (message.type) {
            case 'todo_update':
                this.updateTodoList(message.data);
                break;

            case 'complete':
                this.addMessage('assistant', message.data.response);
                this.setAgentStatus('completed');
                this.elements.stopBtn.disabled = true;
                break;

            case 'error':
                this.addMessage('error', `오류: ${message.data.error}`);
                this.setAgentStatus('failed');
                break;

            case 'hitl_request':
                this.handleHITLRequest(message.data);
                break;

            case 'pong':
                // Ping-pong response
                break;
        }
    }

    sendWSMessage(type, data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, data }));
        }
    }

    // ========== API Calls ==========

    async runAgent(userInput) {
        try {
            const response = await fetch(`${this.apiBase}/api/agent/run-async`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_input: userInput,
                    language: 'KOR',
                }),
            });

            const data = await response.json();
            this.sessionId = data.session_id;
            this.elements.sessionId.textContent = this.sessionId.substring(0, 8) + '...';

            // WebSocket 연결
            this.connectWebSocket(this.sessionId);

            return data;
        } catch (error) {
            console.error('[API] Error:', error);
            throw error;
        }
    }

    async stopAgent() {
        if (!this.sessionId) return;

        try {
            await fetch(`${this.apiBase}/api/agent/stop/${this.sessionId}`, {
                method: 'POST',
            });
            this.setAgentStatus('stopped');
            this.elements.stopBtn.disabled = true;
        } catch (error) {
            console.error('[API] Stop error:', error);
        }
    }

    // ========== UI Updates ==========

    async handleSubmit(e) {
        e.preventDefault();

        const userInput = this.elements.userInput.value.trim();
        if (!userInput) return;

        // Add user message
        this.addMessage('user', userInput);
        this.elements.userInput.value = '';

        // Disable input
        this.elements.sendBtn.disabled = true;
        this.elements.stopBtn.disabled = false;
        this.setAgentStatus('running');

        try {
            await this.runAgent(userInput);
        } catch (error) {
            this.addMessage('error', `연결 오류: ${error.message}`);
            this.setAgentStatus('failed');
        } finally {
            this.elements.sendBtn.disabled = false;
        }
    }

    addMessage(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.innerHTML = `<p>${this.formatMessage(content)}</p>`;

        this.elements.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    formatMessage(content) {
        // Basic markdown-like formatting
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }

    scrollToBottom() {
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }

    updateConnectionStatus(connected) {
        const el = this.elements.connectionStatus;
        el.textContent = connected ? 'Connected' : 'Disconnected';
        el.className = `status-badge ${connected ? 'connected' : 'disconnected'}`;
    }

    setAgentStatus(status) {
        this.elements.agentStatus.textContent = status;
    }

    updateTodoList(data) {
        // TODO: Render todos
        if (data.todos && data.todos.length > 0) {
            this.elements.todoList.innerHTML = data.todos.map(todo => `
                <div class="todo-item ${todo.status}">
                    <div class="task">${todo.task}</div>
                    <div class="meta">${todo.status}</div>
                </div>
            `).join('');
        }
    }

    handleHITLRequest(data) {
        // TODO: HITL 모달 표시
        this.addMessage('system', `[HITL] ${data.message}`);
    }

    clearChat() {
        this.elements.chatMessages.innerHTML = `
            <div class="message system">
                <p>대화가 초기화되었습니다.</p>
            </div>
        `;
        this.elements.todoList.innerHTML = '<p class="empty-state">실행 중인 작업이 없습니다.</p>';
        this.sessionId = null;
        this.elements.sessionId.textContent = '-';
        this.setAgentStatus('idle');
        this.elements.stopBtn.disabled = true;

        if (this.ws) {
            this.ws.close();
        }
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    window.agentClient = new DreamAgentClient();
});
