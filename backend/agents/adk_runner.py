"""ADK Runner integration for GridGuardian multi-agent workflow.

Provides run_adk_workflow() which attempts to execute the full incident
response pipeline using Google ADK's Runner with the gridguardian_agent
SequentialAgent.  Returns None if ADK is unavailable (no API key, import
error, runtime error), allowing the caller to fall back to the legacy
orchestrator path.
"""

import logging
from typing import Any

from backend.config import settings
from backend.services.streaming import StreamManager

logger = logging.getLogger(__name__)


async def run_adk_workflow(
    scenario: dict[str, Any],
    incident_id: str,
    stream_manager: StreamManager,
) -> dict[str, Any] | None:
    """Execute the full GridGuardian pipeline via ADK Runner.

    Args:
        scenario: Dict with at least "scenario" (str) and optionally
            "trigger_source", "location", "region".
        incident_id: Pre-created incident ID in Firestore.
        stream_manager: SSE broadcast manager.

    Returns:
        Dict with keys hazard_output, vulnerability_output, route_output,
        resource_output, plan, audit_result, alerts extracted from ADK
        session state -- or None if ADK is unavailable / fails (triggers
        legacy fallback).
    """
    # ------------------------------------------------------------------
    # Guard: no API key means we cannot run ADK agents
    # ------------------------------------------------------------------
    if settings.is_mock or not settings.GEMINI_API_KEY:
        logger.info("GEMINI_API_KEY not set -- skipping ADK runner, will use legacy path")
        return None

    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types

        from backend.agents.adk_agents import gridguardian_agent

        # --------------------------------------------------------------
        # 1. Session service + runner
        # --------------------------------------------------------------
        session_service = InMemorySessionService()
        runner = Runner(
            agent=gridguardian_agent,
            app_name="gridguardian",
            session_service=session_service,
        )

        # --------------------------------------------------------------
        # 2. Create a session and seed state with scenario info
        # --------------------------------------------------------------
        session = await session_service.create_session(
            app_name="gridguardian",
            user_id="system",
        )

        scenario_text = scenario.get("scenario", "Unknown scenario")
        location = scenario.get("location", "Tampa, FL")
        region = scenario.get("region", "Tampa Bay, FL")

        user_prompt = (
            f"INCIDENT ID: {incident_id}\n"
            f"SCENARIO: {scenario_text}\n"
            f"LOCATION: {location}\n"
            f"REGION: {region}\n\n"
            "Execute the full disaster response pipeline: "
            "gather hazard data, map vulnerabilities, plan routes, "
            "coordinate resources, create a unified plan, audit it, "
            "and draft public alerts."
        )

        content = types.Content(
            role="user",
            parts=[types.Part(text=user_prompt)],
        )

        # --------------------------------------------------------------
        # 3. Broadcast: ADK workflow started
        # --------------------------------------------------------------
        await stream_manager.broadcast("incident_update", {
            "incident_id": incident_id,
            "status": "analyzing",
            "engine": "adk",
        })

        # --------------------------------------------------------------
        # 4. Run the agent pipeline
        # --------------------------------------------------------------
        last_author = None
        async for event in runner.run_async(
            user_id="system",
            session_id=session.id,
            new_message=content,
        ):
            author = getattr(event, "author", None)
            if author and author != last_author:
                last_author = author
                await stream_manager.broadcast("agent_status", {
                    "incident_id": incident_id,
                    "agent": author,
                    "status": "running",
                    "engine": "adk",
                })
                logger.info("ADK agent running: %s", author)

        # --------------------------------------------------------------
        # 5. Extract results from session state
        # --------------------------------------------------------------
        updated_session = await session_service.get_session(
            app_name="gridguardian", user_id="system", session_id=session.id,
        )
        state = updated_session.state if updated_session else {}

        result_keys = [
            "hazard_output",
            "vulnerability_output",
            "route_output",
            "resource_output",
            "plan",
            "audit_result",
            "alerts",
        ]

        results: dict[str, Any] = {}
        for key in result_keys:
            value = state.get(key)
            if value is not None:
                results[key] = value

        if not results:
            logger.warning("ADK runner completed but session state is empty -- falling back")
            return None

        await stream_manager.broadcast("incident_update", {
            "incident_id": incident_id,
            "status": "adk_complete",
            "keys_populated": list(results.keys()),
        })

        logger.info(
            "ADK workflow for incident %s completed, keys: %s",
            incident_id,
            list(results.keys()),
        )
        return results

    except Exception as exc:
        logger.warning("ADK runner failed (%s) -- will use legacy fallback", exc)
        return None
