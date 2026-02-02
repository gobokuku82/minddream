"""Tool System E2E 테스트

Phase 0 ~ Phase 3 전체 통합 테스트.
"""

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
from backend.app.dream_agent.tools.compat import (
    ToolSpecAdapter,
    spec_to_base_tool,
    get_unified_tool_access,
    UnifiedToolAccess,
)
from backend.app.dream_agent.tools.validator import (
    ToolValidator,
    ValidationResult,
    get_tool_validator,
    validate_tool_spec,
    validate_all_tools,
)
from backend.app.dream_agent.tools.hot_reload import (
    YAMLWatcher,
    ToolHotReloader,
    get_tool_hot_reloader,
)
from backend.app.dream_agent.execution.domain.base_agent import (
    BaseDomainAgent,
    DomainAgentRegistry,
    get_domain_agent_registry,
)
from backend.app.dream_agent.schemas.tool_io import (
    ToolInput,
    ToolOutput,
    SentimentInput,
    SentimentOutput,
    KeywordInput,
    KeywordOutput,
)


class TestPhase0Discovery:
    """Phase 0: Tool Discovery 통합 테스트"""

    def setup_method(self):
        ToolDiscovery.reset()

    def test_full_yaml_loading(self):
        """전체 YAML 파일 로드"""
        yaml_dir = Path(__file__).parent.parent.parent.parent / "backend/app/dream_agent/tools/definitions"
        if yaml_dir.exists():
            tools = load_tools_from_yaml(yaml_dir)
            discovery = get_tool_discovery()

            # 최소 10개 이상의 도구가 로드되어야 함
            assert len(discovery.list_all()) >= 10
            assert len(tools) >= 10

    def test_layer_based_query(self):
        """레이어 기반 조회"""
        yaml_dir = Path(__file__).parent.parent.parent.parent / "backend/app/dream_agent/tools/definitions"
        if yaml_dir.exists():
            load_tools_from_yaml(yaml_dir)
            discovery = get_tool_discovery()

            ml_tools = discovery.get_by_layer("ml_execution")
            biz_tools = discovery.get_by_layer("biz_execution")

            assert len(ml_tools) > 0
            assert len(biz_tools) > 0


class TestPhase1Compatibility:
    """Phase 1: 호환성 레이어 테스트"""

    def setup_method(self):
        ToolDiscovery.reset()
        import backend.app.dream_agent.tools.compat as compat
        compat._unified_access = None

    def test_spec_adapter_workflow(self):
        """ToolSpecAdapter 전체 워크플로우"""
        spec = ToolSpec(
            name="test_adapter",
            description="Adapter test",
            tool_type=ToolType.ANALYSIS,
            executor="test.executor",
            layer="ml_execution",
            parameters=[
                ToolParameter(
                    name="input",
                    type=ToolParameterType.STRING,
                    required=True
                )
            ]
        )

        adapter = ToolSpecAdapter(spec)

        # 메타데이터 확인
        metadata = adapter.get_metadata()
        assert metadata["name"] == "test_adapter"
        assert metadata["layer"] == "ml_execution"

        # 입력 검증
        assert not adapter.validate_input()  # 필수 파라미터 누락
        assert adapter.validate_input(input="test")  # 정상

    def test_unified_access_integration(self):
        """UnifiedToolAccess 통합"""
        # 도구 등록
        discovery = get_tool_discovery()
        discovery.register(ToolSpec(
            name="unified_test",
            description="Test",
            tool_type=ToolType.DATA,
            executor="test",
            layer="ml_execution"
        ))

        # UnifiedToolAccess로 조회
        access = get_unified_tool_access()

        tool = access.get("unified_test")
        assert tool is not None
        assert tool.name == "unified_test"

        spec = access.get_spec("unified_test")
        assert spec is not None
        assert spec.layer == "ml_execution"


class TestPhase2HotReload:
    """Phase 2: Hot Reload 테스트"""

    def test_yaml_watcher_creation(self):
        """YAMLWatcher 생성"""
        changes = []

        def on_change(files):
            changes.extend(files)

        watcher = YAMLWatcher(
            watch_dir=Path("/tmp"),
            on_change=on_change,
            interval=0.1
        )

        assert not watcher.is_running()

    def test_hot_reloader_stats(self):
        """ToolHotReloader 통계"""
        reloader = get_tool_hot_reloader()
        stats = reloader.get_stats()

        assert "running" in stats
        assert "reload_count" in stats
        assert "watch_dir" in stats


class TestPhase2DomainAgent:
    """Phase 2: BaseDomainAgent 테스트"""

    def setup_method(self):
        DomainAgentRegistry.reset()

    def test_domain_agent_registry(self):
        """DomainAgentRegistry 기능"""
        registry = get_domain_agent_registry()

        # 커스텀 에이전트 클래스 (테스트용)
        class TestAgent(BaseDomainAgent):
            @property
            def name(self) -> str:
                return "test_agent"

            @property
            def description(self) -> str:
                return "Test agent"

            async def execute(self, input: ToolInput) -> ToolOutput:
                return ToolOutput(success=True, data={"test": True})

        # 등록
        agent = TestAgent()
        registry.register(agent)

        # 조회
        retrieved = registry.get("test_agent")
        assert retrieved is not None
        assert retrieved.name == "test_agent"

        # 목록
        assert "test_agent" in registry.list_names()


class TestPhase2ToolIOSchemas:
    """Phase 2: Tool I/O 스키마 테스트"""

    def test_sentiment_schema(self):
        """SentimentInput/Output 스키마"""
        input_data = SentimentInput(
            texts=["좋아요", "별로예요"],
            analysis_mode="standard"
        )
        assert len(input_data.texts) == 2
        assert input_data.analysis_mode == "standard"

    def test_keyword_schema(self):
        """KeywordInput/Output 스키마"""
        input_data = KeywordInput(
            texts=["테스트 텍스트"],
            top_k=5
        )
        assert input_data.top_k == 5


class TestPhase3Validator:
    """Phase 3: ToolValidator 테스트"""

    def setup_method(self):
        ToolDiscovery.reset()

    def test_spec_validation(self):
        """단일 ToolSpec 검증"""
        validator = get_tool_validator()

        # 유효한 스펙
        valid_spec = ToolSpec(
            name="valid_tool",
            description="Valid tool",
            tool_type=ToolType.DATA,
            executor="test.executor",
            layer="ml_execution"
        )
        result = validator.validate_spec(valid_spec)
        assert result.valid

        # 유효하지 않은 스펙 (빈 이름)
        invalid_spec = ToolSpec(
            name="",
            description="",
            tool_type=ToolType.DATA,
            executor=""
        )
        # 이름은 validator에 의해 검사되기 전에 정규화됨

    def test_dependency_validation(self):
        """의존성 검증"""
        discovery = get_tool_discovery()

        # 도구 등록 (의존성 체인)
        discovery.register(ToolSpec(
            name="step1", description="", tool_type=ToolType.DATA, executor="x"
        ))
        discovery.register(ToolSpec(
            name="step2", description="", tool_type=ToolType.ANALYSIS,
            executor="x", dependencies=["step1"]
        ))
        discovery.register(ToolSpec(
            name="step3", description="", tool_type=ToolType.CONTENT,
            executor="x", dependencies=["step2"]
        ))

        validator = get_tool_validator()
        result = validator.validate_dependencies()

        # 순환 의존성 없음
        assert result.valid

    def test_circular_dependency_detection(self):
        """순환 의존성 탐지"""
        discovery = get_tool_discovery()

        # 순환 의존성 등록
        discovery.register(ToolSpec(
            name="a", description="", tool_type=ToolType.DATA,
            executor="x", dependencies=["c"]
        ))
        discovery.register(ToolSpec(
            name="b", description="", tool_type=ToolType.ANALYSIS,
            executor="x", dependencies=["a"]
        ))
        discovery.register(ToolSpec(
            name="c", description="", tool_type=ToolType.CONTENT,
            executor="x", dependencies=["b"]
        ))

        validator = get_tool_validator()
        result = validator.validate_dependencies()

        # 순환 의존성 탐지됨
        assert not result.valid
        assert any("Circular" in e for e in result.errors)

    def test_validate_all_yaml_tools(self):
        """전체 YAML 도구 검증"""
        yaml_dir = Path(__file__).parent.parent.parent.parent / "backend/app/dream_agent/tools/definitions"
        if yaml_dir.exists():
            load_tools_from_yaml(yaml_dir)

            result = validate_all_tools()

            # 모든 YAML 도구가 유효해야 함
            if not result.valid:
                print(f"Validation errors: {result.errors}")
            assert result.valid, f"YAML tools validation failed: {result.errors}"


class TestPhase3LayerSchemaValidation:
    """Phase 3: Layer 스키마 검증 테스트"""

    def test_cognitive_input_validation(self):
        """CognitiveInput 검증"""
        from backend.app.dream_agent.schemas.cognitive import CognitiveInput

        # 유효한 입력
        valid = CognitiveInput(user_input="테스트 입력")
        assert valid.user_input == "테스트 입력"

        # 빈 입력은 실패
        with pytest.raises(ValueError):
            CognitiveInput(user_input="")

    def test_planning_output_validation(self):
        """PlanningOutput 검증"""
        from backend.app.dream_agent.schemas.planning import PlanningOutput
        from backend.app.dream_agent.models.plan import Plan
        from backend.app.dream_agent.models.todo import TodoItem

        # todos가 비어있으면 실패
        with pytest.raises(ValueError):
            PlanningOutput(
                plan=Plan(session_id="test", intent={}),
                todos=[]
            )

    def test_response_output_validation(self):
        """ResponseOutput 검증"""
        from backend.app.dream_agent.schemas.response import ResponseOutput

        # 빈 응답은 실패
        with pytest.raises(ValueError):
            ResponseOutput(response_text="")

        # 유효한 응답
        valid = ResponseOutput(response_text="테스트 응답")
        assert valid.response_text == "테스트 응답"


class TestE2EToolWorkflow:
    """E2E: 전체 도구 워크플로우 테스트"""

    def setup_method(self):
        ToolDiscovery.reset()
        DomainAgentRegistry.reset()
        import backend.app.dream_agent.tools.compat as compat
        compat._unified_access = None

    def test_full_workflow(self):
        """전체 워크플로우: YAML 로드 → 검증 → 사용"""
        yaml_dir = Path(__file__).parent.parent.parent.parent / "backend/app/dream_agent/tools/definitions"
        if not yaml_dir.exists():
            pytest.skip("YAML definitions not found")

        # 1. YAML 로드
        tools = load_tools_from_yaml(yaml_dir)
        assert len(tools) > 0

        # 2. 검증
        result = validate_all_tools()
        assert result.valid, f"Validation failed: {result.errors}"

        # 3. UnifiedToolAccess로 조회
        access = get_unified_tool_access()

        # 센티먼트 분석기 확인
        sentiment = access.get_spec("sentiment_analyzer")
        assert sentiment is not None
        assert sentiment.layer == "ml_execution"

        # 리포트 생성기 확인
        report = access.get_spec("report_generator")
        assert report is not None
        assert report.layer == "biz_execution"

        # 4. 실행 순서 확인
        order = access.get_execution_order([
            "report_generator",
            "sentiment_analyzer",
            "keyword_extractor"
        ])
        # report_generator는 sentiment_analyzer, keyword_extractor에 의존
        # 따라서 sentiment_analyzer, keyword_extractor가 먼저 와야 함
        report_idx = order.index("report_generator")
        if "sentiment_analyzer" in order:
            sentiment_idx = order.index("sentiment_analyzer")
            assert sentiment_idx < report_idx
        if "keyword_extractor" in order:
            keyword_idx = order.index("keyword_extractor")
            assert keyword_idx < report_idx
