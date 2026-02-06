"""Tool Registry

YAML 기반 도구 레지스트리
"""

from pathlib import Path
from typing import Any, Optional

import yaml

from app.core.logging import get_logger
from app.dream_agent.models import ToolCategory, ToolParameter, ToolParameterType, ToolSpec

logger = get_logger(__name__)

# 도구 정의 디렉토리
DEFINITIONS_DIR = Path(__file__).parent / "definitions"


class ToolRegistry:
    """도구 레지스트리

    YAML 파일에서 도구 정의를 로드하고 관리
    """

    def __init__(self):
        self._tools: dict[str, ToolSpec] = {}
        self._loaded = False

    def load(self) -> None:
        """도구 정의 로드"""
        if self._loaded:
            return

        logger.info("Loading tool definitions", path=str(DEFINITIONS_DIR))

        yaml_files = DEFINITIONS_DIR.glob("*.yaml")

        for yaml_file in yaml_files:
            # 스키마 파일 제외
            if yaml_file.name.startswith("_"):
                continue

            try:
                tool_spec = self._load_yaml(yaml_file)
                if tool_spec:
                    self._tools[tool_spec.name] = tool_spec
                    logger.debug("Tool loaded", name=tool_spec.name)
            except Exception as e:
                logger.error("Failed to load tool", file=yaml_file.name, error=str(e))

        self._loaded = True
        logger.info("Tool definitions loaded", count=len(self._tools))

    def _load_yaml(self, path: Path) -> Optional[ToolSpec]:
        """YAML 파일에서 도구 정의 로드"""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or not data.get("name"):
            return None

        # Category 파싱
        category_str = data.get("category", "data")
        try:
            category = ToolCategory(category_str)
        except ValueError:
            category = ToolCategory.DATA

        # Parameters 파싱
        parameters = []
        for param_data in data.get("parameters", []):
            param_type_str = param_data.get("type", "string")
            try:
                param_type = ToolParameterType(param_type_str)
            except ValueError:
                param_type = ToolParameterType.STRING

            parameters.append(
                ToolParameter(
                    name=param_data.get("name", ""),
                    type=param_type,
                    required=param_data.get("required", False),
                    default=param_data.get("default"),
                    description=param_data.get("description", ""),
                )
            )

        return ToolSpec(
            name=data.get("name"),
            description=data.get("description", ""),
            category=category,
            executor=data.get("executor", ""),
            parameters=parameters,
            timeout_sec=data.get("timeout_sec", 300),
            max_retries=data.get("max_retries", 3),
            dependencies=data.get("dependencies", []),
            produces=data.get("produces", []),
            requires_approval=data.get("requires_approval", False),
            has_cost=data.get("has_cost", False),
            estimated_cost_usd=data.get("estimated_cost", 0.0),
        )

    def get(self, name: str) -> Optional[ToolSpec]:
        """도구 조회

        Args:
            name: 도구 이름

        Returns:
            ToolSpec 또는 None
        """
        if not self._loaded:
            self.load()

        return self._tools.get(name)

    def get_all(self) -> list[ToolSpec]:
        """모든 도구 조회"""
        if not self._loaded:
            self.load()

        return list(self._tools.values())

    def get_by_category(self, category: ToolCategory) -> list[ToolSpec]:
        """카테고리별 도구 조회"""
        if not self._loaded:
            self.load()

        return [t for t in self._tools.values() if t.category == category]

    def get_names(self) -> list[str]:
        """도구 이름 목록"""
        if not self._loaded:
            self.load()

        return list(self._tools.keys())

    def exists(self, name: str) -> bool:
        """도구 존재 여부"""
        if not self._loaded:
            self.load()

        return name in self._tools

    def get_for_domain(self, domain: str) -> list[ToolSpec]:
        """도메인에 적합한 도구 목록

        Args:
            domain: 의도 도메인 (analysis, content, operation, inquiry)

        Returns:
            적합한 도구 목록
        """
        if not self._loaded:
            self.load()

        # 도메인 → 카테고리 매핑
        domain_categories = {
            "analysis": [ToolCategory.DATA, ToolCategory.ANALYSIS],
            "content": [ToolCategory.CONTENT],
            "operation": [ToolCategory.OPS],
            "inquiry": [],
        }

        categories = domain_categories.get(domain, [])

        if not categories:
            return []

        return [t for t in self._tools.values() if t.category in categories]


# 싱글톤 인스턴스
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """레지스트리 싱글톤 반환"""
    global _registry

    if _registry is None:
        _registry = ToolRegistry()
        _registry.load()

    return _registry
