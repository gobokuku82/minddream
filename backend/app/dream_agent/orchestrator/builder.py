"""Graph Builder

LangGraph StateGraph 빌드
Reference: docs/specs/ARCHITECTURE.md#Graph
"""

from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph

from app.core.logging import get_logger
from app.dream_agent.cognitive.cognitive_node import cognitive_node
from app.dream_agent.execution.execution_node import execution_node
from app.dream_agent.orchestrator.checkpointer import get_checkpointer
from app.dream_agent.orchestrator.config import OrchestratorConfig, default_config
from app.dream_agent.orchestrator.router import (
    route_after_cognitive,
    route_after_execution,
    route_after_planning,
)
from app.dream_agent.planning.planning_node import planning_node
from app.dream_agent.response.response_node import response_node
from app.dream_agent.states.agent_state import AgentState

logger = get_logger(__name__)


def build_graph(config: OrchestratorConfig = default_config) -> StateGraph:
    """StateGraph 빌드

    Args:
        config: 오케스트레이터 설정

    Returns:
        빌드된 StateGraph (컴파일 전)
    """
    logger.info("Building StateGraph...")

    # Create graph
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node(config.node_cognitive, cognitive_node)
    graph.add_node(config.node_planning, planning_node)
    graph.add_node(config.node_execution, execution_node)
    graph.add_node(config.node_response, response_node)

    # Entry point
    graph.add_edge(START, config.node_cognitive)

    # Conditional edges
    graph.add_conditional_edges(
        config.node_cognitive,
        route_after_cognitive,
        {
            "planning": config.node_planning,
            "__end__": END,
        },
    )

    graph.add_conditional_edges(
        config.node_planning,
        route_after_planning,
        {
            "execution": config.node_execution,
            "__end__": END,
        },
    )

    graph.add_conditional_edges(
        config.node_execution,
        route_after_execution,
        {
            "execution": config.node_execution,
            "response": config.node_response,
            "__end__": END,
        },
    )

    # Response -> END
    graph.add_edge(config.node_response, END)

    logger.info("StateGraph built successfully")
    return graph


async def create_agent(
    config: OrchestratorConfig = default_config,
) -> CompiledGraph:
    """컴파일된 에이전트 생성

    Args:
        config: 오케스트레이터 설정

    Returns:
        컴파일된 LangGraph 에이전트
    """
    logger.info("Creating agent...")

    # Get checkpointer
    checkpointer = await get_checkpointer()

    # Build and compile graph
    graph = build_graph(config)
    agent = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=config.interrupt_before,
    )

    logger.info(
        "Agent created successfully",
        interrupt_before=config.interrupt_before,
    )

    return agent


# Agent singleton
_agent: CompiledGraph | None = None


async def get_agent() -> CompiledGraph:
    """Agent 싱글톤 반환"""
    global _agent

    if _agent is None:
        _agent = await create_agent()

    return _agent
