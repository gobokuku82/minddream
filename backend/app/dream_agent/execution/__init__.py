"""Dream Agent Execution - 통합 실행 레이어

ml_execution과 biz_execution을 통합한 단일 실행 레이어입니다.

구조:
- execution/core/: 핵심 클래스 (BaseExecutor, ExecutorRegistry, ExecutionCache)
- execution/data_executor.py: 데이터 수집/처리 실행기
- execution/insight_executor.py: 인사이트 생성 실행기
- execution/content_executor.py: 콘텐츠 생성 실행기
- execution/ops_executor.py: 운영(세일즈, 재고, 대시보드) 실행기
- execution/supervisor.py: ExecutionSupervisor
- execution/execution_node.py: LangGraph 노드

사용 예:
    ```python
    from app.dream_agent.execution import (
        get_execution_supervisor,
        DataExecutor,
        InsightExecutor,
        ContentExecutor,
        OpsExecutor,
    )

    # Supervisor를 통한 실행
    supervisor = get_execution_supervisor()
    result = await supervisor.execute_todo(todo, context)

    # 개별 Executor 사용
    data_executor = DataExecutor()
    result = await data_executor.execute(todo, context)
    ```
"""

# Core
from .core import (
    BaseExecutor,
    ExecutorRegistry,
    get_executor_registry,
    ExecutionCache,
    get_execution_cache,
)

from .core.base_executor import (
    ExecutionResult,
    register_executor,
    get_registered_executors,
    create_executor,
)

# Executors
from .data_executor import DataExecutor
from .insight_executor import InsightExecutor
from .content_executor import ContentExecutor
from .ops_executor import OpsExecutor

# Supervisor
from .supervisor import (
    ExecutionSupervisor,
    get_execution_supervisor,
    TOOL_TO_EXECUTOR,
)

# Execution Nodes
from .execution_node import (
    execution_node,
    data_execution_node,
    insight_execution_node,
    content_execution_node,
    ops_execution_node,
)

# New Executor Structure (v0.005)
from . import collection_executor
from . import analysis_executor
from . import insight_agents
from . import content_agents
from . import report_executor
from . import ops_agents
from . import toolkit

__all__ = [
    # Core
    "BaseExecutor",
    "ExecutorRegistry",
    "get_executor_registry",
    "ExecutionCache",
    "get_execution_cache",
    "ExecutionResult",
    "register_executor",
    "get_registered_executors",
    "create_executor",
    # Executors (legacy)
    "DataExecutor",
    "InsightExecutor",
    "ContentExecutor",
    "OpsExecutor",
    # New Agent Modules (v0.005)
    "collection_executor",
    "analysis_executor",
    "insight_agents",
    "content_agents",
    "report_executor",
    "ops_agents",
    "toolkit",
    # Supervisor
    "ExecutionSupervisor",
    "get_execution_supervisor",
    "TOOL_TO_EXECUTOR",
    # Execution Nodes
    "execution_node",
    "data_execution_node",
    "insight_execution_node",
    "content_execution_node",
    "ops_execution_node",
]
