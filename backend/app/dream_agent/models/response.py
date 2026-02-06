"""Response Models

Reference: docs/specs/DATA_MODELS.md#Response-Models
"""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class Attachment(BaseModel):
    """응답 첨부파일"""

    type: Literal["image", "pdf", "video", "chart", "table", "file"]
    title: str
    url: str  # 파일 URL 또는 base64
    description: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResponsePayload(BaseModel):
    """최종 응답"""

    format: Literal["text", "image", "pdf", "video", "mixed"] = "text"
    text: str  # 메인 텍스트 응답
    summary: str = ""  # 한줄 요약
    attachments: list[Attachment] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)  # 추천 후속 작업
    metadata: dict[str, Any] = Field(default_factory=dict)
