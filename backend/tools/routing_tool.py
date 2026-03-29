"""Route planning tool with mock and live paths."""

import logging
from datetime import datetime
from uuid import uuid4

from backend.config import settings

logger = logging.getLogger(__name__)


async def get_routes(
    origin: str, destination: str, avoid_zones: list[str] | None = None
) -> dict:
    """Retrieve route options between two points, optionally avoiding hazard zones.

    Args:
        origin: Starting location.
        destination: Target location.
        avoid_zones: List of zone IDs to route around.

    Returns:
        Structured route data with recommendations.
    """
    if avoid_zones is None:
        avoid_zones = []

    if settings.is_mock:
        return _mock_routes(origin, destination, avoid_zones)
    return await _live_routes(origin, destination, avoid_zones)


def _mock_routes(origin: str, destination: str, avoid_zones: list[str]) -> dict:
    """Return deterministic mock routing data."""
    route_a_id = f"R-{uuid4().hex[:8]}"
    route_b_id = f"R-{uuid4().hex[:8]}"
    route_c_id = f"R-{uuid4().hex[:8]}"

    closures = []
    detours_a: list[str] = []
    if avoid_zones:
        closures = [
            f"Road closure near zone {z} - bridge out" for z in avoid_zones[:2]
        ]
        detours_a = [f"Detour around zone {z} via Highway 7" for z in avoid_zones[:1]]

    routes = [
        {
            "route_id": route_a_id,
            "name": f"Primary Route: {origin} to {destination} via Highway 9",
            "distance_mi": 14.2,
            "estimated_time_min": 28,
            "risk_level": "low" if not avoid_zones else "medium",
            "closures": [],
            "detours": detours_a,
        },
        {
            "route_id": route_b_id,
            "name": f"Alternate Route: {origin} to {destination} via County Road 12",
            "distance_mi": 18.7,
            "estimated_time_min": 35,
            "risk_level": "medium",
            "closures": closures[:1],
            "detours": [f"Use FM-2210 bypass around {destination} east side"],
        },
        {
            "route_id": route_c_id,
            "name": f"Emergency Route: {origin} to {destination} via Interstate 35",
            "distance_mi": 22.1,
            "estimated_time_min": 20,
            "risk_level": "high",
            "closures": closures,
            "detours": [],
        },
    ]

    result = {
        "routes": routes,
        "recommended_route_id": route_a_id,
        "origin": origin,
        "destination": destination,
        "avoid_zones": avoid_zones,
        "retrieved_at": datetime.utcnow().isoformat(),
    }
    logger.info("Mock routes generated: %s -> %s (%d routes)", origin, destination, len(routes))
    return result


async def _live_routes(origin: str, destination: str, avoid_zones: list[str]) -> dict:
    """Placeholder for real routing API integration."""
    logger.warning("Live routing API not configured, falling back to mock")
    return _mock_routes(origin, destination, avoid_zones)
