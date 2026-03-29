"""Route planning tool with mock and live paths."""

import logging
from datetime import datetime, timezone
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
        "retrieved_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    logger.info("Mock routes generated: %s -> %s (%d routes)", origin, destination, len(routes))
    return result


async def _live_routes(origin: str, destination: str, avoid_zones: list[str]) -> dict:
    """Fetch routes from OSRM (free, no API key).

    Uses the public OSRM demo server for routing.
    Falls back to mock if the API is unreachable.
    """
    import httpx

    # Map location names to Tampa, FL area coordinates for demo
    _COORDS = {
        "emergency operations center": (-82.4572, 27.9506),
        "zone a - riverside district": (-82.4700, 27.9300),
        "zone b - medical district": (-82.4500, 27.9600),
        "zone a - oak valley": (-82.4800, 27.9400),
        "fire station 7": (-82.4400, 27.9700),
        "supply depot": (-82.4300, 27.9450),
        "metro convention center": (-82.4580, 27.9420),
    }

    origin_coords = _COORDS.get(origin.lower(), (-82.4572, 27.9506))
    dest_coords = _COORDS.get(destination.lower(), (-82.4700, 27.9300))

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = (
                f"https://router.project-osrm.org/route/v1/driving/"
                f"{origin_coords[0]},{origin_coords[1]};"
                f"{dest_coords[0]},{dest_coords[1]}"
                f"?overview=full&alternatives=true&steps=false"
            )
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        routes = []
        for i, route in enumerate(data.get("routes", [])[:3]):
            distance_mi = round(route["distance"] / 1609.34, 1)
            time_min = round(route["duration"] / 60)
            risk = "low" if not avoid_zones else ("high" if i > 0 else "medium")
            routes.append({
                "route_id": f"OSRM-{i+1:03d}",
                "name": f"Route {chr(65+i)} ({distance_mi} mi)",
                "distance_mi": distance_mi,
                "estimated_time_min": time_min,
                "risk_level": risk,
                "closures": [],
                "detours": [],
            })

        result = {
            "routes": routes if routes else _mock_routes(origin, destination, avoid_zones)["routes"],
            "recommended_route_id": routes[0]["route_id"] if routes else "R-A",
            "origin": origin,
            "destination": destination,
            "source": "osrm" if routes else "mock_fallback",
            "retrieved_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        logger.info("Live routes: %s -> %s (%d routes from OSRM)", origin, destination, len(routes))
        return result

    except Exception as exc:
        logger.warning("OSRM routing failed (%s), falling back to mock", exc)
        return _mock_routes(origin, destination, avoid_zones)
