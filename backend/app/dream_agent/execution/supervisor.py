"""Execution Supervisor

Tool → Executor 매핑 및 실행 관리
"""

from datetime import datetime
from typing import Any, Optional

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext, ExecutionResult, TodoItem

logger = get_logger(__name__)


class ExecutionSupervisor:
    """실행 감독기

    Tool을 적절한 Executor에 매핑하고 실행을 관리
    """

    # Tool → Executor 매핑 (Phase 2: 기본 매핑)
    TOOL_EXECUTOR_MAP: dict[str, str] = {
        # Data tools
        "collector": "data_executor",
        "preprocessor": "data_executor",
        "scraper": "data_executor",

        # Analysis tools
        "sentiment_analyzer": "analysis_executor",
        "keyword_extractor": "analysis_executor",
        "trend_analyzer": "analysis_executor",

        # Content tools
        "report_generator": "content_executor",
        "chart_maker": "content_executor",
        "summary_generator": "content_executor",

        # Ops tools
        "exporter": "ops_executor",
        "notifier": "ops_executor",
        "dashboard_builder": "ops_executor",
    }

    def __init__(self):
        self._executors: dict[str, Any] = {}

    def get_executor_type(self, tool: str) -> str:
        """Tool에 대한 Executor 타입 반환

        Args:
            tool: 도구 이름

        Returns:
            Executor 타입
        """
        return self.TOOL_EXECUTOR_MAP.get(tool, "default_executor")

    async def execute(
        self,
        todo: TodoItem,
        context: ExecutionContext,
    ) -> ExecutionResult:
        """Todo 실행

        Args:
            todo: 실행할 Todo
            context: 실행 컨텍스트

        Returns:
            실행 결과
        """
        started_at = datetime.utcnow()

        logger.info(
            "Executing todo",
            todo_id=todo.id,
            tool=todo.tool,
            session_id=context.session_id,
        )

        try:
            # Executor 가져오기
            executor_type = self.get_executor_type(todo.tool)

            # Phase 2: Mock 실행
            # 실제 구현에서는 executor를 동적으로 로드하여 실행
            result_data = await self._mock_execute(todo, context)

            completed_at = datetime.utcnow()
            execution_time = (completed_at - started_at).total_seconds() * 1000

            result = ExecutionResult(
                success=True,
                data=result_data,
                error=None,
                todo_id=todo.id,
                tool=todo.tool,
                started_at=started_at,
                completed_at=completed_at,
                execution_time_ms=execution_time,
            )

            logger.info(
                "Todo executed successfully",
                todo_id=todo.id,
                tool=todo.tool,
                execution_time_ms=execution_time,
            )

            return result

        except Exception as e:
            completed_at = datetime.utcnow()
            execution_time = (completed_at - started_at).total_seconds() * 1000

            logger.error(
                "Todo execution failed",
                todo_id=todo.id,
                tool=todo.tool,
                error=str(e),
            )

            return ExecutionResult(
                success=False,
                data={},
                error=str(e),
                todo_id=todo.id,
                tool=todo.tool,
                started_at=started_at,
                completed_at=completed_at,
                execution_time_ms=execution_time,
            )

    async def _mock_execute(
        self,
        todo: TodoItem,
        context: ExecutionContext,
    ) -> dict[str, Any]:
        """Mock 실행 (Phase 2)

        실제 구현에서는 각 Executor 클래스에서 처리

        Args:
            todo: 실행할 Todo
            context: 실행 컨텍스트

        Returns:
            실행 결과 데이터
        """
        import asyncio

        # 실행 시뮬레이션
        await asyncio.sleep(0.1)

        # 도구별 Mock 결과
        mock_results: dict[str, dict[str, Any]] = {
            "collector": {
                "collected_count": 100,
                "source": todo.tool_params.get("source", "unknown"),
                "data_preview": ["review 1", "review 2", "review 3"],
            },
            "preprocessor": {
                "processed_count": 95,
                "removed_count": 5,
                "cleaned": True,
            },
            "sentiment_analyzer": {
                "positive": 0.72,
                "negative": 0.15,
                "neutral": 0.13,
                "total_analyzed": 95,
            },
            "keyword_extractor": {
                "keywords": [
                    {"word": "보습", "count": 45},
                    {"word": "촉촉", "count": 32},
                    {"word": "가격", "count": 28},
                ],
            },
            "report_generator": {
                "report_path": "/reports/analysis_report.pdf",
                "format": "pdf",
            },
        }

        return mock_results.get(todo.tool, {"status": "completed", "tool": todo.tool})
