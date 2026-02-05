"""Business Data Store - 비즈니스 데이터 JSON 저장소

세션별 비즈니스 데이터 (Plan, Todos, Execution Results) 영구 저장.
DB_SCHEMA_260205.md의 plans, todos, execution_results 테이블에 대응.

저장 구조:
  data/business/{session_id}/
    plan.json       - Plan 메타데이터 (intent, cost, duration 등)
    todos.json      - Todo 리스트 (상태, 결과 포함)
    results.json    - Execution 결과 리스트

추후: PostgreSQL/SQLAlchemy로 교체 가능 — BusinessStore 인터페이스만 구현하면 됨
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from backend.app.core.logging import get_logger

logger = get_logger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "business"


class BusinessStore(ABC):
    """비즈니스 데이터 저장소 인터페이스"""

    # ── Plan ──
    @abstractmethod
    def save_plan(self, session_id: str, plan_data: Dict[str, Any]) -> None: ...

    @abstractmethod
    def load_plan(self, session_id: str) -> Optional[Dict[str, Any]]: ...

    # ── Todos ──
    @abstractmethod
    def save_todos(self, session_id: str, todos: List[Dict[str, Any]]) -> None: ...

    @abstractmethod
    def load_todos(self, session_id: str) -> Optional[List[Dict[str, Any]]]: ...

    # ── Execution Results ──
    @abstractmethod
    def save_execution_result(
        self, session_id: str, result: Dict[str, Any]
    ) -> None: ...

    @abstractmethod
    def load_execution_results(
        self, session_id: str
    ) -> Optional[List[Dict[str, Any]]]: ...


class JsonBusinessStore(BusinessStore):
    """JSON 파일 기반 비즈니스 데이터 저장소

    저장 경로: data/business/{session_id}/
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or DATA_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _session_dir(self, session_id: str) -> Path:
        d = self.base_dir / session_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _write_json(self, path: Path, data: Any) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def _read_json(self, path: Path) -> Optional[Any]:
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ── Plan ──

    def save_plan(self, session_id: str, plan_data: Dict[str, Any]) -> None:
        plan_data["_updated_at"] = datetime.now().isoformat()
        path = self._session_dir(session_id) / "plan.json"
        self._write_json(path, plan_data)
        logger.debug(f"Plan saved: {session_id}")

    def load_plan(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._read_json(self._session_dir(session_id) / "plan.json")

    # ── Todos ──

    def save_todos(self, session_id: str, todos: List[Dict[str, Any]]) -> None:
        data = {
            "session_id": session_id,
            "total_todos": len(todos),
            "todos": todos,
            "_updated_at": datetime.now().isoformat(),
        }
        path = self._session_dir(session_id) / "todos.json"
        self._write_json(path, data)
        logger.debug(f"Todos saved: {session_id} ({len(todos)} items)")

    def load_todos(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        data = self._read_json(self._session_dir(session_id) / "todos.json")
        if data is None:
            return None
        return data.get("todos", [])

    # ── Execution Results ──

    def save_execution_result(
        self, session_id: str, result: Dict[str, Any]
    ) -> None:
        path = self._session_dir(session_id) / "results.json"
        existing = self._read_json(path) or {"results": []}
        result["_saved_at"] = datetime.now().isoformat()
        existing["results"].append(result)
        existing["_updated_at"] = datetime.now().isoformat()
        existing["total_results"] = len(existing["results"])
        self._write_json(path, existing)
        logger.debug(f"Execution result saved: {session_id}")

    def load_execution_results(
        self, session_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        data = self._read_json(self._session_dir(session_id) / "results.json")
        if data is None:
            return None
        return data.get("results", [])


# 글로벌 인스턴스
_store: Optional[BusinessStore] = None


def get_business_store() -> BusinessStore:
    """비즈니스 데이터 저장소 인스턴스 반환

    추후 PostgreSQL 전환 시 이 함수만 수정하면 됨.
    """
    global _store
    if _store is None:
        _store = JsonBusinessStore()
    return _store
