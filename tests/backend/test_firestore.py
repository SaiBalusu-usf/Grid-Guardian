"""Tests for the Firestore service layer.

All tests use an in-memory fallback -- no real Firestore instance needed.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import pytest


# ============================================================================
# In-memory Firestore service (mirrors backend/services/firestore_service.py)
# ============================================================================

class InMemoryFirestoreService:
    """In-memory Firestore stand-in for testing without any external deps."""

    def __init__(self):
        self._collections: dict[str, dict[str, dict]] = {}

    def _col(self, name: str) -> dict[str, dict]:
        if name not in self._collections:
            self._collections[name] = {}
        return self._collections[name]

    # -- Incidents ----------------------------------------------------------

    async def create_incident(self, incident: dict[str, Any]) -> dict[str, Any]:
        incident_id = incident.get("incident_id") or f"INC-{uuid.uuid4().hex[:8].upper()}"
        doc = {
            **incident,
            "incident_id": incident_id,
            "created_at": incident.get("created_at") or _now(),
            "updated_at": _now(),
        }
        self._col("incidents")[incident_id] = doc
        return doc

    async def get_incident(self, incident_id: str) -> dict[str, Any] | None:
        return self._col("incidents").get(incident_id)

    async def update_incident(self, incident_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        doc = self._col("incidents").get(incident_id)
        if doc is None:
            return None
        doc.update(updates)
        doc["updated_at"] = _now()
        return doc

    async def list_incidents(self, status: str | None = None) -> list[dict[str, Any]]:
        docs = list(self._col("incidents").values())
        if status:
            docs = [d for d in docs if d.get("status") == status]
        return sorted(docs, key=lambda d: d.get("created_at", ""), reverse=True)

    # -- Agent Runs ---------------------------------------------------------

    async def log_agent_run(self, run: dict[str, Any]) -> dict[str, Any]:
        run_id = run.get("run_id") or f"RUN-{uuid.uuid4().hex[:8].upper()}"
        doc = {
            **run,
            "run_id": run_id,
            "timestamp": run.get("timestamp") or _now(),
        }
        self._col("agent_runs")[run_id] = doc
        return doc

    async def get_agent_run(self, run_id: str) -> dict[str, Any] | None:
        return self._col("agent_runs").get(run_id)

    # -- Traces -------------------------------------------------------------

    async def add_trace(self, trace: dict[str, Any]) -> dict[str, Any]:
        trace_id = trace.get("trace_id") or f"TRC-{uuid.uuid4().hex[:8].upper()}"
        doc = {
            **trace,
            "trace_id": trace_id,
            "timestamp": trace.get("timestamp") or _now(),
        }
        self._col("traces")[trace_id] = doc
        return doc

    async def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        return self._col("traces").get(trace_id)

    async def list_traces(self, incident_id: str) -> list[dict[str, Any]]:
        return [
            t for t in self._col("traces").values()
            if t.get("incident_id") == incident_id
        ]

    # -- Tasks --------------------------------------------------------------

    async def create_task(self, task: dict[str, Any]) -> dict[str, Any]:
        task_id = task.get("task_id") or f"TSK-{uuid.uuid4().hex[:8].upper()}"
        doc = {
            **task,
            "task_id": task_id,
            "status": task.get("status", "pending"),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self._col("tasks")[task_id] = doc
        return doc

    async def get_task(self, task_id: str) -> dict[str, Any] | None:
        return self._col("tasks").get(task_id)

    async def update_task(self, task_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        doc = self._col("tasks").get(task_id)
        if doc is None:
            return None
        doc.update(updates)
        doc["updated_at"] = _now()
        return doc

    # -- Alerts -------------------------------------------------------------

    async def create_alert(self, alert: dict[str, Any]) -> dict[str, Any]:
        alert_id = alert.get("alert_id") or f"ALR-{uuid.uuid4().hex[:8].upper()}"
        doc = {
            **alert,
            "alert_id": alert_id,
            "acknowledged": False,
            "acknowledged_at": None,
            "acknowledged_by": None,
            "created_at": _now(),
        }
        self._col("alerts")[alert_id] = doc
        return doc

    async def get_alert(self, alert_id: str) -> dict[str, Any] | None:
        return self._col("alerts").get(alert_id)

    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> dict[str, Any] | None:
        doc = self._col("alerts").get(alert_id)
        if doc is None:
            return None
        doc["acknowledged"] = True
        doc["acknowledged_at"] = _now()
        doc["acknowledged_by"] = acknowledged_by
        return doc

    async def list_alerts(self, acknowledged: bool | None = None) -> list[dict[str, Any]]:
        docs = list(self._col("alerts").values())
        if acknowledged is not None:
            docs = [d for d in docs if d.get("acknowledged") == acknowledged]
        return sorted(docs, key=lambda d: d.get("created_at", ""), reverse=True)

    # -- Dashboard ----------------------------------------------------------

    async def get_dashboard_data(self) -> dict[str, Any]:
        incidents = list(self._col("incidents").values())
        alerts = list(self._col("alerts").values())
        tasks = list(self._col("tasks").values())
        agent_runs = list(self._col("agent_runs").values())

        active_incidents = [i for i in incidents if i.get("status") == "active"]
        unacked_alerts = [a for a in alerts if not a.get("acknowledged")]
        pending_tasks = [t for t in tasks if t.get("status") == "pending"]

        return {
            "total_incidents": len(incidents),
            "active_incidents": len(active_incidents),
            "total_alerts": len(alerts),
            "unacknowledged_alerts": len(unacked_alerts),
            "total_tasks": len(tasks),
            "pending_tasks": len(pending_tasks),
            "total_agent_runs": len(agent_runs),
            "recent_incidents": active_incidents[:5],
            "recent_alerts": unacked_alerts[:5],
        }


def _now() -> str:
    """ISO timestamp string."""
    from datetime import datetime, timezone
    return datetime.now(tz=timezone.utc).isoformat() + "Z"


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def db():
    """Fresh in-memory Firestore service for each test."""
    return InMemoryFirestoreService()


# ============================================================================
# Tests
# ============================================================================

class TestIncidents:
    """Tests for incident CRUD."""

    @pytest.mark.asyncio
    async def test_create_incident(self, db, sample_incident):
        result = await db.create_incident(sample_incident)

        assert result["incident_id"] == "INC-TEST-001"
        assert result["type"] == "hurricane"
        assert result["severity"] == "high"
        assert result["status"] == "active"
        assert "created_at" in result
        assert "updated_at" in result

    @pytest.mark.asyncio
    async def test_update_incident(self, db, sample_incident):
        await db.create_incident(sample_incident)

        updated = await db.update_incident("INC-TEST-001", {
            "status": "resolved",
            "resolution": "Hurricane downgraded, all-clear issued",
        })

        assert updated is not None
        assert updated["status"] == "resolved"
        assert updated["resolution"] == "Hurricane downgraded, all-clear issued"
        assert updated["type"] == "hurricane"  # original fields preserved

    @pytest.mark.asyncio
    async def test_update_nonexistent_incident(self, db):
        result = await db.update_incident("NONEXISTENT", {"status": "resolved"})
        assert result is None

    @pytest.mark.asyncio
    async def test_get_incident(self, db, sample_incident):
        await db.create_incident(sample_incident)
        result = await db.get_incident("INC-TEST-001")

        assert result is not None
        assert result["incident_id"] == "INC-TEST-001"

    @pytest.mark.asyncio
    async def test_list_incidents_by_status(self, db):
        await db.create_incident({"incident_id": "INC-1", "status": "active", "type": "flood"})
        await db.create_incident({"incident_id": "INC-2", "status": "resolved", "type": "fire"})
        await db.create_incident({"incident_id": "INC-3", "status": "active", "type": "storm"})

        active = await db.list_incidents(status="active")
        assert len(active) == 2
        assert all(i["status"] == "active" for i in active)


class TestAgentRuns:
    """Tests for agent run logging."""

    @pytest.mark.asyncio
    async def test_log_agent_run(self, db):
        run = {
            "run_id": "RUN-001",
            "incident_id": "INC-TEST-001",
            "agent": "weather_analyst",
            "status": "completed",
            "duration_ms": 245.5,
            "input_summary": "Analyze weather for Tampa, FL hurricane scenario",
            "output_summary": "Category 3 hurricane, 120mph winds",
        }
        result = await db.log_agent_run(run)

        assert result["run_id"] == "RUN-001"
        assert result["agent"] == "weather_analyst"
        assert result["status"] == "completed"
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_get_agent_run(self, db):
        await db.log_agent_run({"run_id": "RUN-002", "agent": "shelter_specialist"})
        result = await db.get_agent_run("RUN-002")

        assert result is not None
        assert result["agent"] == "shelter_specialist"


class TestTraces:
    """Tests for trace events."""

    @pytest.mark.asyncio
    async def test_add_trace(self, db):
        trace = {
            "trace_id": "TRC-001",
            "incident_id": "INC-TEST-001",
            "event_type": "agent_start",
            "agent": "weather_analyst",
            "message": "Starting weather analysis for hurricane scenario",
            "data": {"scenario": "hurricane", "location": "Tampa, FL"},
        }
        result = await db.add_trace(trace)

        assert result["trace_id"] == "TRC-001"
        assert result["incident_id"] == "INC-TEST-001"
        assert result["event_type"] == "agent_start"
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_list_traces_for_incident(self, db):
        await db.add_trace({"trace_id": "TRC-A", "incident_id": "INC-1", "event_type": "start"})
        await db.add_trace({"trace_id": "TRC-B", "incident_id": "INC-1", "event_type": "tool_call"})
        await db.add_trace({"trace_id": "TRC-C", "incident_id": "INC-2", "event_type": "start"})

        traces = await db.list_traces("INC-1")
        assert len(traces) == 2
        assert all(t["incident_id"] == "INC-1" for t in traces)


class TestTasks:
    """Tests for task management."""

    @pytest.mark.asyncio
    async def test_create_task(self, db):
        task = {
            "task_id": "TSK-001",
            "incident_id": "INC-TEST-001",
            "title": "Deploy generators to SH-002",
            "assigned_to": "logistics_coordinator",
            "priority": "high",
        }
        result = await db.create_task(task)

        assert result["task_id"] == "TSK-001"
        assert result["status"] == "pending"
        assert result["priority"] == "high"
        assert "created_at" in result

    @pytest.mark.asyncio
    async def test_update_task(self, db):
        await db.create_task({"task_id": "TSK-002", "title": "Evacuate Zone A"})

        updated = await db.update_task("TSK-002", {"status": "in_progress"})
        assert updated is not None
        assert updated["status"] == "in_progress"


class TestAlerts:
    """Tests for alert creation and acknowledgement."""

    @pytest.mark.asyncio
    async def test_create_alert(self, db):
        alert = {
            "alert_id": "ALR-001",
            "incident_id": "INC-TEST-001",
            "severity": "critical",
            "title": "Shelter SH-002 at capacity",
            "message": "Eastside High School Gymnasium has reached 96% occupancy",
        }
        result = await db.create_alert(alert)

        assert result["alert_id"] == "ALR-001"
        assert result["severity"] == "critical"
        assert result["acknowledged"] is False
        assert result["acknowledged_at"] is None

    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, db):
        await db.create_alert({"alert_id": "ALR-002", "title": "Power outage detected"})

        result = await db.acknowledge_alert("ALR-002", acknowledged_by="operator_jane")

        assert result is not None
        assert result["acknowledged"] is True
        assert result["acknowledged_by"] == "operator_jane"
        assert result["acknowledged_at"] is not None

    @pytest.mark.asyncio
    async def test_acknowledge_nonexistent_alert(self, db):
        result = await db.acknowledge_alert("NONEXISTENT", acknowledged_by="operator")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_unacknowledged_alerts(self, db):
        await db.create_alert({"alert_id": "ALR-A", "title": "Alert A"})
        await db.create_alert({"alert_id": "ALR-B", "title": "Alert B"})
        await db.acknowledge_alert("ALR-A", acknowledged_by="operator")

        unacked = await db.list_alerts(acknowledged=False)
        assert len(unacked) == 1
        assert unacked[0]["alert_id"] == "ALR-B"


class TestDashboard:
    """Tests for aggregated dashboard data."""

    @pytest.mark.asyncio
    async def test_get_dashboard_data(self, db):
        # Seed data
        await db.create_incident({"incident_id": "INC-1", "status": "active", "type": "flood"})
        await db.create_incident({"incident_id": "INC-2", "status": "resolved", "type": "fire"})
        await db.create_alert({"alert_id": "ALR-1", "title": "Flood warning"})
        await db.create_alert({"alert_id": "ALR-2", "title": "Power outage"})
        await db.acknowledge_alert("ALR-1", acknowledged_by="operator")
        await db.create_task({"task_id": "TSK-1", "title": "Deploy resources"})
        await db.log_agent_run({"run_id": "RUN-1", "agent": "weather_analyst"})

        dashboard = await db.get_dashboard_data()

        assert dashboard["total_incidents"] == 2
        assert dashboard["active_incidents"] == 1
        assert dashboard["total_alerts"] == 2
        assert dashboard["unacknowledged_alerts"] == 1
        assert dashboard["total_tasks"] == 1
        assert dashboard["pending_tasks"] == 1
        assert dashboard["total_agent_runs"] == 1
        assert len(dashboard["recent_incidents"]) == 1
        assert len(dashboard["recent_alerts"]) == 1

    @pytest.mark.asyncio
    async def test_get_dashboard_data_empty(self, db):
        """Dashboard should return zeros when no data exists."""
        dashboard = await db.get_dashboard_data()

        assert dashboard["total_incidents"] == 0
        assert dashboard["active_incidents"] == 0
        assert dashboard["total_alerts"] == 0
        assert dashboard["unacknowledged_alerts"] == 0
        assert dashboard["total_tasks"] == 0
        assert dashboard["pending_tasks"] == 0
        assert dashboard["total_agent_runs"] == 0
        assert dashboard["recent_incidents"] == []
        assert dashboard["recent_alerts"] == []
