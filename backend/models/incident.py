"""Incident model representing a disaster event being managed by GridGuardian."""

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class Incident(BaseModel):
    """A disaster incident tracked through the full response lifecycle."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    scenario: str
    trigger_source: str = "simulation"
    started_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    severity: str = "unknown"  # low/medium/high/critical
    confidence: float = 0.0
    impacted_zones: list[str] = []
    status: str = "initiated"  # initiated/analyzing/planning/auditing/executing/completed/failed
    final_plan: dict | None = None
