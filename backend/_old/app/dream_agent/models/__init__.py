"""Models - Pydantic 모델 패키지

이 패키지는 states/에서 분리된 순수 Pydantic 모델을 포함합니다.
LangGraph 상태 관련 코드(TypedDict, Reducers, Accessors)는 states/에 유지됩니다.

구조:
- todo.py: TodoItem 및 관련 메타데이터 모델
- plan.py: Plan, PlanVersion, PlanChange 모델
- resource.py: AgentResource, ResourceAllocation 등 자원 모델
- execution_graph.py: ExecutionNode, ExecutionGraph DAG 모델
- results.py: IntentResult, MLResult, BizResult 등 결과 모델

사용 예:
    from backend.app.dream_agent.models import TodoItem, Plan
    # 또는
    from backend.app.dream_agent.models.todo import TodoItem
"""

# Todo Models
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

# Result Models
from .results import (
    IntentResult,
    PlanResult,
    MLResult,
    BizResult,
    FinalResponse,
)

# Intent Models (SSOT — 3-depth 계층적 Intent 체계)
from .intent import (
    IntentDomain,
    IntentCategory,
    IntentSubcategory,
    HierarchicalIntent,
    Intent,  # backward-compatible alias for HierarchicalIntent
    Entity,
    DOMAIN_TO_CATEGORIES,
    CATEGORY_TO_SUBCATEGORIES,
    get_categories_for_domain,
    get_subcategories_for_category,
    validate_intent_hierarchy,
)

# Execution Models (Phase 0.5 신규)
from .execution import (
    ExecutionResult,
    ExecutionContext,
    ExecutionStatus,
)

# Tool Models (Phase 0 신규)
from .tool import (
    ToolSpec,
    ToolType,
    ToolParameter,
    ToolParameterType,
    ToolRegistry,
)

__all__ = [
    # Todo
    "TodoItem",
    "TodoMetadata",
    "TodoExecutionConfig",
    "TodoDataConfig",
    "TodoDependencyConfig",
    "TodoProgress",
    "TodoApproval",
    # Plan
    "Plan",
    "PlanVersion",
    "PlanChange",
    "create_plan",
    "create_plan_change",
    "create_plan_version",
    # Resource
    "AgentResource",
    "ResourceAllocation",
    "ResourceConstraints",
    "ResourcePlan",
    "create_agent_resource",
    "create_resource_allocation",
    "create_resource_constraints",
    # Execution Graph
    "ExecutionNode",
    "ExecutionGroup",
    "ExecutionGraph",
    "create_execution_node",
    "create_execution_group",
    "create_execution_graph",
    # Results
    "IntentResult",
    "PlanResult",
    "MLResult",
    "BizResult",
    "FinalResponse",
    # Intent (SSOT — 3-depth 계층적 Intent 체계)
    "IntentDomain",
    "IntentCategory",
    "IntentSubcategory",
    "HierarchicalIntent",
    "Intent",
    "Entity",
    "DOMAIN_TO_CATEGORIES",
    "CATEGORY_TO_SUBCATEGORIES",
    "get_categories_for_domain",
    "get_subcategories_for_category",
    "validate_intent_hierarchy",
    # Execution (Phase 0.5 신규)
    "ExecutionResult",
    "ExecutionContext",
    "ExecutionStatus",
    # Tool (Phase 0 신규)
    "ToolSpec",
    "ToolType",
    "ToolParameter",
    "ToolParameterType",
    "ToolRegistry",
]
