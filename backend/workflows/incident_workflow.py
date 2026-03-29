"""Incident workflow wrapper that ties the orchestrator to the FastAPI lifecycle."""

import asyncio
import logging

from backend.agents.orchestrator import run_incident_workflow
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


async def cancel_all_workflows() -> None:
    """Cancel all running workflow tasks (called during shutdown)."""
    for iid, task in list(_running_workflows.items()):
        if not task.done():
            task.cancel()
            logger.info("Cancelled workflow for incident %s", iid)
    _running_workflows.clear()
