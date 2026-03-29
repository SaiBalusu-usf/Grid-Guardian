"""Resource model for tracking physical assets deployed during incident response."""

from uuid import uuid4

from pydantic import BaseModel, Field


class Resource(BaseModel):
    """A physical resource (crew, equipment, supply) assigned to incident response."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    resource_type: str  # crew/generator/battery/supply_kit/medical
    quantity: int = 1
    location: str = ""
    status: str = "available"  # available/deployed/exhausted/reserved
    assigned_task_id: str | None = None
