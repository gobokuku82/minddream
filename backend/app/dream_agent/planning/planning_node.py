"""Planning Layer - 계획 수립 노드"""

import json
from typing import Dict, Any

from backend.app.core.logging import get_logger, LogContext
from backend.app.dream_agent.states.accessors import (
    get_user_input,
    get_intent,
    get_current_context,
    get_session_id,
)
from backend.app.dream_agent.workflow_manager.todo_manager import create_todo
from backend.app.dream_agent.llm_manager import (
    get_llm_client,
    PLANNING_SYSTEM_PROMPT,
    format_planning_prompt
)
from backend.app.dream_agent.workflow_manager import TodoValidator
from backend.app.dream_agent.workflow_manager.planning_manager import (
    plan_manager,
    resource_planner,
    execution_graph_builder
)

logger = get_logger(__name__)


async def planning_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Planning Layer - 계획 수립 및 Todo 생성

    Args:
        state: AgentState

    Returns:
        Dict with 'plan', 'todos', 'target_context'
    """
    log = LogContext(logger, node="planning")
    user_input = get_user_input(state)
    intent = get_intent(state)
    current_context = get_current_context(state)

    log.info(f"Starting planning for intent type: {intent.get('intent_type', 'unknown')}")
    log.info(f"[planning] Intent flags: requires_ml={intent.get('requires_ml')}, requires_biz={intent.get('requires_biz')}")

    # Session ID 가져오기
    session_id = get_session_id(state) or "unknown_session"

    # LLM 호출
    llm_client = get_llm_client()
    prompt = format_planning_prompt(user_input, intent, current_context)

    try:
        log.debug("Calling LLM for plan generation")
        response = await llm_client.chat_with_system(
            system_prompt=PLANNING_SYSTEM_PROMPT,
            user_message=prompt,
            max_tokens=1000,
            response_format={"type": "json_object"}  # JSON 형식 강제
        )

        # JSON 파싱 시도
        plan_data = json.loads(response)
        plan_description_text = {
            "plan_description": plan_data.get("plan_description", ""),
            "total_steps": plan_data.get("total_steps", 0),
            "estimated_complexity": plan_data.get("estimated_complexity", "low"),
            "workflow_type": plan_data.get("workflow_type", "linear"),
        }

        # Todo 생성
        todos = []
        raw_todos = plan_data.get("todos", [])

        # todos가 리스트가 아닌 경우 처리
        if not isinstance(raw_todos, list):
            log.warning(f"LLM returned non-list todos: {type(raw_todos)}. Using fallback.")
            raise ValueError("Invalid todos format from LLM")

        for idx, todo_data in enumerate(raw_todos):
            try:
                # LLM이 반환한 metadata dict를 개별 파라미터로 추출
                metadata_dict = todo_data.get("metadata", {})

                # task 필드 추출 (LLM이 'task' 또는 'description'으로 반환할 수 있음)
                task = todo_data.get("task") or todo_data.get("description") or todo_data.get("name")
                layer = todo_data.get("layer")

                # layer 검증 및 자동 추론/수정
                tool = metadata_dict.get("tool", "").lower()
                source = metadata_dict.get("source", "")
                tool_params = metadata_dict.get("tool_params", {})

                # task 필드 자동 생성 (LLM이 task를 반환하지 않은 경우)
                if not task:
                    if tool == "collector" and source:
                        task = f"{source}에서 데이터 수집"
                    elif tool == "collector" and tool_params.get("keyword"):
                        task = f"{tool_params['keyword']} 데이터 수집"
                    elif tool == "preprocessor":
                        task = "데이터 전처리"
                    elif tool == "analyzer":
                        task = "데이터 분석"
                    elif tool in ["insight", "insight_generator", "insight_with_trends"]:
                        task = "인사이트 도출"
                    elif tool == "report_agent":
                        task = "보고서 생성"
                    elif tool:
                        task = f"{tool} 실행"
                    else:
                        log.warning(f"Todo {idx} missing 'task' field and cannot auto-generate: {todo_data}")
                        continue  # 이 todo는 스킵

                    log.info(f"Auto-generated task '{task}' for todo {idx} (tool={tool})")
                task_lower = task.lower() if task else ""

                # ML 도구 목록 (모든 변형 포함)
                ml_tools = [
                    "collector", "preprocessor", "analyzer", "insight",
                    "keyword_extractor", "absa_analyzer", "insight_generator",
                    "problem_classifier", "google_trends", "trends",
                    "sentiment", "sentiment_analyzer", "extractor",
                    # 새로 추가된 Agent
                    "hashtag_analyzer", "hashtag",
                    "competitor_analyzer", "competitor", "brand_comparison",
                    # K-Beauty 트렌드 RAG 인사이트
                    "insight_with_trends", "kbeauty_insight", "trend_insight", "rag_insight"
                ]

                # BIZ 도구 목록
                biz_tools = [
                    "report_agent", "dashboard_agent", "ad_creative_agent",
                    "storyboard_agent", "video_agent", "sales_agent"
                ]

                # task 내용 키워드
                ml_task_keywords = [
                    "수집", "collect", "전처리", "preprocess", "분석", "analy",
                    "감성", "sentiment", "키워드", "keyword", "인사이트", "insight",
                    "트렌드", "trend", "추출", "extract",
                    # 새로 추가된 키워드
                    "해시태그", "hashtag", "바이럴", "viral",
                    "경쟁사", "competitor", "브랜드 비교", "brand comparison", "SWOT"
                ]

                biz_task_keywords = [
                    "보고서 생성", "report 생성", "대시보드", "dashboard", "광고 생성", "ad creative",
                    "스토리보드", "storyboard", "비디오", "video", "영상", "동영상",
                    "콘텐츠 제작", "content creation", "숏폼", "릴스", "reels", "마케팅 영상"
                ]

                # ================================================================
                # Tool 자동 추론 (tool이 누락된 경우)
                # ================================================================
                inferred_tool = None
                if not tool:
                    # task 내용에서 tool 추론
                    if any(kw in task_lower for kw in ["수집", "collect", "크롤", "crawl"]):
                        inferred_tool = "collector"
                    elif any(kw in task_lower for kw in ["전처리", "preprocess", "정제", "clean"]):
                        inferred_tool = "preprocessor"
                    elif any(kw in task_lower for kw in ["키워드", "keyword", "추출", "extract"]):
                        inferred_tool = "keyword_extractor"
                    elif any(kw in task_lower for kw in ["해시태그", "hashtag", "바이럴"]):
                        inferred_tool = "hashtag_analyzer"
                    elif any(kw in task_lower for kw in ["감성", "sentiment", "긍정", "부정"]):
                        inferred_tool = "sentiment_analyzer"
                    elif any(kw in task_lower for kw in ["문제", "problem", "이슈", "불만"]):
                        inferred_tool = "problem_classifier"
                    elif any(kw in task_lower for kw in ["인사이트", "insight", "분석 결과", "도출"]):
                        # 사용자 요청에 트렌드 관련 키워드가 있으면 K-Beauty RAG 인사이트 사용
                        user_input_lower = user_input.lower() if user_input else ""
                        if any(kw in user_input_lower for kw in ["트렌드", "trend", "k-beauty", "kbeauty", "글로벌", "global", "마케팅", "marketing"]):
                            inferred_tool = "insight_with_trends"
                            log.info(f"Using insight_with_trends due to trend context in user request")
                        else:
                            inferred_tool = "insight"
                    elif any(kw in task_lower for kw in ["트렌드", "trend", "google"]):
                        # 트렌드 분석 (인사이트가 아닌 순수 트렌드 검색)
                        inferred_tool = "google_trends"
                    elif any(kw in task_lower for kw in ["경쟁", "competitor", "swot", "비교"]):
                        inferred_tool = "competitor_analyzer"
                    elif any(kw in task_lower for kw in ["보고서", "report", "리포트"]):
                        inferred_tool = "report_agent"
                    elif any(kw in task_lower for kw in ["대시보드", "dashboard"]):
                        inferred_tool = "dashboard_agent"
                    elif any(kw in task_lower for kw in ["광고", "ad", "크리에이티브"]):
                        inferred_tool = "ad_creative_agent"
                    elif any(kw in task_lower for kw in ["영상", "비디오", "video", "동영상", "숏폼", "릴스", "reels"]):
                        # 비디오 생성 요청: storyboard_agent → video_agent 순서
                        inferred_tool = "video_agent"
                    elif any(kw in task_lower for kw in ["스토리보드", "storyboard", "콘텐츠 기획", "content plan"]):
                        inferred_tool = "storyboard_agent"
                    else:
                        inferred_tool = "preprocessor"  # 기본값

                    tool = inferred_tool
                    log.info(f"Auto-inferred tool '{tool}' for todo: {task}")

                # ================================================================
                # layer 결정 로직 (tool 기반 우선, task 키워드 보조)
                # ================================================================
                inferred_layer = None
                if tool in ml_tools:
                    inferred_layer = "ml_execution"
                elif tool in biz_tools:
                    inferred_layer = "biz_execution"
                elif any(kw in task_lower for kw in ml_task_keywords):
                    inferred_layer = "ml_execution"
                elif any(kw in task_lower for kw in biz_task_keywords):
                    inferred_layer = "biz_execution"
                else:
                    inferred_layer = "ml_execution"  # 기본값은 ML

                # layer가 없으면 추론된 값 사용
                if not layer:
                    layer = inferred_layer
                    log.info(f"Auto-inferred layer '{layer}' for todo: {task} (tool={tool})")
                # layer가 있지만 tool과 불일치하면 수정 (tool 기반이 우선)
                elif layer != inferred_layer and tool:
                    log.warning(f"Layer mismatch for '{task}': LLM said '{layer}', but tool '{tool}' requires '{inferred_layer}'. Correcting.")
                    layer = inferred_layer

                todo = create_todo(
                    task=task,
                    layer=layer,
                    priority=todo_data.get("priority", 5),
                    tool=tool,  # 추론된 tool 사용 (LLM이 지정 안 한 경우 자동 추론됨)
                    tool_params=metadata_dict.get("tool_params", {}),
                    depends_on=metadata_dict.get("depends_on", []),
                    output_path=metadata_dict.get("output_path")
                )
                todos.append(todo)
            except Exception as todo_err:
                log.warning(f"Failed to create todo {idx}: {todo_err}. Skipping.")
                continue

        # LLM이 반환한 todos가 모두 invalid한 경우 fallback
        if not todos and raw_todos:
            log.warning("All LLM todos were invalid. Using fallback.")
            raise ValueError("No valid todos from LLM")

        log.info(f"Planning completed: {len(todos)} todos created ({plan_description_text['total_steps']} steps)")

        # ========== Phase 2 통합: PlanManager 사용 ==========

        # 1. Plan 객체 생성
        log.info("[Phase 2] Creating Plan object with PlanManager")
        plan_obj = plan_manager.create_plan_for_session(
            session_id=session_id,
            todos=todos,
            intent=intent,
            context={
                "user_input": user_input,
                "current_context": current_context,
                "plan_description": plan_description_text
            }
        )
        log.info(f"[Phase 2] Plan created: plan_id={plan_obj.plan_id}, version={plan_obj.current_version}")

        # 2. Todo 검증 (PlanManager 통합)
        log.info("[Phase 2] Validating todos with PlanManager")
        validation_result = plan_manager.validate_plan_todos(
            plan_id=plan_obj.plan_id,
            user_input=user_input
        )

        if not validation_result["valid"]:
            log.error(f"Todo validation failed: {validation_result['errors']}")
            log.warning("Using fallback todos due to validation failure")
            fallback_todos = TodoValidator.get_fallback_todos(intent, user_input)

            # Fallback todos로 Plan 재생성
            plan_obj = plan_manager.create_plan_for_session(
                session_id=session_id,
                todos=fallback_todos,
                intent=intent,
                context={
                    "user_input": user_input,
                    "current_context": current_context,
                    "plan_description": "Fallback plan due to validation failure"
                }
            )
            todos = fallback_todos
            log.info(f"[planning] Fallback created {len(todos)} todos")
        elif validation_result["warnings"]:
            log.warning(f"Todo validation warnings: {validation_result['warnings']}")

        # 3. 순환 의존성 검사
        log.info("[Phase 2] Checking for circular dependencies")
        cycles = plan_manager.check_circular_dependency(plan_obj.plan_id)
        if cycles:
            log.error(f"Circular dependency detected: {cycles}")
            # 순환 의존성 발견 시 의존성 제거
            for todo in plan_obj.todos:
                todo.depends_on = []
            log.warning("Removed all dependencies to break cycles")

        # 4. 위상 정렬
        log.info("[Phase 2] Applying topological sort to todos")
        sorted_todos = plan_manager.topological_sort_todos(
            plan_id=plan_obj.plan_id,
            apply_to_plan=True
        )
        if sorted_todos:
            todos = sorted_todos
            log.info(f"[Phase 2] Todos sorted topologically: {len(todos)} todos")

        # 5. 자원 할당
        log.info("[Phase 2] Allocating resources with ResourcePlanner")
        resource_plan = resource_planner.allocate_resources(
            plan_id=plan_obj.plan_id,
            todos=todos,
            constraints=None  # 기본 제약 조건 사용
        )
        log.info(f"[Phase 2] Resources allocated: {len(resource_plan.allocations)} allocations")

        # 6. 비용 예상
        cost_estimate = resource_planner.estimate_cost(todos)
        log.info(f"[Phase 2] Cost estimate: ${cost_estimate['total_cost']:.2f}, "
                f"Duration: {cost_estimate['estimated_duration_parallel']:.1f}s (parallel)")

        # 7. 실행 그래프 생성
        log.info("[Phase 2] Building execution graph with ExecutionGraphBuilder")
        execution_graph = execution_graph_builder.build(
            plan_id=plan_obj.plan_id,
            todos=todos,
            resource_plan=resource_plan
        )
        log.info(f"[Phase 2] Execution graph built: {len(execution_graph.nodes)} nodes, "
                f"{len(execution_graph.groups)} groups, "
                f"critical_path={execution_graph.critical_path_duration:.1f}s")

        # 8. Plan 상태를 approved로 변경 (검증 완료)
        plan_obj.status = "approved"
        log.info("[Phase 2] Plan approved and ready for execution")

    except json.JSONDecodeError as e:
        # JSON 파싱 실패 시 fallback todos 사용
        log.warning(f"Planning JSON parsing error: {e}. Using fallback todos.")
        plan_description_text = {
            "plan_description": "Fallback plan due to parsing error",
            "total_steps": 0,
            "estimated_complexity": "low",
            "workflow_type": "linear",
        }
        todos = TodoValidator.get_fallback_todos(intent, user_input)
        log.info(f"Generated {len(todos)} fallback todos")

        # Fallback Plan 생성
        plan_obj = plan_manager.create_plan_for_session(
            session_id=session_id,
            todos=todos,
            intent=intent,
            context={
                "user_input": user_input,
                "current_context": current_context,
                "plan_description": plan_description_text,
                "error": "JSON parsing error"
            }
        )
        plan_obj.status = "approved"

        # 간단한 자원 할당 및 실행 그래프 생성
        resource_plan = resource_planner.allocate_resources(
            plan_id=plan_obj.plan_id,
            todos=todos
        )
        execution_graph = execution_graph_builder.build(
            plan_id=plan_obj.plan_id,
            todos=todos,
            resource_plan=resource_plan
        )
        cost_estimate = resource_planner.estimate_cost(todos)

    except Exception as e:
        # 기타 에러
        log.error(f"Planning node error: {e}", exc_info=True)
        plan_description_text = {
            "plan_description": "Error in planning - using fallback",
            "total_steps": 0,
            "estimated_complexity": "low",
            "workflow_type": "linear",
            "error": str(e)
        }
        todos = TodoValidator.get_fallback_todos(intent, user_input)
        log.info(f"Generated {len(todos)} fallback todos due to error")

        # Fallback Plan 생성
        plan_obj = plan_manager.create_plan_for_session(
            session_id=session_id,
            todos=todos,
            intent=intent,
            context={
                "user_input": user_input,
                "current_context": current_context,
                "plan_description": plan_description_text,
                "error": str(e)
            }
        )
        plan_obj.status = "approved"

        # 간단한 자원 할당 및 실행 그래프 생성
        resource_plan = resource_planner.allocate_resources(
            plan_id=plan_obj.plan_id,
            todos=todos
        )
        execution_graph = execution_graph_builder.build(
            plan_id=plan_obj.plan_id,
            todos=todos,
            resource_plan=resource_plan
        )
        cost_estimate = resource_planner.estimate_cost(todos)

    log.info(f"[planning] Returning {len(todos)} todos to state")
    for t in todos:
        log.info(f"[planning] Todo: task={t.task}, layer={t.layer}, status={t.status}")

    # Phase 2 통합: 상세한 정보 반환
    return {
        # 기존 필드 (하위 호환성 유지)
        "plan": plan_description_text,
        "todos": todos,
        "target_context": plan_description_text["plan_description"],

        # Phase 2 신규 필드
        "plan_obj": plan_obj,  # Plan 객체
        "plan_id": plan_obj.plan_id,
        "resource_plan": resource_plan,
        "execution_graph": execution_graph,
        "cost_estimate": cost_estimate,
        "langgraph_commands": execution_graph.langgraph_commands,
        "mermaid_diagram": execution_graph.mermaid_diagram,
    }
