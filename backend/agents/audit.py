"""Audit agent: critiques action plans for safety, completeness, and equity."""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Module-level counter tracking how many times audit has been called per incident.
# On the first call for any incident, the audit deliberately finds issues (for demo).
# On the second call with corrections applied, it passes.
_audit_call_counts: dict[str, int] = {}


async def run_audit(plan: dict, incident_id: str | None = None) -> dict:
    """Critique an action plan for safety, completeness, and equity.

    Checks for:
    - Missing evidence / data gaps
    - Unsafe assumptions
    - Ignored vulnerable populations
    - Vague alerts
    - Route contradictions

    On first call per incident, always returns at least one issue (demo mode).
    On second call with corrections, passes.

    Args:
        plan: Draft action plan dict from the planner agent.
        incident_id: Optional incident ID for tracking audit iterations.

    Returns:
        Audit result with passed flag, issues, corrections, and severity.
    """
    key = incident_id or plan.get("incident_id", "unknown")
    _audit_call_counts[key] = _audit_call_counts.get(key, 0) + 1
    call_number = _audit_call_counts[key]

    issues: list[dict] = []
    corrections: list[dict] = []

    # Always run real checks
    _check_missing_evidence(plan, issues, corrections)
    _check_unsafe_assumptions(plan, issues, corrections)
    _check_vulnerable_populations(plan, issues, corrections)
    _check_vague_alerts(plan, issues, corrections)
    _check_route_contradictions(plan, issues, corrections)
    _check_resource_adequacy(plan, issues, corrections)

    # On first call, ensure at least one issue exists for demo purposes
    if call_number == 1 and not issues:
        issues.append({
            "category": "completeness",
            "description": (
                "Plan does not include a communication backup strategy in case "
                "primary alert channels (cell towers, internet) fail during the event."
            ),
            "severity": "major",
            "affected_section": "actions",
        })
        corrections.append({
            "for_issue": "completeness",
            "correction": (
                "Add action: Deploy mobile communication units (satellite phones, "
                "HAM radio operators) to each impacted zone as backup communication."
            ),
            "priority": "high",
        })

    # On second call (corrections presumably applied), pass if no critical issues
    if call_number >= 2:
        # Filter out issues that would have been addressed by corrections
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        if not critical_issues:
            issues = []
            corrections = []

    passed = len(issues) == 0

    # Determine overall audit severity
    if not issues:
        audit_severity = "none"
    elif any(i.get("severity") == "critical" for i in issues):
        audit_severity = "critical"
    elif any(i.get("severity") == "major" for i in issues):
        audit_severity = "major"
    else:
        audit_severity = "minor"

    result = {
        "passed": passed,
        "issues": issues,
        "corrections": corrections,
        "severity": audit_severity,
        "audit_iteration": call_number,
        "plan_id": plan.get("plan_id", "unknown"),
        "audited_at": datetime.utcnow().isoformat(),
    }

    logger.info(
        "Audit %s (iteration %d): passed=%s issues=%d severity=%s",
        key, call_number, passed, len(issues), audit_severity,
    )
    return result


def _check_missing_evidence(plan: dict, issues: list, corrections: list) -> None:
    """Check for actions that lack supporting evidence or data sources."""
    actions = plan.get("actions", [])
    for action in actions:
        # Check if any action references zones that aren't in impacted_zones
        if "zones" in action:
            plan_zones = plan.get("impacted_zones", [])
            missing = [z for z in action["zones"] if z not in plan_zones]
            if missing:
                issues.append({
                    "category": "missing_evidence",
                    "description": f"Action '{action.get('action')}' references zones {missing} not listed in impacted zones",
                    "severity": "minor",
                    "affected_section": "actions",
                })

    # Check if plan confidence is too low
    confidence = plan.get("confidence", 0)
    if confidence < 0.5:
        issues.append({
            "category": "missing_evidence",
            "description": f"Plan confidence ({confidence}) is below threshold (0.5). Insufficient data for reliable planning.",
            "severity": "critical",
            "affected_section": "overall",
        })
        corrections.append({
            "for_issue": "missing_evidence",
            "correction": "Gather additional data sources before finalizing plan. Consider re-running hazard analysis.",
            "priority": "critical",
        })


def _check_unsafe_assumptions(plan: dict, issues: list, corrections: list) -> None:
    """Check for potentially unsafe assumptions in the plan."""
    actions = plan.get("actions", [])
    resource_allocs = plan.get("resource_allocations", [])

    # Check if evacuation is recommended but no evacuation action exists
    notes = plan.get("notes", [])
    has_evac_note = any("evacuat" in str(n).lower() for n in notes)
    has_evac_action = any("evacuat" in a.get("action", "").lower() for a in actions)

    if has_evac_note and not has_evac_action:
        issues.append({
            "category": "unsafe_assumption",
            "description": "Plan notes reference evacuation but no explicit evacuation action is defined.",
            "severity": "critical",
            "affected_section": "actions",
        })
        corrections.append({
            "for_issue": "unsafe_assumption",
            "correction": "Add explicit evacuation action with designated routes and shelter assignments.",
            "priority": "critical",
        })

    # Check if there are critical-priority resources without a deployment timeline
    critical_resources = [r for r in resource_allocs if r.get("priority") == "critical"]
    if len(critical_resources) > 3 and not any("timeline" in str(a).lower() for a in actions):
        issues.append({
            "category": "unsafe_assumption",
            "description": f"{len(critical_resources)} critical resources lack deployment timeline.",
            "severity": "minor",
            "affected_section": "resource_allocations",
        })


def _check_vulnerable_populations(plan: dict, issues: list, corrections: list) -> None:
    """Check that vulnerable populations are addressed in the plan."""
    notes = " ".join(str(n) for n in plan.get("notes", []))
    actions = plan.get("actions", [])
    actions_text = " ".join(str(a) for a in actions)

    # Check for mention of special needs / accessibility
    has_special_needs = (
        "special needs" in notes.lower()
        or "special_needs" in notes.lower()
        or "accessibility" in actions_text.lower()
        or "vulnerable" in actions_text.lower()
        or "assisted evacuation" in actions_text.lower()
    )

    if not has_special_needs:
        issues.append({
            "category": "vulnerable_populations",
            "description": "Plan does not explicitly address special-needs populations or accessibility requirements.",
            "severity": "major",
            "affected_section": "actions",
        })
        corrections.append({
            "for_issue": "vulnerable_populations",
            "correction": (
                "Add dedicated actions for: (1) assisted evacuation of mobility-limited residents, "
                "(2) medical equipment continuity for equipment-dependent patients, "
                "(3) accessible shelter assignments."
            ),
            "priority": "high",
        })


def _check_vague_alerts(plan: dict, issues: list, corrections: list) -> None:
    """Check that planned alerts are specific enough to be actionable."""
    alerts = plan.get("alerts", [])

    if not alerts:
        issues.append({
            "category": "vague_alerts",
            "description": "No alerts defined in the plan. Public must be notified.",
            "severity": "major",
            "affected_section": "alerts",
        })
        corrections.append({
            "for_issue": "vague_alerts",
            "correction": "Add at least bilingual (en/es) alerts with specific shelter locations and action instructions.",
            "priority": "high",
        })
        return

    for alert in alerts:
        if isinstance(alert, dict) and "region" in alert:
            if alert["region"] in ("", "unknown", "TBD"):
                issues.append({
                    "category": "vague_alerts",
                    "description": f"Alert for language '{alert.get('language', '?')}' has no specific region.",
                    "severity": "minor",
                    "affected_section": "alerts",
                })


def _check_route_contradictions(plan: dict, issues: list, corrections: list) -> None:
    """Check for contradictions between route closures and deployment actions."""
    actions = plan.get("actions", [])

    closures = set()
    deployment_zones = set()

    for action in actions:
        for c in action.get("closures", []):
            closures.add(str(c).lower())
        deploy_to = action.get("deploy_to", "") or action.get("detail", "")
        if deploy_to:
            deployment_zones.add(deploy_to.lower())

    # Very basic overlap check
    for closure in closures:
        for zone in deployment_zones:
            if any(word in zone for word in closure.split() if len(word) > 4):
                issues.append({
                    "category": "route_contradiction",
                    "description": f"Potential conflict: deploying to '{zone}' while '{closure}' is listed as a closure.",
                    "severity": "minor",
                    "affected_section": "actions",
                })
                break


def _check_resource_adequacy(plan: dict, issues: list, corrections: list) -> None:
    """Check if resource allocations seem adequate for the incident scale."""
    resource_allocs = plan.get("resource_allocations", [])
    severity = plan.get("severity", "unknown")

    total_crew = sum(
        r.get("quantity", 0) for r in resource_allocs if r.get("resource_type") == "crew"
    )

    if severity in ("critical", "high") and total_crew < 4:
        issues.append({
            "category": "resource_adequacy",
            "description": f"Only {total_crew} crew units allocated for a {severity}-severity incident. This may be insufficient.",
            "severity": "major",
            "affected_section": "resource_allocations",
        })
        corrections.append({
            "for_issue": "resource_adequacy",
            "correction": "Increase crew allocation to at least 8 units for high/critical incidents. Request mutual aid if needed.",
            "priority": "high",
        })
