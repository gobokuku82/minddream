"""Response Layer I/O Schema

Response Layer의 입출력 스키마를 정의합니다.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from ..models.results import MLResult, BizResult


class ResponseInput(BaseModel):
    """Response Layer 입력"""
    user_input: str
    language: str = "ko"
    intent_summary: str = ""
    ml_result: Optional[MLResult] = None
    biz_result: Optional[BizResult] = None
    execution_results: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class ResponseOutput(BaseModel):
    """Response Layer 출력"""
    response_text: str
    summary: str = ""
    attachments: List[str] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
