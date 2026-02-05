"""Agent Execution Routes"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
import uuid

from ..schemas.agent import AgentRequest, AgentResponse, AgentStatus
from .websocket import manager
from backend.app.core.session_store import get_session_store
from backend.app.core.business_store import get_business_store

router = APIRouter()


@router.post("/run", response_model=AgentResponse)
async def run_agent(request: AgentRequest):
    """
    Agent 실행 (동기)

    짧은 작업에 적합. 응답이 올 때까지 대기.
    """
    from backend.app.dream_agent.orchestrator import create_agent, get_checkpointer
    from backend.app.dream_agent.states import create_initial_state

    session_id = request.session_id or str(uuid.uuid4())

    try:
        # Agent 생성
        checkpointer = await get_checkpointer()
        agent = create_agent(checkpointer=checkpointer)

        # 초기 상태 생성
        state = create_initial_state(
            user_input=request.user_input,
            language=request.language,
            session_id=session_id,
        )

        # Agent 실행
        config = {"configurable": {"thread_id": session_id}}
        final_state = None

        async for event in agent.astream(state, config):
            final_state = event

        # 결과 반환
        # astream은 {node_name: node_output} 형태로 yield
        # response 노드의 출력: {"response": str, "saved_report_path": ...}
        response_text = ""
        if final_state:
            response_data = final_state.get("response", "")
            if isinstance(response_data, dict):
                response_text = response_data.get("response", "")
            else:
                response_text = response_data or ""

        return AgentResponse(
            session_id=session_id,
            status="completed",
            response=response_text,
            todos=[],  # TODO: Todo 직렬화
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-async", response_model=AgentResponse)
async def run_agent_async(
    request: AgentRequest,
    background_tasks: BackgroundTasks,
):
    """
    Agent 실행 (비동기)

    긴 작업에 적합. WebSocket으로 진행 상황 전송.
    """
    session_id = request.session_id or str(uuid.uuid4())
    store = get_session_store()

    # 세션 초기화 (JSON 파일로 저장)
    store.save(session_id, {
        "status": "running",
        "request": request.model_dump(),
    })

    # 백그라운드에서 Agent 실행
    background_tasks.add_task(
        _run_agent_background,
        session_id,
        request.user_input,
        request.language,
    )

    return AgentResponse(
        session_id=session_id,
        status="running",
        response=None,
        todos=[],
    )


async def _run_agent_background(
    session_id: str,
    user_input: str,
    language: str,
):
    """백그라운드 Agent 실행"""
    from backend.app.dream_agent.orchestrator import create_agent, get_checkpointer
    from backend.app.dream_agent.states import create_initial_state

    session_store = get_session_store()
    biz_store = get_business_store()

    try:
        checkpointer = await get_checkpointer()
        agent = create_agent(checkpointer=checkpointer)
        state = create_initial_state(
            user_input=user_input,
            language=language,
            session_id=session_id,
        )

        config = {"configurable": {"thread_id": session_id}}
        event = None

        async for event in agent.astream(state, config):
            # event = {node_name: state_update_dict}
            for node_name, node_output in event.items():
                if not isinstance(node_output, dict):
                    continue

                # Planning 노드: plan + todos 저장
                if "todos" in node_output:
                    todos_data = _serialize_todos(node_output["todos"])
                    biz_store.save_todos(session_id, todos_data)

                    if "plan_obj" in node_output:
                        plan_data = _serialize_plan(node_output)
                        biz_store.save_plan(session_id, plan_data)

                    await manager.send_update(session_id, {
                        "type": "todo_update",
                        "data": {"todos": todos_data},
                    })

                # Execution 노드: 실행 결과 저장
                if "execution_result" in node_output:
                    result = node_output["execution_result"]
                    if isinstance(result, dict):
                        biz_store.save_execution_result(session_id, result)

        # 완료
        final_response = _extract_response(event)
        session_store.update_field(session_id, "status", "completed")
        session_store.update_field(session_id, "response", final_response)

        await manager.send_update(session_id, {
            "type": "complete",
            "data": {"response": final_response},
        })

    except Exception as e:
        session_store.update_field(session_id, "status", "failed")
        session_store.update_field(session_id, "error", str(e))

        await manager.send_update(session_id, {
            "type": "error",
            "data": {"error": str(e)},
        })


def _serialize_todo(todo) -> dict:
    """TodoItem (Pydantic/dict/object) → JSON-safe dict"""
    if hasattr(todo, "model_dump"):
        return todo.model_dump(mode="json")
    if isinstance(todo, dict):
        return todo
    return {
        "id": str(getattr(todo, "id", "")),
        "task": str(getattr(todo, "task", "")),
        "status": str(getattr(todo, "status", "pending")),
        "layer": str(getattr(todo, "layer", "unknown")),
    }


def _serialize_todos(todos) -> list:
    """TodoItem 리스트 직렬화"""
    return [_serialize_todo(t) for t in todos]


def _serialize_plan(node_output: dict) -> dict:
    """Planning 노드 출력에서 Plan 메타데이터 추출"""
    plan_data = {}
    plan_obj = node_output.get("plan_obj")
    if plan_obj and hasattr(plan_obj, "model_dump"):
        plan_data = plan_obj.model_dump(mode="json")
    elif isinstance(plan_obj, dict):
        plan_data = plan_obj

    # 추가 필드
    for key in ("plan_id", "cost_estimate", "mermaid_diagram"):
        if key in node_output:
            val = node_output[key]
            plan_data[key] = val.model_dump(mode="json") if hasattr(val, "model_dump") else val

    plan_text = node_output.get("plan")
    if isinstance(plan_text, dict):
        plan_data["plan_description"] = plan_text.get("plan_description", "")

    return plan_data


def _extract_response(event) -> str:
    """마지막 astream 이벤트에서 응답 텍스트 추출"""
    if not event:
        return ""
    # event = {node_name: output_dict}
    for node_output in event.values():
        if isinstance(node_output, dict):
            resp = node_output.get("response", "")
            if isinstance(resp, dict):
                return resp.get("response", "")
            if resp:
                return str(resp)
    return ""


@router.get("/status/{session_id}", response_model=AgentStatus)
async def get_agent_status(session_id: str):
    """Agent 실행 상태 조회"""
    store = get_session_store()
    session = store.load(session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return AgentStatus(
        session_id=session_id,
        status=session["status"],
        response=session.get("response"),
        error=session.get("error"),
    )


@router.post("/stop/{session_id}")
async def stop_agent(session_id: str):
    """Agent 실행 중지 (HITL)"""
    store = get_session_store()

    if not store.exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    # TODO: 실제 Agent 중지 로직 구현
    store.update_field(session_id, "status", "stopped")

    return {"message": "Agent stopped", "session_id": session_id}
