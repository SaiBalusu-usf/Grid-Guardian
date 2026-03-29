"""Hazard zone data tool with mock and live paths."""

import logging
from datetime import datetime

from backend.config import settings

logger = logging.getLogger(__name__)

_MOCK_ZONES: dict[str, dict] = {
    "storm": {
        "zones": [
            {
                "zone_id": "Z-001",
                "type": "tornado_path",
                "risk_level": "critical",
                "affected_area_sq_mi": 12.5,
                "population_estimate": 34000,
            },
            {
                "zone_id": "Z-002",
                "type": "flash_flood",
                "risk_level": "high",
                "affected_area_sq_mi": 8.3,
                "population_estimate": 18000,
            },
            {
                "zone_id": "Z-003",
                "type": "wind_damage",
                "risk_level": "medium",
                "affected_area_sq_mi": 25.0,
                "population_estimate": 56000,
            },
        ],
        "flood_stage": "major",
        "evacuation_recommended": True,
    },
    "outage": {
        "zones": [
            {
                "zone_id": "Z-010",
                "type": "ice_accumulation",
                "risk_level": "high",
                "affected_area_sq_mi": 45.0,
                "population_estimate": 120000,
            },
            {
                "zone_id": "Z-011",
                "type": "power_grid_failure",
                "risk_level": "critical",
                "affected_area_sq_mi": 30.0,
                "population_estimate": 85000,
            },
        ],
        "flood_stage": "none",
        "evacuation_recommended": False,
    },
    "multi-zone": {
        "zones": [
            {
                "zone_id": "Z-100",
                "type": "tornado_confirmed",
                "risk_level": "critical",
                "affected_area_sq_mi": 15.0,
                "population_estimate": 42000,
            },
            {
                "zone_id": "Z-101",
                "type": "flash_flood",
                "risk_level": "critical",
                "affected_area_sq_mi": 20.0,
                "population_estimate": 55000,
            },
            {
                "zone_id": "Z-102",
                "type": "severe_wind",
                "risk_level": "high",
                "affected_area_sq_mi": 35.0,
                "population_estimate": 78000,
            },
            {
                "zone_id": "Z-103",
                "type": "hail_damage",
                "risk_level": "medium",
                "affected_area_sq_mi": 18.0,
                "population_estimate": 29000,
            },
            {
                "zone_id": "Z-104",
                "type": "structural_collapse_risk",
                "risk_level": "high",
                "affected_area_sq_mi": 5.0,
                "population_estimate": 12000,
            },
        ],
        "flood_stage": "major",
        "evacuation_recommended": True,
    },
}

_DEFAULT_MOCK: dict = {
    "zones": [
        {
            "zone_id": "Z-050",
            "type": "general_hazard",
            "risk_level": "high",
            "affected_area_sq_mi": 15.0,
            "population_estimate": 40000,
        },
        {
            "zone_id": "Z-051",
            "type": "flood_risk",
            "risk_level": "medium",
            "affected_area_sq_mi": 10.0,
            "population_estimate": 22000,
        },
    ],
    "flood_stage": "moderate",
    "evacuation_recommended": True,
}


async def get_hazard_zones(region: str, scenario: str = "") -> dict:
    """Retrieve flood and hazard zone data for a region.

    Args:
        region: Geographic region identifier.
        scenario: Optional scenario hint for mock mode.

    Returns:
        Structured hazard zone data.
    """
    if settings.is_mock:
        return _mock_hazards(region, scenario)
    return await _live_hazards(region, scenario)


def _mock_hazards(region: str, scenario: str) -> dict:
    """Return deterministic mock hazard data based on scenario keywords."""
    combined = f"{scenario} {region}".lower()
    for key, data in _MOCK_ZONES.items():
        if key in combined:
            result = {**data, "region": region, "retrieved_at": datetime.utcnow().isoformat()}
            logger.info("Mock hazard for '%s' matched scenario '%s'", region, key)
            return result

    result = {**_DEFAULT_MOCK, "region": region, "retrieved_at": datetime.utcnow().isoformat()}
    logger.info("Mock hazard for '%s' using default scenario", region)
    return result


async def _live_hazards(region: str, scenario: str) -> dict:
    """Placeholder for real hazard API integration."""
    logger.warning("Live hazard API not configured, falling back to mock")
    return _mock_hazards(region, scenario)
