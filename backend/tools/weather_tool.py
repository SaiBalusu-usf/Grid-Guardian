"""Weather data tool with mock and live paths."""

import logging
from datetime import datetime

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

_MOCK_SCENARIOS: dict[str, dict] = {
    "storm": {
        "condition": "Severe Thunderstorm",
        "severity": "critical",
        "wind_mph": 75,
        "precipitation": "heavy rain with hail",
        "temperature_f": 68,
        "alerts": [
            "Tornado Watch until 10:00 PM CDT",
            "Severe Thunderstorm Warning until 7:30 PM CDT",
            "Flash Flood Warning until 9:00 PM CDT",
        ],
        "confidence": 0.92,
    },
    "outage": {
        "condition": "Ice Storm",
        "severity": "high",
        "wind_mph": 35,
        "precipitation": "freezing rain, 0.5-1 inch ice accumulation",
        "temperature_f": 28,
        "alerts": [
            "Ice Storm Warning until 6:00 AM EST",
            "Wind Advisory until 12:00 PM EST",
            "Power Outage Risk: HIGH for metro area",
        ],
        "confidence": 0.88,
    },
    "multi-zone": {
        "condition": "Widespread Severe Weather",
        "severity": "critical",
        "wind_mph": 90,
        "precipitation": "heavy rain, large hail, multiple tornado cells",
        "temperature_f": 72,
        "alerts": [
            "Tornado Warning - Zone A (confirmed tornado on ground)",
            "Tornado Watch - Zones B, C, D",
            "Severe Thunderstorm Warning - Zones A through F",
            "Flash Flood Emergency - Zone A, Zone B",
            "Extreme Wind Warning - Zone C",
        ],
        "confidence": 0.95,
    },
}

_DEFAULT_MOCK: dict = {
    "condition": "Severe Weather",
    "severity": "high",
    "wind_mph": 55,
    "precipitation": "heavy rain",
    "temperature_f": 60,
    "alerts": [
        "Severe Weather Advisory in effect",
        "High Wind Warning until midnight",
    ],
    "confidence": 0.80,
}


async def get_weather(location: str, scenario: str = "") -> dict:
    """Retrieve weather data for a location.

    Args:
        location: Geographic location string.
        scenario: Optional scenario hint for mock mode.

    Returns:
        Structured weather data dict.
    """
    if settings.is_mock:
        return _mock_weather(location, scenario)
    return await _live_weather(location, scenario)


def _mock_weather(location: str, scenario: str) -> dict:
    """Return deterministic mock weather based on scenario keywords."""
    combined = f"{scenario} {location}".lower()
    for key, data in _MOCK_SCENARIOS.items():
        if key in combined:
            result = {**data, "location": location, "retrieved_at": datetime.utcnow().isoformat()}
            logger.info("Mock weather for '%s' matched scenario '%s'", location, key)
            return result

    result = {**_DEFAULT_MOCK, "location": location, "retrieved_at": datetime.utcnow().isoformat()}
    logger.info("Mock weather for '%s' using default scenario", location)
    return result


async def _live_weather(location: str, scenario: str) -> dict:
    """Call an external weather API with retry logic."""
    max_retries = 2
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.weather.gov/points/39.7456,-97.0892",
                    headers={"User-Agent": "GridGuardian/1.0"},
                )
                resp.raise_for_status()
                raw = resp.json()
                return {
                    "condition": raw.get("properties", {}).get("forecast", "Unknown"),
                    "severity": "high",
                    "wind_mph": 0,
                    "precipitation": "unknown",
                    "temperature_f": 0,
                    "alerts": [],
                    "confidence": 0.5,
                    "location": location,
                    "retrieved_at": datetime.utcnow().isoformat(),
                    "raw_source": "weather.gov",
                }
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Weather API attempt %d/%d failed: %s", attempt + 1, max_retries, exc
            )

    logger.error("Weather API exhausted retries, falling back to mock")
    return _mock_weather(location, scenario)
