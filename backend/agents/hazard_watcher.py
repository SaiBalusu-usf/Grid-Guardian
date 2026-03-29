"""Hazard Watcher agent: analyzes weather conditions and hazard zones."""

import logging
from datetime import datetime, timezone

from backend.tools.weather_tool import get_weather
from backend.tools.hazard_tool import get_hazard_zones
from backend.tools.news_tool import get_news_feed

logger = logging.getLogger(__name__)


async def run_hazard_watcher(scenario: dict) -> dict:
    """Analyze current hazard conditions for the given scenario.

    Args:
        scenario: Dict with at least "scenario" (description string) and
                  optionally "location" and "region".

    Returns:
        Structured hazard analysis with severity, confidence, impacted zones,
        hazards list, and recommendations.
    """
    scenario_text = scenario.get("scenario", "")
    location = scenario.get("location", "Tampa, FL")
    region = scenario.get("region", "Central Region")
    tool_calls: list[dict] = []

    # --- Weather data ---
    t0 = datetime.now(tz=timezone.utc).isoformat()
    weather = await get_weather(location=location, scenario=scenario_text)
    tool_calls.append({
        "tool": "get_weather",
        "input": {"location": location, "scenario": scenario_text},
        "output_summary": f"condition={weather.get('condition')}, severity={weather.get('severity')}",
        "timestamp": t0,
    })

    # --- Hazard zones ---
    t1 = datetime.now(tz=timezone.utc).isoformat()
    hazards = await get_hazard_zones(region=region, scenario=scenario_text)
    tool_calls.append({
        "tool": "get_hazard_zones",
        "input": {"region": region, "scenario": scenario_text},
        "output_summary": f"zones={len(hazards.get('zones', []))}, flood_stage={hazards.get('flood_stage')}",
        "timestamp": t1,
    })

    # --- News feed for situational awareness ---
    t2 = datetime.now(tz=timezone.utc).isoformat()
    news = await get_news_feed(query=scenario_text, scenario=scenario_text)
    tool_calls.append({
        "tool": "get_news_feed",
        "input": {"query": scenario_text},
        "output_summary": f"articles={len(news.get('articles', []))}",
        "timestamp": t2,
    })

    # --- Analysis ---
    zones = hazards.get("zones", [])
    impacted_zone_ids = [z["zone_id"] for z in zones]

    # Derive overall severity from weather + zone data
    weather_severity = weather.get("severity", "unknown")
    critical_zones = [z for z in zones if z.get("risk_level") == "critical"]
    high_zones = [z for z in zones if z.get("risk_level") == "high"]

    if critical_zones or weather_severity == "critical":
        severity = "critical"
    elif high_zones or weather_severity == "high":
        severity = "high"
    elif weather_severity == "medium":
        severity = "medium"
    else:
        severity = "low"

    # Confidence: higher when more data sources agree
    base_confidence = weather.get("confidence", 0.7)
    zone_boost = min(len(zones) * 0.02, 0.1)
    news_boost = min(len(news.get("articles", [])) * 0.01, 0.05)
    confidence = min(round(base_confidence + zone_boost + news_boost, 2), 0.99)

    # Build hazard list
    hazard_list = []
    for z in zones:
        hazard_list.append({
            "zone_id": z["zone_id"],
            "type": z["type"],
            "risk_level": z["risk_level"],
            "population_estimate": z.get("population_estimate", 0),
            "affected_area_sq_mi": z.get("affected_area_sq_mi", 0),
        })

    # Add weather-derived hazards
    for alert_text in weather.get("alerts", []):
        hazard_list.append({
            "type": "weather_alert",
            "description": alert_text,
            "risk_level": severity,
        })

    # Recommendations
    recommendations = []
    if hazards.get("evacuation_recommended"):
        recommendations.append("Initiate evacuation for affected zones immediately")
    if critical_zones:
        recommendations.append(
            f"Deploy emergency response teams to {len(critical_zones)} critical zone(s)"
        )
    if weather.get("wind_mph", 0) > 60:
        recommendations.append("Issue shelter-in-place order for mobile home communities")
    if hazards.get("flood_stage") in ("major", "moderate"):
        recommendations.append("Activate flood barriers and pre-position rescue boats")
    recommendations.append("Activate all available emergency shelters")
    recommendations.append("Establish incident command post at safe staging area")

    result = {
        "severity": severity,
        "confidence": confidence,
        "impacted_zones": impacted_zone_ids,
        "hazards": hazard_list,
        "recommendations": recommendations,
        "weather_summary": {
            "condition": weather.get("condition"),
            "wind_mph": weather.get("wind_mph"),
            "precipitation": weather.get("precipitation"),
            "alerts_count": len(weather.get("alerts", [])),
        },
        "flood_stage": hazards.get("flood_stage", "unknown"),
        "evacuation_recommended": hazards.get("evacuation_recommended", False),
        "tool_calls": tool_calls,
        "analyzed_at": datetime.now(tz=timezone.utc).isoformat(),
    }

    logger.info(
        "Hazard watcher complete: severity=%s confidence=%.2f zones=%d",
        severity, confidence, len(impacted_zone_ids),
    )
    return result
