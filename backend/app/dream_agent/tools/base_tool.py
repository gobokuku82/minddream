"""Base Tool

도구 추상 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import Any

from app.dream_agent.models import ExecutionContext, ToolSpec


class BaseTool(ABC):
    """도구 기본 클래스"""

    def __init__(self, spec: ToolSpec):
        self.spec = spec

    @property
    def name(self) -> str:
        """도구 이름"""
        return self.spec.name

    @property
    def description(self) -> str:
        """도구 설명"""
        return self.spec.description

    @abstractmethod
    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        """도구 실행

        Args:
            params: 파라미터
            context: 실행 컨텍스트

        Returns:
            실행 결과
        """
        pass

    def validate_params(self, params: dict[str, Any]) -> tuple[bool, list[str]]:
        """파라미터 검증

        Args:
            params: 검증할 파라미터

        Returns:
            (valid, errors)
        """
        errors = []

        for param_spec in self.spec.parameters:
            if param_spec.required and param_spec.name not in params:
                errors.append(f"Required parameter missing: {param_spec.name}")

        return len(errors) == 0, errors

    def get_default_params(self) -> dict[str, Any]:
        """기본 파라미터 반환"""
        defaults = {}

        for param_spec in self.spec.parameters:
            if param_spec.default is not None:
                defaults[param_spec.name] = param_spec.default

        return defaults

    def merge_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """기본값과 파라미터 병합"""
        merged = self.get_default_params()
        merged.update(params)
        return merged
