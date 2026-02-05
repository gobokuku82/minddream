"""서버 실행 스크립트

Windows에서 psycopg async 호환을 위해
SelectorEventLoop 정책을 설정한 후 uvicorn을 시작합니다.

사용법:
    python run_server.py
"""

import sys
import asyncio

# Windows: psycopg async는 SelectorEventLoop 필요
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn
from backend.app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "backend.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
