"""WebSocket Package

WebSocket 핸들러 및 프로토콜

Reference: docs/specs/WEBSOCKET_SPEC.md
"""

from .handler import WebSocketHandler, get_websocket_handler
from .manager import ConnectionManager, get_connection_manager
from .protocol import (
    ClientMessage,
    ClientMessageType,
    ServerMessage,
    ServerMessageType,
    create_complete,
    create_connected,
    create_error,
    create_execution_progress,
    create_hitl_request,
    create_layer_complete,
    create_layer_start,
    create_todo_update,
)

__all__ = [
    # Handler
    "WebSocketHandler",
    "get_websocket_handler",
    # Manager
    "ConnectionManager",
    "get_connection_manager",
    # Protocol
    "ServerMessage",
    "ServerMessageType",
    "ClientMessage",
    "ClientMessageType",
    # Message creators
    "create_layer_start",
    "create_layer_complete",
    "create_todo_update",
    "create_execution_progress",
    "create_hitl_request",
    "create_complete",
    "create_error",
    "create_connected",
]
