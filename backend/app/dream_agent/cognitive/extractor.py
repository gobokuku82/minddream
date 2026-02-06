"""Entity Extractor

엔티티 추출 (IntentClassifier의 결과에서 분리)
"""

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import Entity

logger = get_logger(__name__)


class EntityExtractor:
    """엔티티 추출기

    Note: 현재는 IntentClassifier가 엔티티도 함께 추출하므로,
    이 클래스는 추가적인 엔티티 처리/정규화에 사용됩니다.
    """

    # 엔티티 타입별 정규화 규칙
    NORMALIZATION_RULES: dict[str, dict[str, str]] = {
        "source": {
            "아마존": "amazon",
            "올리브영": "oliveyoung",
            "네이버": "naver",
            "유튜브": "youtube",
            "구글": "google",
        },
        "brand": {
            # 브랜드 정규화 (필요시 추가)
        },
    }

    def normalize_entities(self, entities: list[dict[str, Any]]) -> list[Entity]:
        """엔티티 정규화

        Args:
            entities: 원본 엔티티 리스트

        Returns:
            정규화된 Entity 리스트
        """
        normalized = []

        for e in entities:
            entity_type = e.get("type", "unknown")
            value = e.get("value", "")
            confidence = e.get("confidence", 0.5)

            # 정규화 적용
            if entity_type in self.NORMALIZATION_RULES:
                rules = self.NORMALIZATION_RULES[entity_type]
                normalized_value = rules.get(value, value)
            else:
                normalized_value = value

            normalized.append(
                Entity(
                    type=entity_type,
                    value=normalized_value,
                    confidence=confidence,
                    metadata={"original_value": value} if value != normalized_value else {},
                )
            )

        return normalized

    def merge_entities(
        self,
        entities_1: list[Entity],
        entities_2: list[Entity],
    ) -> list[Entity]:
        """두 엔티티 리스트 병합 (중복 제거)

        Args:
            entities_1: 첫 번째 엔티티 리스트
            entities_2: 두 번째 엔티티 리스트

        Returns:
            병합된 엔티티 리스트
        """
        seen = set()
        merged = []

        for e in entities_1 + entities_2:
            key = (e.type, e.value)
            if key not in seen:
                seen.add(key)
                merged.append(e)

        return merged

    def filter_by_confidence(
        self,
        entities: list[Entity],
        min_confidence: float = 0.5,
    ) -> list[Entity]:
        """신뢰도 기준 필터링

        Args:
            entities: 엔티티 리스트
            min_confidence: 최소 신뢰도

        Returns:
            필터링된 엔티티 리스트
        """
        return [e for e in entities if e.confidence >= min_confidence]

    def get_entities_by_type(
        self,
        entities: list[Entity],
        entity_type: str,
    ) -> list[Entity]:
        """타입별 엔티티 조회

        Args:
            entities: 엔티티 리스트
            entity_type: 엔티티 타입

        Returns:
            해당 타입의 엔티티 리스트
        """
        return [e for e in entities if e.type == entity_type]
