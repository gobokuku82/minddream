"""WebSocket Connection Manager

연결 관리 및 브로드캐스트

Reference: docs/specs/WEBSOCKET_SPEC.md
"""

import asyncio
from typing import Any, Optional

from fastapi import WebSocket

from app.core.logging import get_logger
from .protocol import ServerMessage

logger = get_logger(__name__)


class ConnectionManager:
    """WebSocket 연결 관리자"""

    def __init__(self):
        # session_id → WebSocket
        self._connections: dict[str, WebSocket] = {}
        # session_id → asyncio.Queue (메시지 큐)
        self._queues: dict[str, asyncio.Queue] = {}

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        """연결 수락

        Args:
            websocket: WebSocket 연결
            session_id: 세션 ID
        """
        await websocket.accept()
        self._connections[session_id] = websocket
        self._queues[session_id] = asyncio.Queue()

        logger.info("WebSocket connected", session_id=session_id)

    def disconnect(self, session_id: str) -> None:
        """연결 해제

        Args:
            session_id: 세션 ID
        """
        self._connections.pop(session_id, None)
        self._queues.pop(session_id, None)

        logger.info("WebSocket disconnected", session_id=session_id)

    def is_connected(self, session_id: str) -> bool:
        """연결 상태 확인"""
        return session_id in self._connections

    def get_connection(self, session_id: str) -> Optional[WebSocket]:
        """연결 조회"""
        return self._connections.get(session_id)

    async def send_message(
        self,
        session_id: str,
        message: ServerMessage,
    ) -> bool:
        """메시지 전송

        Args:
            session_id: 세션 ID
            message: 전송할 메시지

        Returns:
            전송 성공 여부
        """
        websocket = self._connections.get(session_id)
        if not websocket:
            logger.warning("No connection for session", session_id=session_id)
            return False

        try:
            await websocket.send_json(message.model_dump(mode="json"))
            return True
        except Exception as e:
            logger.error(
                "Failed to send message",
                session_id=session_id,
                error=str(e),
            )
            self.disconnect(session_id)
            return False

    async def send_json(
        self,
        session_id: str,
        data: dict[str, Any],
    ) -> bool:
        """JSON 직접 전송

        Args:
            session_id: 세션 ID
            data: JSON 데이터

        Returns:
            전송 성공 여부
        """
        websocket = self._connections.get(session_id)
        if not websocket:
            return False

        try:
            await websocket.send_json(data)
            return True
        except Exception as e:
            logger.error(
                "Failed to send json",
                session_id=session_id,
                error=str(e),
            )
            self.disconnect(session_id)
            return False

    async def broadcast(
        self,
        message: ServerMessage,
        exclude: Optional[list[str]] = None,
    ) -> None:
        """모든 연결에 브로드캐스트

        Args:
            message: 전송할 메시지
            exclude: 제외할 세션 ID 목록
        """
        exclude = exclude or []

        for session_id in list(self._connections.keys()):
            if session_id not in exclude:
                await self.send_message(session_id, message)

    def enqueue_message(self, session_id: str, message: ServerMessage) -> bool:
        """메시지 큐에 추가 (비동기 전송용)

        Args:
            session_id: 세션 ID
            message: 전송할 메시지

        Returns:
            큐 추가 성공 여부
        """
        queue = self._queues.get(session_id)
        if not queue:
            return False

        queue.put_nowait(message)
        return True

    async def process_queue(self, session_id: str) -> None:
        """메시지 큐 처리 (백그라운드 태스크)

        Args:
            session_id: 세션 ID
        """
        queue = self._queues.get(session_id)
        if not queue:
            return

        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=1.0)
                await self.send_message(session_id, message)
                queue.task_done()
            except asyncio.TimeoutError:
                if session_id not in self._connections:
                    break
            except Exception as e:
                logger.error(
                    "Queue processing error",
                    session_id=session_id,
                    error=str(e),
                )
                break

    def get_active_sessions(self) -> list[str]:
        """활성 세션 목록"""
        return list(self._connections.keys())

    def get_connection_count(self) -> int:
        """연결 수"""
        return len(self._connections)


# 싱글톤
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """ConnectionManager 싱글톤 반환"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
