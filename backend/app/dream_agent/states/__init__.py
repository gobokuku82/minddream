"""States - 상태 정의 (Pydantic Models Only)

IMPORTANT: Todo helper functions moved to workflow_manager!

Old import (deprecated):
    from backend.app.dream_agent.states import create_todo, update_todo_status

New import:
    from backend.app.dream_agent.workflow_manager.todo_manager import create_todo, update_todo_status
"""

# Todo Models (Pydantic only)
from .todo import (
    TodoItem,
    TodoMetadata,
    TodoExecutionConfig,
    TodoDataConfig,
    TodoDependencyConfig,
    TodoProgress,
    TodoApproval,
)

# Plan Models
from .plan import (
    Plan,
    PlanVersion,
    PlanChange,
    create_plan,
    create_plan_change,
    create_plan_version,
)

# Resource Models
from .resource import (
    AgentResource,
    ResourceAllocation,
    ResourceConstraints,
    ResourcePlan,
    create_agent_resource,
    create_resource_allocation,
    create_resource_constraints,
)

# Execution Graph Models
from .execution_graph import (
    ExecutionNode,
    ExecutionGroup,
    ExecutionGraph,
    create_execution_node,
    create_execution_group,
    create_execution_graph,
)

# Base State
from .base import AgentState, create_initial_state

# Results
from .results import IntentResult, PlanResult, MLResult, BizResult, FinalResponse

# Reducers
from .reducers import todo_reducer, ml_result_reducer, biz_result_reducer

# State Accessors (P0-3.1)
from .accessors import (
    # 기본 Accessors
    get_todos,
    get_user_input,
    get_intent,
    get_current_context,
    get_session_id,
    get_language,
    get_requires_hitl,
    # ML Accessors
    get_current_ml_todo_id,
    get_intermediate_results,
    get_ml_result,
    get_next_ml_tool,
    # Biz Accessors
    get_current_biz_todo_id,
    get_biz_result,
    get_storyboard,
    get_validation_result,
    get_resolution,
    get_fps,
    get_scene_prompts,
    get_comfyui_result,
    get_insights,
    get_report_structure,
    get_output_format,
    get_error,
    # 기타 Accessors
    get_plan,
    get_dialogue_context,
    # 추가 Accessors
    get_next_layer,
    get_plan_obj,
    get_workflow,
    get_use_mock,
    get_response,
    get_target_context,
    # Convenience Functions
    get_completed_todo_count,
    get_pending_todo_count,
    get_todos_by_layer,
    get_todo_by_id,
)

__all__ = [
    # Todo Models
    "TodoItem",
    "TodoMetadata",
    "TodoExecutionConfig",
    "TodoDataConfig",
    "TodoDependencyConfig",
    "TodoProgress",
    "TodoApproval",
    # Plan Models
    "Plan",
    "PlanVersion",
    "PlanChange",
    # Plan Helpers
    "create_plan",
    "create_plan_change",
    "create_plan_version",
    # Resource Models
    "AgentResource",
    "ResourceAllocation",
    "ResourceConstraints",
    "ResourcePlan",
    # Resource Helpers
    "create_agent_resource",
    "create_resource_allocation",
    "create_resource_constraints",
    # Execution Graph Models
    "ExecutionNode",
    "ExecutionGroup",
    "ExecutionGraph",
    # Execution Graph Helpers
    "create_execution_node",
    "create_execution_group",
    "create_execution_graph",
    # Base State
    "AgentState",
    "create_initial_state",
    # Results
    "IntentResult",
    "PlanResult",
    "MLResult",
    "BizResult",
    "FinalResponse",
    # Reducers
    "todo_reducer",
    "ml_result_reducer",
    "biz_result_reducer",
    # State Accessors (P0-3.1)
    "get_todos",
    "get_user_input",
    "get_intent",
    "get_current_context",
    "get_session_id",
    "get_language",
    "get_requires_hitl",
    "get_current_ml_todo_id",
    "get_intermediate_results",
    "get_ml_result",
    "get_next_ml_tool",
    "get_current_biz_todo_id",
    "get_biz_result",
    "get_storyboard",
    "get_validation_result",
    "get_resolution",
    "get_fps",
    "get_scene_prompts",
    "get_comfyui_result",
    "get_insights",
    "get_report_structure",
    "get_output_format",
    "get_error",
    "get_plan",
    "get_dialogue_context",
    "get_next_layer",
    "get_plan_obj",
    "get_workflow",
    "get_use_mock",
    "get_response",
    "get_target_context",
    "get_completed_todo_count",
    "get_pending_todo_count",
    "get_todos_by_layer",
    "get_todo_by_id",
]
