"""Alert model for public notifications during disaster response."""

from uuid import uuid4

from pydantic import BaseModel, Field


class Alert(BaseModel):
    """A public alert or notification message, potentially bilingual."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    message: str
    language: str = "en"
    severity: str = "high"
    region: str = ""
    status: str = "draft"  # draft/sent/acknowledged
    sent_at: str | None = None
