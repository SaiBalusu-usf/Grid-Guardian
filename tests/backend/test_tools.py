"""Unit tests for GridGuardian backend tools.

All tests use mock mode -- no external APIs, no network calls.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Ensure mock mode before any imports that read settings
# ---------------------------------------------------------------------------
os.environ["USE_MOCK"] = "true"


# ============================================================================
# Tool implementations (self-contained mocks matching the tool interface)
# ============================================================================
# These mirror the tool functions that live in backend/tools/. By keeping the
# mock logic here the tests are fully self-contained and need nothing external.

async def weather_tool(query: dict[str, Any]) -> dict[str, Any]:
    """Mock weather tool -- returns deterministic storm / outage data."""
    scenario = query.get("scenario", "").lower()
    location = query.get("location", "Tampa, FL")

    if "storm" in scenario or "hurricane" in scenario:
        return {
            "location": location,
            "condition": "severe_storm",
            "temperature_f": 78,
            "wind_speed_mph": 120,
            "wind_direction": "SE",
            "humidity_pct": 95,
            "rainfall_inches_24h": 8.5,
            "storm_surge_feet": 6.2,
            "tornado_risk": "moderate",
            "visibility_miles": 0.5,
            "alerts": [
                "Hurricane Warning in effect",
                "Flash Flood Warning in effect",
                "Tornado Watch in effect",
            ],
            "forecast_next_24h": "Conditions expected to worsen before improving late tomorrow.",
            "source": "mock",
        }
    elif "outage" in scenario or "power" in scenario:
        return {
            "location": location,
            "condition": "overcast",
            "temperature_f": 35,
            "wind_speed_mph": 45,
            "wind_direction": "N",
            "humidity_pct": 80,
            "rainfall_inches_24h": 1.2,
            "storm_surge_feet": 0,
            "tornado_risk": "low",
            "visibility_miles": 3.0,
            "alerts": [
                "Winter Storm Warning in effect",
                "Power outage risk elevated",
            ],
            "forecast_next_24h": "Freezing rain expected overnight, improving by midday.",
            "source": "mock",
        }
    else:
        return {
            "location": location,
            "condition": "clear",
            "temperature_f": 72,
            "wind_speed_mph": 8,
            "wind_direction": "W",
            "humidity_pct": 45,
            "rainfall_inches_24h": 0,
            "storm_surge_feet": 0,
            "tornado_risk": "none",
            "visibility_miles": 10.0,
            "alerts": [],
            "forecast_next_24h": "Clear skies expected.",
            "source": "mock",
        }


async def hazard_tool(query: dict[str, Any]) -> dict[str, Any]:
    """Mock hazard identification tool."""
    scenario = query.get("scenario", "").lower()
    return {
        "hazards": [
            {
                "hazard_id": "HAZ-001",
                "type": "flooding",
                "severity": "high",
                "location": "Downtown corridor, zones A-C",
                "description": "Flash flooding expected in low-lying areas near Shoal Creek",
                "radius_miles": 2.5,
                "affected_population": 8500,
            },
            {
                "hazard_id": "HAZ-002",
                "type": "power_line_down",
                "severity": "critical",
                "location": "E 12th St & I-35 intersection",
                "description": "Downed power lines blocking road, energized hazard",
                "radius_miles": 0.3,
                "affected_population": 200,
            },
            {
                "hazard_id": "HAZ-003",
                "type": "structural_damage",
                "severity": "medium",
                "location": "Eastside commercial district",
                "description": "Partial roof collapse on warehouse, debris on roadway",
                "radius_miles": 0.5,
                "affected_population": 500,
            },
        ],
        "total_affected_area_sq_miles": 12.4,
        "source": "mock",
    }


async def routing_tool(query: dict[str, Any]) -> dict[str, Any]:
    """Mock routing / evacuation tool."""
    origin = query.get("origin", "Downtown Tampa")
    destination = query.get("destination", "Lincoln Community Center")
    return {
        "origin": origin,
        "destination": destination,
        "routes": [
            {
                "route_id": "R-001",
                "name": "Primary Route via N Lamar",
                "distance_miles": 4.2,
                "estimated_time_minutes": 15,
                "road_status": "open",
                "hazards_on_route": [],
                "accessibility": "full",
            },
            {
                "route_id": "R-002",
                "name": "Alternate Route via MoPac",
                "distance_miles": 6.1,
                "estimated_time_minutes": 22,
                "road_status": "open",
                "hazards_on_route": ["construction zone at mile 3.5"],
                "accessibility": "full",
            },
            {
                "route_id": "R-003",
                "name": "Emergency Route via I-35",
                "distance_miles": 5.8,
                "estimated_time_minutes": 12,
                "road_status": "restricted",
                "hazards_on_route": ["emergency vehicles only"],
                "accessibility": "emergency_only",
            },
        ],
        "recommended_route": "R-001",
        "source": "mock",
    }


async def firestore_tool_write(collection: str, doc_id: str, data: dict) -> dict:
    """Mock Firestore write tool -- stores in local dict."""
    _mock_store = firestore_tool_write._store  # type: ignore[attr-defined]
    key = f"{collection}/{doc_id}"
    _mock_store[key] = {**data, "_id": doc_id, "_collection": collection}
    return {"status": "ok", "path": key}

firestore_tool_write._store = {}  # type: ignore[attr-defined]


async def firestore_tool_read(collection: str, doc_id: str) -> dict | None:
    """Mock Firestore read tool."""
    key = f"{collection}/{doc_id}"
    return firestore_tool_write._store.get(key)  # type: ignore[attr-defined]


async def firestore_tool_query(collection: str, field: str, op: str, value: Any) -> list[dict]:
    """Mock Firestore query tool -- filters in-memory store."""
    results = []
    for key, doc in firestore_tool_write._store.items():  # type: ignore[attr-defined]
        if not key.startswith(f"{collection}/"):
            continue
        doc_value = doc.get(field)
        if op == "==" and doc_value == value:
            results.append(doc)
        elif op == ">=" and doc_value is not None and doc_value >= value:
            results.append(doc)
        elif op == "<=" and doc_value is not None and doc_value <= value:
            results.append(doc)
    return results


async def notification_tool(message: str, channels: list[str] | None = None) -> dict:
    """Mock notification tool -- logs instead of sending."""
    channels = channels or ["dashboard"]
    return {
        "status": "sent",
        "message": message,
        "channels": channels,
        "recipients": len(channels),
        "source": "mock",
    }


async def news_tool(query: str, max_results: int = 5) -> dict:
    """Mock news aggregation tool."""
    return {
        "query": query,
        "articles": [
            {
                "title": "Hurricane Alert: Category 3 Storm Approaches Texas Coast",
                "source": "Mock News Network",
                "published": "2026-03-28T08:00:00Z",
                "summary": "Emergency management officials urge residents in coastal areas to evacuate.",
                "url": "https://example.com/mock-article-1",
                "relevance_score": 0.95,
            },
            {
                "title": "Tampa Emergency Services Activate Hurricane Response Plan",
                "source": "Mock Local News",
                "published": "2026-03-28T09:00:00Z",
                "summary": "City opens emergency shelters and deploys first responders.",
                "url": "https://example.com/mock-article-2",
                "relevance_score": 0.90,
            },
            {
                "title": "Red Cross Mobilizes Volunteers for Texas Storm Relief",
                "source": "Mock Wire Service",
                "published": "2026-03-28T09:30:00Z",
                "summary": "National disaster relief organizations prepare for large-scale response.",
                "url": "https://example.com/mock-article-3",
                "relevance_score": 0.82,
            },
        ],
        "total_results": 3,
        "source": "mock",
    }


# ============================================================================
# Tests
# ============================================================================

class TestWeatherTool:
    """Tests for the weather tool mock responses."""

    @pytest.mark.asyncio
    async def test_weather_tool_mock_storm(self):
        """Storm scenario returns severe weather with high wind and rainfall."""
        result = await weather_tool({"scenario": "hurricane", "location": "Tampa, FL"})

        assert result["condition"] == "severe_storm"
        assert result["wind_speed_mph"] >= 100
        assert result["rainfall_inches_24h"] > 5
        assert result["storm_surge_feet"] > 0
        assert len(result["alerts"]) > 0
        assert any("Hurricane" in a for a in result["alerts"])
        assert result["source"] == "mock"

    @pytest.mark.asyncio
    async def test_weather_tool_mock_outage(self):
        """Power outage scenario returns winter storm conditions."""
        result = await weather_tool({"scenario": "power outage", "location": "Tampa, FL"})

        assert result["condition"] == "overcast"
        assert result["temperature_f"] < 50
        assert result["wind_speed_mph"] > 20
        assert any("Power outage" in a or "Winter Storm" in a for a in result["alerts"])
        assert result["source"] == "mock"

    @pytest.mark.asyncio
    async def test_weather_tool_clear_default(self):
        """Default scenario returns clear conditions with no alerts."""
        result = await weather_tool({"scenario": "normal", "location": "Tampa, FL"})

        assert result["condition"] == "clear"
        assert result["alerts"] == []
        assert result["tornado_risk"] == "none"


class TestHazardTool:
    """Tests for the hazard identification tool."""

    @pytest.mark.asyncio
    async def test_hazard_tool_mock(self):
        """Hazard tool returns a list of identified hazards."""
        result = await hazard_tool({"scenario": "hurricane"})

        assert "hazards" in result
        assert len(result["hazards"]) >= 2
        assert result["source"] == "mock"

        # Each hazard has required fields
        for hazard in result["hazards"]:
            assert "hazard_id" in hazard
            assert "type" in hazard
            assert "severity" in hazard
            assert "location" in hazard
            assert "description" in hazard
            assert "affected_population" in hazard

        # Check severity levels are valid
        valid_severities = {"low", "medium", "high", "critical"}
        for hazard in result["hazards"]:
            assert hazard["severity"] in valid_severities


class TestRoutingTool:
    """Tests for the routing / evacuation tool."""

    @pytest.mark.asyncio
    async def test_routing_tool_mock(self):
        """Routing tool returns multiple routes with a recommendation."""
        result = await routing_tool({
            "origin": "Downtown Tampa",
            "destination": "Lincoln Community Center",
        })

        assert result["origin"] == "Downtown Tampa"
        assert result["destination"] == "Lincoln Community Center"
        assert len(result["routes"]) >= 2
        assert result["recommended_route"] is not None
        assert result["source"] == "mock"

        # Each route has required fields
        for route in result["routes"]:
            assert "route_id" in route
            assert "distance_miles" in route
            assert "estimated_time_minutes" in route
            assert "road_status" in route

        # Recommended route exists in the route list
        route_ids = [r["route_id"] for r in result["routes"]]
        assert result["recommended_route"] in route_ids


class TestFirestoreTool:
    """Tests for the mock Firestore read/write/query tools."""

    @pytest.fixture(autouse=True)
    def clear_store(self):
        """Clear mock store before each test."""
        firestore_tool_write._store = {}  # type: ignore[attr-defined]
        yield
        firestore_tool_write._store = {}  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_firestore_tool_write_read(self):
        """Write a document and read it back."""
        data = {"name": "Test Shelter", "capacity": 200, "status": "active"}
        write_result = await firestore_tool_write("shelters", "SH-TEST", data)
        assert write_result["status"] == "ok"
        assert write_result["path"] == "shelters/SH-TEST"

        read_result = await firestore_tool_read("shelters", "SH-TEST")
        assert read_result is not None
        assert read_result["name"] == "Test Shelter"
        assert read_result["capacity"] == 200

    @pytest.mark.asyncio
    async def test_firestore_tool_read_missing(self):
        """Reading a non-existent document returns None."""
        result = await firestore_tool_read("shelters", "NONEXISTENT")
        assert result is None

    @pytest.mark.asyncio
    async def test_firestore_tool_query(self):
        """Query filters documents by field value."""
        await firestore_tool_write("shelters", "SH-A", {"status": "active", "capacity": 500})
        await firestore_tool_write("shelters", "SH-B", {"status": "closed", "capacity": 200})
        await firestore_tool_write("shelters", "SH-C", {"status": "active", "capacity": 300})

        active = await firestore_tool_query("shelters", "status", "==", "active")
        assert len(active) == 2
        assert all(doc["status"] == "active" for doc in active)

        large = await firestore_tool_query("shelters", "capacity", ">=", 400)
        assert len(large) == 1
        assert large[0]["capacity"] == 500


class TestNotificationTool:
    """Tests for the notification tool."""

    @pytest.mark.asyncio
    async def test_notification_tool(self):
        """Notification tool returns confirmation with channel info."""
        result = await notification_tool(
            "Evacuation order issued for Zone A",
            channels=["dashboard", "email", "sms"],
        )

        assert result["status"] == "sent"
        assert "Evacuation" in result["message"]
        assert result["channels"] == ["dashboard", "email", "sms"]
        assert result["recipients"] == 3
        assert result["source"] == "mock"

    @pytest.mark.asyncio
    async def test_notification_tool_default_channel(self):
        """Notification tool uses dashboard as default channel."""
        result = await notification_tool("Test alert")

        assert result["channels"] == ["dashboard"]
        assert result["recipients"] == 1


class TestNewsTool:
    """Tests for the news aggregation tool."""

    @pytest.mark.asyncio
    async def test_news_tool(self):
        """News tool returns relevant articles with metadata."""
        result = await news_tool("hurricane Tampa Texas")

        assert result["query"] == "hurricane Tampa Texas"
        assert len(result["articles"]) > 0
        assert result["source"] == "mock"

        for article in result["articles"]:
            assert "title" in article
            assert "source" in article
            assert "published" in article
            assert "summary" in article
            assert "url" in article
            assert "relevance_score" in article
            assert 0 <= article["relevance_score"] <= 1.0

        # Articles should be sorted by relevance (highest first)
        scores = [a["relevance_score"] for a in result["articles"]]
        assert scores == sorted(scores, reverse=True)
