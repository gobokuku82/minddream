"""Execution Strategy

실행 전략 결정
"""

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionStrategy, Plan, TodoItem

logger = get_logger(__name__)


class StrategyDecider:
    """실행 전략 결정기"""

    def decide(self, plan: Plan) -> ExecutionStrategy:
        """실행 전략 결정

        Args:
            plan: 실행 계획

        Returns:
            실행 전략
        """
        todos = plan.todos

        # 단일 Todo
        if len(todos) == 1:
            return ExecutionStrategy.SINGLE

        # 의존성 분석
        has_dependencies = any(t.depends_on for t in todos)

        if not has_dependencies:
            # 의존성 없음 → 병렬 실행 가능
            return ExecutionStrategy.PARALLEL

        # 의존성 체인 분석
        parallel_groups = self._get_parallel_groups(plan)

        if len(parallel_groups) == len(todos):
            # 모든 Todo가 순차적
            return ExecutionStrategy.SEQUENTIAL

        if any(len(g) > 1 for g in parallel_groups):
            # 일부 병렬 가능
            return ExecutionStrategy.PARALLEL

        return ExecutionStrategy.SEQUENTIAL

    def _get_parallel_groups(self, plan: Plan) -> list[list[TodoItem]]:
        """병렬 실행 그룹 생성"""
        from app.dream_agent.planning.dependency import DependencyResolver

        resolver = DependencyResolver()
        return resolver.get_parallel_groups(plan)

    def get_ready_todos(
        self,
        plan: Plan,
        execution_results: dict[str, Any],
    ) -> list[TodoItem]:
        """실행 가능한 Todo 반환

        Args:
            plan: 실행 계획
            execution_results: 현재까지의 실행 결과

        Returns:
            실행 가능한 TodoItem 리스트
        """
        completed_ids = set(execution_results.keys())

        ready = []
        for todo in plan.todos:
            # 이미 완료됨
            if todo.id in completed_ids:
                continue

            # 상태 확인
            if todo.status not in ("pending", "blocked"):
                continue

            # 의존성 확인
            if all(dep_id in completed_ids for dep_id in todo.depends_on):
                ready.append(todo)

        # 우선순위순 정렬
        ready.sort(key=lambda t: t.priority)

        return ready


class ExecutionCoordinator:
    """실행 조율기

    전략에 따라 실행 방식을 조율
    """

    def __init__(self):
        self.strategy_decider = StrategyDecider()

    def should_execute_parallel(
        self,
        plan: Plan,
        ready_todos: list[TodoItem],
    ) -> bool:
        """병렬 실행 여부 판단

        Args:
            plan: 실행 계획
            ready_todos: 실행 가능한 Todo 리스트

        Returns:
            병렬 실행 여부
        """
        if len(ready_todos) <= 1:
            return False

        strategy = plan.strategy

        if strategy == ExecutionStrategy.PARALLEL:
            return True

        if strategy == ExecutionStrategy.SWARM:
            return True

        return False

    def get_batch_size(
        self,
        plan: Plan,
        ready_todos: list[TodoItem],
    ) -> int:
        """배치 크기 결정

        Args:
            plan: 실행 계획
            ready_todos: 실행 가능한 Todo 리스트

        Returns:
            한 번에 실행할 Todo 수
        """
        from app.core.config import settings

        max_parallel = settings.EXECUTION_MAX_PARALLEL

        if plan.strategy in (ExecutionStrategy.SINGLE, ExecutionStrategy.SEQUENTIAL):
            return 1

        return min(len(ready_todos), max_parallel)
