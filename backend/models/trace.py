"""TraceEvent model for the incident event timeline."""

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class TraceEvent(BaseModel):
    """A single event in the incident trace timeline.

    Event types:
        trigger, agent_start, agent_end, tool_call, audit,
        a2a_request, a2a_response, plan_draft, plan_final, action
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    event_type: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    payload: dict = {}
