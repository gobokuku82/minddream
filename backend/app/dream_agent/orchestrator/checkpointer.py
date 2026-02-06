"""Checkpointer Setup

AsyncPostgresSaver 설정
Reference: docs/specs/DB_SCHEMA.md#Checkpointer
"""

from typing import Optional

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Global checkpointer instance
_checkpointer: Optional[AsyncPostgresSaver] = None


async def get_checkpointer() -> AsyncPostgresSaver:
    """AsyncPostgresSaver 인스턴스 반환

    Returns:
        초기화된 AsyncPostgresSaver 인스턴스
    """
    global _checkpointer

    if _checkpointer is None:
        logger.info("Initializing AsyncPostgresSaver...")
        _checkpointer = AsyncPostgresSaver.from_conn_string(
            settings.DATABASE_URL
        )
        # 테이블 자동 생성
        await _checkpointer.setup()
        logger.info("AsyncPostgresSaver initialized successfully")

    return _checkpointer


async def close_checkpointer() -> None:
    """Checkpointer 연결 종료"""
    global _checkpointer

    if _checkpointer is not None:
        # AsyncPostgresSaver doesn't have explicit close method
        # Connection pool handles cleanup
        _checkpointer = None
        logger.info("Checkpointer connection closed")
