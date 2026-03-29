"""Route Planner agent: determines safe routes and identifies closures."""

import logging
from datetime import datetime

from backend.tools.routing_tool import get_routes

logger = logging.getLogger(__name__)

# Default origin/destination pairs for emergency routing
_ROUTE_PAIRS = [
    {"origin": "Emergency Operations Center", "destination": "Zone A - Riverside District"},
    {"origin": "Emergency Operations Center", "destination": "Zone B - Medical District"},
    {"origin": "Fire Station 7", "destination": "Zone A - Oak Valley"},
    {"origin": "Supply Depot", "destination": "Metro Convention Center"},
]


async def run_route_planner(scenario: dict) -> dict:
    """Plan safe routes avoiding hazard zones.

    Args:
        scenario: Dict with "scenario" text, optional "impacted_zones" list,
                  optional "hazard_zones" list of zone dicts.

    Returns:
        Route plan with safe routes, closures, travel risk, alternatives,
        and estimated clearance time.
    """
    scenario_text = scenario.get("scenario", "").lower()
    impacted_zones = scenario.get("impacted_zones", [])
    severity = scenario.get("severity", "high")
    tool_calls: list[dict] = []

    all_routes: list[dict] = []
    all_closures: list[str] = []

    # Query routes for each priority pair
    for pair in _ROUTE_PAIRS:
        t0 = datetime.utcnow().isoformat()
        result = await get_routes(
            origin=pair["origin"],
            destination=pair["destination"],
            avoid_zones=impacted_zones,
        )
        tool_calls.append({
            "tool": "get_routes",
            "input": {**pair, "avoid_zones": impacted_zones},
            "output_summary": f"routes={len(result.get('routes', []))}, recommended={result.get('recommended_route_id')}",
            "timestamp": t0,
        })

        for route in result.get("routes", []):
            all_routes.append(route)
            all_closures.extend(route.get("closures", []))

    # Deduplicate closures
    unique_closures = list(set(all_closures))

    # Identify safe routes (low/medium risk only)
    safe_routes = [r for r in all_routes if r.get("risk_level") in ("low", "medium")]
    alternative_routes = [r for r in all_routes if r.get("risk_level") == "high"]

    # Determine overall travel risk
    if not safe_routes:
        travel_risk = "critical"
    elif len(safe_routes) < len(all_routes) * 0.5:
        travel_risk = "high"
    elif unique_closures:
        travel_risk = "medium"
    else:
        travel_risk = "low"

    # Estimate clearance time based on severity and closures
    clearance_hours_map = {
        "critical": "8-12h",
        "high": "4-6h",
        "medium": "2-4h",
        "low": "1-2h",
    }
    estimated_clearance = clearance_hours_map.get(severity, "4h")

    result = {
        "safe_routes": [
            {
                "route_id": r["route_id"],
                "name": r["name"],
                "distance_mi": r["distance_mi"],
                "estimated_time_min": r["estimated_time_min"],
                "risk_level": r["risk_level"],
                "detours": r.get("detours", []),
            }
            for r in safe_routes
        ],
        "closures": unique_closures,
        "travel_risk": travel_risk,
        "alternative_routes": [
            {
                "route_id": r["route_id"],
                "name": r["name"],
                "distance_mi": r["distance_mi"],
                "estimated_time_min": r["estimated_time_min"],
                "risk_level": r["risk_level"],
                "note": "High risk - use only if no alternatives available",
            }
            for r in alternative_routes
        ],
        "estimated_clearance_time": estimated_clearance,
        "total_routes_evaluated": len(all_routes),
        "tool_calls": tool_calls,
        "analyzed_at": datetime.utcnow().isoformat(),
    }

    logger.info(
        "Route planner complete: %d safe, %d closures, risk=%s",
        len(safe_routes), len(unique_closures), travel_risk,
    )
    return result
