# GridGuardian v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform GridGuardian from async-function MVP into a production-grade platform with real Google ADK agents, command-center UI, API key auth, incident memory, and auto-demo mode.

**Architecture:** Real ADK LlmAgent/ParallelAgent/LoopAgent/SequentialAgent compose the orchestration. FastAPI serves REST+SSE. Next.js frontend with enhanced command-center UI. Firestore for persistence. Cloud Run deployment.

**Tech Stack:** Google ADK 1.28, Gemini 3.1 Pro, FastAPI, Next.js 14, Tailwind, Leaflet, Firestore, Docker, Cloud Run

---

## File Map

### New Files
- `backend/agents/adk_agents.py` — All ADK agent definitions (LlmAgent, ParallelAgent, LoopAgent, SequentialAgent)
- `backend/agents/adk_tools.py` — FunctionTool wrappers for all tools
- `backend/agents/adk_runner.py` — Runner setup + workflow execution
- `backend/services/auth.py` — API key validation, role checking, key management
- `backend/services/metrics.py` — Agent performance metrics collection
- `backend/services/webhooks.py` — Webhook registration and dispatch
- `backend/services/incident_memory.py` — Incident learnings storage and retrieval
- `backend/models/api_key.py` — API key Pydantic model
- `backend/models/metrics.py` — Metrics Pydantic model
- `frontend/src/app/metrics/page.tsx` — Metrics dashboard page
- `frontend/src/app/compare/page.tsx` — Incident comparison page
- `frontend/src/components/WorkflowProgress.tsx` — Workflow stage progress bar
- `frontend/src/components/AuthGate.tsx` — API key entry modal
- `frontend/src/components/MetricsCharts.tsx` — Bar charts for metrics

### Modified Files
- `backend/main.py` — Add auth middleware, new endpoints, security headers
- `backend/agents/orchestrator.py` — Integrate ADK runner alongside existing fallback
- `backend/workflows/incident_workflow.py` — Use ADK runner when available
- `backend/services/firestore_service.py` — Add metrics, learnings, audit_log, webhooks, api_keys methods
- `backend/services/streaming.py` — Add new event types
- `backend/config.py` — Add new env vars (TWILIO, CENSUS, etc.)
- `backend/tools/notification_tool.py` — Add Twilio SMS
- `backend/requirements.txt` — Add twilio
- `frontend/src/app/dashboard/page.tsx` — Workflow progress, streaming agent output
- `frontend/src/app/map/page.tsx` — Vulnerability heatmap, animated routes
- `frontend/src/app/tasks/page.tsx` — Drag columns with status update
- `frontend/src/app/layout.tsx` — AuthGate wrapper
- `frontend/src/components/Navbar.tsx` — Role badge, metrics link
- `frontend/src/components/AgentStatusCard.tsx` — Streaming output text
- `frontend/src/components/StreamingProvider.tsx` — New event types
- `frontend/src/lib/api.ts` — Auth header, new endpoints
- `frontend/src/lib/types.ts` — New types

---

### Task 1: ADK Tool Wrappers

**Files:**
- Create: `backend/agents/adk_tools.py`

- [ ] **Step 1: Create FunctionTool wrappers for all existing tools**

```python
# backend/agents/adk_tools.py
"""ADK FunctionTool wrappers for all GridGuardian tools."""

from google.adk.tools import FunctionTool

from backend.tools.weather_tool import get_weather
from backend.tools.hazard_tool import get_hazard_zones
from backend.tools.routing_tool import get_routes
from backend.tools.news_tool import get_news_feed
from backend.tools.notification_tool import send_notification
from backend.tools.firestore_tool import write_document, read_document, query_collection


weather_fn_tool = FunctionTool(get_weather)
hazard_fn_tool = FunctionTool(get_hazard_zones)
routing_fn_tool = FunctionTool(get_routes)
news_fn_tool = FunctionTool(get_news_feed)
notification_fn_tool = FunctionTool(send_notification)
firestore_write_tool = FunctionTool(write_document)
firestore_read_tool = FunctionTool(read_document)
firestore_query_tool = FunctionTool(query_collection)

# Grouped by agent
HAZARD_WATCHER_TOOLS = [weather_fn_tool, hazard_fn_tool, news_fn_tool]
ROUTE_PLANNER_TOOLS = [routing_fn_tool]
RESOURCE_TOOLS = [firestore_query_tool]
ALERT_TOOLS = [notification_fn_tool]
```

- [ ] **Step 2: Verify imports work**

Run: `cd "c:/Users/balus/Grid Guardian" && py -c "from backend.agents.adk_tools import HAZARD_WATCHER_TOOLS; print(len(HAZARD_WATCHER_TOOLS), 'tools')"`
Expected: `3 tools`

- [ ] **Step 3: Commit**

```bash
git add backend/agents/adk_tools.py
git commit -m "feat(adk): add FunctionTool wrappers for all tools"
```

---

### Task 2: ADK Agent Definitions

**Files:**
- Create: `backend/agents/adk_agents.py`

- [ ] **Step 1: Define all LlmAgent specialists + composed agents**

```python
# backend/agents/adk_agents.py
"""Real Google ADK agent definitions for GridGuardian v2."""

from google.adk.agents import LlmAgent, ParallelAgent, LoopAgent, SequentialAgent

from backend.agents.adk_tools import (
    HAZARD_WATCHER_TOOLS,
    ROUTE_PLANNER_TOOLS,
    RESOURCE_TOOLS,
    ALERT_TOOLS,
)

MODEL = "gemini-2.5-flash"

# --- Specialist Agents ---

hazard_watcher_agent = LlmAgent(
    name="hazard_watcher",
    model=MODEL,
    instruction=(
        "You are a Hazard Watcher agent for disaster response in Tampa, FL. "
        "Use your tools to analyze current weather conditions, hazard zones, and news feeds. "
        "Produce a JSON report with: severity (low/medium/high/critical), confidence (0-1), "
        "impacted_zones (list), hazards (list), and recommendations (list). "
        "Always call get_weather, get_hazard_zones, and get_news_feed tools."
    ),
    tools=HAZARD_WATCHER_TOOLS,
    output_key="hazard_output",
)

vulnerability_mapper_agent = LlmAgent(
    name="vulnerability_mapper",
    model=MODEL,
    instruction=(
        "You are a Vulnerability Mapper agent for Tampa, FL disaster response. "
        "Analyze vulnerable populations: hospitals, senior living, schools, mobile home parks, "
        "homeless services. Score each area 0-1 by vulnerability. "
        "Produce JSON with: priority_areas (list with name, type, vulnerability_score, population, "
        "special_needs), equity_notes (list of equity concerns), critical_facilities (list)."
    ),
    output_key="vulnerability_output",
)

route_planner_agent = LlmAgent(
    name="route_planner",
    model=MODEL,
    instruction=(
        "You are a Route Planner agent for Tampa, FL emergency evacuation. "
        "Use the routing tool to find safe routes between key locations. "
        "Produce JSON with: safe_routes (list), closures (list), travel_risk (low/medium/high/critical), "
        "alternative_routes (list), estimated_clearance_time."
    ),
    tools=ROUTE_PLANNER_TOOLS,
    output_key="route_output",
)

resource_coordinator_agent = LlmAgent(
    name="resource_coordinator",
    model=MODEL,
    instruction=(
        "You are a Resource Coordinator agent for Tampa, FL disaster response. "
        "Recommend crew deployments, generators, medical teams, supply kits, and batteries. "
        "Produce JSON with: recommendations (list with resource_type, quantity, deploy_to, priority, "
        "rationale), total_crews_needed (int), supply_summary (dict)."
    ),
    output_key="resource_output",
)

# --- Composed Agents ---

parallel_specialists = ParallelAgent(
    name="parallel_specialists",
    sub_agents=[
        hazard_watcher_agent,
        vulnerability_mapper_agent,
        route_planner_agent,
        resource_coordinator_agent,
    ],
)

planner_agent = LlmAgent(
    name="planner",
    model=MODEL,
    instruction=(
        "You are a Planner agent that merges outputs from hazard_watcher, vulnerability_mapper, "
        "route_planner, and resource_coordinator into a unified action plan. "
        "Read the outputs from session state keys: hazard_output, vulnerability_output, "
        "route_output, resource_output. "
        "Produce JSON with: plan_id, status='draft', actions (list), tasks (at least 5), "
        "alerts (en and es for each zone), resource_allocations, confidence (0-1), notes."
    ),
    output_key="plan",
)

audit_agent = LlmAgent(
    name="auditor",
    model=MODEL,
    instruction=(
        "You are an Audit agent that critiques disaster response plans. "
        "Read the plan from session state key 'plan'. Check for: "
        "1) Missing evidence, 2) Unsafe assumptions, 3) Ignored vulnerable populations, "
        "4) Vague alerts, 5) Route contradictions, 6) Resource inadequacy. "
        "Return JSON with: passed (bool), issues (list), corrections (list), severity. "
        "On first review, find real problems. On second review, verify fixes were applied."
    ),
    output_key="audit_result",
)

audit_loop = LoopAgent(
    name="audit_loop",
    sub_agents=[audit_agent],
    max_iterations=2,
)

public_alert_agent = LlmAgent(
    name="public_alert",
    model=MODEL,
    instruction=(
        "You are a Public Alert agent that drafts bilingual emergency alerts. "
        "Read the plan and incident from session state. "
        "For each impacted zone, create alerts in English AND Spanish. "
        "Each alert must be specific, actionable, non-panicking, and include shelter names. "
        "Produce JSON array of alerts with: message, language (en/es), severity, region, target_audience."
    ),
    tools=ALERT_TOOLS,
    output_key="alerts",
)

# --- Full Orchestration Pipeline ---

gridguardian_agent = SequentialAgent(
    name="gridguardian_orchestrator",
    sub_agents=[
        parallel_specialists,
        planner_agent,
        audit_loop,
        public_alert_agent,
    ],
)
```

- [ ] **Step 2: Verify agent composition**

Run: `cd "c:/Users/balus/Grid Guardian" && py -c "from backend.agents.adk_agents import gridguardian_agent; print(gridguardian_agent.name, ':', len(gridguardian_agent.sub_agents), 'stages')"`
Expected: `gridguardian_orchestrator : 4 stages`

- [ ] **Step 3: Commit**

```bash
git add backend/agents/adk_agents.py
git commit -m "feat(adk): define LlmAgent, ParallelAgent, LoopAgent, SequentialAgent"
```

---

### Task 3: ADK Runner Integration

**Files:**
- Create: `backend/agents/adk_runner.py`
- Modify: `backend/workflows/incident_workflow.py`

- [ ] **Step 1: Create ADK runner wrapper**

```python
# backend/agents/adk_runner.py
"""ADK Runner wrapper that executes the full agent pipeline."""

import logging
from datetime import datetime, timezone

from backend.config import settings
from backend.services.streaming import StreamManager

logger = logging.getLogger(__name__)


async def run_adk_workflow(scenario: dict, incident_id: str, stream_manager: StreamManager) -> dict:
    """Run the full GridGuardian workflow using real ADK agents.

    Returns the final incident state dict, or None if ADK is unavailable.
    """
    if not settings.GEMINI_API_KEY:
        logger.warning("No GEMINI_API_KEY — cannot run ADK workflow")
        return None

    try:
        from google.adk.agents import LlmAgent
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from backend.agents.adk_agents import gridguardian_agent

        session_service = InMemorySessionService()
        runner = Runner(
            agent=gridguardian_agent,
            app_name="gridguardian",
            session_service=session_service,
        )

        session = await session_service.create_session(
            app_name="gridguardian",
            user_id="system",
        )

        # Seed session state with scenario context
        session.state["scenario"] = scenario.get("scenario", "")
        session.state["incident_id"] = incident_id
        session.state["location"] = scenario.get("location", "Tampa, FL")
        session.state["trigger_source"] = scenario.get("trigger_source", "simulation")

        await stream_manager.broadcast("workflow_stage", {
            "incident_id": incident_id,
            "stage": "adk_running",
            "message": "ADK SequentialAgent pipeline started",
        })

        # Run the full pipeline
        from google.genai import types
        content = types.Content(
            role="user",
            parts=[types.Part(text=f"Respond to this disaster scenario in Tampa, FL: {scenario.get('scenario', '')}")]
        )

        final_state = {}
        async for event in runner.run_async(
            user_id="system",
            session_id=session.id,
            new_message=content,
        ):
            # Broadcast agent events via SSE
            if hasattr(event, 'author') and event.author:
                await stream_manager.broadcast("agent_output", {
                    "incident_id": incident_id,
                    "agent": event.author,
                    "content": str(event.content) if hasattr(event, 'content') else "",
                })

        # Extract results from session state
        final_state = {
            "hazard_output": session.state.get("hazard_output", {}),
            "vulnerability_output": session.state.get("vulnerability_output", {}),
            "route_output": session.state.get("route_output", {}),
            "resource_output": session.state.get("resource_output", {}),
            "plan": session.state.get("plan", {}),
            "audit_result": session.state.get("audit_result", {}),
            "alerts": session.state.get("alerts", []),
        }

        await stream_manager.broadcast("workflow_stage", {
            "incident_id": incident_id,
            "stage": "adk_complete",
        })

        logger.info("ADK workflow completed for incident %s", incident_id)
        return final_state

    except Exception as exc:
        logger.warning("ADK workflow failed (%s), will use legacy pipeline", exc)
        return None
```

- [ ] **Step 2: Integrate into incident_workflow.py — try ADK first, fallback to legacy**

Add to `backend/workflows/incident_workflow.py` after the incident creation, before calling `run_incident_workflow`:

In `start_workflow()`, replace the `_run()` inner function to try ADK first:

```python
    async def _run() -> None:
        try:
            # Try ADK pipeline first
            from backend.agents.adk_runner import run_adk_workflow
            adk_result = await run_adk_workflow(scenario, incident.id, stream_manager)

            if adk_result is not None:
                # ADK succeeded — persist results using existing firestore service
                from backend.services import firestore_service as fs
                from backend.models.task import Task
                from backend.models.alert import Alert

                plan = adk_result.get("plan", {})
                hazard = adk_result.get("hazard_output", {})

                await fs.update_incident(incident.id, {
                    "status": "executing",
                    "severity": hazard.get("severity", "high"),
                    "confidence": hazard.get("confidence", 0.7),
                    "impacted_zones": hazard.get("impacted_zones", []),
                })

                # Create tasks from plan
                for task_data in (plan.get("tasks", []) if isinstance(plan, dict) else [])[:5]:
                    if isinstance(task_data, dict):
                        task = Task(
                            incident_id=incident.id,
                            title=task_data.get("title", "Task"),
                            priority=task_data.get("priority", "medium"),
                            location=task_data.get("location", ""),
                            assignee_type=task_data.get("assignee_type", "crew"),
                        )
                        await fs.create_task(task)

                # Create alerts
                alerts_data = adk_result.get("alerts", [])
                if isinstance(alerts_data, list):
                    for alert_data in alerts_data[:8]:
                        if isinstance(alert_data, dict):
                            alert = Alert(
                                incident_id=incident.id,
                                message=alert_data.get("message", ""),
                                language=alert_data.get("language", "en"),
                                severity=alert_data.get("severity", "high"),
                                region=alert_data.get("region", ""),
                            )
                            await fs.create_alert(alert)

                await fs.update_incident(incident.id, {
                    "status": "completed",
                    "final_plan": plan if isinstance(plan, dict) else {"raw": str(plan)},
                })

                await stream_manager.broadcast("incident_update", {
                    "incident_id": incident.id,
                    "status": "completed",
                })
                logger.info("ADK workflow completed for %s", incident.id)
                return

            # Fallback to legacy pipeline
            result = await run_incident_workflow(
                scenario={**scenario, "_incident_id": incident.id},
                stream_manager=stream_manager,
            )
            logger.info("Legacy workflow for %s finished: status=%s", result.id, result.status)
        except Exception as exc:
            logger.exception("Workflow for %s crashed: %s", incident.id, exc)
        finally:
            _running_workflows.pop(incident.id, None)
```

- [ ] **Step 3: Test ADK import works**

Run: `cd "c:/Users/balus/Grid Guardian" && py -c "from backend.agents.adk_runner import run_adk_workflow; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/agents/adk_runner.py backend/workflows/incident_workflow.py
git commit -m "feat(adk): integrate ADK runner with legacy fallback"
```

---

### Task 4: Auth Service + Security Headers

**Files:**
- Create: `backend/services/auth.py`
- Create: `backend/models/api_key.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Create API key model**

```python
# backend/models/api_key.py
"""API key model for authentication."""

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


class ApiKey(BaseModel):
    key_id: str = Field(default_factory=lambda: f"ak_{uuid4().hex[:16]}")
    key_hash: str = ""
    role: str = "viewer"  # viewer, operator, admin
    label: str = "Default Key"
    created_at: str = Field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())
    last_used_at: str | None = None
    active: bool = True
```

- [ ] **Step 2: Create auth service**

```python
# backend/services/auth.py
"""API key authentication and role-based access control."""

import hashlib
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader

from backend.tools.firestore_tool import write_document, read_document, query_collection

logger = logging.getLogger(__name__)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# In-memory cache of key_hash -> role (refreshed from Firestore)
_key_cache: dict[str, dict] = {}
_bootstrapped = False


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def bootstrap_admin_key() -> str:
    """Create a default admin key on first boot. Returns the raw key."""
    global _bootstrapped
    if _bootstrapped:
        return ""
    _bootstrapped = True

    existing = await query_collection("api_keys")
    if existing:
        for doc in existing:
            _key_cache[doc["key_hash"]] = doc
        logger.info("Loaded %d API keys from store", len(existing))
        return ""

    raw_key = f"gg_{secrets.token_urlsafe(32)}"
    key_hash = _hash_key(raw_key)
    key_doc = {
        "key_id": f"ak_{secrets.token_hex(8)}",
        "key_hash": key_hash,
        "role": "admin",
        "label": "Bootstrap Admin Key",
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
        "active": True,
    }
    await write_document("api_keys", key_doc["key_id"], key_doc)
    _key_cache[key_hash] = key_doc
    logger.info("=== BOOTSTRAP ADMIN KEY: %s ===", raw_key)
    return raw_key


async def validate_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> dict:
    """Validate API key and return key document with role.

    Returns {"role": "admin|operator|viewer", "key_id": "..."} or raises 401.
    For development: if no keys exist, allow all requests as admin.
    """
    if not _key_cache and not _bootstrapped:
        await bootstrap_admin_key()

    if not api_key:
        # If no keys configured at all, allow as admin (dev mode)
        if not _key_cache:
            return {"role": "admin", "key_id": "dev_mode"}
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    key_hash = _hash_key(api_key)
    doc = _key_cache.get(key_hash)

    if not doc or not doc.get("active", False):
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")

    return {"role": doc["role"], "key_id": doc["key_id"]}


def require_role(*allowed_roles: str):
    """FastAPI dependency that checks the caller has one of the allowed roles."""
    async def checker(auth: dict = Security(validate_api_key)):
        if auth["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{auth['role']}' cannot access this endpoint. Required: {allowed_roles}",
            )
        return auth
    return checker
```

- [ ] **Step 3: Add security headers middleware and auth to main.py**

Add these imports and middleware to `backend/main.py`:

```python
from backend.services.auth import validate_api_key, require_role, bootstrap_admin_key

# In lifespan, after the log line:
admin_key = await bootstrap_admin_key()
if admin_key:
    logger.info("Admin API key created — use it in X-API-Key header")

# Add security headers middleware (after CORS middleware):
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Add auth dependency to write endpoints:
# POST /api/incidents/simulate → add dependencies=[Depends(require_role("operator", "admin"))]
# PATCH /api/tasks/{id} → add dependencies=[Depends(require_role("operator", "admin"))]
# POST /api/alerts/{id}/ack → add dependencies=[Depends(require_role("operator", "admin"))]
# POST /api/clear → add dependencies=[Depends(require_role("admin"))]
# POST /api/incidents/{id}/cancel → add dependencies=[Depends(require_role("operator", "admin"))]

# Add new endpoint:
@app.post("/api/keys")
async def create_api_key(label: str = "New Key", role: str = "viewer", auth: dict = Security(require_role("admin"))):
    """Create a new API key (admin only)."""
    import secrets
    from backend.services.auth import _hash_key, _key_cache
    raw_key = f"gg_{secrets.token_urlsafe(32)}"
    key_hash = _hash_key(raw_key)
    key_doc = {
        "key_id": f"ak_{secrets.token_hex(8)}",
        "key_hash": key_hash,
        "role": role,
        "label": label,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
        "active": True,
    }
    await write_document("api_keys", key_doc["key_id"], key_doc)
    _key_cache[key_hash] = key_doc
    return {"key": raw_key, "key_id": key_doc["key_id"], "role": role}
```

- [ ] **Step 4: Commit**

```bash
git add backend/models/api_key.py backend/services/auth.py backend/main.py
git commit -m "feat: API key auth with roles + security headers"
```

---

### Task 5: Metrics Service + Endpoint

**Files:**
- Create: `backend/services/metrics.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Create metrics service**

```python
# backend/services/metrics.py
"""Agent performance metrics collection and retrieval."""

import time
import logging
from datetime import datetime, timezone

from backend.tools.firestore_tool import write_document, read_document, query_collection

logger = logging.getLogger(__name__)

_start_time = time.monotonic()

# In-memory counters (persisted to Firestore periodically)
_agent_metrics: dict[str, dict] = {}
_tool_metrics: dict[str, dict] = {}


def record_agent_run(agent_name: str, duration_ms: float, tokens: int = 0, error: bool = False):
    """Record an agent execution for metrics."""
    if agent_name not in _agent_metrics:
        _agent_metrics[agent_name] = {"total_runs": 0, "total_ms": 0, "total_tokens": 0, "errors": 0}
    m = _agent_metrics[agent_name]
    m["total_runs"] += 1
    m["total_ms"] += duration_ms
    m["total_tokens"] += tokens
    if error:
        m["errors"] += 1


def record_tool_call(tool_name: str, duration_ms: float):
    """Record a tool call for metrics."""
    if tool_name not in _tool_metrics:
        _tool_metrics[tool_name] = {"calls": 0, "total_ms": 0}
    m = _tool_metrics[tool_name]
    m["calls"] += 1
    m["total_ms"] += duration_ms


async def get_metrics() -> dict:
    """Return aggregated metrics."""
    from backend.tools.firestore_tool import query_collection

    incidents = await query_collection("incidents")
    completed = [i for i in incidents if i.get("status") == "completed"]
    failed = [i for i in incidents if i.get("status") == "failed"]
    active = [i for i in incidents if i.get("status") not in ("completed", "failed", "cancelled")]

    agents = {}
    for name, m in _agent_metrics.items():
        runs = m["total_runs"]
        agents[name] = {
            "total_runs": runs,
            "avg_duration_ms": round(m["total_ms"] / runs) if runs else 0,
            "avg_tokens": round(m["total_tokens"] / runs) if runs else 0,
            "errors": m["errors"],
        }

    tools = {}
    for name, m in _tool_metrics.items():
        calls = m["calls"]
        tools[name] = {
            "calls": calls,
            "avg_ms": round(m["total_ms"] / calls) if calls else 0,
        }

    return {
        "agents": agents,
        "tools": tools,
        "incidents": {
            "total": len(incidents),
            "completed": len(completed),
            "failed": len(failed),
            "active": len(active),
        },
        "uptime_seconds": round(time.monotonic() - _start_time),
        "collected_at": datetime.now(tz=timezone.utc).isoformat(),
    }
```

- [ ] **Step 2: Add metrics endpoint to main.py**

```python
from backend.services.metrics import get_metrics

@app.get("/api/metrics")
async def metrics_endpoint():
    return await get_metrics()
```

- [ ] **Step 3: Commit**

```bash
git add backend/services/metrics.py backend/main.py
git commit -m "feat: agent performance metrics service + endpoint"
```

---

### Task 6: Incident Memory + Export + Demo Mode

**Files:**
- Create: `backend/services/incident_memory.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Create incident memory service**

```python
# backend/services/incident_memory.py
"""Incident memory — stores lessons learned for future planning."""

import logging
from datetime import datetime, timezone

from backend.services.gemini_client import generate_json
from backend.tools.firestore_tool import write_document, query_collection

logger = logging.getLogger(__name__)


async def extract_learnings(incident_id: str, scenario: str, plan: dict, audit_corrections: int) -> dict:
    """After incident completes, extract lessons learned via Gemini."""
    learning = {
        "incident_id": incident_id,
        "scenario_summary": scenario[:200],
        "severity": plan.get("severity", "unknown"),
        "plan_confidence": plan.get("confidence", 0),
        "audit_corrections_count": audit_corrections,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
        "key_lessons": [],
    }

    prompt = f"""Analyze this disaster response and extract 2-3 key lessons learned.
Scenario: {scenario[:300]}
Plan confidence: {plan.get('confidence', 0)}
Audit corrections needed: {audit_corrections}
Actions taken: {len(plan.get('actions', []))}

Return JSON: {{"key_lessons": ["lesson 1", "lesson 2"], "scenario_type": "hurricane|flood|outage|multi_zone"}}"""

    result = await generate_json(prompt, system_instruction="Extract concise operational lessons. Return valid JSON.")
    if result:
        learning["key_lessons"] = result.get("key_lessons", [])
        learning["scenario_type"] = result.get("scenario_type", "unknown")

    await write_document("incident_learnings", incident_id, learning)
    logger.info("Stored %d learnings for incident %s", len(learning["key_lessons"]), incident_id)
    return learning


async def get_relevant_learnings(scenario: str, limit: int = 3) -> list[dict]:
    """Retrieve past learnings relevant to the current scenario."""
    all_learnings = await query_collection("incident_learnings")
    if not all_learnings:
        return []
    # Return most recent learnings (in production, use Gemini to match similarity)
    sorted_learnings = sorted(all_learnings, key=lambda x: x.get("created_at", ""), reverse=True)
    return sorted_learnings[:limit]
```

- [ ] **Step 2: Add export, demo, webhook, shelter checkin, and memory endpoints to main.py**

```python
# Add to backend/main.py:

from backend.services.incident_memory import extract_learnings, get_relevant_learnings

# Incident Export
@app.get("/api/incidents/{incident_id}/export")
async def export_incident(incident_id: str):
    incident = await fs.get_incident(incident_id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    traces = await fs.get_traces(incident_id)
    tasks = await fs.get_tasks(incident_id)
    alerts = await fs.get_alerts(incident_id)
    shelters = await fs.get_shelters()
    return {
        "incident": incident.model_dump(),
        "trace_events": [t.model_dump() for t in traces],
        "tasks": [t.model_dump() for t in tasks],
        "alerts": [a.model_dump() for a in alerts],
        "shelters": [s.model_dump() for s in shelters],
        "metadata": {"exported_at": datetime.now(tz=timezone.utc).isoformat(), "version": "2.0.0"},
    }

# Shelter Check-in
@app.post("/api/shelters/{shelter_id}/checkin")
async def shelter_checkin(shelter_id: str, count: int = 1):
    from backend.tools.firestore_tool import read_document, update_document
    doc = await read_document("shelters", shelter_id)
    if not doc:
        raise HTTPException(404, "Shelter not found")
    new_occ = doc.get("occupancy", 0) + count
    await update_document("shelters", shelter_id, {"occupancy": new_occ})
    await stream_manager.broadcast("shelter_update", {
        "shelter_id": shelter_id, "occupancy": new_occ, "capacity": doc.get("capacity", 0),
    })
    return {"shelter_id": shelter_id, "occupancy": new_occ}

# Auto-Demo Mode
@app.post("/api/demo/auto")
@limiter.limit("2/hour")
async def auto_demo(request: Request):
    import asyncio
    from backend.services import firestore_service as fs
    scenarios = [
        {"scenario": "Hurricane watch near USF campus and Tampa General Hospital. 85mph winds, storm surge warning.", "trigger_source": "demo_auto"},
        {"scenario": "Power grid failure across downtown Tampa. TECO substations offline, hospital generators failing.", "trigger_source": "demo_auto"},
        {"scenario": "Multi-zone emergency: storm surge South Tampa, structural collapse Ybor City, hazmat Port Tampa.", "trigger_source": "demo_auto"},
    ]
    await fs.clear_all()
    await stream_manager.broadcast("demo_stage", {"stage": "started", "total": len(scenarios)})
    results = []
    for i, sc in enumerate(scenarios):
        await stream_manager.broadcast("demo_stage", {"stage": f"scenario_{i+1}", "scenario": sc["scenario"][:60]})
        result = await start_workflow(sc)
        results.append(result)
        await asyncio.sleep(2)  # Brief pause between scenarios
    await stream_manager.broadcast("demo_stage", {"stage": "complete"})
    return {"status": "demo_complete", "incidents": results}

# Past Learnings
@app.get("/api/learnings")
async def get_learnings():
    return await get_relevant_learnings("", limit=10)
```

- [ ] **Step 3: Commit**

```bash
git add backend/services/incident_memory.py backend/main.py
git commit -m "feat: incident memory, export, demo mode, shelter checkin"
```

---

### Task 7: Frontend — Auth Gate + Workflow Progress + New Types

**Files:**
- Create: `frontend/src/components/AuthGate.tsx`
- Create: `frontend/src/components/WorkflowProgress.tsx`
- Modify: `frontend/src/lib/types.ts`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/components/StreamingProvider.tsx`

- [ ] **Step 1: Update types.ts with new types**

Add to `frontend/src/lib/types.ts`:
```typescript
export type WorkflowStage = 'initiated' | 'analyzing' | 'planning' | 'auditing' | 'executing' | 'completed' | 'failed' | 'cancelled';

export interface MetricsData {
  agents: Record<string, { total_runs: number; avg_duration_ms: number; avg_tokens: number; errors: number }>;
  tools: Record<string, { calls: number; avg_ms: number }>;
  incidents: { total: number; completed: number; failed: number; active: number };
  uptime_seconds: number;
}
```

- [ ] **Step 2: Update api.ts with new endpoints and auth header**

Replace the `request` function and add new endpoints:
```typescript
function getApiKey(): string {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('gridguardian_api_key') || '';
  }
  return '';
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const apiKey = getApiKey();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (apiKey) headers['X-API-Key'] = apiKey;

  const res = await fetch(`${BASE}${url}`, { headers, ...options });
  if (res.status === 401) {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('gridguardian_api_key');
      window.dispatchEvent(new Event('auth_required'));
    }
    throw new Error('Authentication required');
  }
  if (!res.ok) {
    const text = await res.text().catch(() => 'Unknown error');
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

// New endpoints:
export async function getMetrics(): Promise<any> { return request('/api/metrics'); }
export async function exportIncident(id: string): Promise<any> { return request(`/api/incidents/${id}/export`); }
export async function startAutoDemo(): Promise<any> { return request('/api/demo/auto', { method: 'POST' }); }
export async function shelterCheckin(id: string, count: number): Promise<any> {
  return request(`/api/shelters/${id}/checkin?count=${count}`, { method: 'POST' });
}
export async function getLearnings(): Promise<any> { return request('/api/learnings'); }
export async function createApiKey(label: string, role: string): Promise<any> {
  return request(`/api/keys?label=${encodeURIComponent(label)}&role=${role}`, { method: 'POST' });
}
```

- [ ] **Step 3: Create AuthGate component**

```tsx
// frontend/src/components/AuthGate.tsx
'use client';

import { useState, useEffect } from 'react';
import { Shield, Key, ArrowRight } from 'lucide-react';

export default function AuthGate({ children }: { children: React.ReactNode }) {
  const [hasKey, setHasKey] = useState(true); // assume true to avoid flash
  const [input, setInput] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const key = localStorage.getItem('gridguardian_api_key');
    setHasKey(!!key);
    const handler = () => setHasKey(false);
    window.addEventListener('auth_required', handler);
    return () => window.removeEventListener('auth_required', handler);
  }, []);

  if (hasKey) return <>{children}</>;

  return (
    <div className="fixed inset-0 bg-slate-950/95 z-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-700/50 bg-slate-800/90 p-8 text-center">
        <div className="flex h-14 w-14 mx-auto items-center justify-center rounded-2xl bg-emerald-500/15 border border-emerald-500/30 mb-4">
          <Shield className="h-7 w-7 text-emerald-400" />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">GridGuardian Access</h2>
        <p className="text-sm text-slate-400 mb-6">Enter your API key to continue. Check server logs for the bootstrap admin key.</p>
        <div className="flex gap-2">
          <input
            type="password"
            value={input}
            onChange={(e) => { setInput(e.target.value); setError(''); }}
            placeholder="gg_..."
            className="flex-1 px-4 py-2.5 rounded-xl bg-slate-900/60 border border-slate-700/50 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-emerald-500/50"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && input.trim()) {
                localStorage.setItem('gridguardian_api_key', input.trim());
                setHasKey(true);
              }
            }}
          />
          <button
            onClick={() => {
              if (!input.trim()) { setError('Key required'); return; }
              localStorage.setItem('gridguardian_api_key', input.trim());
              setHasKey(true);
            }}
            className="px-4 py-2.5 rounded-xl bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-500"
          >
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
        <button
          onClick={() => { localStorage.setItem('gridguardian_api_key', 'dev_skip'); setHasKey(true); }}
          className="mt-4 text-xs text-slate-500 hover:text-slate-300"
        >
          Skip (dev mode)
        </button>
        {error && <p className="mt-2 text-xs text-red-400">{error}</p>}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Create WorkflowProgress component**

```tsx
// frontend/src/components/WorkflowProgress.tsx
'use client';

import { cn } from '@/lib/utils';

const STAGES = ['initiated', 'analyzing', 'planning', 'auditing', 'executing', 'completed'];
const LABELS: Record<string, string> = {
  initiated: 'Trigger', analyzing: 'Analyzing', planning: 'Planning',
  auditing: 'Auditing', executing: 'Executing', completed: 'Complete',
};

export default function WorkflowProgress({ currentStage }: { currentStage: string }) {
  const currentIdx = STAGES.indexOf(currentStage);

  return (
    <div className="flex items-center gap-1 w-full">
      {STAGES.map((stage, i) => {
        const isActive = i === currentIdx;
        const isDone = i < currentIdx;
        const isFuture = i > currentIdx;
        return (
          <div key={stage} className="flex-1 flex flex-col items-center gap-1">
            <div className={cn(
              'h-2 w-full rounded-full transition-all duration-500',
              isDone && 'bg-emerald-500',
              isActive && 'bg-blue-500 animate-pulse',
              isFuture && 'bg-slate-700',
            )} />
            <span className={cn(
              'text-[9px] font-medium',
              isDone && 'text-emerald-400',
              isActive && 'text-blue-400',
              isFuture && 'text-slate-600',
            )}>
              {LABELS[stage] || stage}
            </span>
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 5: Add AuthGate to layout.tsx and new SSE events to StreamingProvider**

In `frontend/src/app/layout.tsx`, wrap children with AuthGate:
```tsx
import AuthGate from '@/components/AuthGate';
// Inside the body:
<StreamingProvider>
  <AuthGate>
    <Navbar />
    {children}
  </AuthGate>
</StreamingProvider>
```

In `StreamingProvider.tsx`, add listeners for new event types:
```typescript
es.addEventListener('workflow_stage', (e) => {
  try { const data = JSON.parse(e.data); setIncident((prev) => prev ? { ...prev, status: data.stage || prev.status } : prev); } catch {}
});
es.addEventListener('agent_output', (e) => {
  try { const data = JSON.parse(e.data); /* store in agents state */ } catch {}
});
es.addEventListener('shelter_update', (e) => {
  try { const data = JSON.parse(e.data); /* could update shelter state */ } catch {}
});
es.addEventListener('demo_stage', (e) => {
  try { const data = JSON.parse(e.data); /* handle demo navigation */ } catch {}
});
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/AuthGate.tsx frontend/src/components/WorkflowProgress.tsx frontend/src/lib/types.ts frontend/src/lib/api.ts frontend/src/components/StreamingProvider.tsx frontend/src/app/layout.tsx
git commit -m "feat: auth gate, workflow progress, new SSE events, API auth headers"
```

---

### Task 8: Metrics Page + Enhanced Dashboard

**Files:**
- Create: `frontend/src/app/metrics/page.tsx`
- Modify: `frontend/src/app/dashboard/page.tsx`
- Modify: `frontend/src/components/Navbar.tsx`

- [ ] **Step 1: Create metrics page**

Create `frontend/src/app/metrics/page.tsx` with bar charts showing agent execution times, tool call counts, and incident stats. Use simple div-based bars (no chart library needed).

- [ ] **Step 2: Add WorkflowProgress to dashboard**

In `frontend/src/app/dashboard/page.tsx`, add `<WorkflowProgress currentStage={incident?.status || 'initiated'} />` between the IncidentBanner and the stats row.

- [ ] **Step 3: Add metrics + compare links to Navbar**

Add `/metrics` and `/compare` nav items to the Navbar.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/metrics/page.tsx frontend/src/app/dashboard/page.tsx frontend/src/components/Navbar.tsx
git commit -m "feat: metrics page + workflow progress on dashboard"
```

---

### Task 9: Enhanced Map + Task Drag + Shelter Checkin

**Files:**
- Modify: `frontend/src/app/map/page.tsx`
- Modify: `frontend/src/app/tasks/page.tsx`
- Modify: `frontend/src/app/shelters/page.tsx`

- [ ] **Step 1: Add animated routes and vulnerability heatmap to map**

In map page, add CSS animation for route dashes and size zone circles by vulnerability score.

- [ ] **Step 2: Add task status update buttons to task board**

Each TaskCard gets a "Advance Status" button that calls `PATCH /api/tasks/{id}`.

- [ ] **Step 3: Add shelter checkin button**

Each shelter card gets a "Check In" button that calls `POST /api/shelters/{id}/checkin`.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/map/page.tsx frontend/src/app/tasks/page.tsx frontend/src/app/shelters/page.tsx
git commit -m "feat: animated map, task status update, shelter checkin"
```

---

### Task 10: Tests + Deploy + README

**Files:**
- Modify: `tests/backend/test_incident_simulation.py`
- Modify: `backend/requirements.txt`
- Modify: `docs/README.md`, `README.md`

- [ ] **Step 1: Run existing tests to verify no regressions**

Run: `cd "c:/Users/balus/Grid Guardian" && py -m pytest tests/backend/ -q -W error::DeprecationWarning`
Expected: 55 passed

- [ ] **Step 2: Add tests for new endpoints**

Add tests for `/api/metrics`, `/api/incidents/{id}/export`, `/api/shelters/{id}/checkin` to `test_incident_simulation.py`.

- [ ] **Step 3: Rebuild and deploy all 3 services to Cloud Run**

```bash
export PATH="$PATH:/c/Users/balus/AppData/Local/Google/Cloud SDK/google-cloud-sdk/bin"
# Backend
cd backend && gcloud builds submit --tag us-central1-docker.pkg.dev/gridguardian-491621/gridguardian/backend:latest --project=gridguardian-491621
gcloud run deploy backend --image us-central1-docker.pkg.dev/gridguardian-491621/gridguardian/backend:latest --region us-central1 --allow-unauthenticated --port 8000 --memory 512Mi --timeout=3600 --set-env-vars="USE_MOCK=false,SHELTER_AGENT_URL=https://shelter-agent-747675777203.us-central1.run.app,GOOGLE_CLOUD_PROJECT=gridguardian-491621,GEMINI_API_KEY=...,LOG_LEVEL=INFO,ALLOWED_ORIGINS=https://frontend-747675777203.us-central1.run.app" --project=gridguardian-491621 --quiet

# Frontend
cd frontend && gcloud builds submit --config=cloudbuild.yaml --project=gridguardian-491621
gcloud run deploy frontend --image us-central1-docker.pkg.dev/gridguardian-491621/gridguardian/frontend:latest --region us-central1 --allow-unauthenticated --port 3000 --memory 256Mi --project=gridguardian-491621 --quiet
```

- [ ] **Step 4: Update README with v2 features**

- [ ] **Step 5: Final commit and push**

```bash
git add -A
git commit -m "feat: GridGuardian v2 — ADK agents, auth, metrics, demo mode, incident memory"
git push origin master
```
