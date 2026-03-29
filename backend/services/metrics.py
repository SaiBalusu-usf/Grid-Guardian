"""In-memory agent and tool performance metrics collection.

Provides lightweight counters for agent runs and tool calls, plus
aggregated stats for the /api/metrics endpoint.  All data is in-memory
only -- it resets on server restart.
"""

import logging
import time
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal counters
# ---------------------------------------------------------------------------

_start_time: float = time.time()

_agent_runs: dict[str, dict[str, Any]] = defaultdict(lambda: {
    "count": 0,
    "errors": 0,
    "total_duration_ms": 0.0,
    "total_tokens": 0,
})

_tool_calls: dict[str, dict[str, Any]] = defaultdict(lambda: {
    "count": 0,
    "total_duration_ms": 0.0,
})

_incident_count: int = 0
_incident_completed: int = 0
_incident_failed: int = 0


# ---------------------------------------------------------------------------
# Recording functions
# ---------------------------------------------------------------------------

def record_agent_run(
    agent_name: str,
    duration_ms: float = 0.0,
    tokens: int = 0,
    error: bool = False,
) -> None:
    """Record a single agent run.

    Args:
        agent_name: Name of the agent that ran.
        duration_ms: Wall-clock duration in milliseconds.
        tokens: Estimated token usage (input + output).
        error: Whether the run ended in error.
    """
    entry = _agent_runs[agent_name]
    entry["count"] += 1
    entry["total_duration_ms"] += duration_ms
    entry["total_tokens"] += tokens
    if error:
        entry["errors"] += 1


def record_tool_call(
    tool_name: str,
    duration_ms: float = 0.0,
) -> None:
    """Record a single tool invocation.

    Args:
        tool_name: Name of the tool that was called.
        duration_ms: Wall-clock duration in milliseconds.
    """
    entry = _tool_calls[tool_name]
    entry["count"] += 1
    entry["total_duration_ms"] += duration_ms


def record_incident(completed: bool = True) -> None:
    """Record an incident lifecycle event.

    Args:
        completed: True if the incident completed successfully, False if it failed.
    """
    global _incident_count, _incident_completed, _incident_failed
    _incident_count += 1
    if completed:
        _incident_completed += 1
    else:
        _incident_failed += 1


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

def get_metrics() -> dict[str, Any]:
    """Return current metrics snapshot.

    Returns:
        Dict with agents, tools, incidents stats, and uptime.
    """
    uptime_seconds = round(time.time() - _start_time, 2)

    agents = {}
    for name, data in _agent_runs.items():
        count = data["count"]
        agents[name] = {
            "count": count,
            "errors": data["errors"],
            "total_duration_ms": round(data["total_duration_ms"], 2),
            "avg_duration_ms": round(data["total_duration_ms"] / count, 2) if count else 0,
            "total_tokens": data["total_tokens"],
        }

    tools = {}
    for name, data in _tool_calls.items():
        count = data["count"]
        tools[name] = {
            "count": count,
            "total_duration_ms": round(data["total_duration_ms"], 2),
            "avg_duration_ms": round(data["total_duration_ms"] / count, 2) if count else 0,
        }

    return {
        "uptime_seconds": uptime_seconds,
        "agents": agents,
        "tools": tools,
        "incidents": {
            "total": _incident_count,
            "completed": _incident_completed,
            "failed": _incident_failed,
        },
    }
