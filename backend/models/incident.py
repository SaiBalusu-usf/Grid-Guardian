"""Incident model representing a disaster event being managed by GridGuardian."""

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

INCIDENT_STATUSES = ("initiated", "analyzing", "planning", "auditing", "executing", "completed", "failed", "cancelled")
SEVERITIES = ("unknown", "low", "medium", "high", "critical")


class Incident(BaseModel):
    """A disaster incident tracked through the full response lifecycle."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    scenario: str
    trigger_source: str = "simulation"
    started_at: str = Field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())
    severity: str = "unknown"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    impacted_zones: list[str] = []
    status: str = "initiated"
    final_plan: dict | None = None
