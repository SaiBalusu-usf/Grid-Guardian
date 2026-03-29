# GridGuardian v2 — Next Generation Design Spec

**Date:** 2026-03-29
**Timeline:** 6 hours
**Target Audience:** Hackathon judges, technical reviewers, emergency management professionals
**Location:** Tampa, FL
**GCP Project:** gridguardian-491621

---

## Overview

GridGuardian v2 transforms the MVP from a working demo into a production-grade, competition-winning multi-agent disaster response platform. The upgrade touches every layer: real Google ADK agents, command-center UI, authentication, smarter data integrations, and demo polish.

## Non-Goals (6-hour scope)

- OAuth/OIDC/JWT user accounts
- FEMA IPAWS or Red Cross API integration
- Mobile native app
- Multi-tenancy (multiple organizations)
- Internationalization beyond EN/ES

---

## Phase 1: Real Google ADK Agents

**Goal:** Replace async function wrappers with real ADK primitives.

### Architecture

```
SequentialAgent (orchestrator)
  ├── Step 1: Create incident + trigger trace
  ├── Step 2: ParallelAgent
  │     ├── LlmAgent: hazard_watcher (tools: weather, hazard, news)
  │     ├── LlmAgent: vulnerability_mapper (tools: census_data)
  │     ├── LlmAgent: route_planner (tools: routing)
  │     └── LlmAgent: resource_coordinator (tools: resource_db)
  ├── Step 3: LlmAgent: planner (merges parallel outputs)
  ├── Step 4: LoopAgent (max_iterations=2)
  │     └── LlmAgent: auditor (critiques plan, returns pass/fail)
  ├── Step 5: A2A call to shelter specialist
  ├── Step 6: LlmAgent: public_alert (bilingual Gemini alerts)
  └── Step 7: Execute actions (create tasks, alerts, finalize)
```

### Agent Definitions

Each LlmAgent gets:
- `model`: gemini-3.1-pro-preview
- `instruction`: System prompt defining role, output format, constraints
- `tools`: List of `FunctionTool` instances wrapping existing tool functions
- `output_key`: Where the agent writes its result in session state

### Shared State

ADK `session.state` dictionary replaces manual dict passing:
- `state["incident"]` — Current incident object
- `state["hazard_output"]` — Hazard watcher results
- `state["vulnerability_output"]` — Vulnerability mapper results
- `state["route_output"]` — Route planner results
- `state["resource_output"]` — Resource coordinator results
- `state["plan"]` — Draft/final action plan
- `state["audit_result"]` — Latest audit pass/fail
- `state["shelter_data"]` — A2A shelter response
- `state["alerts"]` — Generated public alerts

### Tool Definitions

Each existing tool function becomes an ADK `FunctionTool`:
- `weather_tool` → `FunctionTool(get_weather)` with schema
- `hazard_tool` → `FunctionTool(get_hazard_zones)` with schema
- `routing_tool` → `FunctionTool(get_routes)` with schema
- `news_tool` → `FunctionTool(get_news_feed)` with schema
- `firestore_tool` → `FunctionTool(write_document)`, `FunctionTool(read_document)`
- `notification_tool` → `FunctionTool(send_notification)`

### Trace Integration

ADK provides built-in tracing. We hook into it to:
- Write trace events to Firestore (as before)
- Broadcast via SSE (as before)
- But now traces include Gemini token counts, tool call details, and agent reasoning

### Fallback

If ADK/Gemini is unavailable, the system falls back to the existing async function pipeline. The orchestrator detects this and switches mode.

---

## Phase 2: Command Center UI

**Goal:** Transform the dashboard into an impressive operations command center.

### New/Enhanced Pages

#### Dashboard Enhancements
- **Workflow stage indicator** — Horizontal progress bar: Trigger → Analyzing → Planning → Auditing → Executing → Complete. Each stage lights up in real-time via SSE.
- **Agent cards with streaming output** — When an agent is running, its card shows a live text feed of what it's doing (tool calls, reasoning snippets). Uses SSE `agent_output` events.
- **Stats with sparklines** — Small inline charts on stat cards showing trend over recent incidents.

#### Map Enhancements
- **Vulnerability heatmap** — Colored overlay circles sized by vulnerability score from mapper agent.
- **Animated evacuation routes** — Dashed line animation showing direction of travel.
- **Shelter occupancy badges** — Live occupancy % shown on shelter markers, color-coded.
- **Click interaction** — Click any marker for a detail popup with action buttons.

#### New: Metrics Page (`/metrics`)
- Agent execution time bar chart (per agent, per incident)
- Tool call frequency chart
- Gemini token usage chart
- Incident count over time

#### Task Board Enhancement
- **Drag-and-drop columns** — Pending | In Progress | Completed | Cancelled
- Each card has a quick-action button to advance status
- Color-coded by priority

#### Incident Comparison (`/compare`)
- Select two incidents side by side
- Compare: severity, confidence, zones, task count, alert count, agent timings
- Highlights differences

### SSE Event Additions
- `agent_output` — Streaming text from agent reasoning
- `workflow_stage` — Current stage of the pipeline
- `shelter_update` — Real-time shelter occupancy changes
- `metric_update` — Agent performance data

---

## Phase 3: Production Security & Auth

**Goal:** API key auth with role-based access control.

### API Key System

#### Firestore Collection: `api_keys`
```
{
  key_id: "ak_...",
  key_hash: "sha256:...",   // Never store plaintext
  role: "admin" | "operator" | "viewer",
  label: "Demo Key",
  created_at: "...",
  last_used_at: "...",
  active: true
}
```

#### Roles & Permissions
| Endpoint | viewer | operator | admin |
|----------|:---:|:---:|:---:|
| GET /health | yes | yes | yes |
| GET /api/* (read) | yes | yes | yes |
| POST /api/incidents/simulate | no | yes | yes |
| PATCH /api/tasks/{id} | no | yes | yes |
| POST /api/alerts/{id}/ack | no | yes | yes |
| POST /api/clear | no | no | yes |
| POST /api/keys | no | no | yes |
| GET /api/metrics | yes | yes | yes |

#### Implementation
- `X-API-Key` header on every request (except `/health`)
- FastAPI dependency `get_current_role()` validates key, returns role
- Unauthorized → 401, insufficient role → 403
- Default seed: one admin key printed to logs on first boot

#### Frontend
- On first visit, prompt for API key (simple modal)
- Store in localStorage
- Include in all fetch() calls as header
- Show current role in Navbar

### Audit Log

Firestore collection `audit_log`:
```
{
  timestamp: "...",
  key_id: "ak_...",
  role: "operator",
  method: "POST",
  path: "/api/incidents/simulate",
  status_code: 200,
  ip: "...",
  duration_ms: 1234
}
```

### Security Headers

Middleware adds to all responses:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Strict-Transport-Security: max-age=31536000`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

---

## Phase 4: Smarter Data & Agent Intelligence

**Goal:** Agents that learn, adapt, and connect to richer data.

### Incident Memory

Firestore collection `incident_learnings`:
```
{
  incident_id: "...",
  scenario_type: "hurricane",  // classified by Gemini
  severity: "critical",
  key_lessons: ["...", "..."],  // Gemini-extracted
  plan_confidence: 0.92,
  audit_corrections_count: 1,
  created_at: "..."
}
```

After each incident completes, Gemini summarizes key lessons. The planner agent queries past learnings for similar scenarios and incorporates them.

### Dynamic Severity Escalation

During active incidents, a background task polls NWS every 60s. If new severe alerts appear for the Tampa area:
1. Re-run hazard watcher with fresh data
2. Compare new severity to current
3. If escalated, broadcast `severity_escalation` SSE event
4. Dashboard shows alert banner: "Severity escalated from HIGH to CRITICAL"

### Shelter Check-In

New endpoint: `POST /api/shelters/{id}/checkin`
- Body: `{"count": 5}` (number of evacuees)
- Updates shelter occupancy in Firestore
- Broadcasts `shelter_update` via SSE
- Map and shelter panel update in real-time
- Demo script: automated check-ins during simulation

### SMS Alert (Twilio)

One real SMS per incident (to a configured demo number):
- Add `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`, `DEMO_PHONE_NUMBER` env vars
- Notification tool checks if Twilio is configured, sends one SMS for the first critical alert
- Falls back to mock for all other alerts
- Trace shows "sms_sent" event

### Census Data

Replace hardcoded `_VULNERABLE_AREAS` with real data:
- US Census ACS API (free, key from census.gov)
- Query Hillsborough County tracts for: total_population, median_age, poverty_rate, disability_rate
- Vulnerability mapper scores tracts using census data + scenario type
- Add `CENSUS_API_KEY` env var

---

## Phase 5: Observability & Demo Polish

**Goal:** Production-grade observability and a flawless demo experience.

### Structured Logging

Replace `logging.basicConfig` with:
```python
{
  "timestamp": "2026-03-29T10:00:00Z",
  "level": "INFO",
  "service": "gridguardian",
  "agent": "hazard_watcher",
  "incident_id": "abc-123",
  "duration_ms": 450,
  "message": "Hazard analysis complete",
  "tool_calls": 3,
  "gemini_tokens": 1200
}
```

### Metrics Endpoint

`GET /api/metrics` returns:
```json
{
  "agents": {
    "hazard_watcher": {"avg_duration_ms": 3200, "total_runs": 15, "avg_tokens": 800},
    ...
  },
  "incidents": {"total": 12, "completed": 10, "failed": 1, "active": 1},
  "tools": {"weather": {"calls": 30, "avg_ms": 450}, ...},
  "uptime_seconds": 3600
}
```

Stored in Firestore `metrics` collection, updated after each agent run.

### Error Recovery

When an agent fails mid-workflow:
1. Incident status set to `"error_recoverable"`
2. Dashboard shows which agent failed with error message
3. "Retry Agent" button calls `POST /api/incidents/{id}/retry?agent=hazard_watcher`
4. Orchestrator re-runs just that agent, then continues the pipeline

### Auto-Demo Mode

`POST /api/demo/auto` triggers:
1. Clear all data
2. Run Scenario 1 (Hurricane) — wait for completion
3. Run Scenario 2 (Grid Outage) — wait for completion
4. Run Scenario 3 (Multi-Zone) — wait for completion
5. Each scenario broadcasts `demo_stage` SSE events
6. Frontend auto-navigates: Landing → Dashboard → Map → Trace → Alerts → Tasks

### Incident Export

`GET /api/incidents/{id}/export` returns complete JSON:
```json
{
  "incident": {...},
  "trace_events": [...],
  "tasks": [...],
  "alerts": [...],
  "agent_runs": [...],
  "shelters_used": [...],
  "plan": {...},
  "metadata": {"exported_at": "...", "version": "2.0.0"}
}
```

### Webhook Support

Firestore collection `webhooks`:
```
{
  url: "https://example.com/hook",
  events: ["incident_completed", "severity_escalation"],
  active: true,
  created_at: "..."
}
```

`POST /api/webhooks` to register. On matching event, POST the payload to the URL with HMAC signature header.

---

## Implementation Priority (6-hour budget)

| Phase | Time | Priority |
|-------|------|----------|
| Phase 1: Real ADK Agents | 2 hours | Critical (judges check this) |
| Phase 2: Command Center UI | 1.5 hours | Critical (visual impact) |
| Phase 3: Auth & Security | 45 min | High (production credibility) |
| Phase 4: Smart Data | 1 hour | High (differentiator) |
| Phase 5: Demo Polish | 45 min | High (demo flow) |

---

## Success Criteria

1. All agents are real ADK `LlmAgent` instances with Gemini 3.1 Pro
2. ParallelAgent and LoopAgent used natively (not simulated)
3. Dashboard shows live agent streaming output
4. API key auth works with 3 roles
5. At least one real SMS sends during demo
6. Incident memory influences planning
7. Auto-demo mode runs all 3 scenarios hands-free
8. 55+ tests passing, 0 warnings
9. All deployed to Cloud Run with public URLs
10. README updated with v2 features
