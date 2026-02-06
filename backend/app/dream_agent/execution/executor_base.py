"""Base Executor

Executor 추상 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import Any

from app.dream_agent.models import ExecutionContext, ExecutionResult, TodoItem


class BaseExecutor(ABC):
    """Executor 기본 클래스"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Executor 이름"""
        pass

    @property
    @abstractmethod
    def supported_tools(self) -> list[str]:
        """지원하는 도구 목록"""
        pass

    @abstractmethod
    async def execute(
        self,
        todo: TodoItem,
        context: ExecutionContext,
    ) -> ExecutionResult:
        """도구 실행

        Args:
            todo: 실행할 Todo
            context: 실행 컨텍스트

        Returns:
            실행 결과
        """
        pass

    def can_handle(self, tool: str) -> bool:
        """도구 처리 가능 여부

        Args:
            tool: 도구 이름

        Returns:
            처리 가능 여부
        """
        return tool in self.supported_tools

    async def validate_params(
        self,
        todo: TodoItem,
    ) -> tuple[bool, list[str]]:
        """파라미터 검증

        Args:
            todo: 검증할 Todo

        Returns:
            (valid, errors)
        """
        # 기본 구현: 항상 유효
        return True, []

    async def pre_execute(
        self,
        todo: TodoItem,
        context: ExecutionContext,
    ) -> None:
        """실행 전 처리

        Args:
            todo: 실행할 Todo
            context: 실행 컨텍스트
        """
        pass

    async def post_execute(
        self,
        todo: TodoItem,
        context: ExecutionContext,
        result: ExecutionResult,
    ) -> ExecutionResult:
        """실행 후 처리

        Args:
            todo: 실행한 Todo
            context: 실행 컨텍스트
            result: 실행 결과

        Returns:
            후처리된 결과
        """
        return result
