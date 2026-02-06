"""FastAPI Application

Main application entry point
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import agent_router, health_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.dream_agent.orchestrator import close_checkpointer, get_checkpointer

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler

    Startup: Initialize resources
    Shutdown: Cleanup resources
    """
    # === Startup ===
    logger.info(
        "Starting application",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )

    # Setup logging
    setup_logging()

    # Initialize checkpointer
    try:
        await get_checkpointer()
        logger.info("Checkpointer initialized")
    except Exception as e:
        logger.error("Failed to initialize checkpointer", error=str(e))
        # Continue without checkpointer for now

    yield

    # === Shutdown ===
    logger.info("Shutting down application")

    # Close checkpointer
    await close_checkpointer()

    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create FastAPI application"""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Dream Agent V2 - 4-Layer Hand-off Architecture AI Agent",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_router)
    app.include_router(agent_router, prefix="/api")

    return app


# Application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
