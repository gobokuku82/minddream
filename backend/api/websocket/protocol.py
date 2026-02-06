"""WebSocket Protocol

메시지 프로토콜 정의

Reference: docs/specs/WEBSOCKET_SPEC.md
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ServerMessageType(str, Enum):
    """서버 → 클라이언트 메시지 타입"""

    # 레이어 진행
    LAYER_START = "layer_start"
    LAYER_COMPLETE = "layer_complete"

    # Todo 상태
    TODO_UPDATE = "todo_update"

    # 실행 진행
    EXECUTION_PROGRESS = "execution_progress"

    # HITL
    HITL_REQUEST = "hitl_request"

    # 완료/에러
    COMPLETE = "complete"
    ERROR = "error"

    # 연결
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class ClientMessageType(str, Enum):
    """클라이언트 → 서버 메시지 타입"""

    # HITL 응답
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"
    INPUT = "input"

    # 제어
    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"

    # 하트비트
    PING = "ping"


class ServerMessage(BaseModel):
    """서버 메시지"""

    type: ServerMessageType
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None


class ClientMessage(BaseModel):
    """클라이언트 메시지"""

    type: ClientMessageType
    data: dict[str, Any] = Field(default_factory=dict)
    request_id: Optional[str] = None


# ── 메시지 생성 헬퍼 ──


def create_layer_start(layer: str, session_id: str) -> ServerMessage:
    """레이어 시작 메시지"""
    return ServerMessage(
        type=ServerMessageType.LAYER_START,
        data={"layer": layer},
        session_id=session_id,
    )


def create_layer_complete(
    layer: str,
    result: dict[str, Any],
    session_id: str,
) -> ServerMessage:
    """레이어 완료 메시지"""
    return ServerMessage(
        type=ServerMessageType.LAYER_COMPLETE,
        data={"layer": layer, "result": result},
        session_id=session_id,
    )


def create_todo_update(
    todo_id: str,
    status: str,
    progress: Optional[int] = None,
    session_id: Optional[str] = None,
) -> ServerMessage:
    """Todo 업데이트 메시지"""
    data = {"todo_id": todo_id, "status": status}
    if progress is not None:
        data["progress"] = progress

    return ServerMessage(
        type=ServerMessageType.TODO_UPDATE,
        data=data,
        session_id=session_id,
    )


def create_execution_progress(
    completed: int,
    total: int,
    current: Optional[str] = None,
    session_id: Optional[str] = None,
) -> ServerMessage:
    """실행 진행률 메시지"""
    return ServerMessage(
        type=ServerMessageType.EXECUTION_PROGRESS,
        data={
            "completed": completed,
            "total": total,
            "current": current,
        },
        session_id=session_id,
    )


def create_hitl_request(
    request_type: str,
    message: str,
    options: Optional[list[str]] = None,
    plan: Optional[dict] = None,
    session_id: Optional[str] = None,
) -> ServerMessage:
    """HITL 요청 메시지"""
    data = {
        "type": request_type,
        "message": message,
    }
    if options:
        data["options"] = options
    if plan:
        data["plan"] = plan

    return ServerMessage(
        type=ServerMessageType.HITL_REQUEST,
        data=data,
        session_id=session_id,
    )


def create_complete(
    response: dict[str, Any],
    session_id: Optional[str] = None,
) -> ServerMessage:
    """완료 메시지"""
    return ServerMessage(
        type=ServerMessageType.COMPLETE,
        data={"response": response},
        session_id=session_id,
    )


def create_error(
    code: str,
    message: str,
    session_id: Optional[str] = None,
) -> ServerMessage:
    """에러 메시지"""
    return ServerMessage(
        type=ServerMessageType.ERROR,
        data={"code": code, "message": message},
        session_id=session_id,
    )


def create_connected(session_id: str) -> ServerMessage:
    """연결 완료 메시지"""
    return ServerMessage(
        type=ServerMessageType.CONNECTED,
        data={"session_id": session_id},
        session_id=session_id,
    )
