"""Weather data tool with mock and live paths."""

import logging
from datetime import datetime, timezone

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
            result = {**data, "location": location, "retrieved_at": datetime.now(tz=timezone.utc).isoformat()}
            logger.info("Mock weather for '%s' matched scenario '%s'", location, key)
            return result

    result = {**_DEFAULT_MOCK, "location": location, "retrieved_at": datetime.now(tz=timezone.utc).isoformat()}
    logger.info("Mock weather for '%s' using default scenario", location)
    return result


async def _live_weather(location: str, scenario: str) -> dict:
    """Fetch real weather from NWS API (free, no key).

    1. Get grid point from NWS points endpoint (Tampa, FL coords)
    2. Fetch forecast from the grid endpoint
    3. Also fetch active alerts
    Falls back to mock on failure.
    """
    # Tampa, FL coordinates
    lat, lon = 27.9506, -82.4572
    headers = {"User-Agent": "GridGuardian/1.0 (disaster-response-demo)"}

    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get grid info
                points_resp = await client.get(
                    f"https://api.weather.gov/points/{lat},{lon}",
                    headers=headers,
                )
                points_resp.raise_for_status()
                props = points_resp.json().get("properties", {})
                forecast_url = props.get("forecast", "")

                # Get forecast
                condition = "unknown"
                wind_mph = 0
                temperature_f = 0
                precipitation = "unknown"
                if forecast_url:
                    fc_resp = await client.get(forecast_url, headers=headers)
                    fc_resp.raise_for_status()
                    periods = fc_resp.json().get("properties", {}).get("periods", [])
                    if periods:
                        p = periods[0]
                        condition = p.get("shortForecast", "unknown")
                        temperature_f = p.get("temperature", 0)
                        wind_mph = int("".join(c for c in p.get("windSpeed", "0") if c.isdigit()) or "0")
                        precipitation = p.get("detailedForecast", "")[:200]

                # Get active alerts
                alerts_resp = await client.get(
                    f"https://api.weather.gov/alerts/active",
                    params={"point": f"{lat},{lon}"},
                    headers=headers,
                )
                alert_texts = []
                if alerts_resp.status_code == 200:
                    for feat in alerts_resp.json().get("features", [])[:5]:
                        headline = feat.get("properties", {}).get("headline", "")
                        if headline:
                            alert_texts.append(headline)

                severity = "critical" if len(alert_texts) >= 3 else "high" if alert_texts else "medium" if wind_mph > 30 else "low"
                confidence = 0.85 if alert_texts else 0.7

                return {
                    "condition": condition,
                    "severity": severity,
                    "wind_mph": wind_mph,
                    "precipitation": precipitation,
                    "temperature_f": temperature_f,
                    "alerts": alert_texts,
                    "confidence": confidence,
                    "location": location,
                    "source": "weather.gov",
                    "retrieved_at": datetime.now(tz=timezone.utc).isoformat(),
                }
        except Exception as exc:
            logger.warning("Weather API attempt %d/2 failed: %s", attempt + 1, exc)

    logger.error("Weather API exhausted retries, falling back to mock")
    return _mock_weather(location, scenario)
