"""Ambiguity Detector & Clarifier

모호성 탐지 및 명확화 질문 생성
"""

from typing import Any, Optional

from app.core.logging import get_logger
from app.dream_agent.models import Intent

logger = get_logger(__name__)


class AmbiguityDetector:
    """모호성 탐지기"""

    # 모호성 탐지 규칙
    AMBIGUITY_RULES = {
        "no_entities": {
            "condition": lambda intent, result: len(result.get("entities", [])) == 0,
            "severity": "high",
            "default_question": "분석 대상(브랜드, 제품명 등)을 알려주세요.",
        },
        "low_confidence": {
            "condition": lambda intent, result: result.get("intent", {}).get("confidence", 1.0) < 0.7,
            "severity": "medium",
            "default_question": "요청을 좀 더 구체적으로 설명해주시겠어요?",
        },
        "missing_source": {
            "condition": lambda intent, result: (
                result.get("intent", {}).get("domain") == "analysis"
                and not any(e.get("type") == "source" for e in result.get("entities", []))
            ),
            "severity": "low",
            "default_question": "어떤 플랫폼(아마존, 올리브영 등)에서 데이터를 수집할까요?",
        },
    }

    def detect(self, intent: Intent, raw_result: dict[str, Any]) -> dict[str, Any]:
        """모호성 탐지

        Args:
            intent: 분류된 의도
            raw_result: LLM 원본 응답

        Returns:
            {
                "is_ambiguous": bool,
                "ambiguity_types": list[str],
                "severity": str,
                "clarification_question": str
            }
        """
        # LLM이 이미 모호성을 감지한 경우
        if raw_result.get("requires_clarification"):
            return {
                "is_ambiguous": True,
                "ambiguity_types": ["llm_detected"],
                "severity": "high",
                "clarification_question": raw_result.get("clarification_question", ""),
            }

        # 규칙 기반 추가 탐지
        detected = []
        max_severity = "low"
        severity_order = {"low": 0, "medium": 1, "high": 2}

        for rule_name, rule in self.AMBIGUITY_RULES.items():
            if rule["condition"](intent, raw_result):
                detected.append(rule_name)
                if severity_order[rule["severity"]] > severity_order[max_severity]:
                    max_severity = rule["severity"]

        if detected:
            # 가장 중요한 규칙의 질문 사용
            primary_rule = max(detected, key=lambda r: severity_order[self.AMBIGUITY_RULES[r]["severity"]])
            question = self.AMBIGUITY_RULES[primary_rule]["default_question"]

            return {
                "is_ambiguous": True,
                "ambiguity_types": detected,
                "severity": max_severity,
                "clarification_question": question,
            }

        return {
            "is_ambiguous": False,
            "ambiguity_types": [],
            "severity": "none",
            "clarification_question": None,
        }


class Clarifier:
    """명확화 질문 생성기"""

    def __init__(self):
        self.detector = AmbiguityDetector()

    def needs_clarification(
        self,
        intent: Intent,
        raw_result: dict[str, Any],
    ) -> bool:
        """명확화 필요 여부 확인

        Args:
            intent: 분류된 의도
            raw_result: LLM 원본 응답

        Returns:
            명확화 필요 여부
        """
        result = self.detector.detect(intent, raw_result)
        return result["is_ambiguous"] and result["severity"] in ("medium", "high")

    def get_clarification_question(
        self,
        intent: Intent,
        raw_result: dict[str, Any],
    ) -> Optional[str]:
        """명확화 질문 가져오기

        Args:
            intent: 분류된 의도
            raw_result: LLM 원본 응답

        Returns:
            명확화 질문 또는 None
        """
        result = self.detector.detect(intent, raw_result)

        if not result["is_ambiguous"]:
            return None

        return result["clarification_question"]

    def generate_options(
        self,
        intent: Intent,
        ambiguity_type: str,
    ) -> list[str]:
        """선택지 생성 (HITL용)

        Args:
            intent: 분류된 의도
            ambiguity_type: 모호성 타입

        Returns:
            선택지 리스트
        """
        # 모호성 타입별 기본 선택지
        options_map = {
            "no_entities": [],  # 자유 입력
            "missing_source": ["아마존", "올리브영", "네이버", "전체"],
            "low_confidence": [],  # 자유 입력
        }

        return options_map.get(ambiguity_type, [])
