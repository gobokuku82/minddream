"""Tool Discovery 테스트"""

import pytest
from pathlib import Path

from backend.app.dream_agent.models.tool import (
    ToolSpec,
    ToolType,
    ToolParameter,
    ToolParameterType,
)
from backend.app.dream_agent.tools.discovery import ToolDiscovery, get_tool_discovery
from backend.app.dream_agent.tools.loader import YAMLToolLoader, load_tools_from_yaml


class TestToolSpec:
    """ToolSpec 모델 테스트"""

    def test_create_minimal(self):
        """최소 필드로 생성"""
        spec = ToolSpec(
            name="test_tool",
            description="Test tool",
            tool_type=ToolType.DATA,
            executor="test.executor"
        )
        assert spec.name == "test_tool"
        assert spec.tool_type == ToolType.DATA

    def test_name_normalization(self):
        """이름 정규화"""
        spec = ToolSpec(
            name="Test Tool Name",
            description="Test",
            tool_type=ToolType.ANALYSIS,
            executor="test"
        )
        assert spec.name == "test_tool_name"

    def test_parameters(self):
        """파라미터 검증"""
        param = ToolParameter(
            name="test_param",
            type=ToolParameterType.STRING,
            required=True,
            description="Test parameter"
        )
        spec = ToolSpec(
            name="test",
            description="Test",
            tool_type=ToolType.DATA,
            executor="test",
            parameters=[param]
        )
        assert len(spec.parameters) == 1
        assert spec.get_required_params()[0].name == "test_param"

    def test_to_langchain_schema(self):
        """LangChain 스키마 변환"""
        spec = ToolSpec(
            name="test",
            description="Test tool",
            tool_type=ToolType.ANALYSIS,
            executor="test",
            parameters=[
                ToolParameter(
                    name="input",
                    type=ToolParameterType.STRING,
                    required=True
                )
            ]
        )
        schema = spec.to_langchain_schema()
        assert schema["name"] == "test"
        assert "parameters" in schema
        assert "input" in schema["parameters"]["properties"]


class TestToolDiscovery:
    """ToolDiscovery 테스트"""

    def setup_method(self):
        """각 테스트 전 Discovery 리셋"""
        ToolDiscovery.reset()

    def test_singleton(self):
        """싱글톤 패턴"""
        d1 = get_tool_discovery()
        d2 = get_tool_discovery()
        assert d1 is d2

    def test_register_and_get(self):
        """등록 및 조회"""
        discovery = get_tool_discovery()
        spec = ToolSpec(
            name="test",
            description="Test",
            tool_type=ToolType.DATA,
            executor="test"
        )
        discovery.register(spec)

        result = discovery.get("test")
        assert result is not None
        assert result.name == "test"

    def test_get_by_type(self):
        """타입별 조회"""
        discovery = get_tool_discovery()
        discovery.register(ToolSpec(
            name="data1", description="", tool_type=ToolType.DATA, executor="x"
        ))
        discovery.register(ToolSpec(
            name="analysis1", description="", tool_type=ToolType.ANALYSIS, executor="x"
        ))

        data_tools = discovery.get_by_type(ToolType.DATA)
        assert len(data_tools) == 1
        assert data_tools[0].name == "data1"

    def test_get_by_tag(self):
        """태그별 조회"""
        discovery = get_tool_discovery()
        discovery.register(ToolSpec(
            name="test", description="", tool_type=ToolType.DATA,
            executor="x", tags=["nlp", "sentiment"]
        ))

        nlp_tools = discovery.get_by_tag("nlp")
        assert len(nlp_tools) == 1

    def test_execution_order(self):
        """의존성 기반 실행 순서"""
        discovery = get_tool_discovery()
        discovery.register(ToolSpec(
            name="collector", description="", tool_type=ToolType.DATA,
            executor="x", dependencies=[]
        ))
        discovery.register(ToolSpec(
            name="analyzer", description="", tool_type=ToolType.ANALYSIS,
            executor="x", dependencies=["collector"]
        ))
        discovery.register(ToolSpec(
            name="reporter", description="", tool_type=ToolType.CONTENT,
            executor="x", dependencies=["analyzer"]
        ))

        order = discovery.get_execution_order(["reporter", "analyzer", "collector"])
        assert order.index("collector") < order.index("analyzer")
        assert order.index("analyzer") < order.index("reporter")


class TestYAMLLoader:
    """YAMLToolLoader 테스트"""

    def setup_method(self):
        """각 테스트 전 Discovery 리셋"""
        ToolDiscovery.reset()

    def test_load_all(self):
        """전체 YAML 로드"""
        yaml_dir = Path(__file__).parent.parent.parent.parent / "backend/app/dream_agent/tools/definitions"
        if yaml_dir.exists():
            loader = YAMLToolLoader(yaml_dir)
            tools = loader.load_all()
            assert len(tools) >= 1  # 최소 1개 이상

    def test_load_tools_from_yaml(self):
        """헬퍼 함수로 로드"""
        yaml_dir = Path(__file__).parent.parent.parent.parent / "backend/app/dream_agent/tools/definitions"
        if yaml_dir.exists():
            tools = load_tools_from_yaml(yaml_dir)
            discovery = get_tool_discovery()
            assert len(discovery.list_all()) >= 1
