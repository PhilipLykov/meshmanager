"""Schemas for node data."""

from datetime import datetime

from pydantic import BaseModel


class NodeResponse(BaseModel):
    """Response schema for a node."""

    id: str
    source_id: str
    source_name: str | None = None

    # Node identification
    node_num: int
    node_id: str | None = None
    short_name: str | None = None
    long_name: str | None = None
    hw_model: str | None = None
    role: str | None = None

    # Position
    latitude: float | None = None
    longitude: float | None = None
    altitude: int | None = None
    position_time: datetime | None = None
    position_precision_bits: int | None = None

    # Status
    last_heard: datetime | None = None
    is_licensed: bool = False

    # Timestamps
    first_seen: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NodeSummary(BaseModel):
    """Summary of a node for list views."""

    id: str
    source_id: str
    source_name: str | None = None
    node_num: int
    node_id: str | None = None
    short_name: str | None = None
    long_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    last_heard: datetime | None = None

    model_config = {"from_attributes": True}
