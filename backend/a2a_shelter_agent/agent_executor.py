"""A2A Agent Executor for the Shelter Specialist."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from agent import analyze_shelters
from agent_card import AgentCardValidationError, validate_query

logger = logging.getLogger("shelter_agent.executor")


class ShelterAgentExecutor:
    """Executes shelter specialist tasks following the A2A protocol."""

    def __init__(self) -> None:
        self._tasks: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute a task received from an A2A orchestrator.

        Args:
            task: A2A task envelope. Expected shape::

                {
                    "task_id": "<optional-client-supplied-id>",
                    "message": {
                        "role": "user",
                        "content": { ...query parameters... }
                    }
                }

        Returns:
            A2A task result dict with ``task_id``, ``status``, ``result``,
            ``agent``, and timing metadata.
        """
        task_id = task.get("task_id") or str(uuid.uuid4())
        start = time.monotonic()

        # Mark task as running
        self._tasks[task_id] = {
            "task_id": task_id,
            "status": "running",
            "agent": "shelter_specialist",
            "created_at": time.time(),
        }

        try:
            # ---- Extract query from A2A message ----
            message = task.get("message")
            if message is None:
                raise ValueError("Task must contain a 'message' field")

            # The content can be the query dict directly, or wrapped in a
            # message envelope with role/content.
            if isinstance(message, dict) and "content" in message:
                raw_query = message["content"]
            else:
                raw_query = message

            # If the content arrived as a string, treat it as a scenario description.
            if isinstance(raw_query, str):
                raw_query = {"scenario": raw_query}

            # ---- Validate ----
            query = validate_query(raw_query)

            # ---- Execute core logic ----
            analysis = await analyze_shelters(query)

            elapsed_ms = round((time.monotonic() - start) * 1000, 2)

            result = {
                "task_id": task_id,
                "status": "completed",
                "result": analysis,
                "agent": "shelter_specialist",
                "metadata": {
                    "execution_time_ms": elapsed_ms,
                    "query": query,
                    "shelters_evaluated": len(analysis.get("shelters", [])),
                },
            }
            self._tasks[task_id] = result
            logger.info("Task %s completed in %.1f ms", task_id, elapsed_ms)
            return result

        except AgentCardValidationError as exc:
            return self._fail(task_id, start, "validation_error", str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Task %s failed", task_id)
            return self._fail(task_id, start, "error", str(exc))

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        """Retrieve a stored task result by ID."""
        return self._tasks.get(task_id)

    def list_tasks(self) -> list[dict[str, Any]]:
        """Return all stored task results (most recent first)."""
        return sorted(
            self._tasks.values(),
            key=lambda t: t.get("metadata", {}).get("execution_time_ms", 0),
            reverse=True,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fail(
        self, task_id: str, start: float, status: str, detail: str
    ) -> dict[str, Any]:
        elapsed_ms = round((time.monotonic() - start) * 1000, 2)
        result = {
            "task_id": task_id,
            "status": status,
            "error": detail,
            "agent": "shelter_specialist",
            "metadata": {"execution_time_ms": elapsed_ms},
        }
        self._tasks[task_id] = result
        return result
