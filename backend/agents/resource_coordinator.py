"""Resource Coordinator agent: recommends resource allocation for incident response."""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Base resource templates keyed by severity
_RESOURCE_TEMPLATES = {
    "critical": {
        "base_crews": 12,
        "generators": 8,
        "supply_kits": 500,
        "medical_teams": 6,
        "batteries": 200,
        "water_trucks": 4,
    },
    "high": {
        "base_crews": 8,
        "generators": 5,
        "supply_kits": 300,
        "medical_teams": 4,
        "batteries": 100,
        "water_trucks": 2,
    },
    "medium": {
        "base_crews": 4,
        "generators": 2,
        "supply_kits": 150,
        "medical_teams": 2,
        "batteries": 50,
        "water_trucks": 1,
    },
    "low": {
        "base_crews": 2,
        "generators": 1,
        "supply_kits": 50,
        "medical_teams": 1,
        "batteries": 20,
        "water_trucks": 0,
    },
}


async def run_resource_coordinator(scenario: dict) -> dict:
    """Recommend resource allocation based on scenario analysis.

    Args:
        scenario: Dict with "scenario" text, "severity", optional
                  "impacted_zones", "priority_areas", "hazards".

    Returns:
        Resource allocation recommendations with quantities, deployment
        targets, priorities, and rationale.
    """
    scenario_text = scenario.get("scenario", "").lower()
    severity = scenario.get("severity", "high")
    impacted_zones = scenario.get("impacted_zones", [])
    priority_areas = scenario.get("priority_areas", [])
    hazards = scenario.get("hazards", [])

    template = _RESOURCE_TEMPLATES.get(severity, _RESOURCE_TEMPLATES["high"])

    # Scale by number of impacted zones
    zone_multiplier = max(1.0, len(impacted_zones) * 0.3)
    zone_multiplier = min(zone_multiplier, 3.0)

    recommendations: list[dict] = []

    # --- Crew deployment ---
    crew_count = int(template["base_crews"] * zone_multiplier)
    if impacted_zones:
        crews_per_zone = max(2, crew_count // len(impacted_zones))
        for zone_id in impacted_zones:
            recommendations.append({
                "resource_type": "crew",
                "quantity": crews_per_zone,
                "deploy_to": zone_id,
                "priority": "critical" if severity in ("critical", "high") else "high",
                "rationale": f"Emergency response crew deployment to impacted zone {zone_id}",
            })
    else:
        recommendations.append({
            "resource_type": "crew",
            "quantity": crew_count,
            "deploy_to": "Incident Command Post",
            "priority": "high",
            "rationale": "Standby crews at command post for rapid deployment",
        })

    # --- Generators for critical facilities ---
    gen_count = int(template["generators"] * zone_multiplier)
    critical_facilities = [
        a for a in priority_areas
        if a.get("vulnerability_score", 0) >= 0.80 or a.get("type") in ("hospital", "assisted_living")
    ]
    if critical_facilities:
        for facility in critical_facilities[:gen_count]:
            recommendations.append({
                "resource_type": "generator",
                "quantity": 1,
                "deploy_to": facility.get("name", "Critical Facility"),
                "priority": "critical",
                "rationale": f"Backup power for {facility.get('type', 'critical facility')}: {facility.get('name', 'N/A')}",
            })
    else:
        recommendations.append({
            "resource_type": "generator",
            "quantity": gen_count,
            "deploy_to": "Emergency Shelters",
            "priority": "high",
            "rationale": "Backup power for activated emergency shelters",
        })

    # --- Medical teams ---
    med_count = int(template["medical_teams"] * zone_multiplier)
    med_areas = [a for a in priority_areas if a.get("type") in ("hospital", "elderly_housing", "assisted_living")]
    if med_areas:
        for area in med_areas[:med_count]:
            recommendations.append({
                "resource_type": "medical",
                "quantity": 1,
                "deploy_to": area.get("name", "Medical Facility"),
                "priority": "critical",
                "rationale": f"Medical support team for vulnerable population at {area.get('name', 'N/A')}",
            })
    else:
        recommendations.append({
            "resource_type": "medical",
            "quantity": med_count,
            "deploy_to": "Field Hospital / Triage Point",
            "priority": "high",
            "rationale": "Medical teams staged for field triage and emergency care",
        })

    # --- Supply kits ---
    supply_count = int(template["supply_kits"] * zone_multiplier)
    recommendations.append({
        "resource_type": "supply_kit",
        "quantity": supply_count,
        "deploy_to": "Distribution Points & Shelters",
        "priority": "high",
        "rationale": f"Emergency supply kits for estimated affected population across {len(impacted_zones)} zones",
    })

    # --- Batteries ---
    battery_count = int(template["batteries"] * zone_multiplier)
    recommendations.append({
        "resource_type": "battery",
        "quantity": battery_count,
        "deploy_to": "Communication Stations & Shelters",
        "priority": "medium",
        "rationale": "Portable batteries for communication equipment and device charging stations",
    })

    # --- Water trucks (if applicable) ---
    water_trucks = int(template["water_trucks"] * zone_multiplier)
    if water_trucks > 0:
        recommendations.append({
            "resource_type": "water_truck",
            "quantity": water_trucks,
            "deploy_to": "Shelter Complexes",
            "priority": "high",
            "rationale": "Potable water delivery for shelters and distribution points",
        })

    # Summary
    total_crews = sum(r["quantity"] for r in recommendations if r["resource_type"] == "crew")
    supply_summary = {}
    for rec in recommendations:
        rtype = rec["resource_type"]
        supply_summary[rtype] = supply_summary.get(rtype, 0) + rec["quantity"]

    result = {
        "recommendations": recommendations,
        "total_crews_needed": total_crews,
        "supply_summary": supply_summary,
        "severity_basis": severity,
        "zone_multiplier": round(zone_multiplier, 2),
        "analyzed_at": datetime.utcnow().isoformat(),
    }

    logger.info(
        "Resource coordinator complete: %d recommendations, %d total crews",
        len(recommendations), total_crews,
    )
    return result
