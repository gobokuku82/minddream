"""LLM Configuration"""

from dataclasses import dataclass, field
from typing import Literal, Optional


@dataclass
class LLMConfig:
    """LLM 설정"""

    # Provider
    provider: Literal["openai", "anthropic"] = "openai"

    # Model
    model: str = "gpt-4o"

    # Generation params
    temperature: float = 0.3
    max_tokens: int = 4096
    top_p: float = 1.0

    # Timeout
    timeout_sec: int = 60

    # Retry
    max_retries: int = 3
    retry_delay_sec: float = 1.0


@dataclass
class PromptConfig:
    """프롬프트 설정"""

    # System prompt
    system_prompt: str = ""

    # User template
    user_template: str = ""

    # LLM config override
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


# Layer별 기본 설정
LAYER_CONFIGS: dict[str, LLMConfig] = {
    "cognitive": LLMConfig(
        temperature=0.3,
        max_tokens=2048,
    ),
    "planning": LLMConfig(
        temperature=0.5,
        max_tokens=4096,
    ),
    "execution": LLMConfig(
        temperature=0.2,
        max_tokens=2048,
    ),
    "response": LLMConfig(
        temperature=0.7,
        max_tokens=4096,
    ),
}
