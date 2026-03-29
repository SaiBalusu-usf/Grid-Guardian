"""Planner agent: merges parallel specialist outputs into a unified action plan."""

import logging
from datetime import datetime
from uuid import uuid4

logger = logging.getLogger(__name__)


async def run_planner(
    incident_id: str,
    hazard_output: dict,
    vulnerability_output: dict,
    route_output: dict,
    resource_output: dict,
) -> dict:
    """Merge all specialist agent outputs into a draft action plan.

    Args:
        incident_id: Parent incident ID.
        hazard_output: Output from hazard_watcher.
        vulnerability_output: Output from vulnerability_mapper.
        route_output: Output from route_planner.
        resource_output: Output from resource_coordinator.

    Returns:
        Unified draft action plan.
    """
    plan_id = str(uuid4())

    # --- Build actions from specialist outputs ---
    actions: list[dict] = []
    action_seq = 1

    # Evacuation actions from hazard analysis
    if hazard_output.get("evacuation_recommended"):
        actions.append({
            "sequence": action_seq,
            "action": "Initiate evacuation",
            "detail": "Begin mandatory evacuation of all impacted zones",
            "source_agent": "hazard_watcher",
            "priority": "critical",
            "zones": hazard_output.get("impacted_zones", []),
        })
        action_seq += 1

    # Shelter activation
    actions.append({
        "sequence": action_seq,
        "action": "Activate emergency shelters",
        "detail": "Open and staff all designated emergency shelters in affected region",
        "source_agent": "planner",
        "priority": "critical",
    })
    action_seq += 1

    # Vulnerable population evacuation
    critical_areas = vulnerability_output.get("critical_facilities", [])
    if critical_areas:
        actions.append({
            "sequence": action_seq,
            "action": "Priority evacuation of vulnerable populations",
            "detail": f"Assisted evacuation for: {', '.join(critical_areas[:5])}",
            "source_agent": "vulnerability_mapper",
            "priority": "critical",
            "facilities": critical_areas,
        })
        action_seq += 1

    # Route management
    closures = route_output.get("closures", [])
    if closures:
        actions.append({
            "sequence": action_seq,
            "action": "Establish traffic control and road closures",
            "detail": f"Manage {len(closures)} road closure(s) and redirect traffic to safe routes",
            "source_agent": "route_planner",
            "priority": "high",
            "closures": closures,
        })
        action_seq += 1

    # Resource deployment
    for rec in resource_output.get("recommendations", [])[:6]:
        actions.append({
            "sequence": action_seq,
            "action": f"Deploy {rec['resource_type']} to {rec['deploy_to']}",
            "detail": f"Quantity: {rec['quantity']}. Rationale: {rec['rationale']}",
            "source_agent": "resource_coordinator",
            "priority": rec["priority"],
        })
        action_seq += 1

    # Communication actions
    actions.append({
        "sequence": action_seq,
        "action": "Issue public alerts via all channels",
        "detail": "Broadcast bilingual emergency alerts via SMS, siren, TV, radio, social media",
        "source_agent": "planner",
        "priority": "critical",
    })
    action_seq += 1

    # --- Build tasks ---
    tasks: list[dict] = [
        {
            "title": "Set up Incident Command Post at safe staging area",
            "priority": "critical",
            "assignee_type": "crew",
            "location": "Emergency Operations Center",
        },
        {
            "title": "Deploy search and rescue teams to highest-risk zones",
            "priority": "critical",
            "assignee_type": "crew",
            "location": hazard_output.get("impacted_zones", ["Zone A"])[0] if hazard_output.get("impacted_zones") else "Zone A",
        },
        {
            "title": "Staff and supply emergency shelters",
            "priority": "high",
            "assignee_type": "shelter",
            "location": "All activated shelters",
        },
        {
            "title": "Establish medical triage points",
            "priority": "high",
            "assignee_type": "medical",
            "location": "Field locations near impacted zones",
        },
        {
            "title": "Coordinate volunteer intake and assignments",
            "priority": "medium",
            "assignee_type": "volunteer",
            "location": "Volunteer staging area",
        },
    ]

    # --- Build alert stubs ---
    alerts: list[dict] = [
        {
            "severity": hazard_output.get("severity", "high"),
            "region": "All impacted zones",
            "language": "en",
        },
        {
            "severity": hazard_output.get("severity", "high"),
            "region": "All impacted zones",
            "language": "es",
        },
    ]

    # --- Resource allocations summary ---
    resource_allocations = resource_output.get("recommendations", [])

    # --- Confidence calculation ---
    hazard_confidence = hazard_output.get("confidence", 0.7)
    route_count = route_output.get("total_routes_evaluated", 0)
    vuln_count = len(vulnerability_output.get("priority_areas", []))

    # Base confidence from hazard analysis, adjusted by data richness
    plan_confidence = hazard_confidence * 0.6 + 0.2 * min(route_count / 10, 1.0) + 0.2 * min(vuln_count / 8, 1.0)
    plan_confidence = round(min(plan_confidence, 0.95), 2)

    # --- Notes ---
    notes: list[str] = []
    equity_notes = vulnerability_output.get("equity_notes", [])
    if equity_notes:
        notes.extend(equity_notes)
    if route_output.get("travel_risk") in ("high", "critical"):
        notes.append(
            f"ROUTING: Travel risk is {route_output['travel_risk']}. "
            f"Estimated road clearance: {route_output.get('estimated_clearance_time', 'unknown')}."
        )
    notes.append(
        f"RESOURCES: {resource_output.get('total_crews_needed', 0)} total crew units recommended. "
        f"Supply summary: {resource_output.get('supply_summary', {})}."
    )

    plan = {
        "plan_id": plan_id,
        "incident_id": incident_id,
        "status": "draft",
        "actions": actions,
        "tasks": tasks,
        "alerts": alerts,
        "resource_allocations": resource_allocations,
        "confidence": plan_confidence,
        "notes": notes,
        "severity": hazard_output.get("severity", "high"),
        "impacted_zones": hazard_output.get("impacted_zones", []),
        "created_at": datetime.utcnow().isoformat(),
    }

    logger.info(
        "Planner complete: plan=%s actions=%d tasks=%d confidence=%.2f",
        plan_id, len(actions), len(tasks), plan_confidence,
    )
    return plan
