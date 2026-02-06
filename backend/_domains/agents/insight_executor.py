"""InsightExecutor - 인사이트 생성 실행기

분석 도구(sentiment, keyword, hashtag, problem, competitor) 및
인사이트 생성기(insight_generator)를 실행합니다.
"""

from typing import Any, Dict, Optional, List
import logging

from .core import BaseExecutor
from .core.base_executor import register_executor, ExecutionResult

logger = logging.getLogger(__name__)


@register_executor("insight_executor")
class InsightExecutor(BaseExecutor):
    """인사이트 생성 실행기

    Attributes:
        supported_tools: sentiment, keyword, hashtag, problem, competitor, insight

    지원하는 작업:
    - 감성 분석 (sentiment)
    - 키워드 추출 (keyword)
    - 해시태그 분석 (hashtag)
    - 문제점 분류 (problem)
    - 경쟁사 분석 (competitor)
    - 종합 인사이트 생성 (insight)

    Example:
        ```python
        executor = InsightExecutor()
        result = await executor.execute(todo, context)
        ```
    """

    name: str = "insight_executor"
    category: str = "insight"
    supported_tools: List[str] = [
        "sentiment",
        "keyword",
        "hashtag",
        "problem",
        "competitor",
        "insight",
    ]
    version: str = "1.0.0"

    def __init__(self, enable_hitl: bool = True, **kwargs):
        """인사이트 실행기 초기화

        Args:
            enable_hitl: HITL 활성화 여부
            **kwargs: 추가 설정
        """
        super().__init__(enable_hitl=enable_hitl, **kwargs)
        self._tools_initialized = False

    def initialize(self) -> None:
        """도구 임포트 및 초기화"""
        if self._initialized:
            return

        try:
            # 분석 도구 모듈 임포트 (lazy loading)
            from ..tools import analysis
            self._analysis_module = analysis
            self._tools_initialized = True
            logger.info(f"[{self.name}] Analysis tools initialized")
        except ImportError as e:
            logger.warning(f"[{self.name}] Analysis tools import failed: {e}")
            self._tools_initialized = False

        self._initialized = True

    async def _execute_impl(self, todo: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """분석/인사이트 도구 실행

        Args:
            todo: TodoItem 인스턴스
            context: 실행 컨텍스트

        Returns:
            실행 결과 딕셔너리
        """
        # 도구 이름 추출
        tool_name = self._get_tool_name(todo)
        if not tool_name:
            raise ValueError(f"No tool specified in todo: {getattr(todo, 'id', None)}")

        # 도구 파라미터 추출
        params = self._get_tool_params(todo, context)

        logger.info(f"[{self.name}] Executing tool: {tool_name} with params: {list(params.keys())}")

        # 도구별 실행
        if tool_name == "sentiment":
            return await self._execute_sentiment(params)
        elif tool_name == "keyword":
            return await self._execute_keyword(params)
        elif tool_name == "hashtag":
            return await self._execute_hashtag(params)
        elif tool_name == "problem":
            return await self._execute_problem(params)
        elif tool_name == "competitor":
            return await self._execute_competitor(params)
        elif tool_name == "insight":
            return await self._execute_insight(params)
        else:
            raise ValueError(f"Unsupported tool: {tool_name}")

    async def _execute_sentiment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """감성 분석 실행

        Args:
            params: 감성 분석 파라미터
                - texts: 분석할 텍스트 목록

        Returns:
            감성 분석 결과
        """
        from ..tools.analysis import analyze_sentiment_direct

        texts = params.get("texts", [])
        if not texts:
            reviews = params.get("reviews", [])
            if reviews:
                texts = [r.get("content", "") for r in reviews if r.get("content")]

        if not texts:
            return {
                "tool": "sentiment",
                "result": {},
                "success": True,
                "message": "No texts to analyze",
            }

        result = analyze_sentiment_direct(texts=texts)

        return {
            "tool": "sentiment",
            "analysis": result.get("analysis", {}),
            "stats": result.get("stats", {}),
            "success": result.get("success", True),
        }

    async def _execute_keyword(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """키워드 추출 실행

        Args:
            params: 키워드 추출 파라미터
                - texts: 분석할 텍스트 목록
                - top_n: 상위 키워드 개수 (optional)

        Returns:
            키워드 추출 결과
        """
        from ..tools.analysis import extract_keywords_direct

        texts = params.get("texts", [])
        if not texts:
            reviews = params.get("reviews", [])
            if reviews:
                texts = [r.get("content", "") for r in reviews if r.get("content")]

        if not texts:
            return {
                "tool": "keyword",
                "keywords": [],
                "success": True,
                "message": "No texts to analyze",
            }

        top_n = params.get("top_n", 20)
        result = extract_keywords_direct(texts=texts, top_n=top_n)

        return {
            "tool": "keyword",
            "keywords": result.get("keywords", []),
            "bigrams": result.get("bigrams", []),
            "success": result.get("success", True),
        }

    async def _execute_hashtag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """해시태그 분석 실행

        Args:
            params: 해시태그 분석 파라미터
                - texts: 분석할 텍스트 목록
                - keyword: 검색 키워드

        Returns:
            해시태그 분석 결과
        """
        from ..tools.analysis import extract_hashtags_direct

        texts = params.get("texts", [])
        keyword = params.get("keyword", "")

        if not texts and not keyword:
            return {
                "tool": "hashtag",
                "hashtags": [],
                "success": True,
                "message": "No texts or keyword provided",
            }

        result = extract_hashtags_direct(texts=texts, keyword=keyword)

        return {
            "tool": "hashtag",
            "hashtags": result.get("hashtags", []),
            "trending": result.get("trending", []),
            "success": result.get("success", True),
        }

    async def _execute_problem(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """문제점 분류 실행

        Args:
            params: 문제점 분류 파라미터
                - texts: 분석할 텍스트 목록

        Returns:
            문제점 분류 결과
        """
        from ..tools.analysis import classify_problems_direct

        texts = params.get("texts", [])
        if not texts:
            reviews = params.get("reviews", [])
            if reviews:
                texts = [r.get("content", "") for r in reviews if r.get("content")]

        if not texts:
            return {
                "tool": "problem",
                "problems": [],
                "success": True,
                "message": "No texts to analyze",
            }

        result = classify_problems_direct(texts=texts)

        return {
            "tool": "problem",
            "problems": result.get("problems", []),
            "summary": result.get("summary", {}),
            "success": result.get("success", True),
        }

    async def _execute_competitor(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """경쟁사 분석 실행

        Args:
            params: 경쟁사 분석 파라미터
                - brands: 비교할 브랜드 목록
                - keyword: 검색 키워드

        Returns:
            경쟁사 분석 결과
        """
        from ..tools.analysis import compare_brands_direct

        brands = params.get("brands", [])
        keyword = params.get("keyword", "")

        if not brands:
            return {
                "tool": "competitor",
                "comparison": {},
                "success": True,
                "message": "No brands provided",
            }

        result = compare_brands_direct(brands=brands, keyword=keyword)

        return {
            "tool": "competitor",
            "comparison": result.get("comparison", {}),
            "ranking": result.get("ranking", []),
            "success": result.get("success", True),
        }

    async def _execute_insight(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """종합 인사이트 생성 실행

        Args:
            params: 인사이트 생성 파라미터
                - ml_result: ML 분석 결과 딕셔너리
                - brand: 타겟 브랜드 (optional)
                - with_trends: K-Beauty 트렌드 포함 여부 (optional)

        Returns:
            인사이트 리포트
        """
        from ..ml_execution.agents.insight_generator_agent import (
            generate_insights_direct,
            generate_insights_with_trends_direct,
        )

        ml_result = params.get("ml_result", {})
        brand = params.get("brand", "Amorepacific")
        with_trends = params.get("with_trends", False)

        if not ml_result:
            # context에서 이전 분석 결과 조합
            ml_result = self._build_ml_result_from_context(params)

        if not ml_result:
            return {
                "tool": "insight",
                "insights": [],
                "success": True,
                "message": "No ML results to generate insights from",
            }

        try:
            if with_trends:
                result = generate_insights_with_trends_direct(
                    ml_result=ml_result,
                    brand=brand,
                )
            else:
                result = generate_insights_direct(ml_result=ml_result)

            return {
                "tool": "insight",
                "report_id": result.get("report_id"),
                "insights": result.get("insights", []),
                "summary": result.get("summary", ""),
                "key_metrics": result.get("key_metrics", {}),
                "trend_context": result.get("trend_context"),
                "kbeauty_insights": result.get("kbeauty_insights"),
                "success": True,
            }
        except Exception as e:
            logger.error(f"[{self.name}] Insight generation failed: {e}")
            return {
                "tool": "insight",
                "insights": [],
                "success": False,
                "error": str(e),
            }

    def _build_ml_result_from_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """컨텍스트에서 ML 결과 조합

        Args:
            context: 실행 컨텍스트

        Returns:
            ML 결과 딕셔너리
        """
        ml_result = {}

        # 이전 실행 결과에서 데이터 추출
        if "sentiment_result" in context:
            ml_result["absa_analyzer"] = context["sentiment_result"]
        if "keyword_result" in context:
            ml_result["extractor"] = context["keyword_result"]
        if "problem_result" in context:
            ml_result["problem_classifier"] = context["problem_result"]
        if "trends_result" in context:
            ml_result["google_trends"] = context["trends_result"]

        return ml_result

    def _get_tool_name(self, todo: Any) -> Optional[str]:
        """Todo에서 도구 이름 추출

        Args:
            todo: TodoItem 인스턴스

        Returns:
            도구 이름 또는 None
        """
        if hasattr(todo, "metadata"):
            metadata = todo.metadata
            if hasattr(metadata, "execution") and metadata.execution:
                return metadata.execution.get("tool")

        if hasattr(todo, "tool"):
            return todo.tool

        return None

    def _get_tool_params(self, todo: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Todo에서 도구 파라미터 추출

        Args:
            todo: TodoItem 인스턴스
            context: 실행 컨텍스트

        Returns:
            파라미터 딕셔너리
        """
        params = {}

        if hasattr(todo, "metadata"):
            metadata = todo.metadata
            if hasattr(metadata, "execution") and metadata.execution:
                tool_params = metadata.execution.get("tool_params", {})
                params.update(tool_params)

            if hasattr(metadata, "data") and metadata.data:
                input_data = metadata.data.get("input_data", {})
                params.update(input_data)

        params.update(context)

        return params
