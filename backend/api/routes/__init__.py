"""API Routes"""

from api.routes.agent import router as agent_router
from api.routes.health import router as health_router

__all__ = ["agent_router", "health_router"]
