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


# ============================================================
# Phase 1: Compatibility Layer 테스트
# ============================================================
from backend.app.dream_agent.tools.compat import (
    ToolSpecAdapter,
    spec_to_base_tool,
    base_tool_to_spec,
    get_unified_tool_access,
    UnifiedToolAccess,
    LAYER_TO_EXECUTOR,
)


class TestToolSpecAdapter:
    """ToolSpecAdapter 테스트 (Phase 1)"""

    def setup_method(self):
        ToolDiscovery.reset()

    def test_adapter_creation(self):
        """어댑터 생성"""
        spec = ToolSpec(
            name="test_tool",
            description="Test description",
            tool_type=ToolType.DATA,
            executor="test.executor",
            layer="ml_execution"
        )
        adapter = ToolSpecAdapter(spec)

        assert adapter.name == "test_tool"
        assert adapter.description == "Test description"
        assert adapter.category == "data"

    def test_adapter_metadata(self):
        """어댑터 메타데이터"""
        spec = ToolSpec(
            name="test",
            description="Test",
            tool_type=ToolType.ANALYSIS,
            executor="test",
            layer="ml_execution",
            tags=["nlp", "sentiment"],
            dependencies=["preprocessor"]
        )
        adapter = ToolSpecAdapter(spec)
        metadata = adapter.get_metadata()

        assert metadata["name"] == "test"
        assert metadata["layer"] == "ml_execution"
        assert "nlp" in metadata["tags"]

    def test_spec_to_base_tool(self):
        """spec_to_base_tool 변환"""
        spec = ToolSpec(
            name="converter_test",
            description="Test",
            tool_type=ToolType.CONTENT,
            executor="test"
        )
        tool = spec_to_base_tool(spec)

        assert tool.name == "converter_test"
        assert tool.category == "content"


class TestUnifiedToolAccess:
    """UnifiedToolAccess 테스트 (Phase 1)"""

    def setup_method(self):
        ToolDiscovery.reset()
        # Reset unified access singleton
        import backend.app.dream_agent.tools.compat as compat
        compat._unified_access = None

    def test_get_from_discovery(self):
        """Discovery에서 도구 조회"""
        discovery = get_tool_discovery()
        discovery.register(ToolSpec(
            name="unified_test",
            description="Test",
            tool_type=ToolType.DATA,
            executor="test",
            layer="ml_execution"
        ))

        access = get_unified_tool_access()
        tool = access.get("unified_test")

        assert tool is not None
        assert tool.name == "unified_test"

    def test_get_spec(self):
        """ToolSpec 조회"""
        discovery = get_tool_discovery()
        discovery.register(ToolSpec(
            name="spec_test",
            description="Test",
            tool_type=ToolType.ANALYSIS,
            executor="test",
            layer="ml_execution"
        ))

        access = get_unified_tool_access()
        spec = access.get_spec("spec_test")

        assert spec is not None
        assert spec.name == "spec_test"
        assert spec.tool_type == ToolType.ANALYSIS

    def test_get_by_layer(self):
        """레이어별 조회"""
        discovery = get_tool_discovery()
        discovery.register(ToolSpec(
            name="ml_tool", description="", tool_type=ToolType.DATA,
            executor="x", layer="ml_execution"
        ))
        discovery.register(ToolSpec(
            name="biz_tool", description="", tool_type=ToolType.CONTENT,
            executor="x", layer="biz_execution"
        ))

        access = get_unified_tool_access()
        ml_tools = access.get_by_layer("ml_execution")
        biz_tools = access.get_by_layer("biz_execution")

        assert len(ml_tools) == 1
        assert ml_tools[0].name == "ml_tool"
        assert len(biz_tools) == 1
        assert biz_tools[0].name == "biz_tool"

    def test_execution_order(self):
        """실행 순서 조회"""
        discovery = get_tool_discovery()
        discovery.register(ToolSpec(
            name="step1", description="", tool_type=ToolType.DATA,
            executor="x", dependencies=[]
        ))
        discovery.register(ToolSpec(
            name="step2", description="", tool_type=ToolType.ANALYSIS,
            executor="x", dependencies=["step1"]
        ))

        access = get_unified_tool_access()
        order = access.get_execution_order(["step2", "step1"])

        assert order.index("step1") < order.index("step2")
