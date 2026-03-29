"""Incident workflow wrapper that ties the orchestrator to the FastAPI lifecycle."""

import asyncio
import logging

from backend.agents.orchestrator import run_incident_workflow
from backend.agents.adk_runner import run_adk_workflow
from backend.services.streaming import stream_manager

logger = logging.getLogger(__name__)

# Track running workflows so we can await or cancel them during shutdown
_running_workflows: dict[str, asyncio.Task] = {}


async def start_workflow(scenario: dict) -> dict:
    """Launch the incident workflow as a background asyncio task.

    Args:
        scenario: Dict with "scenario" (str) and optionally "trigger_source".

    Returns:
        Stub dict with the incident_id so the caller can poll for progress.
    """
    from backend.models.incident import Incident
    from backend.services import firestore_service as fs

    # Create the incident once here; the orchestrator will reuse it via _incident_id
    incident = Incident(
        scenario=scenario.get("scenario", "Unknown"),
        trigger_source=scenario.get("trigger_source", "simulation"),
        status="initiated",
    )
    incident = await fs.create_incident(incident)

    async def _run() -> None:
        try:
            # ----------------------------------------------------------
            # Try ADK runner first; falls back to legacy if it returns None
            # ----------------------------------------------------------
            adk_result = await run_adk_workflow(
                scenario=scenario,
                incident_id=incident.id,
                stream_manager=stream_manager,
            )

            if adk_result is not None:
                # ADK succeeded -- persist results to Firestore
                await _persist_adk_results(incident.id, adk_result)
                logger.info("ADK workflow for incident %s completed", incident.id)
                return

            # ----------------------------------------------------------
            # Legacy fallback path (existing orchestrator)
            # ----------------------------------------------------------
            result = await run_incident_workflow(
                scenario={**scenario, "_incident_id": incident.id},
                stream_manager=stream_manager,
            )
            logger.info("Workflow for incident %s finished: status=%s", result.id, result.status)
        except Exception as exc:
            logger.exception("Workflow for incident %s crashed: %s", incident.id, exc)
        finally:
            _running_workflows.pop(incident.id, None)

    task = asyncio.create_task(_run())
    _running_workflows[incident.id] = task

    return {
        "incident_id": incident.id,
        "status": "initiated",
        "scenario": incident.scenario,
        "message": "Incident workflow started. Poll GET /api/incidents/{id} for progress.",
    }


async def _persist_adk_results(incident_id: str, adk_result: dict) -> None:
    """Persist ADK runner output into Firestore (tasks, alerts, incident update)."""
    from backend.models.task import Task
    from backend.models.alert import Alert
    from backend.services import firestore_service as fs

    # Create tasks from the plan
    plan = adk_result.get("plan")
    if isinstance(plan, dict):
        for task_data in plan.get("phases", []):
            for action_text in task_data.get("actions", []):
                task = Task(
                    incident_id=incident_id,
                    title=action_text[:500] if isinstance(action_text, str) else str(action_text)[:500],
                    priority="high" if task_data.get("phase") == "immediate" else "medium",
                    assignee_type="crew",
                    status="pending",
                )
                await fs.create_task(task)
                await stream_manager.broadcast("task_update", {
                    "incident_id": incident_id,
                    "task_id": task.id,
                    "title": task.title,
                    "status": "pending",
                })

    # Create alerts
    alerts_data = adk_result.get("alerts")
    if isinstance(alerts_data, dict):
        for alert_info in alerts_data.get("alerts_sent", []):
            alert = Alert(
                incident_id=incident_id,
                message=alert_info.get("channel", "broadcast") + " alert dispatched",
                severity=alert_info.get("severity", "high"),
                region="Tampa Bay, FL",
                status="draft",
            )
            await fs.create_alert(alert)
            await stream_manager.broadcast("alert_update", {
                "incident_id": incident_id,
                "alert_id": alert.id,
                "severity": alert.severity,
            })

    # Finalize the incident
    severity = "high"
    confidence = 0.0
    if isinstance(plan, dict):
        severity = plan.get("severity", "high")
        confidence = 0.85

    await fs.update_incident(incident_id, {
        "status": "completed",
        "severity": severity,
        "confidence": confidence,
        "final_plan": plan,
    })

    await stream_manager.broadcast("incident_update", {
        "incident_id": incident_id,
        "status": "completed",
        "engine": "adk",
    })


async def cancel_all_workflows() -> None:
    """Cancel all running workflow tasks (called during shutdown)."""
    for iid, task in list(_running_workflows.items()):
        if not task.done():
            task.cancel()
            logger.info("Cancelled workflow for incident %s", iid)
    _running_workflows.clear()
