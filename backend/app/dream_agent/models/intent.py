"""Intent Models

Reference: docs/specs/DATA_MODELS.md#Intent-Models
"""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.dream_agent.models.enums import IntentCategory, IntentDomain


class Entity(BaseModel):
    """추출된 엔티티"""

    model_config = ConfigDict(frozen=True)

    type: str  # brand, product, date_range, platform, category, competitor
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Intent(BaseModel):
    """분류된 의도"""

    model_config = ConfigDict(frozen=True)

    domain: IntentDomain
    category: Optional[IntentCategory] = None
    subcategory: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)

    # Entities
    entities: list[Entity] = Field(default_factory=list)

    # Context
    summary: str = ""
    plan_hint: str = ""  # 어떤 계획이 필요한지 힌트
    raw_input: str = ""
    language: str = "ko"
