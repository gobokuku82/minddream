"""Dependency Resolver

DAG 빌드 및 위상 정렬
"""

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import Plan, TodoItem

logger = get_logger(__name__)


class DependencyResolver:
    """의존성 해결기"""

    def validate_dependencies(self, plan: Plan) -> tuple[bool, list[str]]:
        """의존성 검증

        Args:
            plan: 검증할 계획

        Returns:
            (valid, errors) - 유효성 여부와 에러 메시지 리스트
        """
        errors = []
        todo_ids = {t.id for t in plan.todos}

        # 1. 알 수 없는 의존성 확인
        for todo in plan.todos:
            for dep_id in todo.depends_on:
                if dep_id not in todo_ids:
                    errors.append(f"Todo '{todo.id}' has unknown dependency: {dep_id}")

        # 2. 자기 참조 확인
        for todo in plan.todos:
            if todo.id in todo.depends_on:
                errors.append(f"Todo '{todo.id}' has self-reference")

        # 3. 순환 의존성 확인
        if self.has_cycle(plan):
            errors.append("Circular dependency detected")

        return len(errors) == 0, errors

    def has_cycle(self, plan: Plan) -> bool:
        """순환 의존성 검사 (DFS)

        Args:
            plan: 검사할 계획

        Returns:
            순환 있으면 True
        """
        # 인접 리스트 구성
        graph: dict[str, list[str]] = {todo.id: todo.depends_on for todo in plan.todos}

        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for todo_id in graph:
            if todo_id not in visited:
                if dfs(todo_id):
                    return True

        return False

    def topological_sort(self, plan: Plan) -> list[TodoItem]:
        """위상 정렬

        Args:
            plan: 정렬할 계획

        Returns:
            정렬된 TodoItem 리스트
        """
        if self.has_cycle(plan):
            raise ValueError("Cannot sort: circular dependency exists")

        # 진입 차수 계산
        in_degree: dict[str, int] = {todo.id: 0 for todo in plan.todos}
        for todo in plan.todos:
            for dep_id in todo.depends_on:
                if dep_id in in_degree:
                    # dep_id가 todo보다 먼저 와야 함 → todo의 진입차수 증가
                    pass

        # 실제로는 역방향으로 계산
        # A → B (B depends on A) → A가 먼저 와야 함
        graph: dict[str, list[str]] = {todo.id: [] for todo in plan.todos}
        for todo in plan.todos:
            for dep_id in todo.depends_on:
                if dep_id in graph:
                    graph[dep_id].append(todo.id)
                    in_degree[todo.id] += 1

        # Kahn's algorithm
        queue = [todo_id for todo_id, degree in in_degree.items() if degree == 0]
        result_ids = []

        while queue:
            current = queue.pop(0)
            result_ids.append(current)

            for neighbor in graph.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # ID → TodoItem 매핑
        todo_map = {todo.id: todo for todo in plan.todos}
        return [todo_map[todo_id] for todo_id in result_ids if todo_id in todo_map]

    def get_ready_todos(self, plan: Plan, completed_ids: set[str]) -> list[TodoItem]:
        """실행 가능한 Todo 목록

        Args:
            plan: 계획
            completed_ids: 완료된 Todo ID 집합

        Returns:
            실행 가능한 TodoItem 리스트
        """
        ready = []

        for todo in plan.todos:
            if todo.status != "pending":
                continue

            # 모든 의존성이 완료되었는지 확인
            if all(dep_id in completed_ids for dep_id in todo.depends_on):
                ready.append(todo)

        # 우선순위순 정렬
        ready.sort(key=lambda t: t.priority)

        return ready

    def get_parallel_groups(self, plan: Plan) -> list[list[TodoItem]]:
        """병렬 실행 그룹 생성

        같은 레벨(동일 의존성 깊이)의 Todo를 그룹화

        Args:
            plan: 계획

        Returns:
            병렬 실행 그룹 리스트
        """
        # 레벨 계산 (BFS)
        levels: dict[str, int] = {}
        todo_map = {todo.id: todo for todo in plan.todos}

        # 의존성 없는 노드는 레벨 0
        queue = []
        for todo in plan.todos:
            if not todo.depends_on:
                levels[todo.id] = 0
                queue.append(todo.id)

        # BFS로 레벨 전파
        while queue:
            current_id = queue.pop(0)
            current_level = levels[current_id]

            # 이 노드에 의존하는 노드들
            for todo in plan.todos:
                if current_id in todo.depends_on:
                    # 모든 의존성의 레벨이 결정되면 이 노드의 레벨 결정
                    dep_levels = [levels.get(dep_id, -1) for dep_id in todo.depends_on]
                    if all(l >= 0 for l in dep_levels):
                        new_level = max(dep_levels) + 1
                        if todo.id not in levels:
                            levels[todo.id] = new_level
                            queue.append(todo.id)

        # 레벨별 그룹화
        max_level = max(levels.values()) if levels else 0
        groups: list[list[TodoItem]] = [[] for _ in range(max_level + 1)]

        for todo in plan.todos:
            level = levels.get(todo.id, 0)
            groups[level].append(todo)

        # 빈 그룹 제거
        return [g for g in groups if g]
