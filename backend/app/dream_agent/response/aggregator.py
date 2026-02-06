"""Result Aggregator

실행 결과 집계 및 요약
"""

from pathlib import Path
from typing import Any

import yaml

from app.core.logging import get_logger
from app.dream_agent.llm_manager import get_llm_client
from app.dream_agent.models import Intent

logger = get_logger(__name__)

# 프롬프트 로드
PROMPT_PATH = Path(__file__).parent.parent / "llm_manager" / "prompts" / "response.yaml"


def load_prompt_config() -> dict[str, Any]:
    """프롬프트 설정 로드"""
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return {}


class ResultAggregator:
    """결과 집계기"""

    def __init__(self):
        self.client = get_llm_client("response")
        self._prompt_config = load_prompt_config()

    def aggregate(
        self,
        execution_results: dict[str, Any],
    ) -> dict[str, Any]:
        """실행 결과 집계

        Args:
            execution_results: todo_id → result 매핑

        Returns:
            집계된 결과
        """
        aggregated = {
            "total_tasks": len(execution_results),
            "successful": 0,
            "failed": 0,
            "data": {},
        }

        for todo_id, result in execution_results.items():
            if isinstance(result, dict):
                if result.get("success", True):
                    aggregated["successful"] += 1
                    # 데이터 병합
                    data = result.get("data", {})
                    aggregated["data"][todo_id] = data
                else:
                    aggregated["failed"] += 1
            else:
                aggregated["successful"] += 1

        return aggregated

    async def summarize(
        self,
        aggregated: dict[str, Any],
        intent: Intent,
        language: str = "ko",
    ) -> dict[str, Any]:
        """결과 요약 생성 (LLM 사용)

        Args:
            aggregated: 집계된 결과
            intent: 원본 의도
            language: 언어

        Returns:
            {text, summary, next_actions}
        """
        logger.info("Summarizing results")

        # 프롬프트 구성
        system_prompt = self._prompt_config.get("system_prompt", "")
        user_template = self._prompt_config.get("user_template", "")

        if not user_template:
            # 기본 템플릿
            user_template = """
다음 분석 결과를 사용자에게 전달할 응답으로 작성해주세요.

## 원본 요청
{user_input}

## 분석 결과
{execution_results}

## 언어
{language}

JSON 형식으로 응답해주세요:
{{"format": "text|mixed", "text": "응답 텍스트", "summary": "한줄 요약", "next_actions": ["다음 액션1", "다음 액션2"]}}
"""

        import json

        user_prompt = user_template.format(
            user_input=intent.raw_input or intent.summary,
            execution_results=json.dumps(aggregated["data"], ensure_ascii=False, indent=2),
            language=language,
        )

        try:
            result = await self.client.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
            )

            return {
                "format": result.get("format", "text"),
                "text": result.get("text", ""),
                "summary": result.get("summary", ""),
                "next_actions": result.get("next_actions", []),
            }

        except Exception as e:
            logger.error("Summary generation failed", error=str(e))
            # 기본 요약
            return self._create_default_summary(aggregated, intent, language)

    def _create_default_summary(
        self,
        aggregated: dict[str, Any],
        intent: Intent,
        language: str,
    ) -> dict[str, Any]:
        """기본 요약 생성"""
        total = aggregated["total_tasks"]
        successful = aggregated["successful"]

        if language == "ko":
            text = f"""## 작업 완료

{intent.summary}에 대한 처리가 완료되었습니다.

### 실행 결과
- 총 {total}개 작업 중 {successful}개 완료

### 데이터 요약
"""
            for todo_id, data in aggregated["data"].items():
                if isinstance(data, dict):
                    for key, value in list(data.items())[:3]:
                        text += f"- {key}: {value}\n"

            summary = f"{total}개 작업 완료"
            next_actions = ["추가 분석", "보고서 생성"]

        else:
            text = f"""## Task Completed

Processing completed for: {intent.summary}

### Execution Results
- {successful} of {total} tasks completed
"""
            summary = f"{total} tasks completed"
            next_actions = ["Additional analysis", "Generate report"]

        return {
            "format": "text",
            "text": text,
            "summary": summary,
            "next_actions": next_actions,
        }
