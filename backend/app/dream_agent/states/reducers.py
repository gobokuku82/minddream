"""Custom Reducers for AgentState

LangGraph에서 상태 병합 시 사용되는 리듀서 함수들
"""

from typing import Any


def todo_reducer(existing: list[dict], updates: list[dict]) -> list[dict]:
    """Todo 리스트 병합 (ID 기반)

    동작:
    1. 같은 ID → 업데이트로 교체 (final state 제외)
    2. 새 ID → 추가
    3. completed/failed/skipped/cancelled → 덮어쓰기 방지 (final state)

    Args:
        existing: 기존 Todo 리스트
        updates: 업데이트할 Todo 리스트

    Returns:
        병합된 Todo 리스트
    """
    if not existing:
        return updates or []
    if not updates:
        return existing

    existing_map = {t["id"]: t for t in existing}
    final_statuses = {"completed", "failed", "skipped", "cancelled"}

    for update in updates:
        todo_id = update.get("id")
        if not todo_id:
            continue

        if todo_id in existing_map:
            # Final status면 덮어쓰기 방지
            current_status = existing_map[todo_id].get("status")
            if current_status not in final_statuses:
                existing_map[todo_id] = update
        else:
            existing_map[todo_id] = update

    return list(existing_map.values())


def results_reducer(existing: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """실행 결과 병합

    동작:
    1. 재귀적 딕셔너리 병합
    2. 동일 todo_id → 최신 결과로 교체

    Args:
        existing: 기존 결과 딕셔너리
        new: 새로운 결과 딕셔너리

    Returns:
        병합된 결과 딕셔너리
    """
    if not existing:
        return new or {}
    if not new:
        return existing

    merged = {**existing}

    for key, value in new.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            # 중첩 딕셔너리는 재귀적으로 병합
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value

    return merged


def trace_reducer(existing: list[dict], new: list[dict]) -> list[dict]:
    """트레이스 로그 병합 (append-only)

    Args:
        existing: 기존 트레이스 로그
        new: 새로운 트레이스 로그

    Returns:
        병합된 트레이스 로그 (append)
    """
    if not existing:
        return new or []
    if not new:
        return existing

    return existing + new
