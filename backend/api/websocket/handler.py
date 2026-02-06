"""WebSocket Handler

WebSocket 요청 처리

Reference: docs/specs/WEBSOCKET_SPEC.md
"""

import asyncio
from typing import Any, Optional

from fastapi import WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.dream_agent.workflow_managers.hitl_manager import (
    get_hitl_manager,
    get_pause_controller,
)
from .manager import ConnectionManager, get_connection_manager
from .protocol import (
    ClientMessage,
    ClientMessageType,
    ServerMessage,
    ServerMessageType,
    create_connected,
    create_error,
)

logger = get_logger(__name__)


class WebSocketHandler:
    """WebSocket 핸들러"""

    def __init__(
        self,
        connection_manager: Optional[ConnectionManager] = None,
    ):
        self.manager = connection_manager or get_connection_manager()
        self.hitl_manager = get_hitl_manager()
        self.pause_controller = get_pause_controller()

    async def handle_connection(
        self,
        websocket: WebSocket,
        session_id: str,
    ) -> None:
        """WebSocket 연결 처리

        Args:
            websocket: WebSocket 연결
            session_id: 세션 ID
        """
        await self.manager.connect(websocket, session_id)

        try:
            # 연결 완료 메시지 전송
            await self.manager.send_message(
                session_id,
                create_connected(session_id),
            )

            # 메시지 수신 루프
            await self._receive_loop(websocket, session_id)

        except WebSocketDisconnect:
            logger.info("Client disconnected", session_id=session_id)
        except Exception as e:
            logger.error(
                "WebSocket error",
                session_id=session_id,
                error=str(e),
            )
        finally:
            self.manager.disconnect(session_id)
            self._cleanup(session_id)

    async def _receive_loop(
        self,
        websocket: WebSocket,
        session_id: str,
    ) -> None:
        """메시지 수신 루프"""
        while True:
            try:
                data = await websocket.receive_json()
                message = ClientMessage(**data)
                await self._handle_message(session_id, message)
            except WebSocketDisconnect:
                raise
            except Exception as e:
                logger.error(
                    "Message handling error",
                    session_id=session_id,
                    error=str(e),
                )
                await self.manager.send_message(
                    session_id,
                    create_error("INVALID_MESSAGE", str(e), session_id),
                )

    async def _handle_message(
        self,
        session_id: str,
        message: ClientMessage,
    ) -> None:
        """메시지 처리

        Args:
            session_id: 세션 ID
            message: 클라이언트 메시지
        """
        logger.debug(
            "Received message",
            session_id=session_id,
            type=message.type.value,
        )

        handlers = {
            ClientMessageType.APPROVE: self._handle_approve,
            ClientMessageType.REJECT: self._handle_reject,
            ClientMessageType.MODIFY: self._handle_modify,
            ClientMessageType.INPUT: self._handle_input,
            ClientMessageType.PAUSE: self._handle_pause,
            ClientMessageType.RESUME: self._handle_resume,
            ClientMessageType.CANCEL: self._handle_cancel,
            ClientMessageType.PING: self._handle_ping,
        }

        handler = handlers.get(message.type)
        if handler:
            await handler(session_id, message)
        else:
            logger.warning(
                "Unknown message type",
                session_id=session_id,
                type=message.type.value,
            )

    async def _handle_approve(
        self,
        session_id: str,
        message: ClientMessage,
    ) -> None:
        """승인 처리"""
        request = self.hitl_manager.get_pending_request(session_id)
        if not request:
            return

        self.hitl_manager.submit_response(
            request_id=request.request_id,
            action="approve",
            value=message.data.get("value"),
            comment=message.data.get("comment"),
        )

        logger.info("Plan approved via WebSocket", session_id=session_id)

    async def _handle_reject(
        self,
        session_id: str,
        message: ClientMessage,
    ) -> None:
        """거부 처리"""
        request = self.hitl_manager.get_pending_request(session_id)
        if not request:
            return

        self.hitl_manager.submit_response(
            request_id=request.request_id,
            action="reject",
            comment=message.data.get("comment"),
        )

        logger.info("Plan rejected via WebSocket", session_id=session_id)

    async def _handle_modify(
        self,
        session_id: str,
        message: ClientMessage,
    ) -> None:
        """수정 처리"""
        request = self.hitl_manager.get_pending_request(session_id)
        if not request:
            return

        self.hitl_manager.submit_response(
            request_id=request.request_id,
            action="modify",
            value=message.data.get("instruction"),
            comment=message.data.get("comment"),
        )

        logger.info("Plan modification requested via WebSocket", session_id=session_id)

    async def _handle_input(
        self,
        session_id: str,
        message: ClientMessage,
    ) -> None:
        """사용자 입력 처리"""
        request = self.hitl_manager.get_pending_request(session_id)
        if not request:
            return

        self.hitl_manager.submit_response(
            request_id=request.request_id,
            action="input",
            value=message.data.get("value"),
        )

        logger.info("User input received via WebSocket", session_id=session_id)

    async def _handle_pause(
        self,
        session_id: str,
        message: ClientMessage,
    ) -> None:
        """일시정지 처리"""
        reason = message.data.get("reason", "user_request")
        success = self.pause_controller.pause(session_id, reason)

        if success:
            await self.manager.send_message(
                session_id,
                ServerMessage(
                    type=ServerMessageType.TODO_UPDATE,
                    data={"status": "paused", "reason": reason},
                    session_id=session_id,
                ),
            )

    async def _handle_resume(
        self,
        session_id: str,
        message: ClientMessage,
    ) -> None:
        """재개 처리"""
        success = self.pause_controller.resume(session_id)

        if success:
            await self.manager.send_message(
                session_id,
                ServerMessage(
                    type=ServerMessageType.TODO_UPDATE,
                    data={"status": "resumed"},
                    session_id=session_id,
                ),
            )

    async def _handle_cancel(
        self,
        session_id: str,
        message: ClientMessage,
    ) -> None:
        """취소 처리"""
        request = self.hitl_manager.get_pending_request(session_id)
        if request:
            self.hitl_manager.cancel_request(request.request_id)

        logger.info("Session cancelled via WebSocket", session_id=session_id)

    async def _handle_ping(
        self,
        session_id: str,
        message: ClientMessage,
    ) -> None:
        """핑 응답"""
        await self.manager.send_json(
            session_id,
            {"type": "pong", "timestamp": message.data.get("timestamp")},
        )

    def _cleanup(self, session_id: str) -> None:
        """세션 정리"""
        self.hitl_manager.cleanup(session_id)
        self.pause_controller.cleanup(session_id)


# 싱글톤
_handler: Optional[WebSocketHandler] = None


def get_websocket_handler() -> WebSocketHandler:
    """WebSocketHandler 싱글톤 반환"""
    global _handler
    if _handler is None:
        _handler = WebSocketHandler()
    return _handler
