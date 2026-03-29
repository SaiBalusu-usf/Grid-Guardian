"""Shared pytest fixtures for GridGuardian backend tests."""

from __future__ import annotations

import asyncio
import os
from typing import Any, Generator

import pytest


# ---------------------------------------------------------------------------
# Event loop fixture for async tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for pytest-asyncio."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Environment fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure all tests run in mock mode with no external dependencies."""
    monkeypatch.setenv("USE_MOCK", "true")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "gridguardian-test")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("FIRESTORE_EMULATOR_HOST", "")
    monkeypatch.setenv("SHELTER_AGENT_URL", "http://localhost:8001")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_incident() -> dict[str, Any]:
    """Return a sample incident dict for testing."""
    return {
        "incident_id": "INC-TEST-001",
        "type": "hurricane",
        "severity": "high",
        "location": {
            "city": "Tampa",
            "state": "TX",
            "coordinates": {"lat": 30.2672, "lng": -97.7431},
        },
        "description": "Category 3 hurricane approaching Tampa metro area",
        "status": "active",
        "affected_population": 15000,
        "created_at": "2026-03-28T10:00:00Z",
        "updated_at": "2026-03-28T10:00:00Z",
        "agents_dispatched": [
            "weather_analyst",
            "infrastructure_monitor",
            "shelter_specialist",
            "logistics_coordinator",
        ],
        "response_plan": None,
        "audit_result": None,
    }


@pytest.fixture
def sample_scenario() -> dict[str, Any]:
    """Return a sample scenario dict for simulation requests."""
    return {
        "scenario_type": "hurricane",
        "severity": "high",
        "location": "Tampa, FL",
        "description": "Category 3 hurricane with 120mph winds, expected landfall in 6 hours",
        "affected_population": 15000,
        "special_requirements": ["pet_friendly", "medical_staff"],
    }


@pytest.fixture
def sample_response_plan() -> dict[str, Any]:
    """Return a sample response plan that agents would produce."""
    return {
        "incident_id": "INC-TEST-001",
        "plan_version": 1,
        "sections": {
            "weather_analysis": {
                "agent": "weather_analyst",
                "status": "completed",
                "summary": "Category 3 hurricane, 120mph winds, heavy rainfall expected",
                "data": {
                    "wind_speed_mph": 120,
                    "rainfall_inches": 8.5,
                    "storm_surge_feet": 6.2,
                    "tornado_risk": "moderate",
                },
            },
            "infrastructure_status": {
                "agent": "infrastructure_monitor",
                "status": "completed",
                "summary": "3 power outages detected, 2 road closures",
                "data": {
                    "power_outages": 3,
                    "road_closures": 2,
                    "bridge_status": "open",
                    "hospital_status": "operational",
                },
            },
            "shelter_analysis": {
                "agent": "shelter_specialist",
                "status": "completed",
                "summary": "4 shelters active, 1527 total capacity available",
                "data": {
                    "total_shelters": 4,
                    "total_capacity": 1527,
                    "critical_shelters": 1,
                    "ada_compliant": 2,
                },
            },
            "logistics": {
                "agent": "logistics_coordinator",
                "status": "completed",
                "summary": "Evacuation routes planned, resources allocated",
                "data": {
                    "evacuation_routes": 3,
                    "buses_dispatched": 12,
                    "supply_trucks": 5,
                    "estimated_evacuation_hours": 4,
                },
            },
        },
        "recommendations": [
            "Evacuate Zone A immediately",
            "Open all shelters to full capacity",
            "Deploy generators to SH-002 (no backup power)",
            "Stage medical teams at Lincoln Community Center",
        ],
    }


@pytest.fixture
def sample_audit_result_fail() -> dict[str, Any]:
    """Return a sample failed audit result."""
    return {
        "passed": False,
        "issues": [
            {
                "severity": "critical",
                "category": "shelter_capacity",
                "description": "Shelter SH-002 is at 96% capacity but no overflow plan provided",
                "recommendation": "Add overflow routing to SH-004 or SH-003",
            },
            {
                "severity": "warning",
                "category": "resource_allocation",
                "description": "No generator deployment planned for shelters without backup power",
                "recommendation": "Deploy portable generators to SH-002",
            },
        ],
        "score": 65,
        "audit_agent": "plan_auditor",
        "timestamp": "2026-03-28T10:05:00Z",
    }


@pytest.fixture
def sample_audit_result_pass() -> dict[str, Any]:
    """Return a sample passing audit result."""
    return {
        "passed": True,
        "issues": [],
        "score": 92,
        "audit_agent": "plan_auditor",
        "timestamp": "2026-03-28T10:10:00Z",
    }
