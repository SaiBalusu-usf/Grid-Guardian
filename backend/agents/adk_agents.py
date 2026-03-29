"""GridGuardian v2 agent hierarchy built with Google ADK primitives.

Defines the full multi-agent pipeline:
  parallel_specialists  (ParallelAgent)
    hazard_watcher_agent
    vulnerability_mapper_agent
    route_planner_agent
    resource_coordinator_agent
  planner_agent          (LlmAgent)
  audit_loop             (LoopAgent)
    audit_agent
  public_alert_agent     (LlmAgent)
  gridguardian_agent     (SequentialAgent - root)
"""

from google.adk.agents import LlmAgent, ParallelAgent, LoopAgent, SequentialAgent

from backend.agents.adk_tools import (
    HAZARD_WATCHER_TOOLS,
    ROUTE_PLANNER_TOOLS,
    RESOURCE_TOOLS,
    ALERT_TOOLS,
)

MODEL = "gemini-2.5-flash"

# ─────────────────────────────────────────────────────────────────────────────
# 1. Specialist agents (run in parallel)
# ─────────────────────────────────────────────────────────────────────────────

hazard_watcher_agent = LlmAgent(
    name="hazard_watcher_agent",
    model=MODEL,
    instruction=(
        "You are the Hazard Watcher for the Tampa, FL metropolitan area. "
        "Your job is to gather the latest weather conditions, active hazard zones, "
        "and breaking news related to disasters in the Tampa Bay region.\n\n"
        "Use all three of your tools:\n"
        "  1. get_weather - call with location='Tampa, FL'\n"
        "  2. get_hazard_zones - call with region='Tampa Bay, FL'\n"
        "  3. get_news_feed - call with query='Tampa FL disaster emergency'\n\n"
        "After gathering data, produce a JSON object with this structure:\n"
        "{\n"
        '  "weather": { ... weather tool result ... },\n'
        '  "hazard_zones": { ... hazard tool result ... },\n'
        '  "news": { ... news tool result ... },\n'
        '  "summary": "One-paragraph situational summary for Tampa Bay",\n'
        '  "overall_severity": "low | medium | high | critical"\n'
        "}"
    ),
    tools=HAZARD_WATCHER_TOOLS,
    output_key="hazard_output",
)

vulnerability_mapper_agent = LlmAgent(
    name="vulnerability_mapper_agent",
    model=MODEL,
    instruction=(
        "You are the Vulnerability Mapper for Tampa, FL. "
        "Using the hazard data available in session state (key: 'hazard_output'), "
        "identify the most vulnerable populations and infrastructure in the affected zones.\n\n"
        "Consider Tampa-specific factors:\n"
        "  - Flood-prone areas along the Hillsborough River and Bayshore Boulevard\n"
        "  - Mobile home communities in Hillsborough and Pinellas counties\n"
        "  - Elderly populations in assisted-living facilities\n"
        "  - Hospital and school proximity to hazard zones\n"
        "  - Low-income neighborhoods with limited transportation\n\n"
        "Produce a JSON object with this structure:\n"
        "{\n"
        '  "vulnerable_populations": [\n'
        '    {"group": "...", "estimated_count": N, "location": "...", "risk_level": "..."}\n'
        "  ],\n"
        '  "critical_infrastructure": [\n'
        '    {"name": "...", "type": "hospital|school|shelter|utility", "status": "...", "at_risk": true|false}\n'
        "  ],\n"
        '  "priority_zones": ["zone_id_1", "zone_id_2"],\n'
        '  "summary": "One-paragraph vulnerability assessment"\n'
        "}"
    ),
    output_key="vulnerability_output",
)

route_planner_agent = LlmAgent(
    name="route_planner_agent",
    model=MODEL,
    instruction=(
        "You are the Route Planner for Tampa, FL emergency operations. "
        "Plan safe evacuation and supply-delivery routes that avoid active hazard zones.\n\n"
        "Use your get_routes tool to find routes between key Tampa locations:\n"
        "  - Emergency Operations Center (origin)\n"
        "  - Affected zones identified in session state\n"
        "  - Tampa General Hospital, MacDill AFB, shelters\n\n"
        "Call get_routes at least once, e.g.:\n"
        "  get_routes(origin='Emergency Operations Center', "
        "destination='Zone A - Riverside District', avoid_zones=['Z-001','Z-002'])\n\n"
        "Produce a JSON object with this structure:\n"
        "{\n"
        '  "evacuation_routes": [ ... route objects ... ],\n'
        '  "supply_routes": [ ... route objects ... ],\n'
        '  "blocked_roads": ["road1", "road2"],\n'
        '  "recommended_primary_route": "route_id",\n'
        '  "summary": "One-paragraph routing assessment for Tampa Bay"\n'
        "}"
    ),
    tools=ROUTE_PLANNER_TOOLS,
    output_key="route_output",
)

resource_coordinator_agent = LlmAgent(
    name="resource_coordinator_agent",
    model=MODEL,
    instruction=(
        "You are the Resource Coordinator for Tampa, FL disaster response. "
        "Track and allocate emergency resources across the Tampa Bay area.\n\n"
        "You may use query_collection to look up resource inventories in Firestore, e.g.:\n"
        "  query_collection(collection='resources', filters={'region': 'tampa_bay'})\n\n"
        "Based on the hazard and vulnerability data in session state, recommend "
        "resource allocation for:\n"
        "  - Search & rescue teams\n"
        "  - Medical supplies and ambulances\n"
        "  - Temporary shelters (use Tampa Convention Center, USF Sun Dome, etc.)\n"
        "  - Water, food, generators\n"
        "  - National Guard units if severity is critical\n\n"
        "Produce a JSON object with this structure:\n"
        "{\n"
        '  "allocations": [\n'
        '    {"resource": "...", "quantity": N, "destination": "...", "priority": "high|medium|low"}\n'
        "  ],\n"
        '  "shortages": ["resource1", "resource2"],\n'
        '  "mutual_aid_needed": true|false,\n'
        '  "summary": "One-paragraph resource assessment"\n'
        "}"
    ),
    tools=RESOURCE_TOOLS,
    output_key="resource_output",
)

# ─────────────────────────────────────────────────────────────────────────────
# 5. Parallel Specialists
# ─────────────────────────────────────────────────────────────────────────────

parallel_specialists = ParallelAgent(
    name="parallel_specialists",
    sub_agents=[
        hazard_watcher_agent,
        vulnerability_mapper_agent,
        route_planner_agent,
        resource_coordinator_agent,
    ],
)

# ─────────────────────────────────────────────────────────────────────────────
# 6. Planner Agent
# ─────────────────────────────────────────────────────────────────────────────

planner_agent = LlmAgent(
    name="planner_agent",
    model=MODEL,
    instruction=(
        "You are the Master Planner for Tampa, FL disaster response. "
        "Synthesize all specialist outputs from session state into a unified "
        "Disaster Response Plan.\n\n"
        "Read from session state keys:\n"
        "  - hazard_output: current hazard situation\n"
        "  - vulnerability_output: vulnerable populations and infrastructure\n"
        "  - route_output: evacuation and supply routes\n"
        "  - resource_output: resource allocations\n\n"
        "Produce a JSON object with this structure:\n"
        "{\n"
        '  "plan_id": "DRP-TAMPA-<timestamp>",\n'
        '  "incident_type": "...",\n'
        '  "severity": "low | medium | high | critical",\n'
        '  "phases": [\n'
        '    {\n'
        '      "phase": "immediate | short_term | recovery",\n'
        '      "actions": ["action1", "action2"],\n'
        '      "responsible_agency": "...",\n'
        '      "timeline_hours": N\n'
        "    }\n"
        "  ],\n"
        '  "evacuation_order": {"zones": [...], "shelter_locations": [...]},\n'
        '  "resource_deployment": [ ... ],\n'
        '  "communication_plan": "...",\n'
        '  "summary": "Executive summary of the disaster response plan"\n'
        "}"
    ),
    output_key="plan",
)

# ─────────────────────────────────────────────────────────────────────────────
# 7-8. Audit Agent + Loop
# ─────────────────────────────────────────────────────────────────────────────

audit_agent = LlmAgent(
    name="audit_agent",
    model=MODEL,
    instruction=(
        "You are the Audit Agent for Tampa, FL disaster response plans. "
        "Review the disaster response plan in session state (key: 'plan') "
        "for completeness, feasibility, and safety.\n\n"
        "Check for:\n"
        "  1. All critical hazard zones addressed\n"
        "  2. Vulnerable populations accounted for (elderly, disabled, non-English speakers)\n"
        "  3. Evacuation routes avoid active hazard zones\n"
        "  4. Resource quantities are realistic for Tampa Bay population\n"
        "  5. Communication plan covers multiple channels (EAS, SMS, social media)\n"
        "  6. Timeline is feasible given current conditions\n"
        "  7. Mutual aid agreements activated if severity >= high\n\n"
        "Produce a JSON object with this structure:\n"
        "{\n"
        '  "approved": true|false,\n'
        '  "score": 0-100,\n'
        '  "findings": [\n'
        '    {"issue": "...", "severity": "critical|major|minor", "recommendation": "..."}\n'
        "  ],\n"
        '  "missing_elements": ["element1", "element2"],\n'
        '  "summary": "One-paragraph audit conclusion"\n'
        "}"
    ),
    output_key="audit_result",
)

audit_loop = LoopAgent(
    name="audit_loop",
    sub_agents=[audit_agent],
    max_iterations=2,
)

# ─────────────────────────────────────────────────────────────────────────────
# 9. Public Alert Agent
# ─────────────────────────────────────────────────────────────────────────────

public_alert_agent = LlmAgent(
    name="public_alert_agent",
    model=MODEL,
    instruction=(
        "You are the Public Alert Agent for Tampa, FL. "
        "Using the approved disaster response plan (key: 'plan') and audit results "
        "(key: 'audit_result') from session state, compose and send public alerts.\n\n"
        "Use the send_notification tool to dispatch alerts. Send at least:\n"
        "  1. A critical broadcast alert via 'broadcast' channel for immediate dangers\n"
        "  2. An SMS alert for evacuation zones with severity='critical'\n"
        "  3. An info-level notification summarizing shelter locations\n\n"
        "Produce a JSON object with this structure:\n"
        "{\n"
        '  "alerts_sent": [\n'
        '    {"channel": "broadcast|sms|email|push", "severity": "...", "recipient_count": N, "notification_id": "..."}\n'
        "  ],\n"
        '  "total_recipients_reached": N,\n'
        '  "channels_used": ["broadcast", "sms", "push"],\n'
        '  "summary": "One-paragraph summary of all alerts dispatched for Tampa Bay"\n'
        "}"
    ),
    tools=ALERT_TOOLS,
    output_key="alerts",
)

# ─────────────────────────────────────────────────────────────────────────────
# 10. Root orchestrator
# ─────────────────────────────────────────────────────────────────────────────

gridguardian_agent = SequentialAgent(
    name="gridguardian_agent",
    sub_agents=[
        parallel_specialists,
        planner_agent,
        audit_loop,
        public_alert_agent,
    ],
)
