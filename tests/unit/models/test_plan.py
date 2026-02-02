"""Plan 모델 테스트

위치: backend.app.dream_agent.models.plan
"""

import pytest
from datetime import datetime

from backend.app.dream_agent.models.plan import (
    Plan,
    PlanVersion,
    PlanChange,
    create_plan,
    create_plan_change,
    create_plan_version,
)
from backend.app.dream_agent.models.todo import TodoItem


class TestPlan:
    """Plan 테스트"""

    def test_create_minimal(self):
        """최소 필수 필드로 생성"""
        plan = Plan(session_id="test-session")

        assert plan.session_id == "test-session"
        assert plan.status == "draft"
        assert plan.current_version == 1
        assert plan.todos == []
        assert plan.versions == []
        assert plan.changes == []

    def test_create_with_todos(self):
        """Todo와 함께 생성"""
        todos = [
            TodoItem(task="작업1", layer="ml_execution"),
            TodoItem(task="작업2", layer="biz_execution"),
        ]
        plan = Plan(session_id="test-session", todos=todos)

        assert len(plan.todos) == 2
        assert plan.todos[0].task == "작업1"
        assert plan.todos[1].task == "작업2"

    def test_status_values(self):
        """상태 값 검증"""
        valid_statuses = [
            "draft", "approved", "executing", "paused",
            "waiting", "completed", "failed", "cancelled"
        ]

        for status in valid_statuses:
            plan = Plan(session_id="test", status=status)
            assert plan.status == status

    def test_get_todo_by_id(self):
        """ID로 Todo 조회"""
        todos = [
            TodoItem(task="작업1", layer="ml_execution"),
            TodoItem(task="작업2", layer="biz_execution"),
        ]
        plan = Plan(session_id="test", todos=todos)

        found = plan.get_todo_by_id(todos[0].id)
        assert found is not None
        assert found.task == "작업1"

        not_found = plan.get_todo_by_id("non-existent")
        assert not_found is None

    def test_get_todos_by_status(self):
        """상태별 Todo 조회"""
        todos = [
            TodoItem(task="작업1", layer="ml_execution", status="pending"),
            TodoItem(task="작업2", layer="ml_execution", status="completed"),
            TodoItem(task="작업3", layer="ml_execution", status="pending"),
        ]
        plan = Plan(session_id="test", todos=todos)

        pending = plan.get_todos_by_status("pending")
        assert len(pending) == 2

        completed = plan.get_todos_by_status("completed")
        assert len(completed) == 1

    def test_get_todos_by_layer(self):
        """레이어별 Todo 조회"""
        todos = [
            TodoItem(task="ML작업1", layer="ml_execution"),
            TodoItem(task="ML작업2", layer="ml_execution"),
            TodoItem(task="Biz작업", layer="biz_execution"),
        ]
        plan = Plan(session_id="test", todos=todos)

        ml_todos = plan.get_todos_by_layer("ml_execution")
        assert len(ml_todos) == 2

        biz_todos = plan.get_todos_by_layer("biz_execution")
        assert len(biz_todos) == 1

    def test_get_todo_statistics(self):
        """Todo 통계"""
        todos = [
            TodoItem(task="작업1", layer="ml_execution", status="pending"),
            TodoItem(task="작업2", layer="ml_execution", status="completed"),
            TodoItem(task="작업3", layer="biz_execution", status="failed"),
        ]
        plan = Plan(session_id="test", todos=todos)

        stats = plan.get_todo_statistics()
        assert stats["pending"] == 1
        assert stats["completed"] == 1
        assert stats["failed"] == 1
        assert stats["total"] == 3
        assert stats["ml_todos"] == 2
        assert stats["biz_todos"] == 1

    def test_get_progress_percentage(self):
        """진행률 계산"""
        todos = [
            TodoItem(task="작업1", layer="ml_execution", status="completed"),
            TodoItem(task="작업2", layer="ml_execution", status="completed"),
            TodoItem(task="작업3", layer="ml_execution", status="pending"),
            TodoItem(task="작업4", layer="ml_execution", status="pending"),
        ]
        plan = Plan(session_id="test", todos=todos)

        progress = plan.get_progress_percentage()
        assert progress == 50.0

    def test_empty_plan_progress(self):
        """빈 Plan 진행률"""
        plan = Plan(session_id="test", todos=[])
        assert plan.get_progress_percentage() == 0.0


class TestPlanChange:
    """PlanChange 테스트"""

    def test_create_change(self):
        """변경 이력 생성"""
        change = PlanChange(
            change_type="create",
            reason="Initial plan creation",
            actor="system"
        )

        assert change.change_type == "create"
        assert change.reason == "Initial plan creation"
        assert change.actor == "system"
        assert change.change_id is not None

    def test_change_types(self):
        """변경 타입 검증"""
        valid_types = [
            "create", "add_todo", "remove_todo", "modify_todo",
            "reorder", "replan", "rollback", "user_decision"
        ]

        for change_type in valid_types:
            change = PlanChange(change_type=change_type, reason="test")
            assert change.change_type == change_type

    def test_decision_fields(self):
        """의사결정 필드"""
        change = PlanChange(
            change_type="user_decision",
            reason="사용자 결정",
            decision_request_id="req-001",
            decision_action="approve",
            decision_data={"approved": True}
        )

        assert change.decision_request_id == "req-001"
        assert change.decision_action == "approve"
        assert change.decision_data["approved"] is True


class TestPlanVersion:
    """PlanVersion 테스트"""

    def test_create_version(self):
        """버전 생성"""
        todos = [TodoItem(task="작업", layer="ml_execution")]
        version = PlanVersion(
            version=1,
            todos=todos,
            change_id="change-001",
            change_summary="Initial version"
        )

        assert version.version == 1
        assert len(version.todos) == 1
        assert version.change_summary == "Initial version"


class TestPlanHelpers:
    """Plan 헬퍼 함수 테스트"""

    def test_create_plan_helper(self):
        """create_plan 헬퍼"""
        todos = [
            TodoItem(task="ML작업", layer="ml_execution"),
            TodoItem(task="Biz작업", layer="biz_execution"),
        ]

        plan = create_plan(
            session_id="test-session",
            todos=todos,
            intent={"type": "analysis"},
            context={"brand": "라네즈"}
        )

        assert plan.session_id == "test-session"
        assert len(plan.todos) == 2
        assert plan.intent["type"] == "analysis"
        assert plan.context["brand"] == "라네즈"
        # 초기 버전과 변경 이력 확인
        assert len(plan.versions) == 1
        assert len(plan.changes) == 1
        assert plan.changes[0].change_type == "create"

    def test_create_plan_change_helper(self):
        """create_plan_change 헬퍼"""
        change = create_plan_change(
            change_type="add_todo",
            reason="새 작업 추가",
            actor="user",
            affected_todo_ids=["todo-001"]
        )

        assert change.change_type == "add_todo"
        assert change.reason == "새 작업 추가"
        assert "todo-001" in change.affected_todo_ids


class TestPlanSerialization:
    """Plan 직렬화 테스트"""

    def test_to_dict(self):
        """딕셔너리 변환"""
        plan = Plan(session_id="test")
        data = plan.model_dump()

        assert isinstance(data, dict)
        assert data["session_id"] == "test"

    def test_to_json(self):
        """JSON 변환"""
        plan = Plan(session_id="test")
        json_str = plan.model_dump_json()

        assert isinstance(json_str, str)
        assert "test" in json_str
