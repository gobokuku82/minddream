"""Session Manager

세션 영속화 및 관리

Reference: docs/specs/SESSION_SPEC.md
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SessionData(BaseModel):
    """세션 데이터 모델"""

    session_id: str
    user_id: Optional[str] = None
    language: str = "ko"
    status: str = "active"

    # 상태 데이터
    state: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)

    # 메타데이터
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    # 통계
    message_count: int = 0
    total_duration_ms: float = 0.0


class SessionStore(ABC):
    """세션 저장소 추상 클래스"""

    @abstractmethod
    async def get(self, session_id: str) -> Optional[SessionData]:
        """세션 조회"""
        pass

    @abstractmethod
    async def set(self, session: SessionData) -> bool:
        """세션 저장"""
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """세션 삭제"""
        pass

    @abstractmethod
    async def exists(self, session_id: str) -> bool:
        """세션 존재 여부"""
        pass

    @abstractmethod
    async def extend(self, session_id: str, ttl_seconds: int) -> bool:
        """세션 TTL 연장"""
        pass


class MemorySessionStore(SessionStore):
    """메모리 기반 세션 저장소"""

    def __init__(self, default_ttl: int = 3600):
        self._sessions: dict[str, SessionData] = {}
        self.default_ttl = default_ttl

    async def get(self, session_id: str) -> Optional[SessionData]:
        session = self._sessions.get(session_id)
        if session:
            # 만료 체크
            if session.expires_at and session.expires_at < datetime.utcnow():
                await self.delete(session_id)
                return None
        return session

    async def set(self, session: SessionData) -> bool:
        if not session.expires_at:
            session.expires_at = datetime.utcnow() + timedelta(seconds=self.default_ttl)
        session.updated_at = datetime.utcnow()
        self._sessions[session.session_id] = session
        return True

    async def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    async def exists(self, session_id: str) -> bool:
        session = await self.get(session_id)
        return session is not None

    async def extend(self, session_id: str, ttl_seconds: int) -> bool:
        session = await self.get(session_id)
        if session:
            session.expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            session.updated_at = datetime.utcnow()
            return True
        return False

    async def cleanup_expired(self) -> int:
        """만료된 세션 정리"""
        now = datetime.utcnow()
        expired = [
            sid for sid, session in self._sessions.items()
            if session.expires_at and session.expires_at < now
        ]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)

    def get_active_count(self) -> int:
        """활성 세션 수"""
        return len(self._sessions)


class RedisSessionStore(SessionStore):
    """Redis 기반 세션 저장소"""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: int = 3600,
        prefix: str = "session:",
    ):
        self.redis_url = redis_url or settings.REDIS_URL
        self.default_ttl = default_ttl
        self.prefix = prefix
        self._redis: Any = None

    async def _get_redis(self) -> Any:
        """Redis 클라이언트 획득"""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(self.redis_url)
            except ImportError:
                logger.error("redis package not installed")
                raise
        return self._redis

    def _key(self, session_id: str) -> str:
        """Redis 키 생성"""
        return f"{self.prefix}{session_id}"

    async def get(self, session_id: str) -> Optional[SessionData]:
        try:
            r = await self._get_redis()
            data = await r.get(self._key(session_id))
            if data:
                return SessionData(**json.loads(data))
            return None
        except Exception as e:
            logger.error("Redis get error", error=str(e))
            return None

    async def set(self, session: SessionData) -> bool:
        try:
            r = await self._get_redis()
            session.updated_at = datetime.utcnow()
            data = session.model_dump_json()

            ttl = self.default_ttl
            if session.expires_at:
                ttl = int((session.expires_at - datetime.utcnow()).total_seconds())
                ttl = max(ttl, 1)  # 최소 1초

            await r.setex(self._key(session.session_id), ttl, data)
            return True
        except Exception as e:
            logger.error("Redis set error", error=str(e))
            return False

    async def delete(self, session_id: str) -> bool:
        try:
            r = await self._get_redis()
            result = await r.delete(self._key(session_id))
            return result > 0
        except Exception as e:
            logger.error("Redis delete error", error=str(e))
            return False

    async def exists(self, session_id: str) -> bool:
        try:
            r = await self._get_redis()
            return await r.exists(self._key(session_id)) > 0
        except Exception as e:
            logger.error("Redis exists error", error=str(e))
            return False

    async def extend(self, session_id: str, ttl_seconds: int) -> bool:
        try:
            r = await self._get_redis()
            return await r.expire(self._key(session_id), ttl_seconds)
        except Exception as e:
            logger.error("Redis extend error", error=str(e))
            return False

    async def close(self) -> None:
        """연결 종료"""
        if self._redis:
            await self._redis.close()
            self._redis = None


class SessionManager:
    """세션 관리자"""

    def __init__(self, store: Optional[SessionStore] = None):
        self.store = store or MemorySessionStore()

    async def create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        language: str = "ko",
        initial_state: Optional[dict[str, Any]] = None,
        ttl_seconds: Optional[int] = None,
    ) -> SessionData:
        """세션 생성

        Args:
            session_id: 세션 ID
            user_id: 사용자 ID
            language: 언어
            initial_state: 초기 상태
            ttl_seconds: TTL (초)

        Returns:
            생성된 세션
        """
        expires_at = None
        if ttl_seconds:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

        session = SessionData(
            session_id=session_id,
            user_id=user_id,
            language=language,
            state=initial_state or {},
            expires_at=expires_at,
        )

        await self.store.set(session)
        logger.info("Session created", session_id=session_id)

        return session

    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """세션 조회"""
        return await self.store.get(session_id)

    async def update_session(
        self,
        session_id: str,
        state: Optional[dict[str, Any]] = None,
        context: Optional[dict[str, Any]] = None,
        status: Optional[str] = None,
    ) -> Optional[SessionData]:
        """세션 업데이트

        Args:
            session_id: 세션 ID
            state: 업데이트할 상태
            context: 업데이트할 컨텍스트
            status: 업데이트할 상태

        Returns:
            업데이트된 세션
        """
        session = await self.store.get(session_id)
        if not session:
            return None

        if state:
            session.state.update(state)
        if context:
            session.context.update(context)
        if status:
            session.status = status

        session.message_count += 1
        await self.store.set(session)

        return session

    async def delete_session(self, session_id: str) -> bool:
        """세션 삭제"""
        result = await self.store.delete(session_id)
        if result:
            logger.info("Session deleted", session_id=session_id)
        return result

    async def extend_session(
        self,
        session_id: str,
        ttl_seconds: int,
    ) -> bool:
        """세션 연장"""
        return await self.store.extend(session_id, ttl_seconds)

    async def session_exists(self, session_id: str) -> bool:
        """세션 존재 여부"""
        return await self.store.exists(session_id)


# 싱글톤
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """SessionManager 싱글톤 반환"""
    global _session_manager
    if _session_manager is None:
        # Redis URL이 설정되어 있으면 Redis 사용
        if hasattr(settings, "REDIS_URL") and settings.REDIS_URL:
            store = RedisSessionStore()
        else:
            store = MemorySessionStore()
        _session_manager = SessionManager(store)
    return _session_manager
