"""TodoItem 모델 테스트

위치: backend.app.dream_agent.models.todo
"""

import pytest
from datetime import datetime

from backend.app.dream_agent.models.todo import (
    TodoItem,
    TodoMetadata,
    TodoExecutionConfig,
    TodoDataConfig,
    TodoDependencyConfig,
    TodoProgress,
    TodoApproval,
)


class TestTodoItem:
    """TodoItem 테스트"""

    def test_create_minimal(self):
        """최소 필수 필드로 생성"""
        todo = TodoItem(
            task="테스트 작업",
            layer="ml_execution"
        )

        assert todo.task == "테스트 작업"
        assert todo.layer == "ml_execution"
        assert todo.status == "pending"
        assert todo.priority == 5
        assert todo.id is not None

    def test_create_full(self, sample_todo_data):
        """전체 필드로 생성"""
        todo = TodoItem(**sample_todo_data)

        assert todo.task == sample_todo_data["task"]
        assert todo.task_type == sample_todo_data["task_type"]
        assert todo.layer == sample_todo_data["layer"]
        assert todo.status == sample_todo_data["status"]
        assert todo.priority == sample_todo_data["priority"]

    def test_metadata_default(self):
        """메타데이터 기본값"""
        todo = TodoItem(task="테스트", layer="ml_execution")

        assert isinstance(todo.metadata, TodoMetadata)
        assert isinstance(todo.metadata.execution, TodoExecutionConfig)
        assert isinstance(todo.metadata.data, TodoDataConfig)
        assert isinstance(todo.metadata.dependency, TodoDependencyConfig)
        assert isinstance(todo.metadata.progress, TodoProgress)
        assert isinstance(todo.metadata.approval, TodoApproval)

    def test_version_increment(self):
        """버전 증가"""
        todo = TodoItem(task="테스트", layer="ml_execution")
        assert todo.version == 1

        # model_copy로 버전 업데이트
        updated = todo.model_copy(update={"version": todo.version + 1})
        assert updated.version == 2

    def test_history_tracking(self):
        """히스토리 추적"""
        todo = TodoItem(task="테스트", layer="ml_execution")
        assert todo.history == []

        # 히스토리 추가
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "status_change",
            "from": "pending",
            "to": "in_progress"
        }
        updated = todo.model_copy(update={"history": [history_entry]})
        assert len(updated.history) == 1

    def test_layer_validation(self):
        """레이어 값 검증"""
        valid_layers = ["cognitive", "planning", "ml_execution", "biz_execution", "response"]

        for layer in valid_layers:
            todo = TodoItem(task="테스트", layer=layer)
            assert todo.layer == layer

    def test_status_values(self):
        """상태 값 검증"""
        valid_statuses = [
            "pending", "in_progress", "completed", "failed",
            "blocked", "skipped", "needs_approval", "cancelled"
        ]

        for status in valid_statuses:
            todo = TodoItem(task="테스트", layer="ml_execution", status=status)
            assert todo.status == status

    def test_priority_range(self):
        """우선순위 범위 검증"""
        # 기본값
        todo = TodoItem(task="테스트", layer="ml_execution")
        assert 0 <= todo.priority <= 10

        # 최소값
        todo_min = TodoItem(task="테스트", layer="ml_execution", priority=0)
        assert todo_min.priority == 0

        # 최대값
        todo_max = TodoItem(task="테스트", layer="ml_execution", priority=10)
        assert todo_max.priority == 10


class TestTodoMetadata:
    """TodoMetadata 테스트"""

    def test_execution_config(self):
        """실행 설정"""
        config = TodoExecutionConfig(
            tool="sentiment_analyzer",
            tool_params={"mode": "absa"},
            timeout=300,
            max_retries=5
        )

        assert config.tool == "sentiment_analyzer"
        assert config.tool_params["mode"] == "absa"
        assert config.timeout == 300
        assert config.max_retries == 5
        assert config.retry_count == 0

    def test_data_config(self):
        """데이터 설정"""
        config = TodoDataConfig(
            input_data={"reviews": ["좋아요", "별로"]},
            output_path="/data/results.json"
        )

        assert config.input_data["reviews"] == ["좋아요", "별로"]
        assert config.output_path == "/data/results.json"

    def test_dependency_config(self):
        """의존성 설정"""
        config = TodoDependencyConfig(
            depends_on=["todo-1", "todo-2"],
            blocks=["todo-3"]
        )

        assert "todo-1" in config.depends_on
        assert "todo-2" in config.depends_on
        assert "todo-3" in config.blocks

    def test_progress_tracking(self):
        """진행 상황 추적"""
        progress = TodoProgress(
            progress_percentage=50,
            started_at=datetime.now()
        )

        assert progress.progress_percentage == 50
        assert progress.started_at is not None
        assert progress.completed_at is None
        assert progress.error_message is None

    def test_approval_config(self):
        """승인 설정"""
        approval = TodoApproval(
            requires_approval=True,
            user_notes="검토 필요"
        )

        assert approval.requires_approval is True
        assert approval.user_notes == "검토 필요"
        assert approval.approved_by is None


class TestTodoSerialization:
    """Todo 직렬화 테스트"""

    def test_to_dict(self):
        """딕셔너리 변환"""
        todo = TodoItem(task="테스트", layer="ml_execution")
        data = todo.model_dump()

        assert isinstance(data, dict)
        assert data["task"] == "테스트"
        assert data["layer"] == "ml_execution"
        assert "metadata" in data

    def test_to_json(self):
        """JSON 변환"""
        todo = TodoItem(task="테스트", layer="ml_execution")
        json_str = todo.model_dump_json()

        assert isinstance(json_str, str)
        assert "테스트" in json_str

    def test_from_dict(self):
        """딕셔너리에서 생성"""
        data = {
            "task": "테스트",
            "layer": "ml_execution",
            "status": "completed"
        }
        todo = TodoItem(**data)

        assert todo.task == "테스트"
        assert todo.status == "completed"
