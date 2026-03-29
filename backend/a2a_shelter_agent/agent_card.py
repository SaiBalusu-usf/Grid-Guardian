"""A2A Agent Card for the Shelter Specialist agent."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

AGENT_CARD: dict[str, Any] = {
    "name": "Shelter Specialist",
    "description": (
        "Analyzes shelter capacity, accessibility, and supply availability "
        "for disaster response coordination."
    ),
    "version": "1.0.0",
    "protocol": "a2a",
    "capabilities": [
        "shelter_capacity_analysis",
        "accessibility_assessment",
        "supply_inventory",
        "evacuation_recommendations",
    ],
    "endpoint": "/a2a/execute",
    "health_endpoint": "/health",
    "input_schema": {
        "type": "object",
        "properties": {
            "zone": {
                "type": "string",
                "description": "Geographic zone to focus on",
            },
            "accessibility_required": {
                "type": "string",
                "enum": ["standard", "wheelchair", "full_ada"],
                "description": "Minimum accessibility level required",
            },
            "capacity_needed": {
                "type": "integer",
                "description": "Minimum aggregate capacity needed",
            },
            "scenario": {
                "type": "string",
                "description": "Disaster scenario context (e.g. 'hurricane', 'earthquake')",
            },
        },
        "additionalProperties": False,
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "shelters": {
                "type": "array",
                "description": "Enriched shelter records sorted by score",
            },
            "total_available_capacity": {
                "type": "integer",
                "description": "Sum of available beds across all matching shelters",
            },
            "critical_shelters": {
                "type": "array",
                "description": "Shelters at or above 80% occupancy",
            },
            "supply_warnings": {
                "type": "array",
                "description": "Human-readable supply warnings with shelter context",
            },
            "recommendations": {
                "type": "array",
                "description": "Actionable recommendations for emergency coordinators",
            },
            "accessibility_summary": {
                "type": "object",
                "description": "Count of shelters by accessibility tier",
            },
        },
        "required": [
            "shelters",
            "total_available_capacity",
            "critical_shelters",
            "supply_warnings",
            "recommendations",
            "accessibility_summary",
        ],
    },
}

# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

_VALID_ACCESSIBILITY = {"standard", "wheelchair", "full_ada"}


def get_agent_card() -> dict[str, Any]:
    """Return a deep copy of the agent card so callers cannot mutate the original."""
    return deepcopy(AGENT_CARD)


class AgentCardValidationError(Exception):
    """Raised when an incoming query fails validation against the input schema."""


def validate_query(query: dict | None) -> dict:
    """Validate and normalise an incoming query dict against the input schema.

    Returns the cleaned query dict.
    Raises ``AgentCardValidationError`` on invalid input.
    """
    if query is None:
        return {}

    if not isinstance(query, dict):
        raise AgentCardValidationError(
            f"Query must be a JSON object, got {type(query).__name__}"
        )

    cleaned: dict[str, Any] = {}

    # zone
    zone = query.get("zone")
    if zone is not None:
        if not isinstance(zone, str):
            raise AgentCardValidationError("'zone' must be a string")
        cleaned["zone"] = zone.strip()

    # accessibility_required
    acc = query.get("accessibility_required")
    if acc is not None:
        if not isinstance(acc, str) or acc not in _VALID_ACCESSIBILITY:
            raise AgentCardValidationError(
                f"'accessibility_required' must be one of {sorted(_VALID_ACCESSIBILITY)}"
            )
        cleaned["accessibility_required"] = acc

    # capacity_needed
    cap = query.get("capacity_needed")
    if cap is not None:
        if isinstance(cap, bool) or not isinstance(cap, (int, float)):
            raise AgentCardValidationError("'capacity_needed' must be an integer")
        cap = int(cap)
        if cap < 0:
            raise AgentCardValidationError("'capacity_needed' must be non-negative")
        cleaned["capacity_needed"] = cap

    # scenario
    scenario = query.get("scenario")
    if scenario is not None:
        if not isinstance(scenario, str):
            raise AgentCardValidationError("'scenario' must be a string")
        cleaned["scenario"] = scenario.strip()

    # Reject unknown keys
    allowed = {"zone", "accessibility_required", "capacity_needed", "scenario"}
    unknown = set(query.keys()) - allowed
    if unknown:
        raise AgentCardValidationError(f"Unknown query fields: {sorted(unknown)}")

    return cleaned
