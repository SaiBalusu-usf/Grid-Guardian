"""GridGuardian FastAPI application -- multi-agent disaster response backend."""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sse_starlette.sse import EventSourceResponse

from backend.config import settings
from backend.services import firestore_service as fs
from backend.services.streaming import stream_manager
from backend.services.auth import (
    bootstrap_admin_key,
    create_api_key,
    require_role,
    validate_api_key,
)
from backend.services.metrics import get_metrics
from backend.services.incident_memory import extract_learnings, get_relevant_learnings
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
# Rate limiter
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    logger.info("GridGuardian starting (mock=%s, sse=%s)", settings.is_mock, settings.is_sse_enabled)
    await bootstrap_admin_key()
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

app.state.limiter = limiter

# CORS -- restrict in production, allow-all in dev
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.add_middleware(SecurityHeadersMiddleware)


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "rate_limit_exceeded", "detail": "Too many requests. Please slow down."},
    )


@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        if request.url.path.startswith("/api/"):
            await validate_api_key(request.headers.get("X-API-Key"))
        response = await call_next(request)
        return response
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    except Exception as exc:
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": "internal_server_error", "detail": "An internal error occurred"},
        )


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class SimulateRequest(BaseModel):
    scenario: str = Field(min_length=1, max_length=2000, description="Disaster scenario description")
    trigger_source: str = Field(default="simulation", max_length=100)


class TaskStatusUpdate(BaseModel):
    status: str = Field(pattern="^(pending|in_progress|completed|cancelled)$")


class AckResponse(BaseModel):
    alert_id: str
    status: str


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
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
@app.post("/api/incidents/simulate", dependencies=[Depends(require_role("operator", "admin"))])
@limiter.limit("20/minute")
async def simulate_incident(body: SimulateRequest, request: Request):
    result = await start_workflow(body.model_dump())
    return result


@app.get("/api/incidents")
async def list_incidents():
    return await fs.list_incidents()


@app.get("/api/incidents/{incident_id}")
async def get_incident(incident_id: str):
    incident = await fs.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return incident.model_dump()


@app.get("/api/incidents/{incident_id}/trace")
async def get_incident_trace(incident_id: str):
    traces = await fs.get_traces(incident_id)
    return [t.model_dump() for t in traces]


@app.post("/api/incidents/{incident_id}/cancel", dependencies=[Depends(require_role("operator", "admin"))])
@limiter.limit("10/minute")
async def cancel_incident(incident_id: str, request: Request):
    incident = await fs.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    await fs.update_incident(incident_id, {"status": "cancelled"})
    await stream_manager.broadcast("incident_update", {
        "incident_id": incident_id,
        "status": "cancelled",
    })
    return {"incident_id": incident_id, "status": "cancelled"}


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------
@app.get("/api/tasks")
async def get_tasks(incident_id: str | None = Query(default=None)):
    tasks = await fs.get_tasks(incident_id)
    return [t.model_dump() for t in tasks]


@app.patch("/api/tasks/{task_id}", dependencies=[Depends(require_role("operator", "admin"))])
async def update_task_status(task_id: str, body: TaskStatusUpdate):
    try:
        task = await fs.update_task(task_id, {"status": body.status})
        await stream_manager.broadcast("task_update", task.model_dump())
        return task.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------
@app.get("/api/alerts")
async def get_alerts(incident_id: str | None = Query(default=None)):
    alerts = await fs.get_alerts(incident_id)
    return [a.model_dump() for a in alerts]


@app.post("/api/alerts/{alert_id}/ack", dependencies=[Depends(require_role("operator", "admin"))])
async def acknowledge_alert(alert_id: str):
    try:
        alert = await fs.acknowledge_alert(alert_id)
        return AckResponse(alert_id=alert.id, status=alert.status)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ---------------------------------------------------------------------------
# Shelters
# ---------------------------------------------------------------------------
@app.get("/api/shelters")
async def get_shelters():
    shelters = await fs.get_shelters()
    return [s.model_dump() for s in shelters]


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.get("/api/dashboard")
async def get_dashboard():
    return await fs.get_dashboard_data()


# ---------------------------------------------------------------------------
# Clear data
# ---------------------------------------------------------------------------
@app.post("/api/clear", dependencies=[Depends(require_role("admin"))])
@limiter.limit("5/hour")
async def clear_data(request: Request):
    await fs.clear_all()
    return {"status": "cleared"}


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
@app.get("/api/metrics")
async def metrics():
    return get_metrics()


# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------
class CreateKeyRequest(BaseModel):
    role: str = Field(default="viewer", pattern="^(viewer|operator|admin)$")
    label: str = Field(default="", max_length=200)


@app.post("/api/keys", dependencies=[Depends(require_role("admin"))])
async def create_key(body: CreateKeyRequest):
    result = await create_api_key(role=body.role, label=body.label)
    return result


# ---------------------------------------------------------------------------
# Learnings (incident memory)
# ---------------------------------------------------------------------------
@app.get("/api/learnings")
async def get_learnings(scenario: str = Query(default=""), limit: int = Query(default=3, ge=1, le=50)):
    return await get_relevant_learnings(scenario=scenario, limit=limit)


# ---------------------------------------------------------------------------
# Incident export
# ---------------------------------------------------------------------------
@app.get("/api/incidents/{incident_id}/export")
async def export_incident(incident_id: str):
    incident = await fs.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    traces = await fs.get_traces(incident_id)
    tasks = await fs.get_tasks(incident_id)
    alerts = await fs.get_alerts(incident_id)
    return {
        "incident": incident.model_dump(),
        "traces": [t.model_dump() for t in traces],
        "tasks": [t.model_dump() for t in tasks],
        "alerts": [a.model_dump() for a in alerts],
    }


# ---------------------------------------------------------------------------
# Shelter check-in
# ---------------------------------------------------------------------------
@app.post("/api/shelters/{shelter_id}/checkin")
async def shelter_checkin(shelter_id: str, count: int = Query(default=1, ge=1, le=500)):
    from backend.tools.firestore_tool import read_document, update_document
    doc = await read_document("shelters", shelter_id)
    if doc is None:
        # Ensure shelters are seeded, then retry
        await fs.get_shelters()
        doc = await read_document("shelters", shelter_id)
        if doc is None:
            raise HTTPException(status_code=404, detail=f"Shelter {shelter_id} not found")
    current_occupancy = doc.get("occupancy", 0)
    capacity = doc.get("capacity", 0)
    new_occupancy = current_occupancy + count
    if new_occupancy > capacity:
        raise HTTPException(
            status_code=400,
            detail=f"Check-in would exceed capacity ({new_occupancy}/{capacity})",
        )
    await update_document("shelters", shelter_id, {"occupancy": new_occupancy})
    await stream_manager.broadcast("incident_update", {
        "event": "shelter_checkin",
        "shelter_id": shelter_id,
        "occupancy": new_occupancy,
        "capacity": capacity,
    })
    return {
        "shelter_id": shelter_id,
        "occupancy": new_occupancy,
        "capacity": capacity,
    }


# ---------------------------------------------------------------------------
# Demo mode
# ---------------------------------------------------------------------------
DEMO_SCENARIOS = [
    "Category 4 hurricane approaching Tampa Bay with 130mph winds and 12ft storm surge expected within 6 hours",
    "Major flooding in downtown Tampa after levee breach on Hillsborough River, 5000 residents at risk",
    "Chemical plant explosion in East Tampa industrial district, toxic plume moving northwest toward residential areas",
]


@app.post("/api/demo/auto", dependencies=[Depends(require_role("operator", "admin"))])
@limiter.limit("2/hour")
async def demo_auto(request: Request):
    import asyncio
    # Clear existing data
    await fs.clear_all()

    results = []
    for scenario_text in DEMO_SCENARIOS:
        result = await start_workflow({
            "scenario": scenario_text,
            "trigger_source": "demo",
        })
        results.append(result)
        # Brief pause between scenarios to spread out processing
        await asyncio.sleep(0.5)

    return {
        "status": "demo_started",
        "scenarios_launched": len(results),
        "incidents": results,
    }


# ---------------------------------------------------------------------------
# SSE Stream
# ---------------------------------------------------------------------------
@app.get("/api/stream")
async def sse_stream(request: Request):
    async def event_generator() -> AsyncGenerator:
        async for event in stream_manager.subscribe():
            if await request.is_disconnected():
                break
            yield event

    return EventSourceResponse(event_generator())
