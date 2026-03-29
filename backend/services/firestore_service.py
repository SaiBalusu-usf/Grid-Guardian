"""High-level Firestore service managing all GridGuardian collections."""

import logging
from datetime import datetime

from backend.models.incident import Incident
from backend.models.agent_run import AgentRun
from backend.models.trace import TraceEvent
from backend.models.task import Task
from backend.models.alert import Alert
from backend.models.shelter import Shelter
from backend.tools.firestore_tool import (
    write_document,
    read_document,
    query_collection,
    update_document,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Collection name constants
# ---------------------------------------------------------------------------
COL_INCIDENTS = "incidents"
COL_AGENT_RUNS = "agent_runs"
COL_TRACES = "traces"
COL_TASKS = "tasks"
COL_ALERTS = "alerts"
COL_SHELTERS = "shelters"

# ---------------------------------------------------------------------------
# Seed data for shelters (created on first access)
# ---------------------------------------------------------------------------
_SEED_SHELTERS: list[dict] = [
    {
        "shelter_id": "shelter-001",
        "name": "Tampa Convention Center",
        "capacity": 500,
        "occupancy": 0,
        "accessibility": "full_ada",
        "supplies": {"water_gallons": 800, "cots": 350, "first_aid_kits": 75, "blankets": 400},
    },
    {
        "shelter_id": "shelter-002",
        "name": "Hillsborough High School Gymnasium",
        "capacity": 300,
        "occupancy": 0,
        "accessibility": "wheelchair",
        "supplies": {"water_gallons": 500, "cots": 150, "first_aid_kits": 20, "blankets": 180},
    },
    {
        "shelter_id": "shelter-003",
        "name": "Idlewild Baptist Church",
        "capacity": 200,
        "occupancy": 0,
        "accessibility": "standard",
        "supplies": {"water_gallons": 400, "cots": 180, "first_aid_kits": 40, "blankets": 200},
    },
    {
        "shelter_id": "shelter-004",
        "name": "Florida State Fairgrounds",
        "capacity": 1000,
        "occupancy": 0,
        "accessibility": "full_ada",
        "supplies": {"water_gallons": 1500, "cots": 800, "first_aid_kits": 100, "blankets": 900},
    },
]

_shelters_seeded = False


# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------

async def create_incident(incident: Incident) -> Incident:
    """Persist a new incident."""
    data = incident.model_dump()
    await write_document(COL_INCIDENTS, incident.id, data)
    logger.info("Created incident %s", incident.id)
    return incident


async def update_incident(incident_id: str, updates: dict) -> Incident:
    """Update fields on an existing incident and return the refreshed model."""
    await update_document(COL_INCIDENTS, incident_id, updates)
    doc = await read_document(COL_INCIDENTS, incident_id)
    if doc is None:
        raise ValueError(f"Incident {incident_id} not found after update")
    logger.info("Updated incident %s: %s", incident_id, list(updates.keys()))
    return Incident(**doc)


async def get_incident(incident_id: str) -> Incident | None:
    """Retrieve a single incident by ID."""
    doc = await read_document(COL_INCIDENTS, incident_id)
    if doc is None:
        return None
    return Incident(**doc)


async def list_incidents() -> list[dict]:
    """List all incidents, most recent first."""
    docs = await query_collection(COL_INCIDENTS)
    incidents = sorted(docs, key=lambda x: x.get("started_at", ""), reverse=True)
    return incidents


# ---------------------------------------------------------------------------
# Agent runs
# ---------------------------------------------------------------------------

async def log_agent_run(run: AgentRun) -> AgentRun:
    """Persist an agent run record."""
    data = run.model_dump()
    await write_document(COL_AGENT_RUNS, run.id, data)
    logger.debug("Logged agent run %s (%s)", run.id, run.agent_name)
    return run


# ---------------------------------------------------------------------------
# Trace events
# ---------------------------------------------------------------------------

async def add_trace(event: TraceEvent) -> TraceEvent:
    """Persist a trace event."""
    data = event.model_dump()
    await write_document(COL_TRACES, event.id, data)
    logger.debug("Trace %s: %s", event.event_type, event.id)
    return event


async def get_traces(incident_id: str) -> list[TraceEvent]:
    """Retrieve all trace events for an incident, sorted by timestamp."""
    docs = await query_collection(COL_TRACES, {"incident_id": incident_id})
    events = [TraceEvent(**d) for d in docs]
    events.sort(key=lambda e: e.timestamp)
    return events


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

async def create_task(task: Task) -> Task:
    """Persist a new task."""
    data = task.model_dump()
    await write_document(COL_TASKS, task.id, data)
    logger.info("Created task %s: %s", task.id, task.title)
    return task


async def get_tasks(incident_id: str | None = None) -> list[Task]:
    """Retrieve tasks, optionally filtered by incident."""
    filters = {}
    if incident_id:
        filters["incident_id"] = incident_id
    docs = await query_collection(COL_TASKS, filters)
    return [Task(**d) for d in docs]


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

async def create_alert(alert: Alert) -> Alert:
    """Persist a new alert."""
    data = alert.model_dump()
    await write_document(COL_ALERTS, alert.id, data)
    logger.info("Created alert %s (lang=%s)", alert.id, alert.language)
    return alert


async def get_alerts(incident_id: str | None = None) -> list[Alert]:
    """Retrieve alerts, optionally filtered by incident."""
    filters = {}
    if incident_id:
        filters["incident_id"] = incident_id
    docs = await query_collection(COL_ALERTS, filters)
    return [Alert(**d) for d in docs]


async def acknowledge_alert(alert_id: str) -> Alert:
    """Mark an alert as acknowledged."""
    updates = {
        "status": "acknowledged",
        "sent_at": datetime.utcnow().isoformat(),
    }
    await update_document(COL_ALERTS, alert_id, updates)
    doc = await read_document(COL_ALERTS, alert_id)
    if doc is None:
        raise ValueError(f"Alert {alert_id} not found after acknowledgement")
    return Alert(**doc)


# ---------------------------------------------------------------------------
# Shelters
# ---------------------------------------------------------------------------

async def _ensure_shelters_seeded() -> None:
    """Seed default shelters if they don't exist yet."""
    global _shelters_seeded
    if _shelters_seeded:
        return
    existing = await query_collection(COL_SHELTERS)
    if not existing:
        for s in _SEED_SHELTERS:
            await write_document(COL_SHELTERS, s["shelter_id"], s)
        logger.info("Seeded %d default shelters", len(_SEED_SHELTERS))
    _shelters_seeded = True


async def get_shelters() -> list[Shelter]:
    """Retrieve all shelters."""
    await _ensure_shelters_seeded()
    docs = await query_collection(COL_SHELTERS)
    return [Shelter(**d) for d in docs]


# ---------------------------------------------------------------------------
# Dashboard aggregate
# ---------------------------------------------------------------------------

async def get_dashboard_data() -> dict:
    """Return aggregated dashboard statistics."""
    incidents = await query_collection(COL_INCIDENTS)
    tasks = await query_collection(COL_TASKS)
    alerts = await query_collection(COL_ALERTS)
    shelters = await get_shelters()

    active_incidents = [i for i in incidents if i.get("status") not in ("completed", "failed")]
    completed_incidents = [i for i in incidents if i.get("status") == "completed"]
    pending_tasks = [t for t in tasks if t.get("status") == "pending"]
    in_progress_tasks = [t for t in tasks if t.get("status") == "in_progress"]
    unacked_alerts = [a for a in alerts if a.get("status") != "acknowledged"]
    total_shelter_capacity = sum(s.capacity for s in shelters)
    total_shelter_occupancy = sum(s.occupancy for s in shelters)

    return {
        "active_incidents": len(active_incidents),
        "total_tasks": len(tasks),
        "pending_tasks": len(pending_tasks),
        "active_alerts": len(unacked_alerts),
        "shelter_capacity": total_shelter_capacity,
        "shelter_occupancy": total_shelter_occupancy,
        "recent_incidents": [
            {
                "id": i.get("id"),
                "scenario": i.get("scenario"),
                "severity": i.get("severity", "unknown"),
                "confidence": i.get("confidence", 0),
                "status": i.get("status"),
                "started_at": i.get("started_at"),
                "trigger_source": i.get("trigger_source", ""),
                "impacted_zones": i.get("impacted_zones", []),
                "final_plan": i.get("final_plan"),
            }
            for i in sorted(incidents, key=lambda x: x.get("started_at", ""), reverse=True)[:10]
        ],
    }


# ---------------------------------------------------------------------------
# Clear all data
# ---------------------------------------------------------------------------

async def clear_all() -> None:
    """Clear all simulation data from all collections."""
    from backend.tools.firestore_tool import _in_memory_store, _get_client

    client = _get_client()
    if client is not None:
        for col_name in [COL_INCIDENTS, COL_AGENT_RUNS, COL_TRACES, COL_TASKS, COL_ALERTS, COL_SHELTERS]:
            docs = client.collection(col_name).stream()
            for doc in docs:
                doc.reference.delete()
        logger.info("Cleared all Firestore collections")
    else:
        _in_memory_store.clear()
        logger.info("Cleared in-memory store")

    global _shelters_seeded
    _shelters_seeded = False
