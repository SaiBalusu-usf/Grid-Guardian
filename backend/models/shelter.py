"""Shelter model representing emergency shelter facilities."""

from uuid import uuid4

from pydantic import BaseModel, Field


class Shelter(BaseModel):
    """An emergency shelter with capacity, occupancy, and supply tracking."""

    shelter_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    capacity: int
    occupancy: int = 0
    accessibility: str = "standard"  # standard/wheelchair/full_ada
    supplies: dict = {}  # e.g. {"water_gallons": 500, "cots": 200, "first_aid_kits": 50}
