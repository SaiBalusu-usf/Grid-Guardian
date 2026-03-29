# GridGuardian Demo Script

**Target: 2-minute judge demo**

Timing: 30s introduction | 60s live demo | 30s architecture walkthrough

---

## Setup Before Demo

1. Ensure all services are running: `bash scripts/run-local.sh`
2. Open browser to `http://localhost:3000`
3. Have the architecture diagram ready (docs/architecture.md or a slide)
4. Keep the terminal visible in a second monitor/tab for backup

---

## Part 1: Introduction (0:00 - 0:30)

**Open the dashboard. Start talking immediately.**

> "GridGuardian is a multi-agent disaster response system. When a hurricane or earthquake strikes, emergency coordinators need answers in minutes, not hours -- which shelters have capacity, which roads are passable, what resources to deploy."

> "We solve this with four specialized AI agents that work in parallel, coordinated by Google ADK, with a built-in audit loop that catches gaps before the plan goes live."

**Key talking points:**
- Multi-agent (not single-agent) -- real disasters need specialization
- Parallel execution -- all agents work simultaneously
- Audit loop -- plans are reviewed for safety before being finalized
- A2A protocol -- the shelter agent is an independent service

---

## Part 2: Live Demo (0:30 - 1:30)

### Step 1: Trigger a Simulation (0:30 - 0:45)

**Click the "Simulate Incident" button on the dashboard.**

> "Let me simulate a Category 3 hurricane hitting Austin. I'm setting severity to high, with 15,000 affected people."

**Select:**
- Scenario: Hurricane
- Severity: High
- Location: Austin, TX

**Click "Start Simulation."**

> "Watch the agent cards light up -- all four agents just launched in parallel."

### Step 2: Watch Agents Work (0:45 - 1:00)

**Point to the agent status cards as they update.**

> "The Weather Analyst is pulling storm data -- 120mph winds, 8 inches of rain expected. The Infrastructure Monitor found three power outages and two road closures. The Shelter Specialist -- which is actually a separate A2A agent running on its own service -- just analyzed four shelters and found that Eastside High School is at 96% capacity."

> "And the Logistics Coordinator is computing evacuation routes, avoiding the hazards the infrastructure agent just found."

**If agents are still running, point to the trace viewer:**

> "Every tool call and agent decision is logged here in real time -- full observability."

### Step 3: Show the Audit Loop (1:00 - 1:15)

**Scroll to the audit section or click the trace tab.**

> "Now here is the key innovation. The plan doesn't go straight to the coordinator. Our audit agent reviews it first."

> "On the first pass, it flagged that no overflow plan was provided for the near-capacity shelter, and no generators were assigned. So the system automatically revised the plan and re-audited."

> "Second pass: score 92, approved. The coordinator gets a plan that's been quality-checked."

### Step 4: Show the Results (1:15 - 1:30)

**Show the completed response plan with recommendations.**

> "The final plan includes specific shelter assignments, evacuation routes with real-time road status, resource deployment orders, and supply warnings. All generated in about 3 seconds with four agents working in parallel."

**Scroll through recommendations briefly. Point to the map if available.**

---

## Part 3: Architecture (1:30 - 2:00)

**Switch to the architecture diagram or keep the trace viewer visible.**

> "Under the hood: FastAPI backend orchestrating Google ADK agents. Each agent has specialized tools -- weather APIs, hazard databases, routing engines. The shelter agent demonstrates the A2A protocol, running as a fully independent microservice."

> "Everything streams to the frontend via Server-Sent Events, and all traces are persisted to Firestore for post-incident review."

> "The audit loop runs up to two revision cycles, ensuring every plan meets minimum safety thresholds before reaching the coordinator."

**Final statement:**

> "GridGuardian shows how multiple AI agents, working in parallel with real-time coordination and built-in quality checks, can turn minutes of chaos into a structured response plan."

---

## Fallback Plans

### If the frontend doesn't load:
- Open `http://localhost:8000/docs` to show the FastAPI Swagger UI
- Trigger simulation via Swagger: `POST /api/incidents/simulate`
- Show the JSON response and trace data directly

### If the backend crashes:
- Restart with `bash scripts/run-local.sh`
- While waiting, show the architecture diagram and explain the design
- The shelter agent is independent -- open `http://localhost:8001/a2a/agent-card` to demo A2A

### If the agents are slow:
- Use `USE_MOCK=true` (default) which returns instantly
- Talk through the trace viewer while waiting
- Emphasize that mock mode is for demos; production connects to real APIs

### If everything fails:
- Show the test suite: `pytest tests/backend/ -v` (runs in ~2s, all mock)
- Walk through `tests/backend/test_a2a_handshake.py` to show A2A protocol
- Show the code architecture and explain design decisions

---

## Key Phrases to Use

- "Parallel agent execution" -- emphasize speed
- "Audit loop" -- emphasize quality and safety
- "A2A protocol" -- emphasize interoperability
- "Real-time streaming" -- emphasize user experience
- "Zero external dependencies in mock mode" -- emphasize testability
- "Full trace observability" -- emphasize debuggability

## Things to Avoid

- Do not spend time on setup or installation
- Do not deep-dive into code unless asked
- Do not apologize for mock data -- frame it as "deterministic demo mode"
- Do not click around aimlessly -- every action should have a narration
