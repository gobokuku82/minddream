"""Orchestrator Configuration

Graph 설정 및 interrupt points 정의
"""

from dataclasses import dataclass, field


@dataclass
class OrchestratorConfig:
    """오케스트레이터 설정"""

    # Interrupt points (HITL)
    interrupt_before: list[str] = field(
        default_factory=lambda: ["planning"]  # Plan 생성 후 승인 대기
    )

    # Recursion limit (무한 루프 방지)
    recursion_limit: int = 50

    # Debug mode
    debug: bool = False

    # Node names
    node_cognitive: str = "cognitive"
    node_planning: str = "planning"
    node_execution: str = "execution"
    node_response: str = "response"


# Default config singleton
default_config = OrchestratorConfig()
