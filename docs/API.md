# GridGuardian API Documentation

Base URL: `http://localhost:8000` (local) or your Cloud Run backend URL.

**Authentication:** None required for the MVP. All endpoints are publicly accessible. In production, add Firebase Auth or API key middleware.

---

## Health

### GET /health

Check service health.

**Response:**

```json
{
  "status": "ok",
  "service": "gridguardian-backend",
  "version": "1.0.0",
  "mock_mode": true,
  "shelter_agent_url": "http://localhost:8001"
}
```

---

## Incidents

### POST /api/incidents/simulate

Trigger a new incident simulation. This starts the multi-agent pipeline: weather analysis, infrastructure assessment, shelter coordination, and logistics planning -- all running in parallel. Results stream via SSE.

**Request Body:**

```json
{
  "scenario_type": "hurricane",
  "severity": "high",
  "location": "Austin, TX",
  "description": "Category 3 hurricane with 120mph winds, expected landfall in 6 hours",
  "affected_population": 15000,
  "special_requirements": ["pet_friendly", "medical_staff"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `scenario_type` | string | yes | One of: `hurricane`, `earthquake`, `flood`, `wildfire`, `power_outage`, `winter_storm` |
| `severity` | string | no | `low`, `medium`, `high`, `critical`. Default: `medium` |
| `location` | string | no | Geographic location. Default: `Austin, TX` |
| `description` | string | no | Free-text scenario description |
| `affected_population` | integer | no | Estimated affected population |
| `special_requirements` | string[] | no | Special needs: `pet_friendly`, `medical_staff`, `full_ada` |

**Response (200):**

```json
{
  "incident_id": "INC-A1B2C3D4",
  "status": "active",
  "message": "Incident simulation started with 4 agents"
}
```

### GET /api/incidents

List all incidents.

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter by status: `active`, `resolved`, `archived` |

**Response (200):**

```json
{
  "incidents": [
    {
      "incident_id": "INC-A1B2C3D4",
      "type": "hurricane",
      "severity": "high",
      "status": "active",
      "location": "Austin, TX",
      "description": "Category 3 hurricane...",
      "affected_population": 15000,
      "created_at": "2026-03-28T10:00:00Z",
      "updated_at": "2026-03-28T10:05:00Z",
      "agents_dispatched": ["weather_analyst", "infrastructure_monitor", "shelter_specialist", "logistics_coordinator"]
    }
  ],
  "total": 1
}
```

### GET /api/incidents/{incident_id}

Get full incident details including response plan.

**Response (200):**

```json
{
  "incident_id": "INC-A1B2C3D4",
  "type": "hurricane",
  "severity": "high",
  "status": "active",
  "location": "Austin, TX",
  "description": "Category 3 hurricane...",
  "affected_population": 15000,
  "created_at": "2026-03-28T10:00:00Z",
  "updated_at": "2026-03-28T10:05:00Z",
  "agents_dispatched": ["weather_analyst", "infrastructure_monitor", "shelter_specialist", "logistics_coordinator"],
  "response_plan": {
    "status": "completed",
    "plan_version": 2,
    "sections": {
      "weather_analysis": {
        "agent": "weather_analyst",
        "status": "completed",
        "summary": "Category 3 hurricane, 120mph winds, heavy rainfall",
        "data": { "..." : "..." }
      },
      "infrastructure_status": { "..." : "..." },
      "shelter_analysis": { "..." : "..." },
      "logistics": { "..." : "..." }
    },
    "recommendations": [
      "Evacuate Zone A immediately",
      "Open all shelters to full capacity",
      "Deploy generators to SH-002"
    ]
  },
  "audit_result": {
    "passed": true,
    "score": 92,
    "issues": []
  }
}
```

**Response (404):**

```json
{
  "detail": "Incident INC-NOTFOUND not found"
}
```

### GET /api/incidents/{incident_id}/trace

Get the agent execution trace for an incident.

**Response (200):**

```json
{
  "incident_id": "INC-A1B2C3D4",
  "events": [
    {
      "trace_id": "TRC-001",
      "event_type": "incident_created",
      "agent": "orchestrator",
      "message": "Incident INC-A1B2C3D4 created: hurricane",
      "timestamp": "2026-03-28T10:00:00.000Z",
      "data": {}
    },
    {
      "trace_id": "TRC-002",
      "event_type": "agents_dispatched",
      "agent": "orchestrator",
      "message": "Dispatched 4 agents in parallel",
      "timestamp": "2026-03-28T10:00:00.100Z",
      "data": { "agents": ["weather_analyst", "infrastructure_monitor", "shelter_specialist", "logistics_coordinator"] }
    },
    {
      "trace_id": "TRC-003",
      "event_type": "agent_started",
      "agent": "weather_analyst",
      "message": "Weather analysis started",
      "timestamp": "2026-03-28T10:00:00.150Z",
      "data": {}
    },
    {
      "trace_id": "TRC-004",
      "event_type": "tool_called",
      "agent": "weather_analyst",
      "message": "Called weather_tool with scenario=hurricane",
      "timestamp": "2026-03-28T10:00:00.200Z",
      "data": { "tool": "weather_tool", "input": { "scenario": "hurricane" } }
    },
    {
      "trace_id": "TRC-005",
      "event_type": "agent_completed",
      "agent": "weather_analyst",
      "message": "Weather analysis completed in 245ms",
      "timestamp": "2026-03-28T10:00:00.400Z",
      "data": { "duration_ms": 245 }
    },
    {
      "trace_id": "TRC-006",
      "event_type": "audit_started",
      "agent": "plan_auditor",
      "message": "Auditing response plan (attempt 1/3)",
      "timestamp": "2026-03-28T10:00:01.000Z",
      "data": {}
    },
    {
      "trace_id": "TRC-007",
      "event_type": "audit_failed",
      "agent": "plan_auditor",
      "message": "Audit found 2 issues, revising plan",
      "timestamp": "2026-03-28T10:00:01.500Z",
      "data": { "issues_count": 2, "score": 65 }
    },
    {
      "trace_id": "TRC-008",
      "event_type": "audit_passed",
      "agent": "plan_auditor",
      "message": "Plan passed audit (score: 92)",
      "timestamp": "2026-03-28T10:00:02.000Z",
      "data": { "score": 92 }
    }
  ],
  "total_events": 8
}
```

**Trace Event Types:**

| Event Type | Description |
|------------|-------------|
| `incident_created` | New incident initialized |
| `agents_dispatched` | Parallel agents launched |
| `agent_started` | Individual agent began processing |
| `tool_called` | Agent invoked a tool |
| `tool_result` | Tool returned a result |
| `agent_completed` | Agent finished processing |
| `a2a_request` | A2A call sent to external agent |
| `a2a_response` | A2A response received |
| `audit_started` | Plan audit began |
| `audit_failed` | Audit found issues |
| `audit_passed` | Plan passed audit |
| `plan_revised` | Plan updated based on audit feedback |
| `incident_resolved` | Incident marked as resolved |

---

## SSE Event Stream

### GET /api/incidents/{incident_id}/stream

Server-Sent Events stream for real-time incident updates. The connection stays open and pushes events as they occur.

**Headers:**

```
Accept: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

**Event Format:**

```
event: agent_update
data: {"agent": "weather_analyst", "status": "running", "message": "Analyzing weather conditions..."}

event: tool_call
data: {"agent": "weather_analyst", "tool": "weather_tool", "input": {"scenario": "hurricane"}}

event: agent_complete
data: {"agent": "weather_analyst", "status": "completed", "duration_ms": 245, "summary": "Category 3 hurricane detected"}

event: audit_update
data: {"attempt": 1, "status": "failed", "issues_count": 2, "score": 65}

event: plan_update
data: {"version": 2, "status": "revised", "changes": ["Added overflow routing", "Added generator deployment"]}

event: audit_update
data: {"attempt": 2, "status": "passed", "score": 92}

event: incident_complete
data: {"incident_id": "INC-A1B2C3D4", "status": "completed", "total_time_ms": 3200}
```

**SSE Event Types:**

| Event | Payload | Description |
|-------|---------|-------------|
| `agent_update` | `{agent, status, message}` | Agent status change |
| `tool_call` | `{agent, tool, input}` | Agent called a tool |
| `agent_complete` | `{agent, status, duration_ms, summary}` | Agent finished |
| `audit_update` | `{attempt, status, issues_count, score}` | Audit loop update |
| `plan_update` | `{version, status, changes}` | Plan revised |
| `incident_complete` | `{incident_id, status, total_time_ms}` | Simulation done |
| `error` | `{message, agent}` | Error occurred |

---

## Dashboard

### GET /api/dashboard

Aggregated dashboard statistics.

**Response (200):**

```json
{
  "total_incidents": 5,
  "active_incidents": 1,
  "total_alerts": 12,
  "unacknowledged_alerts": 3,
  "total_tasks": 20,
  "pending_tasks": 5,
  "total_agent_runs": 45,
  "recent_incidents": [ "..." ],
  "recent_alerts": [ "..." ]
}
```

---

## Agents

### GET /api/agents

List all agents and their current status.

**Response (200):**

```json
{
  "agents": [
    {
      "name": "Weather Analyst",
      "agent_id": "weather_analyst",
      "status": "idle",
      "description": "Analyzes weather conditions and forecasts for disaster scenarios",
      "tools": ["weather_tool", "news_tool"],
      "last_run": "2026-03-28T10:05:00Z",
      "runs_today": 3
    },
    {
      "name": "Infrastructure Monitor",
      "agent_id": "infrastructure_monitor",
      "status": "idle",
      "description": "Monitors power grid, roads, bridges, and critical infrastructure",
      "tools": ["hazard_tool", "routing_tool"],
      "last_run": "2026-03-28T10:05:00Z",
      "runs_today": 2
    },
    {
      "name": "Shelter Specialist",
      "agent_id": "shelter_specialist",
      "status": "idle",
      "description": "Analyzes shelter capacity, accessibility, and supply status",
      "tools": [],
      "protocol": "a2a",
      "last_run": "2026-03-28T10:05:00Z",
      "runs_today": 4
    },
    {
      "name": "Logistics Coordinator",
      "agent_id": "logistics_coordinator",
      "status": "idle",
      "description": "Plans evacuation routes, resource allocation, and supply chain",
      "tools": ["routing_tool", "notification_tool", "firestore_tool"],
      "last_run": "2026-03-28T10:05:00Z",
      "runs_today": 2
    },
    {
      "name": "Plan Auditor",
      "agent_id": "plan_auditor",
      "status": "idle",
      "description": "Reviews response plans for completeness, safety, and compliance",
      "tools": [],
      "last_run": "2026-03-28T10:05:00Z",
      "runs_today": 3
    }
  ]
}
```

---

## Alerts

### GET /api/alerts

List alerts.

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `acknowledged` | boolean | Filter: `true` for acknowledged, `false` for unacknowledged |

**Response (200):**

```json
{
  "alerts": [
    {
      "alert_id": "ALR-001",
      "incident_id": "INC-A1B2C3D4",
      "severity": "critical",
      "title": "Shelter SH-002 at capacity",
      "message": "Eastside High School Gymnasium has reached 96% occupancy. Redirect new arrivals.",
      "acknowledged": false,
      "acknowledged_at": null,
      "acknowledged_by": null,
      "created_at": "2026-03-28T10:05:00Z"
    }
  ],
  "total": 1
}
```

### POST /api/alerts/{alert_id}/acknowledge

Acknowledge an alert.

**Request Body:**

```json
{
  "acknowledged_by": "operator_jane"
}
```

**Response (200):**

```json
{
  "alert_id": "ALR-001",
  "acknowledged": true,
  "acknowledged_at": "2026-03-28T10:15:00Z",
  "acknowledged_by": "operator_jane"
}
```

---

## Shelters

### GET /api/shelters

List all shelters with current status.

**Response (200):**

```json
{
  "shelters": [
    {
      "shelter_id": "SH-001",
      "name": "Lincoln Community Center",
      "address": "450 Lincoln Ave",
      "capacity": 500,
      "occupancy": 127,
      "available_capacity": 373,
      "occupancy_pct": 25.4,
      "accessibility": "full_ada",
      "backup_power": true,
      "medical_staff": true,
      "pet_friendly": true,
      "coordinates": { "lat": 30.2672, "lng": -97.7431 },
      "supply_warnings": []
    }
  ],
  "total": 4
}
```

---

## A2A Protocol (Shelter Agent)

The shelter agent runs as a separate service on port 8001.

### GET /a2a/agent-card

Retrieve the A2A agent card describing the agent's capabilities.

**Response (200):**

```json
{
  "name": "Shelter Specialist",
  "description": "Analyzes shelter capacity, accessibility, and supply availability for disaster response coordination.",
  "version": "1.0.0",
  "protocol": "a2a",
  "capabilities": [
    "shelter_capacity_analysis",
    "accessibility_assessment",
    "supply_inventory",
    "evacuation_recommendations"
  ],
  "endpoint": "/a2a/execute",
  "health_endpoint": "/health",
  "input_schema": { "..." : "..." },
  "output_schema": { "..." : "..." }
}
```

### POST /a2a/execute

Execute a shelter analysis task.

**Request Body:**

```json
{
  "task_id": "task-001",
  "message": {
    "role": "user",
    "content": {
      "scenario": "hurricane",
      "accessibility_required": "full_ada",
      "capacity_needed": 500
    }
  }
}
```

**Response (200):**

```json
{
  "task_id": "task-001",
  "status": "completed",
  "agent": "shelter_specialist",
  "result": {
    "shelters": [ "..." ],
    "total_available_capacity": 1061,
    "critical_shelters": [ "..." ],
    "supply_warnings": [ "..." ],
    "recommendations": [ "..." ],
    "accessibility_summary": { "full_ada": 2, "wheelchair": 0, "standard": 0 }
  },
  "metadata": {
    "execution_time_ms": 12.5,
    "query": { "scenario": "hurricane", "accessibility_required": "full_ada", "capacity_needed": 500 },
    "shelters_evaluated": 2
  }
}
```

### GET /a2a/tasks/{task_id}

Retrieve a previously executed task result.

**Response (200):** Same shape as execute response.

**Response (404):**

```json
{
  "detail": "Task task-999 not found"
}
```

---

## Error Response Format

All errors follow this structure:

```json
{
  "detail": "Human-readable error message"
}
```

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad request / validation error |
| 404 | Resource not found |
| 422 | Unprocessable entity (invalid request body) |
| 500 | Internal server error |
