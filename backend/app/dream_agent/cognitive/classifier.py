"""Intent Classifier

LLM 기반 의도 분류
"""

from pathlib import Path
from typing import Any, Optional

import yaml

from app.core.logging import get_logger
from app.dream_agent.llm_manager import get_llm_client
from app.dream_agent.models import Entity, Intent, IntentCategory, IntentDomain

logger = get_logger(__name__)

# 프롬프트 로드
PROMPT_PATH = Path(__file__).parent.parent / "llm_manager" / "prompts" / "cognitive.yaml"


def load_prompt_config() -> dict[str, Any]:
    """프롬프트 설정 로드"""
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class IntentClassifier:
    """LLM 기반 의도 분류기"""

    def __init__(self):
        self.client = get_llm_client("cognitive")
        self._prompt_config = load_prompt_config()

    async def classify(
        self,
        user_input: str,
        language: str = "ko",
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """의도 분류

        Args:
            user_input: 사용자 입력
            language: 언어 코드
            context: 이전 대화 맥락

        Returns:
            분류 결과 (dict)
        """
        logger.info(
            "Classifying intent",
            input_length=len(user_input),
            language=language,
        )

        # 프롬프트 구성
        system_prompt = self._prompt_config.get("system_prompt", "")
        user_template = self._prompt_config.get("user_template", "")

        # 언어별 지시 추가
        lang_instructions = self._prompt_config.get("language_instructions", {})
        if language in lang_instructions:
            system_prompt += f"\n\n{lang_instructions[language]}"

        # 사용자 프롬프트 포맷
        user_prompt = user_template.format(
            user_input=user_input,
            language=language,
            context_summary=context.get("summary", "") if context else "",
        )

        try:
            # LLM 호출
            result = await self.client.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
            )

            logger.info(
                "Intent classified",
                domain=result.get("intent", {}).get("domain"),
                confidence=result.get("intent", {}).get("confidence"),
            )

            return result

        except Exception as e:
            logger.error("Intent classification failed", error=str(e))
            # 기본값 반환
            return {
                "intent": {
                    "domain": "inquiry",
                    "category": "general",
                    "subcategory": None,
                    "confidence": 0.5,
                },
                "entities": [],
                "plan_hint": "의도 분류 실패, 기본 질의로 처리",
                "requires_clarification": True,
                "clarification_question": "요청을 이해하지 못했습니다. 다시 설명해주시겠어요?",
                "context_summary": user_input[:100],
            }

    def parse_result(self, result: dict[str, Any], raw_input: str, language: str) -> Intent:
        """분류 결과를 Intent 모델로 변환

        Args:
            result: LLM 응답
            raw_input: 원본 입력
            language: 언어 코드

        Returns:
            Intent 모델
        """
        intent_data = result.get("intent", {})

        # Domain 파싱
        domain_str = intent_data.get("domain", "inquiry")
        try:
            domain = IntentDomain(domain_str)
        except ValueError:
            domain = IntentDomain.INQUIRY

        # Category 파싱 (선택적)
        category_str = intent_data.get("category")
        category = None
        if category_str:
            try:
                category = IntentCategory(category_str)
            except ValueError:
                # 커스텀 카테고리는 무시
                pass

        # Entities 파싱
        entities = []
        for e in result.get("entities", []):
            entities.append(
                Entity(
                    type=e.get("type", "unknown"),
                    value=e.get("value", ""),
                    confidence=e.get("confidence", 0.5),
                )
            )

        return Intent(
            domain=domain,
            category=category,
            subcategory=intent_data.get("subcategory"),
            confidence=intent_data.get("confidence", 0.5),
            entities=entities,
            summary=result.get("context_summary", ""),
            plan_hint=result.get("plan_hint", ""),
            raw_input=raw_input,
            language=language,
        )
