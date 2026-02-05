"""Session Store - 세션 상태 저장소 (Repository 패턴)

현재: JSON 파일 기반 (data/sessions/{session_id}.json)
추후: Redis 또는 PostgreSQL로 교체 가능 — SessionStore 인터페이스만 구현하면 됨
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from backend.app.core.logging import get_logger

logger = get_logger(__name__)

# 기본 저장 경로
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "sessions"


class SessionStore(ABC):
    """세션 저장소 인터페이스 (Repository)"""

    @abstractmethod
    def save(self, session_id: str, data: Dict[str, Any]) -> None:
        """세션 데이터 저장/업데이트"""
        ...

    @abstractmethod
    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 데이터 로드 (없으면 None)"""
        ...

    @abstractmethod
    def exists(self, session_id: str) -> bool:
        """세션 존재 여부"""
        ...

    @abstractmethod
    def delete(self, session_id: str) -> bool:
        """세션 삭제 (성공 시 True)"""
        ...

    @abstractmethod
    def update_field(self, session_id: str, key: str, value: Any) -> bool:
        """세션의 특정 필드만 업데이트"""
        ...


class JsonSessionStore(SessionStore):
    """JSON 파일 기반 세션 저장소

    저장 경로: data/sessions/{session_id}.json
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or DATA_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        return self.base_dir / f"{session_id}.json"

    def save(self, session_id: str, data: Dict[str, Any]) -> None:
        data["_updated_at"] = datetime.now().isoformat()
        path = self._path(session_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        logger.debug(f"Session saved: {session_id}")

    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        path = self._path(session_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def exists(self, session_id: str) -> bool:
        return self._path(session_id).exists()

    def delete(self, session_id: str) -> bool:
        path = self._path(session_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def update_field(self, session_id: str, key: str, value: Any) -> bool:
        data = self.load(session_id)
        if data is None:
            return False
        data[key] = value
        self.save(session_id, data)
        return True


# 글로벌 인스턴스
_store: Optional[SessionStore] = None


def get_session_store() -> SessionStore:
    """세션 저장소 인스턴스 반환

    추후 Redis/DB 전환 시 이 함수만 수정하면 됨.
    """
    global _store
    if _store is None:
        _store = JsonSessionStore()
    return _store
