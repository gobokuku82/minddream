"""Plan Editor

자연어 기반 Plan 수정

Reference: docs/specs/HITL_SPEC.md#Plan-Editing
"""

from typing import Any, Optional

from app.core.logging import get_logger
from app.dream_agent.llm_manager import get_llm_client
from app.dream_agent.models import Plan, PlanChange, TodoItem

logger = get_logger(__name__)


class PlanEditor:
    """Plan 편집기

    자연어 명령을 Plan 수정 작업으로 변환
    """

    def __init__(self):
        self.client = get_llm_client("planning")

    async def parse_instruction(
        self,
        instruction: str,
        plan: Plan,
    ) -> dict[str, Any]:
        """자연어 명령 파싱

        Args:
            instruction: 사용자 명령 ("2번 작업 삭제해줘", "구글 트렌드 추가해줘")
            plan: 현재 Plan

        Returns:
            파싱된 명령 {action, target_todo_ids, params}
        """
        logger.info("Parsing plan edit instruction", instruction=instruction)

        # 프롬프트 구성
        system_prompt = """
당신은 Plan 편집 명령을 파싱하는 AI입니다.

사용자의 자연어 명령을 다음 형식으로 변환하세요:

## 지원 액션
- add: Todo 추가
- remove: Todo 삭제
- modify: Todo 수정
- reorder: 순서 변경

## 응답 형식 (JSON)
{
    "action": "add|remove|modify|reorder",
    "target_todo_ids": ["todo_id1", ...],
    "params": {
        "task": "작업 설명 (add/modify)",
        "tool": "도구명 (add/modify)",
        "priority": 1-10 (modify),
        "new_position": 1-N (reorder)
    },
    "reason": "변경 이유"
}
"""

        # 현재 Todo 목록 문자열
        todos_str = "\n".join([
            f"{i+1}. [{t.id[:8]}] {t.task} (tool: {t.tool}, status: {t.status})"
            for i, t in enumerate(plan.todos)
        ])

        user_prompt = f"""
## 현재 Plan의 Todo 목록
{todos_str}

## 사용자 명령
{instruction}

JSON으로 응답하세요.
"""

        try:
            result = await self.client.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
            )
            return result
        except Exception as e:
            logger.error("Failed to parse instruction", error=str(e))
            return {
                "action": "unknown",
                "target_todo_ids": [],
                "params": {},
                "reason": f"파싱 실패: {str(e)}",
            }

    async def apply_edit(
        self,
        plan: Plan,
        parsed: dict[str, Any],
        user_instruction: str,
    ) -> tuple[Plan, PlanChange]:
        """편집 적용

        Args:
            plan: 현재 Plan
            parsed: 파싱된 명령
            user_instruction: 원본 명령

        Returns:
            (수정된 Plan, 변경 기록)
        """
        action = parsed.get("action", "unknown")
        target_ids = parsed.get("target_todo_ids", [])
        params = parsed.get("params", {})

        logger.info(
            "Applying plan edit",
            action=action,
            target_ids=target_ids,
        )

        # 새 Todo 목록 생성
        new_todos = list(plan.todos)

        if action == "remove":
            new_todos = [t for t in new_todos if t.id not in target_ids]

        elif action == "add":
            new_todo = TodoItem(
                task=params.get("task", "새 작업"),
                tool=params.get("tool", "unknown"),
                priority=params.get("priority", 5),
                plan_id=plan.plan_id,
            )
            new_todos.append(new_todo)
            target_ids = [new_todo.id]

        elif action == "modify":
            for i, todo in enumerate(new_todos):
                if todo.id in target_ids:
                    update_dict = {}
                    if "task" in params:
                        update_dict["task"] = params["task"]
                    if "tool" in params:
                        update_dict["tool"] = params["tool"]
                    if "priority" in params:
                        update_dict["priority"] = params["priority"]

                    new_todos[i] = todo.model_copy(update=update_dict)

        # 변경 기록 생성
        change = PlanChange(
            change_type="nl_edit",
            reason=parsed.get("reason", "사용자 요청"),
            actor="user",
            affected_todo_ids=target_ids,
            change_data={"action": action, "params": params},
            user_instruction=user_instruction,
        )

        # Plan 업데이트
        new_plan = plan.model_copy(
            update={
                "todos": new_todos,
                "version": plan.version + 1,
                "changes": plan.changes + [change],
            }
        )

        return new_plan, change

    async def validate_edit(
        self,
        plan: Plan,
        parsed: dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """편집 유효성 검사

        Args:
            plan: 현재 Plan
            parsed: 파싱된 명령

        Returns:
            (valid, errors)
        """
        errors = []
        action = parsed.get("action", "unknown")
        target_ids = parsed.get("target_todo_ids", [])

        if action == "unknown":
            errors.append("알 수 없는 명령입니다.")
            return False, errors

        if action in ("remove", "modify") and not target_ids:
            errors.append("수정할 대상 Todo가 지정되지 않았습니다.")

        # 대상 Todo 존재 확인
        todo_ids = {t.id for t in plan.todos}
        for tid in target_ids:
            if tid not in todo_ids:
                errors.append(f"Todo를 찾을 수 없습니다: {tid}")

        return len(errors) == 0, errors
