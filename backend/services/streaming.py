"""SSE streaming service for real-time event broadcasting to connected clients."""

import asyncio
import json
import logging
from typing import AsyncGenerator

from backend.config import settings

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL = 15  # seconds — keeps Cloud Run / proxies from killing the connection

# Valid event types
EVENT_TYPES = frozenset({
    "incident_update",
    "agent_status",
    "task_update",
    "alert_update",
    "trace_event",
    "plan_update",
    "heartbeat",
})


class StreamManager:
    """Manages SSE client subscriptions and event broadcasting.

    Each subscriber gets its own asyncio.Queue. Broadcasting pushes the event
    into every active queue. Disconnected clients are cleaned up automatically.
    """

    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue] = []
        self._lock = asyncio.Lock()

    async def subscribe(self) -> AsyncGenerator[dict, None]:
        """Yield SSE-formatted events for a single client connection.

        Sends an immediate heartbeat on connect, then periodic heartbeats
        to keep the connection alive through Cloud Run / reverse proxies.
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=256)
        async with self._lock:
            self._subscribers.append(queue)
        logger.info("SSE client connected (total=%d)", len(self._subscribers))

        # Send immediate connection event so Cloud Run returns headers
        yield {
            "event": "heartbeat",
            "data": json.dumps({"status": "connected", "interval": HEARTBEAT_INTERVAL}),
        }

        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_INTERVAL)
                    yield event
                except asyncio.TimeoutError:
                    # Send periodic heartbeat to keep connection alive
                    yield {
                        "event": "heartbeat",
                        "data": json.dumps({"status": "alive"}),
                    }
        except asyncio.CancelledError:
            pass
        finally:
            async with self._lock:
                if queue in self._subscribers:
                    self._subscribers.remove(queue)
            logger.info("SSE client disconnected (total=%d)", len(self._subscribers))

    async def broadcast(self, event_type: str, data: dict) -> None:
        """Push an event to all connected subscribers.

        Args:
            event_type: One of the EVENT_TYPES constants.
            data: JSON-serializable event payload.
        """
        if not settings.is_sse_enabled:
            return

        message = {
            "event": event_type,
            "data": json.dumps(data, default=str),
        }

        dead_queues: list[asyncio.Queue] = []

        async with self._lock:
            for queue in self._subscribers:
                try:
                    queue.put_nowait(message)
                except asyncio.QueueFull:
                    logger.warning("SSE subscriber queue full, dropping client")
                    dead_queues.append(queue)

            for dq in dead_queues:
                self._subscribers.remove(dq)

        if self._subscribers:
            logger.debug(
                "Broadcast %s to %d subscribers", event_type, len(self._subscribers)
            )


# Module-level singleton used by the application
stream_manager = StreamManager()
