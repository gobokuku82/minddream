"""Checkpointer - LangGraph AsyncPostgresSaver for state persistence

AsyncConnectionPool을 사용한 checkpointer 관리.
Windows에서는 main.py에서 WindowsSelectorEventLoopPolicy를 설정해야 합니다.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from backend.app.core.config import settings
from backend.app.core.logging import get_logger

logger = get_logger(__name__)

# Global connection pool (singleton)
_pool: Optional[AsyncConnectionPool] = None
_checkpointer: Optional[AsyncPostgresSaver] = None


async def get_connection_pool() -> AsyncConnectionPool:
    """
    Get or create the async connection pool for checkpointing.

    Returns:
        AsyncConnectionPool instance
    """
    global _pool

    if _pool is None:
        db_uri = settings.checkpoint_db_uri
        logger.info(f"Creating checkpoint connection pool for: {db_uri[:50]}...")

        _pool = AsyncConnectionPool(
            conninfo=db_uri,
            min_size=2,
            max_size=10,
            open=False,
        )
        await _pool.open()
        logger.info("Checkpoint connection pool opened")

    return _pool


async def get_checkpointer() -> AsyncPostgresSaver:
    """
    Get or create the AsyncPostgresSaver checkpointer.

    Returns:
        AsyncPostgresSaver instance
    """
    global _checkpointer

    if _checkpointer is None:
        pool = await get_connection_pool()
        _checkpointer = AsyncPostgresSaver(pool)
        logger.info("Checkpointer created (using existing tables)")

    return _checkpointer


@asynccontextmanager
async def checkpointer_context() -> AsyncGenerator[AsyncPostgresSaver, None]:
    """
    Context manager for one-off checkpointer usage.

    Usage:
        async with checkpointer_context() as checkpointer:
            agent = create_agent(checkpointer=checkpointer)
            await agent.ainvoke(...)
    """
    checkpointer = await get_checkpointer()
    try:
        yield checkpointer
    finally:
        pass


async def close_checkpointer():
    """
    Close the checkpointer and connection pool.

    Call this during application shutdown.
    """
    global _pool, _checkpointer

    if _pool is not None:
        await _pool.close()
        logger.info("Checkpoint connection pool closed")
        _pool = None

    _checkpointer = None


# ================================
# Lifespan Integration
# ================================

async def setup_checkpointer():
    """
    Setup checkpointer during application startup.

    Call this in FastAPI lifespan or startup event.
    """
    try:
        await get_checkpointer()
        logger.info("Checkpointer initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize checkpointer: {e}")
        raise


async def cleanup_checkpointer():
    """
    Cleanup checkpointer during application shutdown.

    Call this in FastAPI lifespan or shutdown event.
    """
    await close_checkpointer()
    logger.info("Checkpointer cleanup complete")
