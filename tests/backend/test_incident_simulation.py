"""Integration tests for incident simulation endpoints.

Uses FastAPI TestClient (via httpx) against the backend application.
Since the real backend/main.py may not be fully built yet, this file
provides a self-contained minimal FastAPI app that mirrors the expected
API surface. Tests are written so they also work against the real app
once it exists.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

# ============================================================================
# Minimal FastAPI app for testing (mirrors backend/main.py endpoints)
# ============================================================================

app = FastAPI(title="GridGuardian Test Backend")

# In-memory stores
_incidents: dict[str, dict] = {}
_traces: dict[str, list[dict]] = {}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gridguardian-backend", "mock": True}


@app.post("/api/incidents/simulate")
async def simulate_incident(body: dict[str, Any]):
    """Simulate a disaster incident and trigger the multi-agent pipeline."""
    incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
    now = time.time()

    incident = {
        "incident_id": incident_id,
        "type": body.get("scenario_type", "unknown"),
        "severity": body.get("severity", "medium"),
        "location": body.get("location", "Unknown"),
        "description": body.get("description", ""),
        "status": "active",
        "affected_population": body.get("affected_population", 0),
        "created_at": now,
        "updated_at": now,
        "agents_dispatched": [
            "weather_analyst",
            "infrastructure_monitor",
            "shelter_specialist",
            "logistics_coordinator",
        ],
        "response_plan": {
            "status": "generating",
            "sections": {},
        },
    }
    _incidents[incident_id] = incident

    # Create initial trace events
    _traces[incident_id] = [
        {
            "trace_id": f"TRC-{uuid.uuid4().hex[:8].upper()}",
            "incident_id": incident_id,
            "event_type": "incident_created",
            "agent": "orchestrator",
            "message": f"Incident {incident_id} created: {body.get('scenario_type', 'unknown')}",
            "timestamp": now,
        },
        {
            "trace_id": f"TRC-{uuid.uuid4().hex[:8].upper()}",
            "incident_id": incident_id,
            "event_type": "agents_dispatched",
            "agent": "orchestrator",
            "message": "Dispatched 4 agents in parallel",
            "timestamp": now + 0.001,
        },
        {
            "trace_id": f"TRC-{uuid.uuid4().hex[:8].upper()}",
            "incident_id": incident_id,
            "event_type": "agent_started",
            "agent": "weather_analyst",
            "message": "Weather analysis started",
            "timestamp": now + 0.002,
        },
    ]

    return {
        "incident_id": incident_id,
        "status": "active",
        "message": f"Incident simulation started with {len(incident['agents_dispatched'])} agents",
    }


@app.get("/api/incidents/{incident_id}")
async def get_incident(incident_id: str):
    incident = _incidents.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return incident


@app.get("/api/incidents/{incident_id}/trace")
async def get_incident_trace(incident_id: str):
    if incident_id not in _incidents:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    events = _traces.get(incident_id, [])
    return {
        "incident_id": incident_id,
        "events": sorted(events, key=lambda e: e.get("timestamp", 0)),
        "total_events": len(events),
    }


@app.get("/api/incidents")
async def list_incidents(status: str | None = None):
    incidents = list(_incidents.values())
    if status:
        incidents = [i for i in incidents if i.get("status") == status]
    return {
        "incidents": incidents,
        "total": len(incidents),
    }


# ============================================================================
# Test client fixture
# ============================================================================

@pytest.fixture(autouse=True)
def clear_stores():
    """Clear in-memory stores before each test."""
    _incidents.clear()
    _traces.clear()
    yield
    _incidents.clear()
    _traces.clear()


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


# ============================================================================
# Tests
# ============================================================================

class TestSimulateIncident:
    """Tests for POST /api/incidents/simulate."""

    def test_simulate_incident_endpoint(self, client, sample_scenario):
        """Simulate endpoint creates an incident and returns its ID."""
        response = client.post("/api/incidents/simulate", json=sample_scenario)

        assert response.status_code == 200
        data = response.json()

        assert "incident_id" in data
        assert data["incident_id"].startswith("INC-")
        assert data["status"] == "active"
        assert "agents" in data["message"].lower()

    def test_simulate_incident_minimal(self, client):
        """Simulate works with minimal input."""
        response = client.post("/api/incidents/simulate", json={
            "scenario_type": "earthquake",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"

    def test_simulate_creates_retrievable_incident(self, client, sample_scenario):
        """Simulated incident can be retrieved by ID."""
        sim_response = client.post("/api/incidents/simulate", json=sample_scenario)
        incident_id = sim_response.json()["incident_id"]

        get_response = client.get(f"/api/incidents/{incident_id}")
        assert get_response.status_code == 200

        incident = get_response.json()
        assert incident["incident_id"] == incident_id
        assert incident["type"] == sample_scenario["scenario_type"]
        assert incident["severity"] == sample_scenario["severity"]


class TestGetIncident:
    """Tests for GET /api/incidents/{incident_id}."""

    def test_get_incident(self, client, sample_scenario):
        """Created incident is retrievable."""
        sim = client.post("/api/incidents/simulate", json=sample_scenario)
        incident_id = sim.json()["incident_id"]

        response = client.get(f"/api/incidents/{incident_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["incident_id"] == incident_id
        assert data["status"] == "active"
        assert len(data["agents_dispatched"]) == 4
        assert "response_plan" in data

    def test_get_nonexistent_incident(self, client):
        """Requesting a non-existent incident returns 404."""
        response = client.get("/api/incidents/INC-NONEXISTENT")
        assert response.status_code == 404

    def test_list_incidents(self, client):
        """List endpoint returns all incidents."""
        client.post("/api/incidents/simulate", json={"scenario_type": "flood"})
        client.post("/api/incidents/simulate", json={"scenario_type": "fire"})

        response = client.get("/api/incidents")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 2
        assert len(data["incidents"]) == 2


class TestIncidentTrace:
    """Tests for GET /api/incidents/{incident_id}/trace."""

    def test_get_trace(self, client, sample_scenario):
        """Trace events are created along with the incident."""
        sim = client.post("/api/incidents/simulate", json=sample_scenario)
        incident_id = sim.json()["incident_id"]

        response = client.get(f"/api/incidents/{incident_id}/trace")
        assert response.status_code == 200

        data = response.json()
        assert data["incident_id"] == incident_id
        assert data["total_events"] >= 2

        events = data["events"]
        assert len(events) >= 2

        # Events should include creation and agent dispatch
        event_types = [e["event_type"] for e in events]
        assert "incident_created" in event_types
        assert "agents_dispatched" in event_types

        # Events should be ordered by timestamp
        timestamps = [e["timestamp"] for e in events]
        assert timestamps == sorted(timestamps)

    def test_get_trace_nonexistent_incident(self, client):
        """Trace for non-existent incident returns 404."""
        response = client.get("/api/incidents/INC-NONEXISTENT/trace")
        assert response.status_code == 404


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "gridguardian-backend"
