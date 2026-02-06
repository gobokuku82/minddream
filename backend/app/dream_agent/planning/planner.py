"""Plan Generator

LLM 기반 계획 생성
"""

import json
from pathlib import Path
from typing import Any, Optional

import yaml

from app.core.logging import get_logger
from app.dream_agent.llm_manager import get_llm_client
from app.dream_agent.models import (
    ExecutionStrategy,
    Intent,
    Plan,
    PlanStatus,
    TodoItem,
)

logger = get_logger(__name__)

# 프롬프트 로드
PROMPT_PATH = Path(__file__).parent.parent / "llm_manager" / "prompts" / "planning.yaml"


def load_prompt_config() -> dict[str, Any]:
    """프롬프트 설정 로드"""
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class PlanGenerator:
    """LLM 기반 계획 생성기"""

    def __init__(self):
        self.client = get_llm_client("planning")
        self._prompt_config = load_prompt_config()

    async def generate(
        self,
        intent: Intent,
        session_id: str,
        available_tools: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """계획 생성

        Args:
            intent: 분류된 의도
            session_id: 세션 ID
            available_tools: 사용 가능한 도구 목록

        Returns:
            생성된 계획 (dict)
        """
        logger.info(
            "Generating plan",
            session_id=session_id,
            intent_domain=intent.domain.value,
        )

        # 기본 도구 목록
        if available_tools is None:
            available_tools = self._get_default_tools(intent)

        # 프롬프트 구성
        system_prompt = self._prompt_config.get("system_prompt", "")
        user_template = self._prompt_config.get("user_template", "")

        # 엔티티 포맷
        entities_str = json.dumps(
            [{"type": e.type, "value": e.value} for e in intent.entities],
            ensure_ascii=False,
            indent=2,
        )

        # 사용자 프롬프트 포맷
        user_prompt = user_template.format(
            domain=intent.domain.value,
            category=intent.category.value if intent.category else "general",
            summary=intent.summary,
            plan_hint=intent.plan_hint,
            entities=entities_str,
            available_tools=", ".join(available_tools),
        )

        try:
            # LLM 호출
            result = await self.client.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
            )

            logger.info(
                "Plan generated",
                session_id=session_id,
                todo_count=len(result.get("todos", [])),
            )

            return result

        except Exception as e:
            logger.error("Plan generation failed", error=str(e))
            # 기본 계획 반환
            return self._create_fallback_plan(intent)

    def parse_result(
        self,
        result: dict[str, Any],
        intent: Intent,
        session_id: str,
    ) -> Plan:
        """생성 결과를 Plan 모델로 변환

        Args:
            result: LLM 응답
            intent: 분류된 의도
            session_id: 세션 ID

        Returns:
            Plan 모델
        """
        # Todos 생성
        todos = []
        todo_id_map: dict[str, str] = {}  # 임시 ID → 실제 ID 매핑

        for idx, todo_data in enumerate(result.get("todos", [])):
            todo = TodoItem(
                task=todo_data.get("task", f"Task {idx + 1}"),
                description=todo_data.get("description"),
                tool=todo_data.get("tool", "unknown"),
                tool_params=todo_data.get("tool_params", {}),
                priority=todo_data.get("priority", 5),
                depends_on=[],  # 나중에 매핑
            )
            todos.append(todo)
            todo_id_map[f"todo_{idx + 1}"] = todo.id

        # 의존성 매핑
        updated_todos = []
        for idx, (todo, todo_data) in enumerate(zip(todos, result.get("todos", []))):
            depends_on_refs = todo_data.get("depends_on", [])
            depends_on_ids = []

            for ref in depends_on_refs:
                if ref in todo_id_map:
                    depends_on_ids.append(todo_id_map[ref])
                elif ref in [t.id for t in todos]:
                    depends_on_ids.append(ref)

            if depends_on_ids:
                todo = todo.model_copy(update={"depends_on": depends_on_ids})

            updated_todos.append(todo)

        # 의존성 그래프 생성
        dependency_graph = {
            todo.id: todo.depends_on for todo in updated_todos
        }

        # 실행 전략
        strategy_str = result.get("strategy", "sequential")
        try:
            strategy = ExecutionStrategy(strategy_str)
        except ValueError:
            strategy = ExecutionStrategy.SEQUENTIAL

        return Plan(
            session_id=session_id,
            status=PlanStatus.DRAFT,
            todos=updated_todos,
            dependency_graph=dependency_graph,
            strategy=strategy,
            estimated_duration_sec=result.get("estimated_duration_sec", 60),
            estimated_cost_usd=result.get("estimated_cost_usd", 0.0),
            mermaid_diagram=result.get("mermaid_diagram"),
            intent_summary=intent.summary,
        )

    def _get_default_tools(self, intent: Intent) -> list[str]:
        """의도 기반 기본 도구 목록"""
        domain = intent.domain.value

        tools_by_domain = {
            "analysis": [
                "collector",
                "preprocessor",
                "sentiment_analyzer",
                "keyword_extractor",
                "trend_analyzer",
            ],
            "content": [
                "report_generator",
                "chart_maker",
                "summary_generator",
            ],
            "operation": [
                "dashboard_builder",
                "exporter",
                "notifier",
            ],
            "inquiry": [
                "knowledge_search",
            ],
        }

        return tools_by_domain.get(domain, ["collector", "analyzer"])

    def _create_fallback_plan(self, intent: Intent) -> dict[str, Any]:
        """폴백 계획 생성"""
        return {
            "todos": [
                {
                    "task": "요청 처리",
                    "description": intent.summary,
                    "tool": "default_handler",
                    "tool_params": {},
                    "priority": 5,
                    "depends_on": [],
                }
            ],
            "strategy": "single",
            "estimated_duration_sec": 30,
        }
