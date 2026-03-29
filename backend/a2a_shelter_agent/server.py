"""FastAPI server for the Shelter Specialist A2A agent."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent_card import get_agent_card
from agent_executor import ShelterAgentExecutor

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-28s  %(levelname)-5s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("shelter_agent.server")

# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------

executor: ShelterAgentExecutor | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    global executor
    executor = ShelterAgentExecutor()
    logger.info("Shelter Specialist A2A agent started")
    yield
    logger.info("Shelter Specialist A2A agent shutting down")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Shelter Specialist A2A Agent",
    description="Analyzes shelter capacity, accessibility, and supply availability for disaster response.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Middleware: request logging
# ---------------------------------------------------------------------------


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    elapsed = round((time.monotonic() - start) * 1000, 1)
    logger.info(
        "%s %s -> %s (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent": "shelter_specialist",
        "version": "1.0.0",
        "protocol": "a2a",
    }


@app.get("/.well-known/agent-card")
async def well_known_agent_card() -> dict[str, Any]:
    """Return the A2A AgentCard via the well-known path."""
    return get_agent_card()


@app.get("/a2a/agent-card")
async def a2a_agent_card() -> dict[str, Any]:
    """Return the A2A AgentCard via the explicit path."""
    return get_agent_card()


@app.post("/a2a/execute")
async def a2a_execute(request: Request) -> JSONResponse:
    """Receive an A2A task, execute it, and return the result."""
    assert executor is not None, "Server not initialized"

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")

    result = await executor.execute(body)

    status_code = 200 if result.get("status") == "completed" else 422
    if result.get("status") == "error":
        status_code = 500

    return JSONResponse(content=result, status_code=status_code)


@app.get("/a2a/tasks/{task_id}")
async def get_task(task_id: str) -> dict[str, Any]:
    """Retrieve a previously-executed task result by ID."""
    assert executor is not None, "Server not initialized"

    task = executor.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return task


# ---------------------------------------------------------------------------
# Entrypoint (for direct execution)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
