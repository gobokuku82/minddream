"""테스트 설정 및 공통 fixture"""

import sys
from pathlib import Path

import pytest

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_todo_data():
    """샘플 Todo 데이터"""
    return {
        "task": "리뷰 데이터 수집",
        "task_type": "collect",
        "layer": "ml_execution",
        "status": "pending",
        "priority": 5,
    }


@pytest.fixture
def sample_intent_data():
    """샘플 Intent 데이터"""
    return {
        "domain": "analysis",
        "category": "sentiment",
        "confidence": 0.85,
        "requires_ml": True,
        "requires_biz": False,
        "raw_input": "라네즈 리뷰 분석해줘",
        "language": "ko",
    }


@pytest.fixture
def sample_plan_data(sample_todo_data):
    """샘플 Plan 데이터"""
    return {
        "session_id": "test-session-001",
        "status": "draft",
    }


@pytest.fixture
def sample_tool_spec_data():
    """샘플 ToolSpec 데이터"""
    return {
        "name": "sentiment_analyzer",
        "description": "텍스트 감성 분석",
        "tool_type": "analysis",
        "version": "1.0.0",
        "executor": "ml_agent.sentiment_analyzer",
        "timeout_sec": 180,
        "parameters": [
            {
                "name": "texts",
                "type": "array",
                "required": True,
                "description": "분석할 텍스트 리스트"
            }
        ],
        "tags": ["analysis", "nlp", "sentiment"]
    }
