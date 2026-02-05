"""Builder - LangGraph 그래프 조립 (Hand-off Pattern)

각 노드가 Command(goto=...)를 반환하여 다음 노드를 직접 결정합니다.
"""

from langgraph.graph import StateGraph, START

from backend.app.dream_agent.states import AgentState
from backend.app.dream_agent.cognitive import cognitive_node
from backend.app.dream_agent.planning import planning_node
from backend.app.dream_agent.response import response_node
from backend.app.dream_agent.execution import execution_node


def build_agent_graph() -> StateGraph:
    """
    Agent 그래프 빌드 (Hand-off Pattern)

    각 노드가 Command(goto=...)를 반환하여 다음 노드를 직접 결정:
        - cognitive_node  → Command(goto="planning")
        - planning_node   → Command(goto="execution" | "response")
        - execution_node  → Command(goto="execution" | "response")
        - response_node   → Command(goto=END)

    Returns:
        StateGraph 인스턴스
    """
    workflow = StateGraph(AgentState)

    # 노드 추가
    workflow.add_node("cognitive", cognitive_node)
    workflow.add_node("planning", planning_node)
    workflow.add_node("execution", execution_node)
    workflow.add_node("response", response_node)

    # 진입점만 정의 — 나머지는 각 노드의 Command(goto=...)가 결정
    workflow.add_edge(START, "cognitive")

    return workflow


def create_agent(
    checkpointer=None,
    interrupt_before: list[str] | None = None,
):
    """
    Agent 인스턴스 생성

    Args:
        checkpointer: AsyncPostgresSaver (None이면 에러)
        interrupt_before: HITL을 위해 중단할 노드 목록

    Returns:
        컴파일된 그래프

    Raises:
        ValueError: checkpointer가 None인 경우
    """
    if checkpointer is None:
        raise ValueError(
            "checkpointer is required. "
            "Use get_checkpointer() from orchestrator.checkpointer module."
        )

    if interrupt_before is None:
        interrupt_before = []

    workflow = build_agent_graph()

    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt_before
    )
