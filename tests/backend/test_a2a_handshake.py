"""Integration tests for the A2A (Agent-to-Agent) protocol handshake.

Tests the shelter specialist agent's A2A endpoints:
- GET  /a2a/agent-card  -- agent card retrieval
- POST /a2a/execute     -- task execution
- GET  /a2a/tasks/{id}  -- task result retrieval
- GET  /health          -- health check

Uses FastAPI TestClient against a self-contained A2A app that mirrors
the shelter agent's real FastAPI surface.
"""

from __future__ import annotations

import sys
import os
from typing import Any

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

# Add the shelter agent directory to path so we can import its modules
SHELTER_AGENT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "backend", "a2a_shelter_agent"
)
sys.path.insert(0, os.path.abspath(SHELTER_AGENT_DIR))

from agent_card import get_agent_card, validate_query
from agent import analyze_shelters
from agent_executor import ShelterAgentExecutor

# ============================================================================
# Build the A2A FastAPI app (mirrors the shelter agent's main.py)
# ============================================================================

a2a_app = FastAPI(title="Shelter Specialist A2A Agent")
executor = ShelterAgentExecutor()


@a2a_app.get("/health")
async def health():
    return {"status": "ok", "agent": "shelter_specialist", "protocol": "a2a"}


@a2a_app.get("/a2a/agent-card")
async def agent_card():
    return get_agent_card()


@a2a_app.post("/a2a/execute")
async def execute_task(task: dict[str, Any]):
    result = await executor.execute(task)
    return result


@a2a_app.get("/a2a/tasks/{task_id}")
async def get_task(task_id: str):
    result = executor.get_task(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return result


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def client():
    """Test client for the A2A shelter agent app."""
    return TestClient(a2a_app)


# ============================================================================
# Tests
# ============================================================================

class TestAgentCard:
    """Tests for GET /a2a/agent-card."""

    def test_agent_card_retrieval(self, client):
        """Agent card endpoint returns a valid A2A agent card."""
        response = client.get("/a2a/agent-card")
        assert response.status_code == 200

        card = response.json()

        # Required A2A agent card fields
        assert "name" in card
        assert card["name"] == "Shelter Specialist"
        assert "description" in card
        assert "version" in card
        assert "protocol" in card
        assert card["protocol"] == "a2a"

        # Capabilities
        assert "capabilities" in card
        assert isinstance(card["capabilities"], list)
        assert len(card["capabilities"]) > 0
        assert "shelter_capacity_analysis" in card["capabilities"]

        # Endpoints
        assert "endpoint" in card
        assert card["endpoint"] == "/a2a/execute"

        # Schemas
        assert "input_schema" in card
        assert "output_schema" in card
        assert card["input_schema"]["type"] == "object"
        assert card["output_schema"]["type"] == "object"

    def test_agent_card_immutability(self, client):
        """Multiple calls return identical cards (deep copy check)."""
        card1 = client.get("/a2a/agent-card").json()
        card2 = client.get("/a2a/agent-card").json()
        assert card1 == card2


class TestExecuteTask:
    """Tests for POST /a2a/execute."""

    def test_execute_task_basic(self, client):
        """Execute a basic shelter query and get structured results."""
        task = {
            "task_id": "test-task-001",
            "message": {
                "role": "user",
                "content": {
                    "scenario": "hurricane",
                },
            },
        }
        response = client.post("/a2a/execute", json=task)
        assert response.status_code == 200

        result = response.json()

        assert result["task_id"] == "test-task-001"
        assert result["status"] == "completed"
        assert result["agent"] == "shelter_specialist"
        assert "result" in result
        assert "metadata" in result

        # Check result structure
        analysis = result["result"]
        assert "shelters" in analysis
        assert "total_available_capacity" in analysis
        assert "critical_shelters" in analysis
        assert "supply_warnings" in analysis
        assert "recommendations" in analysis
        assert "accessibility_summary" in analysis

        # Shelters should be present
        assert len(analysis["shelters"]) == 4  # all 4 mock shelters
        assert analysis["total_available_capacity"] > 0

        # Metadata should include execution time
        assert result["metadata"]["execution_time_ms"] >= 0
        assert result["metadata"]["shelters_evaluated"] == 4

    def test_execute_task_with_accessibility_filter(self, client):
        """Execute with accessibility filter returns only matching shelters."""
        task = {
            "task_id": "test-task-002",
            "message": {
                "role": "user",
                "content": {
                    "accessibility_required": "full_ada",
                    "scenario": "flood",
                },
            },
        }
        response = client.post("/a2a/execute", json=task)
        assert response.status_code == 200

        result = response.json()
        analysis = result["result"]

        # Only full_ada shelters (SH-001 and SH-004) should be returned
        assert len(analysis["shelters"]) == 2
        for shelter in analysis["shelters"]:
            assert shelter["accessibility"] == "full_ada"

    def test_execute_task_with_capacity_needed(self, client):
        """Execute with capacity_needed includes capacity assessment."""
        task = {
            "task_id": "test-task-003",
            "message": {
                "role": "user",
                "content": {
                    "capacity_needed": 500,
                    "scenario": "earthquake",
                },
            },
        }
        response = client.post("/a2a/execute", json=task)
        assert response.status_code == 200

        result = response.json()
        analysis = result["result"]

        assert analysis["total_available_capacity"] > 0
        assert len(analysis["recommendations"]) > 0

    def test_execute_task_auto_id(self, client):
        """Task without explicit ID gets auto-generated ID."""
        task = {
            "message": {
                "role": "user",
                "content": {"scenario": "wildfire"},
            },
        }
        response = client.post("/a2a/execute", json=task)
        assert response.status_code == 200

        result = response.json()
        assert result["task_id"] is not None
        assert len(result["task_id"]) > 0

    def test_execute_task_string_content(self, client):
        """String content is treated as a scenario description."""
        task = {
            "task_id": "test-string",
            "message": {
                "role": "user",
                "content": "Major hurricane approaching, need shelter assessment",
            },
        }
        response = client.post("/a2a/execute", json=task)
        assert response.status_code == 200

        result = response.json()
        assert result["status"] == "completed"
        # Hurricane keyword should trigger scenario-specific recommendations
        recs = result["result"]["recommendations"]
        assert any("flood" in r.lower() or "hurricane" in r.lower() or "higher ground" in r.lower() for r in recs)

    def test_execute_task_validation_error(self, client):
        """Invalid query fields return a validation error status."""
        task = {
            "task_id": "test-invalid",
            "message": {
                "role": "user",
                "content": {
                    "invalid_field": "not allowed",
                },
            },
        }
        response = client.post("/a2a/execute", json=task)
        assert response.status_code == 200  # A2A returns errors in the task result

        result = response.json()
        assert result["status"] == "validation_error"
        assert "error" in result

    def test_execute_task_missing_message(self, client):
        """Task without message field returns an error."""
        task = {"task_id": "test-no-msg"}
        response = client.post("/a2a/execute", json=task)
        assert response.status_code == 200

        result = response.json()
        assert result["status"] == "error"
        assert "message" in result["error"].lower()


class TestTaskRetrieval:
    """Tests for GET /a2a/tasks/{id}."""

    def test_task_retrieval(self, client):
        """Execute a task then retrieve it by ID."""
        task = {
            "task_id": "test-retrieve-001",
            "message": {
                "role": "user",
                "content": {"scenario": "winter_storm"},
            },
        }
        # Execute
        exec_response = client.post("/a2a/execute", json=task)
        assert exec_response.status_code == 200

        # Retrieve
        get_response = client.get("/a2a/tasks/test-retrieve-001")
        assert get_response.status_code == 200

        stored = get_response.json()
        assert stored["task_id"] == "test-retrieve-001"
        assert stored["status"] == "completed"
        assert stored["agent"] == "shelter_specialist"
        assert "result" in stored

    def test_task_retrieval_not_found(self, client):
        """Requesting a non-existent task returns 404."""
        response = client.get("/a2a/tasks/nonexistent-id")
        assert response.status_code == 404


class TestHealth:
    """Tests for GET /health."""

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert data["agent"] == "shelter_specialist"
        assert data["protocol"] == "a2a"
