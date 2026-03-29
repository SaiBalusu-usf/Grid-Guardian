"""Orchestrator: the core workflow engine that coordinates all agents for incident response."""

import asyncio
import logging
from datetime import datetime

import httpx

from backend.config import settings
from backend.models.incident import Incident
from backend.models.agent_run import AgentRun
from backend.models.trace import TraceEvent
from backend.models.task import Task
from backend.models.alert import Alert
from backend.services import firestore_service as fs
from backend.services.streaming import StreamManager
from backend.agents.hazard_watcher import run_hazard_watcher
from backend.agents.vulnerability_mapper import run_vulnerability_mapper
from backend.agents.route_planner import run_route_planner
from backend.agents.resource_coordinator import run_resource_coordinator
from backend.agents.planner import run_planner
from backend.agents.audit import run_audit
from backend.agents.public_alert import run_public_alert

logger = logging.getLogger(__name__)

MAX_AUDIT_ITERATIONS = 2


async def run_incident_workflow(scenario: dict, stream_manager: StreamManager) -> Incident:
    """Execute the full incident response workflow.

    Steps:
    1. Create incident in Firestore and log trigger trace
    2. Run parallel specialist agents (hazard, vulnerability, route, resource)
    3. Merge results into a draft action plan
    4. Audit loop (max 2 iterations)
    5. A2A call to shelter specialist
    6. Draft public alerts
    7. Create tasks and alerts in Firestore
    8. Finalize incident

    Args:
        scenario: Dict with at least "scenario" (str) and optionally "trigger_source".
        stream_manager: SSE stream manager for broadcasting events.

    Returns:
        Completed Incident model.
    """
    scenario_text = scenario.get("scenario", "Unknown scenario")
    trigger_source = scenario.get("trigger_source", "simulation")

    # -----------------------------------------------------------------------
    # Step 1: Retrieve or create incident
    # -----------------------------------------------------------------------
    pre_created_id = scenario.get("_incident_id")
    if pre_created_id:
        incident = await fs.get_incident(pre_created_id)
        if incident is None:
            incident = Incident(id=pre_created_id, scenario=scenario_text, trigger_source=trigger_source, status="initiated")
            incident = await fs.create_incident(incident)
    else:
        incident = Incident(scenario=scenario_text, trigger_source=trigger_source, status="initiated")
        incident = await fs.create_incident(incident)
    logger.info("Incident %s ready: %s", incident.id, scenario_text)

    await _trace(incident.id, "trigger", {
        "scenario": scenario_text,
        "trigger_source": trigger_source,
    }, stream_manager)

    await stream_manager.broadcast("incident_update", {
        "incident_id": incident.id,
        "status": "initiated",
        "scenario": scenario_text,
    })

    try:
        # -------------------------------------------------------------------
        # Step 2: Run parallel specialist agents
        # -------------------------------------------------------------------
        await fs.update_incident(incident.id, {"status": "analyzing"})
        await stream_manager.broadcast("incident_update", {
            "incident_id": incident.id,
            "status": "analyzing",
        })

        # Trace agent starts
        await asyncio.gather(
            _trace(incident.id, "agent_start", {"agent": "hazard_watcher"}, stream_manager),
            _trace(incident.id, "agent_start", {"agent": "vulnerability_mapper"}, stream_manager),
            _trace(incident.id, "agent_start", {"agent": "route_planner"}, stream_manager),
            _trace(incident.id, "agent_start", {"agent": "resource_coordinator"}, stream_manager),
        )

        # Run agents concurrently
        base_scenario = {
            "scenario": scenario_text,
            "location": scenario.get("location", "Tampa, FL"),
            "region": scenario.get("region", "Central Region"),
        }

        hazard_result, vuln_result, route_result, resource_result = await asyncio.gather(
            _run_agent_tracked(incident.id, "hazard_watcher", run_hazard_watcher, base_scenario, stream_manager),
            _run_agent_tracked(incident.id, "vulnerability_mapper", run_vulnerability_mapper, base_scenario, stream_manager),
            _run_agent_tracked(incident.id, "route_planner", run_route_planner, base_scenario, stream_manager),
            _run_agent_tracked(incident.id, "resource_coordinator", run_resource_coordinator, base_scenario, stream_manager),
        )

        # Update incident with hazard findings
        await fs.update_incident(incident.id, {
            "severity": hazard_result.get("severity", "high"),
            "confidence": hazard_result.get("confidence", 0.0),
            "impacted_zones": hazard_result.get("impacted_zones", []),
        })

        # Enrich subsequent inputs with findings from parallel phase
        enriched_scenario = {
            **base_scenario,
            "severity": hazard_result.get("severity", "high"),
            "impacted_zones": hazard_result.get("impacted_zones", []),
            "priority_areas": vuln_result.get("priority_areas", []),
            "hazards": hazard_result.get("hazards", []),
            "recommendations": hazard_result.get("recommendations", []),
        }

        # -------------------------------------------------------------------
        # Step 3: Merge into draft plan
        # -------------------------------------------------------------------
        await fs.update_incident(incident.id, {"status": "planning"})
        await stream_manager.broadcast("incident_update", {
            "incident_id": incident.id,
            "status": "planning",
        })

        await _trace(incident.id, "agent_start", {"agent": "planner"}, stream_manager)
        plan = await run_planner(
            incident_id=incident.id,
            hazard_output=hazard_result,
            vulnerability_output=vuln_result,
            route_output=route_result,
            resource_output=resource_result,
        )
        await _trace(incident.id, "agent_end", {"agent": "planner"}, stream_manager)
        await _trace(incident.id, "plan_draft", {"plan_id": plan["plan_id"], "confidence": plan["confidence"]}, stream_manager)

        await stream_manager.broadcast("plan_update", {
            "incident_id": incident.id,
            "plan_id": plan["plan_id"],
            "status": "draft",
            "confidence": plan["confidence"],
        })

        # -------------------------------------------------------------------
        # Step 4: Audit loop
        # -------------------------------------------------------------------
        await fs.update_incident(incident.id, {"status": "auditing"})
        await stream_manager.broadcast("incident_update", {
            "incident_id": incident.id,
            "status": "auditing",
        })

        for audit_iter in range(MAX_AUDIT_ITERATIONS):
            await _trace(incident.id, "agent_start", {"agent": "audit", "iteration": audit_iter + 1}, stream_manager)

            audit_result = await run_audit(plan, incident_id=incident.id)

            await _trace(incident.id, "audit", {
                "iteration": audit_iter + 1,
                "passed": audit_result["passed"],
                "issues_count": len(audit_result.get("issues", [])),
                "severity": audit_result.get("severity", "none"),
            }, stream_manager)

            await _trace(incident.id, "agent_end", {"agent": "audit", "iteration": audit_iter + 1}, stream_manager)

            await stream_manager.broadcast("agent_status", {
                "incident_id": incident.id,
                "agent": "audit",
                "iteration": audit_iter + 1,
                "passed": audit_result["passed"],
                "issues": len(audit_result.get("issues", [])),
            })

            if audit_result["passed"]:
                logger.info("Audit passed on iteration %d", audit_iter + 1)
                break

            # Apply corrections
            logger.info(
                "Audit failed iteration %d with %d issues, applying corrections",
                audit_iter + 1, len(audit_result.get("issues", [])),
            )
            plan = _apply_corrections(plan, audit_result)

        # Mark plan as final
        plan["status"] = "final"
        await _trace(incident.id, "plan_final", {
            "plan_id": plan["plan_id"],
            "confidence": plan["confidence"],
            "actions_count": len(plan.get("actions", [])),
        }, stream_manager)

        await stream_manager.broadcast("plan_update", {
            "incident_id": incident.id,
            "plan_id": plan["plan_id"],
            "status": "final",
        })

        # -------------------------------------------------------------------
        # Step 5: A2A shelter specialist call
        # -------------------------------------------------------------------
        shelter_data = await _call_shelter_agent(incident.id, enriched_scenario, stream_manager)

        # -------------------------------------------------------------------
        # Step 6: Public alerts
        # -------------------------------------------------------------------
        await _trace(incident.id, "agent_start", {"agent": "public_alert"}, stream_manager)

        alert_input = {
            **enriched_scenario,
            "shelters": shelter_data.get("shelters", []) if shelter_data else [],
        }
        alert_result = await run_public_alert(alert_input)

        await _trace(incident.id, "agent_end", {"agent": "public_alert"}, stream_manager)

        # -------------------------------------------------------------------
        # Step 7: Create tasks and alerts in Firestore
        # -------------------------------------------------------------------
        await fs.update_incident(incident.id, {"status": "executing"})
        await stream_manager.broadcast("incident_update", {
            "incident_id": incident.id,
            "status": "executing",
        })

        # Create tasks (at least 3 from the plan)
        plan_tasks = plan.get("tasks", [])
        for task_data in plan_tasks:
            task = Task(
                incident_id=incident.id,
                title=task_data.get("title", "Untitled task"),
                priority=task_data.get("priority", "medium"),
                location=task_data.get("location", ""),
                assignee_type=task_data.get("assignee_type", "crew"),
                status="pending",
            )
            await fs.create_task(task)
            await _trace(incident.id, "action", {
                "action": "task_created",
                "task_id": task.id,
                "title": task.title,
            }, stream_manager)
            await stream_manager.broadcast("task_update", {
                "incident_id": incident.id,
                "task_id": task.id,
                "title": task.title,
                "status": "pending",
            })

        # Create alerts
        for alert_data in alert_result.get("alerts", []):
            alert = Alert(
                incident_id=incident.id,
                message=alert_data.get("message", ""),
                language=alert_data.get("language", "en"),
                severity=alert_data.get("severity", "high"),
                region=alert_data.get("region", ""),
                status="draft",
            )
            await fs.create_alert(alert)
            await _trace(incident.id, "action", {
                "action": "alert_created",
                "alert_id": alert.id,
                "language": alert.language,
                "region": alert.region,
            }, stream_manager)
            await stream_manager.broadcast("alert_update", {
                "incident_id": incident.id,
                "alert_id": alert.id,
                "severity": alert.severity,
                "language": alert.language,
            })

        # -------------------------------------------------------------------
        # Step 8: Finalize
        # -------------------------------------------------------------------
        final_updates = {
            "status": "completed",
            "final_plan": plan,
        }
        incident = await fs.update_incident(incident.id, final_updates)

        await stream_manager.broadcast("incident_update", {
            "incident_id": incident.id,
            "status": "completed",
            "severity": incident.severity,
            "confidence": incident.confidence,
        })

        logger.info("Incident %s workflow completed successfully", incident.id)
        return incident

    except Exception as exc:
        logger.exception("Incident %s workflow failed: %s", incident.id, exc)
        try:
            incident = await fs.update_incident(incident.id, {
                "status": "failed",
                "final_plan": {"error": str(exc)},
            })
        except Exception:
            pass
        await stream_manager.broadcast("incident_update", {
            "incident_id": incident.id,
            "status": "failed",
            "error": str(exc),
        })
        return incident


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _trace(
    incident_id: str,
    event_type: str,
    payload: dict,
    stream_manager: StreamManager,
) -> TraceEvent:
    """Create a trace event and broadcast it."""
    event = TraceEvent(
        incident_id=incident_id,
        event_type=event_type,
        payload=payload,
    )
    await fs.add_trace(event)
    await stream_manager.broadcast("trace_event", {
        "incident_id": incident_id,
        "event_type": event_type,
        "trace_id": event.id,
        "payload": payload,
    })
    return event


async def _run_agent_tracked(
    incident_id: str,
    agent_name: str,
    agent_fn,
    input_data: dict,
    stream_manager: StreamManager,
) -> dict:
    """Run an agent function with tracking (AgentRun + traces)."""
    run = AgentRun(
        incident_id=incident_id,
        agent_name=agent_name,
        input=input_data,
    )

    await stream_manager.broadcast("agent_status", {
        "incident_id": incident_id,
        "agent": agent_name,
        "status": "running",
    })

    try:
        output = await agent_fn(input_data)
        run.output = output
        run.end_time = datetime.utcnow().isoformat()
        run.tool_calls = output.get("tool_calls", [])
    except Exception as exc:
        run.error = str(exc)
        run.end_time = datetime.utcnow().isoformat()
        logger.error("Agent %s failed: %s", agent_name, exc)
        output = {"error": str(exc)}
        run.output = output

    await fs.log_agent_run(run)

    await _trace(incident_id, "agent_end", {
        "agent": agent_name,
        "has_error": run.error is not None,
    }, stream_manager)

    await stream_manager.broadcast("agent_status", {
        "incident_id": incident_id,
        "agent": agent_name,
        "status": "error" if run.error else "completed",
    })

    return output


async def _call_shelter_agent(
    incident_id: str,
    scenario: dict,
    stream_manager: StreamManager,
) -> dict:
    """Call the A2A shelter specialist agent via HTTP.

    Falls back to mock data if the shelter agent is unreachable.
    """
    await _trace(incident_id, "a2a_request", {
        "target": "shelter_agent",
        "url": settings.SHELTER_AGENT_URL,
    }, stream_manager)

    request_body = {
        "message": {
            "role": "user",
            "content": {
                "zone": ", ".join(scenario.get("impacted_zones", ["Central Region"])),
                "scenario": scenario.get("scenario", ""),
                "capacity_needed": sum(
                    a.get("population", 0)
                    for a in scenario.get("priority_areas", [])
                    if a.get("vulnerability_score", 0) >= 0.6
                ),
            },
        }
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{settings.SHELTER_AGENT_URL}/a2a/execute",
                json=request_body,
            )
            resp.raise_for_status()
            a2a_result = resp.json()
            shelter_response = a2a_result.get("result", a2a_result)
            shelter_response["status"] = a2a_result.get("status", "completed")
            logger.info("Shelter agent responded: %s", shelter_response.get("status", "ok"))
    except Exception as exc:
        logger.warning("Shelter agent unreachable (%s), using fallback data", exc)
        shelter_response = _fallback_shelter_data(incident_id)

    await _trace(incident_id, "a2a_response", {
        "source": "shelter_agent",
        "shelters_count": len(shelter_response.get("shelters", [])),
        "status": shelter_response.get("status", "fallback"),
    }, stream_manager)

    return shelter_response


def _fallback_shelter_data(incident_id: str) -> dict:
    """Return fallback shelter recommendations when A2A agent is unavailable."""
    return {
        "status": "fallback",
        "incident_id": incident_id,
        "shelters": [
            {
                "shelter_id": "shelter-001",
                "name": "Lincoln Community Center",
                "capacity": 500,
                "recommended_assignment": "Zone A evacuees",
                "accessibility": "full_ada",
                "supplies_adequate": True,
            },
            {
                "shelter_id": "shelter-002",
                "name": "Riverside High School Gymnasium",
                "capacity": 350,
                "recommended_assignment": "Zone B evacuees",
                "accessibility": "wheelchair",
                "supplies_adequate": True,
            },
            {
                "shelter_id": "shelter-004",
                "name": "Metro Convention Center - Hall B",
                "capacity": 1200,
                "recommended_assignment": "Overflow / special needs",
                "accessibility": "full_ada",
                "supplies_adequate": True,
            },
        ],
        "total_capacity": 2050,
        "recommendation": "Activate all three shelters immediately. Prioritize ADA-accessible facilities for special-needs populations.",
    }


def _apply_corrections(plan: dict, audit_result: dict) -> dict:
    """Apply audit corrections to the plan."""
    corrections = audit_result.get("corrections", [])

    for correction in corrections:
        # Add correction as a new action in the plan
        actions = plan.get("actions", [])
        next_seq = max((a.get("sequence", 0) for a in actions), default=0) + 1
        actions.append({
            "sequence": next_seq,
            "action": f"[CORRECTION] {correction.get('correction', 'Applied audit correction')}",
            "detail": f"Added in response to audit issue: {correction.get('for_issue', 'N/A')}",
            "source_agent": "audit",
            "priority": correction.get("priority", "high"),
        })
        plan["actions"] = actions

    # Add note about corrections
    notes = plan.get("notes", [])
    notes.append(
        f"AUDIT: {len(corrections)} correction(s) applied from audit iteration. "
        f"Issues found: {len(audit_result.get('issues', []))}."
    )
    plan["notes"] = notes

    # Bump confidence slightly after corrections
    plan["confidence"] = min(round(plan.get("confidence", 0.5) + 0.05, 2), 0.98)

    return plan
