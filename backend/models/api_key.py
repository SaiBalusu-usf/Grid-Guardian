"""API key model for role-based authentication."""

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class ApiKey(BaseModel):
    """An API key with role-based access control."""

    key_id: str = Field(default_factory=lambda: str(uuid4()))
    key_hash: str = ""
    role: Literal["viewer", "operator", "admin"] = "viewer"
    label: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())
    last_used_at: str | None = None
    active: bool = True
