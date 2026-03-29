"""AgentRun model tracking individual agent executions within an incident."""

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class AgentRun(BaseModel):
    """Record of a single agent execution, including inputs, outputs, and tool calls."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    agent_name: str
    start_time: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    end_time: str | None = None
    input: dict = {}
    output: dict = {}
    tool_calls: list[dict] = []
    retry_count: int = 0
    error: str | None = None
