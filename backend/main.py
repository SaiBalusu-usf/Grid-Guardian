"""GridGuardian FastAPI application -- multi-agent disaster response backend."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from backend.config import settings
from backend.services import firestore_service as fs
from backend.services.streaming import stream_manager
from backend.workflows.incident_workflow import start_workflow, cancel_all_workflows

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("gridguardian")


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan: startup and shutdown hooks."""
    logger.info("GridGuardian starting (mock=%s, sse=%s)", settings.is_mock, settings.is_sse_enabled)
    yield
    logger.info("GridGuardian shutting down, cancelling active workflows")
    await cancel_all_workflows()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="GridGuardian",
    description="Multi-agent disaster response orchestration API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS -- allow all for dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Error handling middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    """Catch unhandled exceptions and return structured JSON errors."""
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": "internal_server_error", "detail": str(exc)},
        )


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class SimulateRequest(BaseModel):
    scenario: str
    trigger_source: str = "simulation"


class AckResponse(BaseModel):
    alert_id: str
    status: str


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "gridguardian-backend",
        "version": "1.0.0",
        "mock_mode": settings.is_mock,
        "shelter_agent_url": settings.SHELTER_AGENT_URL,
    }


# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------
@app.post("/api/incidents/simulate")
async def simulate_incident(body: SimulateRequest):
    """Start a new incident simulation workflow.

    Returns immediately with the incident stub; the workflow runs in the background.
    """
    result = await start_workflow(body.model_dump())
    return result


@app.get("/api/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """Retrieve a single incident by ID."""
    incident = await fs.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return incident.model_dump()


@app.get("/api/incidents/{incident_id}/trace")
async def get_incident_trace(incident_id: str):
    """Retrieve all trace events for an incident, sorted by timestamp."""
    traces = await fs.get_traces(incident_id)
    return [t.model_dump() for t in traces]


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------
@app.get("/api/tasks")
async def get_tasks(incident_id: str | None = Query(default=None)):
    """Retrieve tasks, optionally filtered by incident_id."""
    tasks = await fs.get_tasks(incident_id)
    return [t.model_dump() for t in tasks]


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------
@app.get("/api/alerts")
async def get_alerts(incident_id: str | None = Query(default=None)):
    """Retrieve alerts, optionally filtered by incident_id."""
    alerts = await fs.get_alerts(incident_id)
    return [a.model_dump() for a in alerts]


@app.post("/api/alerts/{alert_id}/ack")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert."""
    try:
        alert = await fs.acknowledge_alert(alert_id)
        return AckResponse(alert_id=alert.id, status=alert.status)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.get("/api/dashboard")
async def get_dashboard():
    """Aggregated dashboard statistics."""
    return await fs.get_dashboard_data()


# ---------------------------------------------------------------------------
# Shelters
# ---------------------------------------------------------------------------
@app.get("/api/shelters")
async def get_shelters():
    """Retrieve all shelters."""
    shelters = await fs.get_shelters()
    return [s.model_dump() for s in shelters]


# ---------------------------------------------------------------------------
# Incidents list
# ---------------------------------------------------------------------------
@app.get("/api/incidents")
async def list_incidents():
    """List all incidents (most recent first)."""
    return await fs.list_incidents()


# ---------------------------------------------------------------------------
# Clear data
# ---------------------------------------------------------------------------
@app.post("/api/clear")
async def clear_data():
    """Clear all simulation data (incidents, tasks, alerts, traces)."""
    await fs.clear_all()
    return {"status": "cleared"}


# ---------------------------------------------------------------------------
# SSE Stream
# ---------------------------------------------------------------------------
@app.get("/api/stream")
async def sse_stream(request: Request):
    """Server-sent events endpoint for real-time updates."""

    async def event_generator() -> AsyncGenerator:
        async for event in stream_manager.subscribe():
            if await request.is_disconnected():
                break
            yield event

    return EventSourceResponse(event_generator())
